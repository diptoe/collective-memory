"""
Collective Memory Platform - OpenAI Provider

GPT model provider implementation.
"""

import os
import logging
from typing import AsyncGenerator, List, Optional

import openai

from .base import BaseModelProvider, StreamChunk, Message

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseModelProvider):
    """Provider for OpenAI's GPT models."""

    # Map short model names to full OpenAI model IDs
    MODEL_MAPPING = {
        # GPT-4 models
        'gpt-4': 'gpt-4',
        'gpt-4-turbo': 'gpt-4-turbo',
        'gpt-4o': 'gpt-4o',
        'gpt-3.5-turbo': 'gpt-3.5-turbo',
        # O1 models
        'o1-preview': 'o1-preview',
        'o1-mini': 'o1-mini',
        # GPT-5 models
        'gpt-5': 'gpt-5',
        'gpt-5.2': 'gpt-5.2',
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = self._validate_api_key(
            api_key or os.getenv('OPENAI_API_KEY'),
            'OPENAI_API_KEY'
        )
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    @property
    def name(self) -> str:
        return 'openai'

    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_MAPPING.keys())

    def _resolve_model(self, model: str) -> str:
        """Resolve short model name to full OpenAI model ID."""
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
        """Stream completion from GPT."""

        # Build messages list with system prompt
        openai_messages = []

        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add conversation messages
        openai_messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ])

        try:
            resolved_model = self._resolve_model(model)
            stream = await self.client.chat.completions.create(
                model=resolved_model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                stream_options={"include_usage": True},
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        done=False
                    )

                # Check for finish reason
                if chunk.choices and chunk.choices[0].finish_reason:
                    usage = None
                    if chunk.usage:
                        usage = {
                            "input_tokens": chunk.usage.prompt_tokens,
                            "output_tokens": chunk.usage.completion_tokens,
                        }
                    yield StreamChunk(
                        content="",
                        done=True,
                        finish_reason=chunk.choices[0].finish_reason,
                        usage=usage
                    )

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
