"""Unit tests for Pydantic schema models."""

import pytest
from pydantic import ValidationError

from col.schema import Context, ModelResponse, SuggestedContextUpdates


class TestContext:
    """Tests for the Context model."""

    def test_empty_context(self):
        """Context can be created with all defaults."""
        ctx = Context()
        assert ctx.goal == ""
        assert ctx.constraints == []
        assert ctx.facts == []
        assert ctx.decisions == []
        assert ctx.tool_outputs == []
        assert ctx.open_questions == []

    def test_context_with_values(self):
        """Context correctly stores provided values."""
        ctx = Context(
            goal="Build a CLI tool",
            constraints=["Must be Python 3.11+"],
            facts=["Using Pydantic for validation"],
            decisions=["Use typer for CLI"],
            tool_outputs=["pip list shows typer installed"],
            open_questions=["What testing framework?"],
        )
        assert ctx.goal == "Build a CLI tool"
        assert len(ctx.constraints) == 1
        assert len(ctx.facts) == 1
        assert len(ctx.decisions) == 1
        assert len(ctx.tool_outputs) == 1
        assert len(ctx.open_questions) == 1

    def test_context_serialization_roundtrip(self):
        """Context can be serialized to dict and back."""
        original = Context(
            goal="Test goal",
            constraints=["c1", "c2"],
            facts=["f1"],
        )
        data = original.model_dump()
        restored = Context.model_validate(data)
        assert restored == original

    def test_context_json_roundtrip(self):
        """Context can be serialized to JSON and back."""
        original = Context(
            goal="JSON test",
            facts=["fact with special chars: \"quotes\" and 'apostrophes'"],
        )
        json_str = original.model_dump_json()
        restored = Context.model_validate_json(json_str)
        assert restored == original

    def test_context_rejects_invalid_goal_type(self):
        """Context rejects non-string goal."""
        with pytest.raises(ValidationError):
            Context(goal=123)

    def test_context_rejects_invalid_list_items(self):
        """Context rejects non-string items in lists."""
        with pytest.raises(ValidationError):
            Context(facts=[1, 2, 3])

    def test_context_accepts_empty_strings_in_lists(self):
        """Context accepts empty strings in lists (valid but unusual)."""
        ctx = Context(facts=["", "actual fact"])
        assert ctx.facts == ["", "actual fact"]


class TestSuggestedContextUpdates:
    """Tests for the SuggestedContextUpdates model."""

    def test_empty_updates(self):
        """Updates can be created with all defaults."""
        updates = SuggestedContextUpdates()
        assert updates.facts == []
        assert updates.decisions == []
        assert updates.constraints == []
        assert updates.tool_outputs == []
        assert updates.open_questions == []

    def test_updates_with_values(self):
        """Updates correctly store provided values."""
        updates = SuggestedContextUpdates(
            facts=["new fact"],
            decisions=["new decision"],
        )
        assert updates.facts == ["new fact"]
        assert updates.decisions == ["new decision"]
        assert updates.constraints == []

    def test_updates_serialization_roundtrip(self):
        """Updates can be serialized to dict and back."""
        original = SuggestedContextUpdates(
            facts=["f1", "f2"],
            open_questions=["q1"],
        )
        data = original.model_dump()
        restored = SuggestedContextUpdates.model_validate(data)
        assert restored == original


class TestModelResponse:
    """Tests for the ModelResponse model."""

    def test_minimal_response(self):
        """Response with just an answer (updates default to empty)."""
        response = ModelResponse(answer="Here is my answer")
        assert response.answer == "Here is my answer"
        assert response.suggested_context_updates.facts == []

    def test_response_with_updates(self):
        """Response with answer and suggested updates."""
        response = ModelResponse(
            answer="Analysis complete",
            suggested_context_updates=SuggestedContextUpdates(
                facts=["discovered fact"],
                decisions=["recommended decision"],
            ),
        )
        assert response.answer == "Analysis complete"
        assert response.suggested_context_updates.facts == ["discovered fact"]
        assert response.suggested_context_updates.decisions == ["recommended decision"]

    def test_response_rejects_missing_answer(self):
        """Response requires an answer field."""
        with pytest.raises(ValidationError):
            ModelResponse()

    def test_response_json_parsing(self):
        """Response can be parsed from JSON (simulates LLM output)."""
        json_str = '''
        {
            "answer": "This is the answer",
            "suggested_context_updates": {
                "facts": ["new fact"],
                "decisions": [],
                "constraints": [],
                "tool_outputs": [],
                "open_questions": []
            }
        }
        '''
        response = ModelResponse.model_validate_json(json_str)
        assert response.answer == "This is the answer"
        assert response.suggested_context_updates.facts == ["new fact"]

    def test_response_json_with_missing_optional_fields(self):
        """Response parsing handles missing optional update fields."""
        json_str = '''
        {
            "answer": "Minimal response",
            "suggested_context_updates": {}
        }
        '''
        response = ModelResponse.model_validate_json(json_str)
        assert response.answer == "Minimal response"
        assert response.suggested_context_updates.facts == []

    def test_response_json_with_default_updates(self):
        """Response parsing handles missing suggested_context_updates entirely."""
        json_str = '{"answer": "Just the answer"}'
        response = ModelResponse.model_validate_json(json_str)
        assert response.answer == "Just the answer"
        assert response.suggested_context_updates.facts == []

    def test_response_serialization_roundtrip(self):
        """Response can be serialized to dict and back."""
        original = ModelResponse(
            answer="Test answer",
            suggested_context_updates=SuggestedContextUpdates(
                facts=["f1"],
                decisions=["d1"],
            ),
        )
        data = original.model_dump()
        restored = ModelResponse.model_validate(data)
        assert restored == original
