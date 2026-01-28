"""Groq provider - direct SDK implementation."""

import os
from datetime import datetime, timezone
from typing import Tuple

from groq import Groq

from .base import LLMProvider


class GroqProvider(LLMProvider):
    """Groq provider using the official SDK.
    
    Requires GROQ_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """Initialize the Groq provider.
        
        Args:
            model: The model identifier (e.g., 'llama-3.3-70b-versatile', 'mixtral-8x7b-32768').
        """
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self._client = Groq(api_key=api_key)
        self._model = model
    
    @property
    def name(self) -> str:
        return "groq"
    
    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, dict]:
        """Send a completion request to Groq.
        
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
