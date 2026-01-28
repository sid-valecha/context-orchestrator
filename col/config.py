"""Configuration handling - env vars and config file."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""
    
    default_provider: str = Field(default="openai", description="Default LLM provider")
    default_model: Optional[str] = Field(default=None, description="Default model for the provider")
    default_context_file: str = Field(default="context.json", description="Default context filename")
    default_output_file: str = Field(default="response.json", description="Default output filename")


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file and environment.
    
    Priority (highest to lowest):
    1. Environment variables (COL_DEFAULT_PROVIDER, etc.)
    2. Config file (if exists)
    3. Built-in defaults
    
    Args:
        config_path: Optional path to config.yaml. If None, looks in CWD.
        
    Returns:
        Config object with merged settings.
    """
    config_data = {}
    
    # Load from file if it exists
    if config_path is None:
        config_path = Path.cwd() / "col.yaml"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            file_data = yaml.safe_load(f) or {}
            config_data.update(file_data)
    
    # Override with environment variables
    env_mappings = {
        "COL_DEFAULT_PROVIDER": "default_provider",
        "COL_DEFAULT_MODEL": "default_model",
        "COL_DEFAULT_CONTEXT_FILE": "default_context_file",
        "COL_DEFAULT_OUTPUT_FILE": "default_output_file",
    }
    
    for env_var, config_key in env_mappings.items():
        value = os.environ.get(env_var)
        if value:
            config_data[config_key] = value
    
    return Config.model_validate(config_data)
