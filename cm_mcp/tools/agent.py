"""
Agent Tools

MCP tools for agent collaboration in the knowledge graph.
"""

import httpx
import mcp.types as types
from typing import Any


async def _make_request(
    config: Any,
    method: str,
    endpoint: str,
    json_data: dict = None,
    params: dict = None,
) -> dict:
    """Make HTTP request to the Collective Memory API"""
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        url = f"{config.api_endpoint}{endpoint}"
        response = await client.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def list_agents(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List all registered AI agents in the collaboration.

    Args:
        active_only: Only show active agents (default True)
    """
    active_only = arguments.get("active_only", True)

    try:
        params = {"active_only": str(active_only).lower()}
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

                    output += f"{status} **{a.get('agent_id')}**{marker}\n"
                    output += f"   Role: {a.get('role')}\n"
                    output += f"   Capabilities: {', '.join(a.get('capabilities', []))}\n"
                    output += f"   Key: {a.get('agent_key')}\n\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No agents registered yet.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing agents: {str(e)}")]


async def get_my_identity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get the current agent's identity in the collective memory.

    Returns the agent's ID, persona, and registration status.
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered with Collective Memory.\n\n"
                 "Set CM_AGENT_ID and CM_PERSONA environment variables to establish identity."
        )]

    output = "## My Identity in Collective Memory\n\n"
    output += f"**Agent ID:** {session_state.get('agent_id')}\n"
    output += f"**Agent Key:** {session_state.get('agent_key')}\n"

    # Persona info
    if session_state.get("persona_name"):
        output += f"\n### Persona\n"
        output += f"**Name:** {session_state.get('persona_name')}\n"
        output += f"**Role:** {session_state.get('persona')}\n"
        output += f"**Persona Key:** {session_state.get('persona_key')}\n"
    else:
        output += f"**Persona:** {session_state.get('persona') or '(not set)'}\n"

    output += f"\n**Registered:** Yes\n"

    return [types.TextContent(type="text", text=output)]


async def update_my_identity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update the agent's identity - change agent ID and/or persona.

    This re-registers with the API under the new identity.

    Args:
        agent_id: New agent ID (optional, keeps current if not provided)
        persona: New persona role (optional, keeps current if not provided)
    """
    new_agent_id = arguments.get("agent_id")
    new_persona = arguments.get("persona")

    # Must provide at least one change
    if not new_agent_id and not new_persona:
        return [types.TextContent(
            type="text",
            text="⚠️ No changes specified.\n\n"
                 "Provide `agent_id` and/or `persona` to update your identity."
        )]

    # Use current values if not changing
    agent_id = new_agent_id or session_state.get("agent_id") or config.agent_id
    persona = new_persona or session_state.get("persona") or config.persona

    if not agent_id:
        return [types.TextContent(
            type="text",
            text="❌ Cannot update identity: No agent_id available.\n\n"
                 "Either provide an agent_id or set CM_AGENT_ID environment variable."
        )]

    try:
        # Register with new identity
        result = await _make_request(
            config,
            "POST",
            "/agents/register",
            json_data={
                "agent_id": agent_id,
                "role": persona or "general",
                "capabilities": config.capabilities_list if hasattr(config, 'capabilities_list') else ["search", "create", "update"],
            }
        )

        if result.get("success"):
            agent_data = result.get("data", {})

            # Update session state with new identity
            old_agent_id = session_state.get("agent_id")
            old_persona = session_state.get("persona")

            session_state["agent_id"] = agent_id
            session_state["agent_key"] = agent_data.get("agent_key")
            session_state["persona"] = persona
            session_state["registered"] = True

            # Clear persona details - they'll need to be re-resolved
            session_state["persona_key"] = None
            session_state["persona_name"] = None

            # Try to resolve new persona details
            if persona:
                try:
                    personas_result = await _make_request(
                        config,
                        "GET",
                        "/personas",
                        params={"role": persona}
                    )
                    if personas_result.get("success"):
                        personas = personas_result.get("data", {}).get("personas", [])
                        if personas:
                            p = personas[0]
                            session_state["persona_key"] = p.get("persona_key")
                            session_state["persona_name"] = p.get("name")
                except Exception:
                    pass  # Persona lookup failed, but identity update succeeded

            # Build response
            output = "## Identity Updated\n\n"

            if old_agent_id != agent_id:
                output += f"**Agent ID:** {old_agent_id} → **{agent_id}**\n"
            else:
                output += f"**Agent ID:** {agent_id}\n"

            output += f"**Agent Key:** {agent_data.get('agent_key')}\n"

            if old_persona != persona:
                output += f"**Persona:** {old_persona or '(none)'} → **{persona}**\n"
            else:
                output += f"**Persona:** {persona or '(not set)'}\n"

            if session_state.get("persona_name"):
                output += f"**Persona Name:** {session_state['persona_name']}\n"

            output += f"\n✅ Re-registered successfully\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to update identity: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error updating identity: {str(e)}"
        )]
