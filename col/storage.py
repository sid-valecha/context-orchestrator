"""File-based JSON persistence for context."""

import json
from pathlib import Path
from typing import Union

from pydantic import ValidationError

from .schema import Context


def load_context(path: Union[str, Path]) -> Context:
    """Load and validate a context file from disk.
    
    Args:
        path: Path to the context JSON file.
        
    Returns:
        Validated Context object.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValidationError: If the JSON does not match the Context schema.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Context.model_validate(data)


def save_context(path: Union[str, Path], context: Context) -> None:
    """Save a context object to disk as JSON.
    
    Performs atomic write by writing to a temp file first.
    
    Args:
        path: Path to save the context file.
        context: The Context object to save.
    """
    path = Path(path)
    temp_path = path.with_suffix(".tmp")
    
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(context.model_dump(), f, indent=2)
        f.write("\n")
    
    temp_path.replace(path)


def init_context(path: Union[str, Path]) -> Context:
    """Create a new context file with the default template.
    
    Args:
        path: Path where the context file will be created.
        
    Returns:
        The newly created Context object.
        
    Raises:
        FileExistsError: If the file already exists.
    """
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Context file already exists: {path}")
    
    context = Context(
        goal="",
        constraints=[],
        facts=[],
        decisions=[],
        tool_outputs=[],
        open_questions=[]
    )
    save_context(path, context)
    return context
