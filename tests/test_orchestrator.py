"""Unit tests for the orchestrator with mocked providers."""

import json
import pytest
from pathlib import Path
from typing import Tuple
from unittest.mock import MagicMock, patch

from col.schema import Context, ModelResponse
from col.core.orchestrator import run_completion, InvalidResponseError
from col.providers.base import LLMProvider


class MockProvider(LLMProvider):
    """A mock LLM provider for testing."""

    def __init__(self, response: str, metadata: dict = None):
        self._response = response
        self._metadata = metadata or {
            "provider": "mock",
            "model": "mock-model",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, dict]:
        return self._response, self._metadata

    @property
    def name(self) -> str:
        return "mock"


class TestRunCompletionValidResponse:
    """Tests for run_completion with valid LLM responses."""

    def test_valid_json_response(self, tmp_path):
        """Valid JSON response is parsed and returned."""
        valid_response = json.dumps({
            "answer": "Here is my answer",
            "suggested_context_updates": {
                "facts": ["new fact"],
                "decisions": [],
                "constraints": [],
                "tool_outputs": [],
                "open_questions": [],
            }
        })
        provider = MockProvider(valid_response)
        context = Context(goal="Test goal")
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            response, metadata = run_completion(context, provider, "test instruction", output_path)

        assert response.answer == "Here is my answer"
        assert response.suggested_context_updates.facts == ["new fact"]
        assert metadata["provider"] == "mock"

    def test_response_saved_to_output_path(self, tmp_path):
        """Response is saved to the specified output path."""
        valid_response = json.dumps({
            "answer": "Saved answer",
            "suggested_context_updates": {}
        })
        provider = MockProvider(valid_response)
        context = Context()
        output_path = tmp_path / "output.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            run_completion(context, provider, "test", output_path)

        assert output_path.exists()
        saved_data = json.loads(output_path.read_text())
        assert saved_data["valid"] is True
        assert saved_data["parsed"]["answer"] == "Saved answer"

    def test_minimal_response_with_defaults(self, tmp_path):
        """Response with minimal fields uses defaults for updates."""
        minimal_response = json.dumps({
            "answer": "Minimal"
        })
        provider = MockProvider(minimal_response)
        context = Context()
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            response, _ = run_completion(context, provider, "test", output_path)

        assert response.answer == "Minimal"
        assert response.suggested_context_updates.facts == []


class TestRunCompletionInvalidResponse:
    """Tests for run_completion with invalid LLM responses."""

    def test_invalid_json_raises_error(self, tmp_path):
        """Invalid JSON raises InvalidResponseError."""
        invalid_json = "This is not JSON"
        provider = MockProvider(invalid_json)
        context = Context()
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            with pytest.raises(InvalidResponseError) as exc_info:
                run_completion(context, provider, "test", output_path)

        assert "Invalid response from LLM" in str(exc_info.value)
        assert exc_info.value.output_path == output_path
        assert exc_info.value.raw_output == invalid_json

    def test_invalid_json_still_saves_raw_output(self, tmp_path):
        """Invalid JSON response is still saved for debugging."""
        invalid_json = "Not valid JSON {{"
        provider = MockProvider(invalid_json)
        context = Context()
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            with pytest.raises(InvalidResponseError):
                run_completion(context, provider, "test", output_path)

        assert output_path.exists()
        saved_data = json.loads(output_path.read_text())
        assert saved_data["valid"] is False
        assert saved_data["raw_response"] == invalid_json
        assert "error" in saved_data

    def test_schema_mismatch_raises_error(self, tmp_path):
        """JSON that doesn't match schema raises InvalidResponseError."""
        # Missing required 'answer' field
        wrong_schema = json.dumps({
            "response": "Wrong field name",
            "suggested_context_updates": {}
        })
        provider = MockProvider(wrong_schema)
        context = Context()
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            with pytest.raises(InvalidResponseError):
                run_completion(context, provider, "test", output_path)

    def test_wrong_type_in_updates_raises_error(self, tmp_path):
        """Wrong type in suggested_context_updates raises error."""
        wrong_type = json.dumps({
            "answer": "Valid answer",
            "suggested_context_updates": {
                "facts": "should be a list, not a string"
            }
        })
        provider = MockProvider(wrong_type)
        context = Context()
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            with pytest.raises(InvalidResponseError):
                run_completion(context, provider, "test", output_path)


class TestInvalidResponseError:
    """Tests for the InvalidResponseError exception."""

    def test_error_attributes(self):
        """InvalidResponseError stores raw output and path."""
        error = InvalidResponseError(
            message="Test error",
            raw_output="raw content",
            output_path=Path("/test/path.json"),
        )
        assert str(error) == "Test error"
        assert error.raw_output == "raw content"
        assert error.output_path == Path("/test/path.json")


class TestPromptBuilding:
    """Tests verifying prompt is built correctly for the provider."""

    def test_context_is_passed_to_prompt_builder(self, tmp_path):
        """Context is used to build the system prompt."""
        valid_response = json.dumps({"answer": "OK"})
        provider = MockProvider(valid_response)
        
        # Track what was passed to the provider
        calls = []
        original_complete = provider.complete
        def tracking_complete(system_prompt, user_prompt):
            calls.append((system_prompt, user_prompt))
            return original_complete(system_prompt, user_prompt)
        provider.complete = tracking_complete
        
        context = Context(
            goal="Specific test goal",
            facts=["test fact"],
        )
        output_path = tmp_path / "response.json"

        with patch("col.core.orchestrator._write_run_artifact"):
            run_completion(context, provider, "user instruction", output_path)

        assert len(calls) == 1
        system_prompt, user_prompt = calls[0]
        assert "Specific test goal" in system_prompt
        assert "test fact" in system_prompt
        assert user_prompt == "user instruction"
