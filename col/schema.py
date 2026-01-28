"""Pydantic models for Context and ModelResponse schemas."""

from typing import List
from pydantic import BaseModel, Field


class Context(BaseModel):
    """The core context schema - the product's primary abstraction.
    
    This is the ONLY source of truth. No chat history, no hidden state.
    """
    goal: str = Field(default="", description="The primary objective")
    constraints: List[str] = Field(default_factory=list, description="Hard constraints on the solution")
    facts: List[str] = Field(default_factory=list, description="Established facts about the problem")
    decisions: List[str] = Field(default_factory=list, description="Decisions that have been made")
    tool_outputs: List[str] = Field(default_factory=list, description="Results from external tools (added manually)")
    open_questions: List[str] = Field(default_factory=list, description="Unresolved questions")


class SuggestedContextUpdates(BaseModel):
    """Model-suggested updates to the context.
    
    These are SUGGESTIONS only. User must approve before they are applied.
    """
    facts: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    tool_outputs: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)


class ModelResponse(BaseModel):
    """The strict response format expected from LLMs.
    
    Models must return this exact structure. If they don't, the run fails
    and raw output is saved for user intervention.
    """
    answer: str = Field(description="The model's response to the current context")
    suggested_context_updates: SuggestedContextUpdates = Field(
        default_factory=SuggestedContextUpdates,
        description="Suggested additions to the context (user must approve)"
    )
