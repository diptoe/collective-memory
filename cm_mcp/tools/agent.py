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

                    output += f"{status} **{a.get('agent_id')}**{marker}\n"

                    # Show client if available
                    if a.get("client"):
                        output += f"   Client: {a.get('client')}\n"

                    # Show persona or legacy role
                    if a.get("persona_key"):
                        output += f"   Persona: {a.get('persona_key')}\n"
                    elif a.get("role"):
                        output += f"   Role: {a.get('role')}\n"

                    # Show focus if set
                    if a.get("focus"):
                        output += f"   Focus: {a.get('focus')}\n"

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

    Returns the agent's ID, client, model, persona, focus, and registration status.
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

    # Client info
    client = session_state.get("client")
    if client:
        output += f"**Client:** {client}\n"

    # Model info
    if session_state.get("model_key"):
        output += f"\n### Model\n"
        output += f"**Model Key:** {session_state.get('model_key')}\n"
        if session_state.get("model_name"):
            output += f"**Model Name:** {session_state.get('model_name')}\n"

    # Persona info
    if session_state.get("persona_name"):
        output += f"\n### Persona\n"
        output += f"**Name:** {session_state.get('persona_name')}\n"
        output += f"**Role:** {session_state.get('persona')}\n"
        output += f"**Persona Key:** {session_state.get('persona_key')}\n"
    else:
        output += f"**Persona:** {session_state.get('persona') or '(not set)'}\n"

    # Focus
    focus = session_state.get("focus")
    if focus:
        output += f"\n### Current Focus\n"
        output += f"{focus}\n"

    # Affinity warning
    affinity_warning = session_state.get("affinity_warning")
    if affinity_warning:
        output += f"\n### Affinity Notice\n"
        output += f"{affinity_warning}\n"

    output += f"\n**Registered:** Yes\n"

    return [types.TextContent(type="text", text=output)]


async def update_my_identity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update the agent's identity - change agent ID, persona, model, and/or focus.

    This re-registers with the API under the new identity.

    Args:
        agent_id: New agent ID (optional, keeps current if not provided)
        persona: New persona role (optional, keeps current if not provided)
        model_key: New model key (optional, keeps current if not provided)
        focus: Current work focus (optional)
    """
    new_agent_id = arguments.get("agent_id")
    new_persona = arguments.get("persona")
    new_model_key = arguments.get("model_key")
    new_focus = arguments.get("focus")

    # Must provide at least one change
    if not new_agent_id and not new_persona and not new_model_key and new_focus is None:
        return [types.TextContent(
            type="text",
            text="No changes specified.\n\n"
                 "Provide `agent_id`, `persona`, `model_key`, and/or `focus` to update your identity."
        )]

    # Use current values if not changing
    agent_id = new_agent_id or session_state.get("agent_id") or config.agent_id
    persona = new_persona or session_state.get("persona") or config.persona
    model_key = new_model_key or session_state.get("model_key") or config.model_key
    focus = new_focus if new_focus is not None else session_state.get("focus") or config.focus
    client = session_state.get("client") or config.detected_client

    if not agent_id:
        return [types.TextContent(
            type="text",
            text="Cannot update identity: No agent_id available.\n\n"
                 "Either provide an agent_id or set CM_AGENT_ID environment variable."
        )]

    try:
        # Build registration payload
        registration_data = {
            "agent_id": agent_id,
            "capabilities": config.capabilities_list if hasattr(config, 'capabilities_list') else ["search", "create", "update"],
        }

        # Add optional fields
        if client:
            registration_data["client"] = client
        if model_key:
            registration_data["model_key"] = model_key
        if persona:
            # Look up persona_key from role
            try:
                personas_result = await _make_request(
                    config,
                    "GET",
                    "/personas/by-role/" + persona
                )
                if personas_result.get("success"):
                    persona_data = personas_result.get("data", {})
                    if persona_data.get("persona_key"):
                        registration_data["persona_key"] = persona_data.get("persona_key")
            except Exception:
                pass  # Persona lookup failed, continue without persona_key
        if focus:
            registration_data["focus"] = focus

        # Register with new identity
        result = await _make_request(
            config,
            "POST",
            "/agents/register",
            json_data=registration_data
        )

        if result.get("success"):
            agent_data = result.get("data", {})

            # Capture old values for comparison
            old_agent_id = session_state.get("agent_id")
            old_persona = session_state.get("persona")
            old_model_key = session_state.get("model_key")
            old_focus = session_state.get("focus")

            # Update session state with new identity
            session_state["agent_id"] = agent_id
            session_state["agent_key"] = agent_data.get("agent_key")
            session_state["persona"] = persona
            session_state["model_key"] = model_key
            session_state["focus"] = focus
            session_state["client"] = client
            session_state["registered"] = True

            # Store affinity warning if present
            if agent_data.get("affinity_warning"):
                session_state["affinity_warning"] = agent_data.get("affinity_warning")

            # Clear persona details - they'll need to be re-resolved
            session_state["persona_key"] = None
            session_state["persona_name"] = None
            session_state["model_name"] = None

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

            # Try to resolve model name
            if model_key:
                try:
                    model_result = await _make_request(
                        config,
                        "GET",
                        f"/models/{model_key}"
                    )
                    if model_result.get("success"):
                        model_data = model_result.get("data", {})
                        session_state["model_name"] = model_data.get("name")
                except Exception:
                    pass

            # Build response
            output = "## Identity Updated\n\n"

            if old_agent_id != agent_id:
                output += f"**Agent ID:** {old_agent_id} -> **{agent_id}**\n"
            else:
                output += f"**Agent ID:** {agent_id}\n"

            output += f"**Agent Key:** {agent_data.get('agent_key')}\n"
            output += f"**Client:** {client}\n"

            if old_model_key != model_key and model_key:
                output += f"**Model:** {old_model_key or '(none)'} -> **{model_key}**\n"
            elif model_key:
                output += f"**Model:** {model_key}\n"
                if session_state.get("model_name"):
                    output += f"**Model Name:** {session_state['model_name']}\n"

            if old_persona != persona:
                output += f"**Persona:** {old_persona or '(none)'} -> **{persona}**\n"
            else:
                output += f"**Persona:** {persona or '(not set)'}\n"

            if session_state.get("persona_name"):
                output += f"**Persona Name:** {session_state['persona_name']}\n"

            if old_focus != focus and focus:
                output += f"**Focus:** {focus}\n"
            elif focus:
                output += f"**Focus:** {focus}\n"

            # Show affinity warning if present
            if agent_data.get("affinity_warning"):
                output += f"\n**Note:** {agent_data.get('affinity_warning')}\n"

            output += f"\nRe-registered successfully\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to update identity: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error updating identity: {str(e)}"
        )]
