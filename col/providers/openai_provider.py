"""OpenAI provider - direct SDK implementation."""

import os
from datetime import datetime, timezone
from typing import Tuple

from openai import OpenAI

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI provider using the official SDK.
    
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        """Initialize the OpenAI provider.
        
        Args:
            model: The model identifier (e.g., 'gpt-4o', 'gpt-4-turbo').
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self._client = OpenAI(api_key=api_key)
        self._model = model
    
    @property
    def name(self) -> str:
        return "openai"
    
    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, dict]:
        """Send a completion request to OpenAI.
        
        Args:
            system_prompt: The system instructions.
            user_prompt: The user's query.
            
        Returns:
            Tuple of (response_text, metadata).
        """
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content or ""
        
        metadata = {
            "provider": self.name,
            "model": self._model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if response.usage:
            metadata["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return content, metadata
