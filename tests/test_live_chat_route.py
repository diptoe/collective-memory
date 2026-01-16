"""
Live route integration tests for chatting with a real AI provider.

These are skipped by default to avoid cost/flakiness.

Enable with:
  CM_RUN_LIVE_AI_TESTS=true

This route currently uses the fixed model:
  gemini-3-flash-preview

So you must also provide:
  GOOGLE_API_KEY=...
"""

import os
import json
import pytest


def _truthy(value: str | None) -> bool:
    return (value or "").lower() in ("1", "true", "yes", "on")


@pytest.mark.integration
def test_live_chat_route_generates_assistant_message(api_client, factory):
    """POST /conversations/<key>/chat returns an assistant message from the real provider."""
    if not _truthy(os.getenv("CM_RUN_LIVE_AI_TESTS")):
        pytest.skip("Set CM_RUN_LIVE_AI_TESTS=true to enable live AI route tests")

    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set (required for /chat route's current fixed model)")

    persona = factory.persona

    # Create conversation
    create_resp = api_client.post(
        "/api/conversations",
        data=json.dumps({"persona_key": persona.persona_key}),
        content_type="application/json",
    )
    assert create_resp.status_code == 201
    conv_key = create_resp.get_json()["data"]["conversation_key"]

    # Call chat route (non-streaming)
    prompt = "Hi Gemini, how are you?"
    chat_resp = api_client.post(
        f"/api/conversations/{conv_key}/chat",
        data=json.dumps({"content": prompt}),
        content_type="application/json",
    )
    assert chat_resp.status_code == 201
    payload = chat_resp.get_json()
    assert payload["success"] is True

    assistant = payload["data"]["assistant_message"]
    assert assistant["role"] == "assistant"
    assert isinstance(assistant.get("content"), str)
    assert assistant["content"].strip() != ""

    # Verify conversation still exists and now has messages persisted
    get_resp = api_client.get(f"/api/conversations/{conv_key}")
    assert get_resp.status_code == 200
    conv_data = get_resp.get_json()["data"]
    assert conv_data["conversation_key"] == conv_key
    assert len(conv_data["messages"]) >= 2


