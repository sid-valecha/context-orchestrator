"""Context merger - applies suggested updates with append-only semantics."""

from typing import List, Tuple

from ..schema import Context, SuggestedContextUpdates


def _dedupe_append(existing: List[str], new_items: List[str]) -> Tuple[List[str], List[str]]:
    """Append new items, deduplicating identical strings.
    
    Args:
        existing: The current list of items.
        new_items: Items to potentially add.
        
    Returns:
        Tuple of (updated_list, actually_added_items).
    """
    existing_set = set(existing)
    added = []
    result = list(existing)
    
    for item in new_items:
        if item not in existing_set:
            result.append(item)
            existing_set.add(item)
            added.append(item)
    
    return result, added


def merge_updates(
    context: Context,
    updates: SuggestedContextUpdates,
) -> Tuple[Context, dict]:
    """Apply suggested updates to a context using append-only semantics.
    
    Policy:
    - Append-only: new items are added to the end
    - Deduplication: identical strings are not added twice
    - No deletions: existing items are never removed
    - No reordering: existing order is preserved
    
    Args:
        context: The current Context object.
        updates: The suggested updates to apply.
        
    Returns:
        Tuple of (new_context, changes_summary).
        changes_summary contains what was actually added.
    """
    changes = {}
    
    # Process each field
    new_facts, added_facts = _dedupe_append(context.facts, updates.facts)
    if added_facts:
        changes["facts"] = added_facts
    
    new_decisions, added_decisions = _dedupe_append(context.decisions, updates.decisions)
    if added_decisions:
        changes["decisions"] = added_decisions
    
    new_constraints, added_constraints = _dedupe_append(context.constraints, updates.constraints)
    if added_constraints:
        changes["constraints"] = added_constraints
    
    new_tool_outputs, added_tool_outputs = _dedupe_append(context.tool_outputs, updates.tool_outputs)
    if added_tool_outputs:
        changes["tool_outputs"] = added_tool_outputs
    
    new_open_questions, added_open_questions = _dedupe_append(context.open_questions, updates.open_questions)
    if added_open_questions:
        changes["open_questions"] = added_open_questions
    
    # Create new context (goal is never updated by the model)
    new_context = Context(
        goal=context.goal,
        constraints=new_constraints,
        facts=new_facts,
        decisions=new_decisions,
        tool_outputs=new_tool_outputs,
        open_questions=new_open_questions,
    )
    
    return new_context, changes
