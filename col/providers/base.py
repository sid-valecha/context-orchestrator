"""Base provider interface - enforces explicit request/response control."""

from abc import ABC, abstractmethod
from typing import Tuple


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    Each provider must implement direct SDK calls with explicit control
    over the request and response. No third-party wrappers.
    """
    
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, dict]:
        """Send a completion request to the LLM.
        
        Args:
            system_prompt: The system instructions (built from context).
            user_prompt: The user's current query/instruction.
            
        Returns:
            Tuple of (response_text, metadata).
            metadata includes: model, timestamp, usage info if available.
            
        Raises:
            Exception: On API errors. Caller handles retries (none in MVP).
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')."""
        pass
