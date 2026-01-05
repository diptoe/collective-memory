"""
Model and Client Tools

MCP tools for model listing, client information, and focus management
in Collective Memory (CM).
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


async def list_models(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List available AI models in the Collective Memory.

    Args:
        provider: Filter by provider (anthropic, openai, google)
        active_only: Only show active models (default True)
    """
    provider = arguments.get("provider")
    active_only = arguments.get("active_only", True)

    try:
        params = {}
        if provider:
            params["provider"] = provider
        if not active_only:
            params["include_deprecated"] = "true"

        result = await _make_request(config, "GET", "/models", params=params)

        if result.get("success"):
            models = result.get("data", {}).get("models", [])
            if models:
                # Group by provider
                by_provider = {}
                for m in models:
                    p = m.get("provider", "unknown")
                    if p not in by_provider:
                        by_provider[p] = []
                    by_provider[p].append(m)

                # Mark current model
                current_model_key = session_state.get("model_key")

                output = f"## Available AI Models ({len(models)})\n\n"

                for provider, provider_models in by_provider.items():
                    output += f"### {provider.title()}\n\n"
                    for m in provider_models:
                        is_current = m.get("model_key") == current_model_key
                        marker = " ← (current)" if is_current else ""
                        status_icon = "🟢" if m.get("status") == "active" else "⚪"

                        output += f"{status_icon} **{m.get('name')}**{marker}\n"
                        output += f"   Model ID: `{m.get('model_id')}`\n"
                        output += f"   Key: `{m.get('model_key')}`\n"
                        if m.get("context_window"):
                            output += f"   Context: {m.get('context_window'):,} tokens\n"
                        if m.get("capabilities"):
                            output += f"   Capabilities: {', '.join(m.get('capabilities'))}\n"
                        output += "\n"

                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No models found.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing models: {str(e)}")]


async def list_clients(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List available client types and their persona affinities.

    Returns all client types with recommended personas for each.
    """
    try:
        result = await _make_request(config, "GET", "/clients")

        if result.get("success"):
            clients = result.get("data", {}).get("clients", [])
            if clients:
                # Mark current client
                current_client = session_state.get("client")

                output = "## Client Types\n\n"
                output += "Clients are the platforms that connect to Collective Memory.\n"
                output += "Each client type has suggested personas that work well with it.\n\n"

                for c in clients:
                    is_current = c.get("client") == current_client
                    marker = " ← (you)" if is_current else ""

                    output += f"### {c.get('client')}{marker}\n"
                    output += f"{c.get('description')}\n\n"

                    affinities = c.get("suggested_personas", [])
                    if affinities:
                        output += f"**Suggested Personas:** {', '.join(affinities)}\n\n"
                    else:
                        output += "**Suggested Personas:** (any)\n\n"

                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No client types found.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing clients: {str(e)}")]


async def update_focus(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update the current work focus for this agent.

    The focus describes what the agent is currently working on,
    visible to other collaborators.

    Args:
        focus: Description of current work (e.g., "Implementing auth module")
    """
    focus = arguments.get("focus", "")

    agent_id = session_state.get("agent_id")
    if not agent_id:
        return [types.TextContent(
            type="text",
            text="❌ Cannot update focus: Not registered.\n\n"
                 "Use get_my_identity to check registration status."
        )]

    try:
        result = await _make_request(
            config,
            "PUT",
            f"/agents/{agent_id}/focus",
            json_data={"focus": focus}
        )

        if result.get("success"):
            # Update session state
            session_state["focus"] = focus

            output = "## Focus Updated\n\n"
            if focus:
                output += f"**Current Focus:** {focus}\n\n"
                output += "Other collaborators can now see what you're working on."
            else:
                output += "Focus cleared. You're now available for new work."

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to update focus: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error updating focus: {str(e)}"
        )]
