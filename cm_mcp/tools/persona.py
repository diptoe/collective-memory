"""
Persona Tools

MCP tools for AI persona operations.
"""

import json
import mcp.types as types
from typing import Any

from .utils import _make_request


async def list_personas(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List available AI personas.

    Returns all configured personas with their roles, models, and capabilities.
    """
    try:
        result = await _make_request(config, "GET", "/personas")

        if result.get("success"):
            personas = result.get("data", {}).get("personas", [])
            if personas:
                output = f"# Available Personas ({len(personas)})\n\n"
                for p in personas:
                    output += f"## {p.get('name', 'Unknown')}\n"
                    output += f"**Role:** {p.get('role', 'N/A')}\n"
                    output += f"**Model:** {p.get('model', 'N/A')}\n"
                    output += f"**Key:** {p.get('persona_key')}\n"
                    if p.get('description'):
                        output += f"\n{p.get('description')}\n"
                    output += "\n---\n\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No personas configured.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to list personas')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing personas: {str(e)}")]


async def chat_with_persona(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Send a message to a specific persona and get a response.

    Args:
        persona_key: The persona key to chat with
        message: The message to send
        conversation_key: Optional existing conversation key (creates new if not provided)
    """
    persona_key = arguments.get("persona_key")
    message = arguments.get("message")
    conversation_key = arguments.get("conversation_key")

    if not persona_key:
        return [types.TextContent(type="text", text="Error: persona_key is required")]
    if not message:
        return [types.TextContent(type="text", text="Error: message is required")]

    try:
        # If no conversation, create one
        if not conversation_key:
            conv_result = await _make_request(
                config,
                "POST",
                "/conversations",
                json_data={
                    "persona_key": persona_key,
                    "title": f"MCP Chat - {message[:30]}...",
                }
            )
            if not conv_result.get("success"):
                return [types.TextContent(type="text", text=f"Error creating conversation: {conv_result.get('msg')}")]

            # API returns conversation data directly in 'data', not nested under 'conversation'
            conv_data = conv_result.get("data", {})
            conversation_key = conv_data.get("conversation_key")
            if not conversation_key:
                return [types.TextContent(type="text", text=f"Error: Failed to get conversation key. Response: {conv_result}")]

        # Send message and get AI response (non-streaming for MCP)
        # Uses /chat endpoint which generates AI response
        msg_result = await _make_request(
            config,
            "POST",
            f"/conversations/{conversation_key}/chat",
            json_data={"content": message}
        )

        if msg_result.get("success"):
            data = msg_result.get("data", {})
            assistant_msg = data.get("assistant_message", {})
            response = assistant_msg.get("content", "No response")
            context_info = data.get("context", {})

            output = f"## Response from Persona\n\n"
            output += f"**Conversation:** {conversation_key}\n\n"

            if context_info and context_info.get("entity_count", 0) > 0:
                output += f"*Context: {context_info.get('entity_count', 0)} entities, {context_info.get('relationship_count', 0)} relationships*\n\n"

            output += f"### Your Message\n{message}\n\n"
            output += f"### Response\n{response}\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {msg_result.get('msg', 'Failed to chat with persona')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error chatting with persona: {str(e)}")]
