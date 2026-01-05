"""
Collective Memory Platform - Provider Tests

Tests for AI model providers and model resolution.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


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
        """Test Gemini 3 Flash Preview model resolution (pass-through)."""
        from api.providers.google import GoogleProvider

        # Gemini 3 models pass through as-is (no .0 suffix)
        assert GoogleProvider.MODEL_MAPPING['gemini-3-flash-preview'] == 'gemini-3-flash-preview'

    @pytest.mark.provider
    def test_gemini_3_pro_preview_resolution(self):
        """Test Gemini 3 Pro Preview model resolution (pass-through)."""
        from api.providers.google import GoogleProvider

        # Gemini 3 models pass through as-is (no .0 suffix)
        assert GoogleProvider.MODEL_MAPPING['gemini-3-pro-preview'] == 'gemini-3-pro-preview'

    @pytest.mark.provider
    def test_resolve_model_method(self):
        """Test _resolve_model returns correct model ID."""
        from api.providers.google import GoogleProvider

        with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
            with patch('api.providers.google.genai'):
                with patch('api.providers.google.genai_types'):
                    provider = GoogleProvider(api_key='fake-key')

                    # Gemini 3 models pass through unchanged
                    assert provider._resolve_model('gemini-3-flash-preview') == 'gemini-3-flash-preview'
                    assert provider._resolve_model('gemini-3-pro-preview') == 'gemini-3-pro-preview'
                    # Gemini 2 models also pass through
                    assert provider._resolve_model('gemini-2.0-flash') == 'gemini-2.0-flash'

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
                    assert provider.supports_model('gemini-2.0-flash')


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


class TestGoogleProviderStreaming:
    """Tests for Google provider streaming functionality."""

    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_stream_completion_builds_correct_contents(self):
        """Test stream_completion builds contents in correct format."""
        from api.providers.google import GoogleProvider
        from api.providers.base import Message

        # Mock the genai module
        mock_genai = MagicMock()
        mock_genai_types = MagicMock()

        # Mock Part.from_text to return a mock part
        mock_part = MagicMock()
        mock_genai_types.Part.from_text.return_value = mock_part

        # Mock Content constructor
        mock_content = MagicMock()
        mock_genai_types.Content.return_value = mock_content

        # Mock GenerateContentConfig
        mock_config = MagicMock()
        mock_genai_types.GenerateContentConfig.return_value = mock_config

        # Mock the streaming response
        mock_chunk = MagicMock()
        mock_chunk.text = "Hello, world!"
        mock_response_stream = [mock_chunk]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response_stream
        mock_genai.Client.return_value = mock_client

        with patch.dict('sys.modules', {'google.genai': mock_genai, 'google.genai.types': mock_genai_types}):
            with patch('api.providers.google.genai', mock_genai):
                with patch('api.providers.google.genai_types', mock_genai_types):
                    with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
                        provider = GoogleProvider(api_key='fake-key')
                        provider.client = mock_client

                        messages = [Message(role='user', content='Hello')]

                        chunks = []
                        async for chunk in provider.stream_completion(
                            messages=messages,
                            model='gemini-3-flash-preview',
                            system_prompt='You are helpful',
                            max_tokens=1024,
                            temperature=0.7
                        ):
                            chunks.append(chunk)

                        # Verify Part.from_text was called for user message
                        mock_genai_types.Part.from_text.assert_any_call(text='Hello')

                        # Verify Content was built with user role
                        mock_genai_types.Content.assert_called()

                        # Verify config was built with stream=True
                        mock_genai_types.GenerateContentConfig.assert_called_once()
                        config_call = mock_genai_types.GenerateContentConfig.call_args
                        assert config_call.kwargs.get('stream') == True

                        # Verify we got content chunks
                        assert len(chunks) >= 1
                        assert chunks[0].content == "Hello, world!"

    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_stream_completion_handles_system_prompt(self):
        """Test stream_completion sets system_instruction correctly."""
        from api.providers.google import GoogleProvider
        from api.providers.base import Message

        mock_genai = MagicMock()
        mock_genai_types = MagicMock()
        mock_part = MagicMock()
        mock_genai_types.Part.from_text.return_value = mock_part
        mock_config = MagicMock()
        mock_genai_types.GenerateContentConfig.return_value = mock_config
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = []
        mock_genai.Client.return_value = mock_client

        with patch('api.providers.google.genai', mock_genai):
            with patch('api.providers.google.genai_types', mock_genai_types):
                with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
                    provider = GoogleProvider(api_key='fake-key')
                    provider.client = mock_client

                    messages = [Message(role='user', content='Hi')]

                    async for _ in provider.stream_completion(
                        messages=messages,
                        model='gemini-3-flash-preview',
                        system_prompt='Be helpful'
                    ):
                        pass

                    # Verify system_instruction was set as list of Parts
                    assert mock_config.system_instruction is not None

    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_stream_completion_yields_done_chunk(self):
        """Test stream_completion yields final done chunk."""
        from api.providers.google import GoogleProvider
        from api.providers.base import Message

        mock_genai = MagicMock()
        mock_genai_types = MagicMock()
        mock_genai_types.Part.from_text.return_value = MagicMock()
        mock_genai_types.GenerateContentConfig.return_value = MagicMock()

        # Empty response stream
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = []
        mock_genai.Client.return_value = mock_client

        with patch('api.providers.google.genai', mock_genai):
            with patch('api.providers.google.genai_types', mock_genai_types):
                with patch.object(GoogleProvider, '_validate_api_key', return_value='fake-key'):
                    provider = GoogleProvider(api_key='fake-key')
                    provider.client = mock_client

                    chunks = []
                    async for chunk in provider.stream_completion(
                        messages=[Message(role='user', content='Hi')],
                        model='gemini-3-flash-preview'
                    ):
                        chunks.append(chunk)

                    # Should have at least the done chunk
                    assert len(chunks) >= 1
                    assert chunks[-1].done == True
                    assert chunks[-1].finish_reason == "stop"
