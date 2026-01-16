"""
Live AI integration tests.

These tests hit real external AI APIs and are therefore:
- skipped by default (to avoid cost/flakiness)
- only enabled when explicitly requested via env vars

Enable by setting:
  CM_RUN_LIVE_AI_TESTS=true

And providing at least one API key:
  ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY

Optionally choose provider/model:
  CM_LIVE_AI_PROVIDER=anthropic|openai|google
  CM_LIVE_AI_MODEL=<model id>
"""

import os
import pytest

from api.providers.base import Message


def _truthy(value: str | None) -> bool:
    return (value or "").lower() in ("1", "true", "yes", "on")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_ai_stream_completion_smoke():
    """
    Smoke test: confirm we can stream at least some content from a real provider.

    This does NOT test our Flask routes; it tests provider + credentials + network.
    """
    if not _truthy(os.getenv("CM_RUN_LIVE_AI_TESTS")):
        pytest.skip("Set CM_RUN_LIVE_AI_TESTS=true to enable live AI tests")

    provider_choice = (os.getenv("CM_LIVE_AI_PROVIDER") or "").strip().lower()
    model_override = (os.getenv("CM_LIVE_AI_MODEL") or "").strip() or None

    provider = None
    model = None

    if provider_choice in ("", "anthropic") and os.getenv("ANTHROPIC_API_KEY"):
        from api.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        model = model_override or "claude-3-5-haiku"
    elif provider_choice in ("", "openai") and os.getenv("OPENAI_API_KEY"):
        from api.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        model = model_override or "gpt-4o-mini"
    elif provider_choice in ("", "google") and os.getenv("GOOGLE_API_KEY"):
        from api.providers.google import GoogleProvider

        provider = GoogleProvider()
        model = model_override or "gemini-2.0-flash"

    if provider is None or model is None:
        pytest.skip(
            "No usable provider configured. Set CM_LIVE_AI_PROVIDER and the matching API key "
            "(ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY)."
        )

    prompt = "Reply with a short greeting."

    chunks = []
    async for chunk in provider.stream_completion(
        messages=[Message(role="user", content=prompt)],
        model=model,
        system_prompt=None,
        max_tokens=32,
        temperature=0.0,
    ):
        if chunk.content:
            chunks.append(chunk.content)
        if chunk.done:
            break

    text = "".join(chunks).strip()
    assert text, "Expected some streamed content from the live provider"




