"""
Collective Memory Platform - Provider Registry

Routes model requests to appropriate providers.
"""

import logging
from typing import Dict, Optional, Type

from .base import BaseModelProvider
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .google import GoogleProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for AI model providers.

    Routes model names to appropriate provider instances.
    """

    _providers: Dict[str, BaseModelProvider] = {}
    _provider_classes: Dict[str, Type[BaseModelProvider]] = {
        'anthropic': AnthropicProvider,
        'openai': OpenAIProvider,
        'google': GoogleProvider,
    }

    @classmethod
    def get_provider(cls, model_name: str) -> BaseModelProvider:
        """
        Get the appropriate provider for a model.

        Args:
            model_name: The model identifier (e.g., 'claude-3-opus', 'gpt-4')

        Returns:
            BaseModelProvider instance

        Raises:
            ValueError: If no provider supports the model
        """
        model_lower = model_name.lower()

        # Check each provider class
        for provider_name, provider_class in cls._provider_classes.items():
            # Create temp instance to check support
            # We'll cache instances per provider type
            if provider_name not in cls._providers:
                try:
                    cls._providers[provider_name] = provider_class()
                except ValueError as e:
                    logger.warning(f"Could not initialize {provider_name}: {e}")
                    continue

            provider = cls._providers[provider_name]
            if provider.supports_model(model_name):
                return provider

        raise ValueError(
            f"No provider found for model '{model_name}'. "
            f"Supported prefixes: claude-*, gpt-*, gemini-*"
        )

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[BaseModelProvider]
    ) -> None:
        """Register a custom provider class."""
        cls._provider_classes[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseModelProvider]]:
        """List all registered provider classes."""
        return cls._provider_classes.copy()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached provider instances."""
        cls._providers.clear()


def get_provider(model_name: str) -> BaseModelProvider:
    """
    Convenience function to get provider for a model.

    Args:
        model_name: The model identifier

    Returns:
        BaseModelProvider instance
    """
    return ProviderRegistry.get_provider(model_name)
