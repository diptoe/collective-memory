"""
Model and Client Tools

MCP tools for model listing, client information, and focus management
in Collective Memory (CM).
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="list_models",
        description="""List available AI models in the Collective Memory.

USE THIS WHEN: You want to see what AI models are available (Claude, GPT, Gemini, etc.).

EXAMPLES:
- {} → All active models
- {"provider": "anthropic"} → Only Anthropic models
- {"active_only": false} → Include deprecated models

RETURNS: Models grouped by provider with capabilities and context windows.""",
        inputSchema={
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Filter by provider: anthropic, openai, google"},
                "active_only": {"type": "boolean", "description": "Only show active models (default true)", "default": True}
            }
        }
    ),
    types.Tool(
        name="list_clients",
        description="""List available client types and their persona affinities.

USE THIS WHEN: You want to understand the different platforms that connect to Collective Memory
and which personas work best with each.

Client types: claude-code, claude-desktop, codex, gemini-cli, cursor

RETURNS: Client types with descriptions and suggested personas.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="update_focus",
        description="""Update your current work focus.

USE THIS WHEN: You want to let other collaborators know what you're working on.

EXAMPLES:
- {"focus": "Implementing authentication module"}
- {"focus": "Reviewing PR #42"}
- {"focus": ""} → Clear focus (available for new work)

The focus is visible to other agents in the collaboration.""",
        inputSchema={
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "Description of current work (empty to clear)"}
            }
        }
    ),
    types.Tool(
        name="set_focused_mode",
        description="""Enable or disable focused mode for faster heartbeats.

USE THIS WHEN: You're actively waiting for a response from another agent and want to be notified quickly.

FOCUSED MODE:
- When ENABLED: Heartbeat interval is 30 seconds (fast polling for messages)
- When DISABLED: Heartbeat interval is 5 minutes (normal polling)
- Auto-expires after the specified duration (default 10 minutes)

EXAMPLES:
- {"enabled": true} → Enable focused mode for 10 minutes (default)
- {"enabled": true, "duration_minutes": 15} → Enable for 15 minutes
- {"enabled": false} → Disable focused mode immediately

WORKFLOW:
1. Send an autonomous task to another agent
2. Enable focused mode: {"enabled": true}
3. Agent works, replies when done
4. You receive the reply quickly (30s polling)
5. Focused mode auto-expires, or disable manually

RETURNS: Current focused mode status with recommended heartbeat interval.""",
        inputSchema={
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "Enable (true) or disable (false) focused mode"},
                "duration_minutes": {"type": "integer", "description": "How long focused mode should last (default 10 minutes)", "default": 10}
            },
            "required": ["enabled"]
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

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
            json={"focus": focus}
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


async def set_focused_mode(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Enable or disable focused mode for faster heartbeats.

    When focused mode is enabled, the agent signals it's actively waiting
    for a response and should use faster heartbeat intervals (30 seconds
    instead of 5 minutes).

    Args:
        enabled: True to enable focused mode, False to disable
        duration_minutes: How long focused mode should last (default 10)
    """
    enabled = arguments.get("enabled")
    duration_minutes = arguments.get("duration_minutes", 10)

    if enabled is None:
        return [types.TextContent(
            type="text",
            text="❌ 'enabled' parameter is required (true or false)"
        )]

    agent_id = session_state.get("agent_id")
    if not agent_id:
        return [types.TextContent(
            type="text",
            text="❌ Cannot set focused mode: Not registered.\n\n"
                 "Use get_my_identity to check registration status."
        )]

    try:
        result = await _make_request(
            config,
            "PUT",
            f"/agents/{agent_id}/focused-mode",
            json={"enabled": enabled, "duration_minutes": duration_minutes}
        )

        if result.get("success"):
            data = result.get("data", {})
            is_focused = data.get("is_focused", False)
            recommended_interval = data.get("recommended_heartbeat_seconds", 300)
            expires_at = data.get("focused_mode_expires_at")

            output = "## Focused Mode Updated\n\n"

            if is_focused:
                output += "🎯 **Focused Mode: ENABLED**\n\n"
                output += f"- Heartbeat interval: **{recommended_interval} seconds**\n"
                if expires_at:
                    output += f"- Expires at: {expires_at}\n"
                output += "\nYou'll receive messages faster while focused mode is active."
            else:
                output += "💤 **Focused Mode: DISABLED**\n\n"
                output += f"- Heartbeat interval: **{recommended_interval} seconds** (5 minutes)\n"
                output += "\nReturned to normal polling interval."

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to set focused mode: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error setting focused mode: {str(e)}"
        )]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "list_models": list_models,
    "list_clients": list_clients,
    "update_focus": update_focus,
    "set_focused_mode": set_focused_mode,
}
