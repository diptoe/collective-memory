"""
Collective Memory Platform - Anthropic Provider

Claude model provider implementation.
"""

import os
import logging
from typing import AsyncGenerator, List, Optional

import anthropic

from .base import BaseModelProvider, StreamChunk, Message

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseModelProvider):
    """Provider for Anthropic's Claude models."""

    # Map short model names to full Anthropic model IDs
    MODEL_MAPPING = {
        # Claude 3 models
        'claude-3-opus': 'claude-3-opus-20240229',
        'claude-3-sonnet': 'claude-3-sonnet-20240229',
        'claude-3-haiku': 'claude-3-haiku-20240307',
        # Claude 3.5 models
        'claude-3-5-sonnet': 'claude-3-5-sonnet-20241022',
        'claude-3.5-sonnet': 'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku': 'claude-3-5-haiku-20241022',
        'claude-3.5-haiku': 'claude-3-5-haiku-20241022',
        # Claude 4 models
        'claude-opus-4': 'claude-opus-4-20250514',
        'claude-4-opus': 'claude-opus-4-20250514',
        'claude-sonnet-4': 'claude-sonnet-4-20250514',
        'claude-4-sonnet': 'claude-sonnet-4-20250514',
        # Claude 4.5 models (various naming formats)
        'claude-opus-4-5': 'claude-opus-4-5-20251101',
        'claude-opus-4.5': 'claude-opus-4-5-20251101',
        'claude-4-5-opus': 'claude-opus-4-5-20251101',
        'claude-4.5-opus': 'claude-opus-4-5-20251101',
        'claude-sonnet-4-5': 'claude-sonnet-4-5-20251101',
        'claude-sonnet-4.5': 'claude-sonnet-4-5-20251101',
        'claude-4-5-sonnet': 'claude-sonnet-4-5-20251101',
        'claude-4.5-sonnet': 'claude-sonnet-4-5-20251101',
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = self._validate_api_key(
            api_key or os.getenv('ANTHROPIC_API_KEY'),
            'ANTHROPIC_API_KEY'
        )
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    @property
    def name(self) -> str:
        return 'anthropic'

    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_MAPPING.keys())

    def _resolve_model(self, model: str) -> str:
        """Resolve short model name to full Anthropic model ID."""
        return self.MODEL_MAPPING.get(model, model)

    async def stream_completion(
        self,
        messages: List[Message],
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream completion from Claude."""

        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role in ('user', 'assistant')
        ]

        try:
            resolved_model = self._resolve_model(model)
            async with self.client.messages.stream(
                model=resolved_model,
                messages=anthropic_messages,
                system=system_prompt or "",
                max_tokens=max_tokens,
                temperature=temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(content=text, done=False)

                # Final chunk with usage
                final_message = await stream.get_final_message()
                yield StreamChunk(
                    content="",
                    done=True,
                    finish_reason=final_message.stop_reason,
                    usage={
                        "input_tokens": final_message.usage.input_tokens,
                        "output_tokens": final_message.usage.output_tokens,
                    }
                )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
