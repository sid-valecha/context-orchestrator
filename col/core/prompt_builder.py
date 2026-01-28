"""Deterministic prompt builder - converts Context to system prompt.

DETERMINISM GUARANTEE:
- Same Context object → identical prompt structure every time
- Stable field ordering: goal, constraints, facts, decisions, tool_outputs, open_questions
- No timestamps, randomness, or run metadata in the prompt
- Template is static and canonical (no dynamic elements)
- List ordering is preserved (append-only semantics upstream)

This ensures model-agnostic portability: a context file created with one provider
will produce the exact same prompt structure when used with another provider.
"""

from ..schema import Context


# Static template with no dynamic elements (timestamps, randomness, metadata)
# Field order is fixed and canonical
SYSTEM_PROMPT_TEMPLATE = '''You are an assistant working within a structured context system.

## Current Context

### Goal
{goal}

### Constraints
{constraints}

### Established Facts
{facts}

### Decisions Made
{decisions}

### Tool Outputs
{tool_outputs}

### Open Questions
{open_questions}

## Your Response Format

You MUST respond with valid JSON in this exact format:

{{
  "answer": "Your response addressing the current goal/question",
  "suggested_context_updates": {{
    "facts": ["new fact 1", "new fact 2"],
    "decisions": ["new decision 1"],
    "constraints": [],
    "tool_outputs": [],
    "open_questions": ["new question if any"]
  }}
}}

Rules:
- Only suggest additions to context, never deletions
- Only include non-empty arrays for fields you want to update
- Your "answer" should directly address the goal or respond to the user
- Suggested updates are SUGGESTIONS - the user will decide whether to apply them
'''


def _format_list(items: list[str], empty_msg: str = "(none)") -> str:
    """Format a list of strings for display in the prompt."""
    if not items:
        return empty_msg
    return "\n".join(f"- {item}" for item in items)


def build_prompt(context: Context) -> str:
    """Build a deterministic system prompt from a Context object.
    
    DETERMINISTIC GUARANTEE: Same context → same prompt, always.
    - No timestamps or randomness
    - Stable field ordering
    - Consistent formatting
    
    The prompt format is consistent across all providers to ensure
    model-agnostic behavior.
    
    Args:
        context: The current Context object.
        
    Returns:
        A formatted system prompt string (deterministic).
    """
    # Fixed field order ensures determinism
    return SYSTEM_PROMPT_TEMPLATE.format(
        goal=context.goal or "(not set)",
        constraints=_format_list(context.constraints),
        facts=_format_list(context.facts),
        decisions=_format_list(context.decisions),
        tool_outputs=_format_list(context.tool_outputs),
        open_questions=_format_list(context.open_questions),
    )
