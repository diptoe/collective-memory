"""
Agent Tools

MCP tools for listing agents in the Collective Memory (CM) knowledge graph.

Identity management has been moved to identity.py.
Team scope management has been moved to team.py.
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="list_agents",
        description="""List all AI agents connected to Collective Memory (CM).

USE THIS WHEN: You want to see who else is collaborating - other Claude instances, different personas, etc.

EXAMPLES:
- {"active_only": true} → Only agents with recent heartbeats
- {"active_only": false} → All registered agents

RETURNS: Agents with their IDs, roles, capabilities, and active status.""",
        inputSchema={
            "type": "object",
            "properties": {
                "active_only": {"type": "boolean", "description": "Only show active agents (heartbeat within 15 min)", "default": True}
            }
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def list_agents(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List all registered AI agents in the collaboration.

    Args:
        active_only: Only show active agents (default True)
        client: Filter by client type (optional)
    """
    active_only = arguments.get("active_only", True)
    client_filter = arguments.get("client")

    try:
        params = {"active_only": str(active_only).lower()}
        if client_filter:
            params["client"] = client_filter
        result = await _make_request(config, "GET", "/agents", params=params)

        if result.get("success"):
            agents = result.get("data", {}).get("agents", [])
            if agents:
                # Mark current agent
                current_id = session_state.get("agent_id")

                output = f"## Collaborating Agents ({len(agents)})\n\n"
                for a in agents:
                    is_me = a.get("agent_id") == current_id
                    marker = " ← (you)" if is_me else ""
                    status = "🟢" if a.get("is_active") else "⚪"
                    focused = " 🎯" if a.get("is_focused") else ""

                    output += f"{status} **{a.get('agent_id')}**{focused}{marker}\n"

                    # Show client if available
                    if a.get("client"):
                        output += f"   Client: {a.get('client')}\n"

                    # Show persona name (from expanded object) or legacy role
                    persona = a.get("persona")
                    if persona and isinstance(persona, dict) and persona.get("name"):
                        output += f"   Persona: {persona.get('name')} ({persona.get('role', '')})\n"
                    elif a.get("persona_key"):
                        # Fallback to key if persona not expanded
                        output += f"   Persona: {a.get('persona_key')}\n"
                    elif a.get("role"):
                        output += f"   Role: {a.get('role')}\n"

                    # Show model name if available
                    model = a.get("model")
                    if model and isinstance(model, dict) and model.get("name"):
                        output += f"   Model: {model.get('name')}\n"

                    # Show focus if set
                    if a.get("focus"):
                        output += f"   Focus: {a.get('focus')}\n"

                    output += f"   Key: {a.get('agent_key')}\n\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No agents registered yet.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing agents: {str(e)}")]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "list_agents": list_agents,
}
