"""Orchestrator - handles the run loop (Context -> Prompt -> API -> Response)."""

import json
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
    user_prompt: str,
    output_path: Union[str, Path],
) -> Tuple[ModelResponse, dict]:
    """Execute a single completion run.
    
    This is stateless - reads context, calls API, returns result.
    Does NOT modify the context file.
    
    Args:
        context: The current Context object.
        provider: The LLM provider to use.
        user_prompt: The user's current instruction/question.
        output_path: Path to save the raw response.
        
    Returns:
        Tuple of (ModelResponse, metadata).
        
    Raises:
        InvalidResponseError: If the response is not valid JSON or doesn't
            match the expected schema. Raw output is saved to output_path.
    """
    output_path = Path(output_path)
    
    # Build the deterministic prompt
    system_prompt = build_prompt(context)
    
    # Call the provider
    raw_response, metadata = provider.complete(system_prompt, user_prompt)
    
    # Always save the raw response
    raw_data = {
        "raw_response": raw_response,
        "metadata": metadata,
    }
    
    # Try to parse and validate
    try:
        response_data = json.loads(raw_response)
        model_response = ModelResponse.model_validate(response_data)
        
        # Save validated response
        raw_data["parsed"] = model_response.model_dump()
        raw_data["valid"] = True
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)
            f.write("\n")
        
        return model_response, metadata
        
    except (json.JSONDecodeError, Exception) as e:
        # Save raw output for user intervention
        raw_data["valid"] = False
        raw_data["error"] = str(e)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)
            f.write("\n")
        
        raise InvalidResponseError(
            f"Invalid response from LLM: {e}. Raw output saved to {output_path}",
            raw_output=raw_response,
            output_path=output_path,
        )
