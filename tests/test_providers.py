"""
Collective Memory Platform - Provider Tests

Tests for AI model providers and model resolution.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAnthropicProvider:
    """Tests for Anthropic provider model resolution."""

    @pytest.mark.provider
    def test_claude_opus_4_5_resolution(self):
        """Test Claude Opus 4.5 model resolution."""
        from api.providers.anthropic import AnthropicProvider

        # Test all naming variations resolve to correct model ID
        expected = 'claude-opus-4-5-20251101'
        assert AnthropicProvider.MODEL_MAPPING['claude-opus-4-5'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-opus-4.5'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-4-5-opus'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-4.5-opus'] == expected

    @pytest.mark.provider
    def test_claude_sonnet_4_5_resolution(self):
        """Test Claude Sonnet 4.5 model resolution."""
        from api.providers.anthropic import AnthropicProvider

        # Test all naming variations resolve to correct model ID
        expected = 'claude-sonnet-4-5-20251101'
        assert AnthropicProvider.MODEL_MAPPING['claude-sonnet-4-5'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-sonnet-4.5'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-4-5-sonnet'] == expected
        assert AnthropicProvider.MODEL_MAPPING['claude-4.5-sonnet'] == expected

    @pytest.mark.provider
    def test_resolve_model_method(self):
        """Test _resolve_model returns correct model ID."""
        from api.providers.anthropic import AnthropicProvider

        with patch.object(AnthropicProvider, '_validate_api_key', return_value='fake-key'):
            provider = AnthropicProvider(api_key='fake-key')

            # Test resolution
            assert provider._resolve_model('claude-4.5-opus') == 'claude-opus-4-5-20251101'
            assert provider._resolve_model('claude-4.5-sonnet') == 'claude-sonnet-4-5-20251101'

            # Unknown models pass through unchanged
            assert provider._resolve_model('unknown-model') == 'unknown-model'

    @pytest.mark.provider
    def test_supports_model(self):
        """Test supports_model correctly identifies supported models."""
        from api.providers.anthropic import AnthropicProvider

        with patch.object(AnthropicProvider, '_validate_api_key', return_value='fake-key'):
            provider = AnthropicProvider(api_key='fake-key')

            # All opus 4.5 variations should be supported
            assert provider.supports_model('claude-opus-4-5')
            assert provider.supports_model('claude-4.5-opus')

            # All sonnet 4.5 variations should be supported
            assert provider.supports_model('claude-sonnet-4-5')
            assert provider.supports_model('claude-4.5-sonnet')


class TestGoogleProvider:
    """Tests for Google provider model resolution."""

    @pytest.mark.provider
    def test_gemini_3_flash_preview_resolution(self):
        """Test Gemini 3 Flash Preview model resolution."""
        from api.providers.google import GoogleProvider

        expected = 'gemini-3.0-flash-preview'
        assert GoogleProvider.MODEL_MAPPING['gemini-3-flash-preview'] == expected
        assert GoogleProvider.MODEL_MAPPING['gemini-3.0-flash-preview'] == expected

    @pytest.mark.provider
    def test_gemini_3_pro_preview_resolution(self):
        """Test Gemini 3 Pro Preview model resolution."""
        from api.providers.google import GoogleProvider

        expected = 'gemini-3.0-pro-preview'
        assert GoogleProvider.MODEL_MAPPING['gemini-3-pro-preview'] == expected
        assert GoogleProvider.MODEL_MAPPING['gemini-3.0-pro-preview'] == expected

    @pytest.mark.provider
    def test_resolve_model_method(self):
        """Test _resolve_model returns correct model ID."""
        from api.providers.google import GoogleProvider

        with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
            with patch('api.providers.google.genai'):
                with patch('api.providers.google.genai_types'):
                    provider = GoogleProvider(api_key='fake-key')

                    assert provider._resolve_model('gemini-3-flash-preview') == 'gemini-3.0-flash-preview'
                    assert provider._resolve_model('gemini-3-pro-preview') == 'gemini-3.0-pro-preview'

    @pytest.mark.provider
    def test_supports_model(self):
        """Test supports_model correctly identifies supported models."""
        from api.providers.google import GoogleProvider

        with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
            with patch('api.providers.google.genai'):
                with patch('api.providers.google.genai_types'):
                    provider = GoogleProvider(api_key='fake-key')

                    assert provider.supports_model('gemini-3-flash-preview')
                    assert provider.supports_model('gemini-3-pro-preview')
                    assert provider.supports_model('gemini-3.0-flash-preview')
                    assert provider.supports_model('gemini-3.0-pro-preview')


class TestOpenAIProvider:
    """Tests for OpenAI provider model resolution."""

    @pytest.mark.provider
    def test_gpt_5_2_resolution(self):
        """Test GPT-5.2 model resolution."""
        from api.providers.openai import OpenAIProvider

        assert OpenAIProvider.MODEL_MAPPING['gpt-5.2'] == 'gpt-5.2'
        assert OpenAIProvider.MODEL_MAPPING['gpt-5'] == 'gpt-5'

    @pytest.mark.provider
    def test_resolve_model_method(self):
        """Test _resolve_model returns correct model ID."""
        from api.providers.openai import OpenAIProvider

        with patch.object(OpenAIProvider, '_validate_api_key', return_value='fake-key'):
            provider = OpenAIProvider(api_key='fake-key')

            assert provider._resolve_model('gpt-5.2') == 'gpt-5.2'
            assert provider._resolve_model('gpt-5') == 'gpt-5'

    @pytest.mark.provider
    def test_supports_model(self):
        """Test supports_model correctly identifies supported models."""
        from api.providers.openai import OpenAIProvider

        with patch.object(OpenAIProvider, '_validate_api_key', return_value='fake-key'):
            provider = OpenAIProvider(api_key='fake-key')

            assert provider.supports_model('gpt-5.2')
            assert provider.supports_model('gpt-5')


class TestProviderRegistry:
    """Tests for provider registry model routing."""

    @pytest.mark.provider
    def test_get_provider_for_claude(self):
        """Test registry returns Anthropic provider for Claude models."""
        from api.providers.registry import ProviderRegistry
        from api.providers.anthropic import AnthropicProvider

        with patch.object(AnthropicProvider, '_validate_api_key', return_value='fake-key'):
            ProviderRegistry.clear_cache()
            provider = ProviderRegistry.get_provider('claude-4.5-opus')
            assert isinstance(provider, AnthropicProvider)

    @pytest.mark.provider
    def test_get_provider_for_gemini(self):
        """Test registry returns Google provider for Gemini models."""
        from api.providers.registry import ProviderRegistry
        from api.providers.google import GoogleProvider

        with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
            with patch('api.providers.google.genai'):
                with patch('api.providers.google.genai_types'):
                    ProviderRegistry.clear_cache()
                    provider = ProviderRegistry.get_provider('gemini-3-flash-preview')
                    assert isinstance(provider, GoogleProvider)

    @pytest.mark.provider
    def test_get_provider_for_gpt(self):
        """Test registry returns OpenAI provider for GPT models."""
        from api.providers.registry import ProviderRegistry
        from api.providers.openai import OpenAIProvider

        with patch.object(OpenAIProvider, '_validate_api_key', return_value='fake-key'):
            ProviderRegistry.clear_cache()
            provider = ProviderRegistry.get_provider('gpt-5.2')
            assert isinstance(provider, OpenAIProvider)

    @pytest.mark.provider
    def test_get_provider_unknown_raises(self):
        """Test registry raises for unknown models."""
        from api.providers.registry import ProviderRegistry

        ProviderRegistry.clear_cache()
        with pytest.raises(ValueError, match="No provider found"):
            ProviderRegistry.get_provider('unknown-model-xyz')
