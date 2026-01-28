"""Orchestrator - handles the run loop (Context -> Prompt -> API -> Response).

STRICT JSON PARSING:
- No retries on parse failure
- No auto-repair attempts
- User must manually fix invalid output
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Union

from ..schema import Context, ModelResponse
from ..providers.base import LLMProvider
from .prompt_builder import build_prompt


class InvalidResponseError(Exception):
    """Raised when the LLM response is not valid JSON or doesn't match schema."""
    
    def __init__(self, message: str, raw_output: str, output_path: Path):
        super().__init__(message)
        self.raw_output = raw_output
        self.output_path = output_path


def run_completion(
    context: Context,
    provider: LLMProvider,
    instruction: str,
    output_path: Union[str, Path],
) -> Tuple[ModelResponse, dict]:
    """Execute a single completion run.
    
    This is stateless - reads context, calls API, returns result.
    Does NOT modify the context file.
    
    Writes a run artifact to .col/runs/<timestamp>.json for replayability.
    
    Args:
        context: The current Context object.
        provider: The LLM provider to use.
        instruction: Ephemeral instruction (not persisted, not stored in context).
        output_path: Path to save the raw response.
        
    Returns:
        Tuple of (ModelResponse, metadata).
        metadata includes 'prompt_hash' - the SHA256 hash of the deterministic prompt.
        
    Raises:
        InvalidResponseError: If the response is not valid JSON or doesn't
            match the expected schema. Raw output is saved to output_path.
    """
    output_path = Path(output_path)
    
    # Build the deterministic prompt (BEFORE provider invocation)
    system_prompt = build_prompt(context)
    
    # Calculate prompt hash for replayability (AFTER deterministic rendering, BEFORE invocation)
    prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
    
    # Record start time
    start_time = time.time()
    
    # Call the provider
    raw_response, metadata = provider.complete(system_prompt, instruction)
    
    # Record end time and calculate latency
    end_time = time.time()
    latency_seconds = end_time - start_time
    
    # Prepare run artifact
    timestamp = datetime.now(timezone.utc)
    artifact = {
        "timestamp": timestamp.isoformat(),
        "provider": metadata.get("provider"),
        "model": metadata.get("model"),
        "prompt_hash": prompt_hash,
        "latency_seconds": round(latency_seconds, 3),
        "token_counts": metadata.get("usage"),
        "raw_output": raw_response,
        "parsed_response": None,
        "valid": False,
        "error": None,
    }
    
    # Always save the raw response
    raw_data = {
        "raw_response": raw_response,
        "metadata": metadata,
    }
    
    # Try to parse and validate (strict, no retries, no auto-repair)
    try:
        response_data = json.loads(raw_response)
        model_response = ModelResponse.model_validate(response_data)
        
        # Save validated response
        raw_data["parsed"] = model_response.model_dump()
        raw_data["valid"] = True
        
        # Update artifact with parsed response
        artifact["parsed_response"] = model_response.model_dump()
        artifact["valid"] = True
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)
            f.write("\n")
        
        # Write run artifact (success case)
        _write_run_artifact(artifact, timestamp)
        
        # Add prompt_hash to metadata for CLI display
        metadata["prompt_hash"] = prompt_hash
        
        return model_response, metadata
        
    except (json.JSONDecodeError, Exception) as e:
        # Save raw output for user intervention
        raw_data["valid"] = False
        raw_data["error"] = str(e)
        
        # Update artifact with error
        artifact["error"] = str(e)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)
            f.write("\n")
        
        # Write run artifact (failure case)
        _write_run_artifact(artifact, timestamp)
        
        raise InvalidResponseError(
            f"Invalid response from LLM: {e}. Raw output saved to {output_path}",
            raw_output=raw_response,
            output_path=output_path,
        )


def _write_run_artifact(artifact: dict, timestamp: datetime) -> None:
    """Write a run artifact for replayability and debugging.
    
    Artifacts are stored in .col/runs/<timestamp>.json and never modify
    the context file.
    
    Args:
        artifact: The artifact data to write.
        timestamp: The timestamp for the artifact filename.
    """
    # Create .col/runs directory if it doesn't exist
    runs_dir = Path(".col/runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with filesystem-safe timestamp
    filename = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3] + ".json"
    artifact_path = runs_dir / filename
    
    # Write artifact
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)
        f.write("\n")
