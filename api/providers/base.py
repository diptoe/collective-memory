"""
Collective Memory Platform - Base Provider

Abstract base class for AI model providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Represents a chunk of streamed content."""
    content: str
    done: bool = False
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # 'user', 'assistant', 'system'
    content: str


class BaseModelProvider(ABC):
    """
    Abstract base class for AI model providers.

    Implementations must handle streaming completions for their respective APIs.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'anthropic', 'openai', 'google')."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of model prefixes this provider supports."""
        pass

    def supports_model(self, model_name: str) -> bool:
        """Check if this provider supports the given model."""
        model_lower = model_name.lower()
        return any(model_lower.startswith(prefix.lower()) for prefix in self.supported_models)

    @abstractmethod
    async def stream_completion(
        self,
        messages: List[Message],
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a completion from the model.

        Args:
            messages: Conversation history
            model: Model identifier
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific options

        Yields:
            StreamChunk objects with incremental content
        """
        pass

    async def complete(
        self,
        messages: List[Message],
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Get a complete response (non-streaming).

        Convenience method that accumulates streamed chunks.
        """
        content = ""
        async for chunk in self.stream_completion(
            messages=messages,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            content += chunk.content
        return content

    def _validate_api_key(self, key: Optional[str], env_var: str) -> str:
        """Validate that an API key is configured."""
        if not key:
            raise ValueError(
                f"{self.name} API key not configured. "
                f"Set {env_var} environment variable."
            )
        return key
