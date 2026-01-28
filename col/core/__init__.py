"""Core logic - prompt builder, orchestrator, and merger."""

from .prompt_builder import build_prompt
from .orchestrator import run_completion
from .merger import merge_updates

__all__ = ["build_prompt", "run_completion", "merge_updates"]
