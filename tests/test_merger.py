"""Unit tests for the context merger."""

import pytest

from col.schema import Context, SuggestedContextUpdates
from col.core.merger import merge_updates, _dedupe_append


class TestDedupeAppend:
    """Tests for the _dedupe_append helper function."""

    def test_append_to_empty_list(self):
        """New items are appended to an empty list."""
        result, added = _dedupe_append([], ["a", "b"])
        assert result == ["a", "b"]
        assert added == ["a", "b"]

    def test_append_new_items(self):
        """New items are appended to an existing list."""
        result, added = _dedupe_append(["a"], ["b", "c"])
        assert result == ["a", "b", "c"]
        assert added == ["b", "c"]

    def test_deduplicate_existing_items(self):
        """Existing items are not added again."""
        result, added = _dedupe_append(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]
        assert added == ["c"]

    def test_all_duplicates(self):
        """If all items exist, nothing is added."""
        result, added = _dedupe_append(["a", "b"], ["a", "b"])
        assert result == ["a", "b"]
        assert added == []

    def test_empty_new_items(self):
        """Empty new items list results in no changes."""
        result, added = _dedupe_append(["a", "b"], [])
        assert result == ["a", "b"]
        assert added == []

    def test_preserves_order(self):
        """Original order is preserved, new items appended at end."""
        result, added = _dedupe_append(["c", "a"], ["b", "d"])
        assert result == ["c", "a", "b", "d"]
        assert added == ["b", "d"]

    def test_duplicate_in_new_items(self):
        """Duplicates within new items are handled (first wins)."""
        result, added = _dedupe_append([], ["a", "a", "b"])
        assert result == ["a", "b"]
        assert added == ["a", "b"]


class TestMergeUpdates:
    """Tests for the merge_updates function."""

    def test_merge_into_empty_context(self):
        """Updates can be merged into an empty context."""
        context = Context()
        updates = SuggestedContextUpdates(
            facts=["fact1"],
            decisions=["decision1"],
        )
        new_ctx, changes = merge_updates(context, updates)
        
        assert new_ctx.facts == ["fact1"]
        assert new_ctx.decisions == ["decision1"]
        assert changes == {
            "facts": ["fact1"],
            "decisions": ["decision1"],
        }

    def test_merge_preserves_existing(self):
        """Existing context items are preserved."""
        context = Context(
            goal="Original goal",
            facts=["existing fact"],
            constraints=["existing constraint"],
        )
        updates = SuggestedContextUpdates(
            facts=["new fact"],
        )
        new_ctx, changes = merge_updates(context, updates)
        
        assert new_ctx.goal == "Original goal"
        assert new_ctx.facts == ["existing fact", "new fact"]
        assert new_ctx.constraints == ["existing constraint"]
        assert changes == {"facts": ["new fact"]}

    def test_merge_deduplicates(self):
        """Duplicate items are not added."""
        context = Context(facts=["existing fact"])
        updates = SuggestedContextUpdates(facts=["existing fact", "new fact"])
        
        new_ctx, changes = merge_updates(context, updates)
        
        assert new_ctx.facts == ["existing fact", "new fact"]
        assert changes == {"facts": ["new fact"]}

    def test_merge_empty_updates(self):
        """Empty updates result in no changes."""
        context = Context(
            goal="Goal",
            facts=["fact"],
        )
        updates = SuggestedContextUpdates()
        
        new_ctx, changes = merge_updates(context, updates)
        
        assert new_ctx == context
        assert changes == {}

    def test_merge_all_fields(self):
        """All fields can be updated simultaneously."""
        context = Context()
        updates = SuggestedContextUpdates(
            facts=["f1"],
            decisions=["d1"],
            constraints=["c1"],
            tool_outputs=["t1"],
            open_questions=["q1"],
        )
        
        new_ctx, changes = merge_updates(context, updates)
        
        assert new_ctx.facts == ["f1"]
        assert new_ctx.decisions == ["d1"]
        assert new_ctx.constraints == ["c1"]
        assert new_ctx.tool_outputs == ["t1"]
        assert new_ctx.open_questions == ["q1"]
        assert len(changes) == 5

    def test_goal_is_never_updated(self):
        """The goal field is never modified by merge."""
        context = Context(goal="Original goal")
        updates = SuggestedContextUpdates(facts=["fact"])
        
        new_ctx, _ = merge_updates(context, updates)
        
        # Goal should remain unchanged
        assert new_ctx.goal == "Original goal"

    def test_merge_returns_new_context_instance(self):
        """Merge returns a new Context, does not modify original."""
        context = Context(facts=["original"])
        updates = SuggestedContextUpdates(facts=["new"])
        
        new_ctx, _ = merge_updates(context, updates)
        
        # Original should be unchanged
        assert context.facts == ["original"]
        # New context should have both
        assert new_ctx.facts == ["original", "new"]

    def test_changes_only_includes_actually_added(self):
        """Changes dict only includes items that were actually added."""
        context = Context(
            facts=["f1", "f2"],
            decisions=["d1"],
        )
        updates = SuggestedContextUpdates(
            facts=["f2", "f3"],  # f2 exists, f3 is new
            decisions=["d1"],   # d1 exists, nothing new
            constraints=["c1"], # c1 is new
        )
        
        new_ctx, changes = merge_updates(context, updates)
        
        assert changes == {
            "facts": ["f3"],
            "constraints": ["c1"],
        }
        # decisions should not be in changes since nothing was added
        assert "decisions" not in changes
