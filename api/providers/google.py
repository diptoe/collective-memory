"""
Collective Memory Platform - Google Provider

Gemini model provider implementation.
"""

import os
import logging
from typing import AsyncGenerator, List, Optional

try:
    import google.genai as genai  # type: ignore
    from google.genai import types as genai_types  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # Keep the API usable even when the optional Google SDK isn't installed.
    # ProviderRegistry will skip initialization if we raise a ValueError in __init__.
    genai = None
    genai_types = None

from .base import BaseModelProvider, StreamChunk, Message

logger = logging.getLogger(__name__)


class GoogleProvider(BaseModelProvider):
    """Provider for Google's Gemini models."""

    # Map short model names to full Google model IDs
    MODEL_MAPPING = {
        # Gemini 1.x models
        'gemini-pro': 'gemini-1.0-pro',
        'gemini-1.5-pro': 'gemini-1.5-pro',
        'gemini-1.5-flash': 'gemini-1.5-flash',
        # Gemini 2.x models
        'gemini-2.0-flash': 'gemini-2.0-flash',
        'gemini-2.0-pro': 'gemini-2.0-pro',
        # Gemini 3.x preview models
        'gemini-3-flash-preview': 'gemini-3.0-flash-preview',
        'gemini-3-pro-preview': 'gemini-3.0-pro-preview',
        'gemini-3.0-flash-preview': 'gemini-3.0-flash-preview',
        'gemini-3.0-pro-preview': 'gemini-3.0-pro-preview',
    }

    def __init__(self, api_key: Optional[str] = None):
        if genai is None or genai_types is None:
            raise ValueError(
                "Google provider requires the 'google-genai' package. "
                "Install it with: python -m pip install google-genai"
            )
        self.api_key = self._validate_api_key(
            api_key or os.getenv('GOOGLE_API_KEY'),
            'GOOGLE_API_KEY'
        )
        self.client = genai.Client(api_key=self.api_key)

    @property
    def name(self) -> str:
        return 'google'

    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_MAPPING.keys())

    def _resolve_model(self, model: str) -> str:
        """Resolve short model name to full Google model ID."""
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
        """Stream completion from Gemini."""

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = 'user' if msg.role == 'user' else 'model'
            contents.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part(text=msg.content)]
            ))

        # Build config
        config = genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if system_prompt:
            config.system_instruction = system_prompt

        try:
            resolved_model = self._resolve_model(model)
            async for response in self.client.aio.models.generate_content_stream(
                model=resolved_model,
                contents=contents,
                config=config,
            ):
                if response.text:
                    yield StreamChunk(
                        content=response.text,
                        done=False
                    )

            # Final chunk
            yield StreamChunk(
                content="",
                done=True,
                finish_reason="stop"
            )

        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise
