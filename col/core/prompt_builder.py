"""Deterministic prompt builder - converts Context to system prompt."""

from ..schema import Context


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
    
    The prompt format is consistent across all providers to ensure
    model-agnostic behavior.
    
    Args:
        context: The current Context object.
        
    Returns:
        A formatted system prompt string.
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        goal=context.goal or "(not set)",
        constraints=_format_list(context.constraints),
        facts=_format_list(context.facts),
        decisions=_format_list(context.decisions),
        tool_outputs=_format_list(context.tool_outputs),
        open_questions=_format_list(context.open_questions),
    )
