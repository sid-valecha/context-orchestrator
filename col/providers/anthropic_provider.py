"""Anthropic provider - direct SDK implementation."""

import os
from datetime import datetime, timezone
from typing import Tuple

import anthropic

from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic provider using the official SDK.
    
    Requires ANTHROPIC_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize the Anthropic provider.
        
        Args:
            model: The model identifier (e.g., 'claude-sonnet-4-20250514').
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, dict]:
        """Send a completion request to Anthropic.
        
        Args:
            system_prompt: The system instructions.
            user_prompt: The user's query.
            
        Returns:
            Tuple of (response_text, metadata).
        """
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract text from content blocks
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        
        metadata = {
            "provider": self.name,
            "model": self._model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if response.usage:
            metadata["usage"] = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        
        return content, metadata
