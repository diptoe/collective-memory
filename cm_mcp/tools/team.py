"""
Team Tools

MCP tools for team scope management in the Collective Memory (CM) knowledge graph.
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="list_my_scopes",
        description="""List all scopes the current agent can access.

USE THIS WHEN: You want to see what scopes are available for creating entities or understanding visibility.

SCOPES determine entity visibility:
- domain: Visible to everyone in the domain
- team: Visible only to team members
- user: Private to the user

RETURNS: Available scopes grouped by type with your access level, plus your default scope for new entities.""",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="set_active_team",
        description="""Set active team for this session. New entities will default to this team's scope.

USE THIS WHEN: You want to focus work on a specific team and have new entities scoped to that team.

EXAMPLES:
- {"team_key": "team-abc123"} → Set team as active, new entities will be team-scoped
- {} or {"team_key": null} → Clear active team, use domain scope instead

RETURNS: Confirmation with the new default scope.""",
        inputSchema={
            "type": "object",
            "properties": {
                "team_key": {"type": "string", "description": "Team key to set as active (null/omit to clear)"}
            }
        }
    ),
    types.Tool(
        name="list_teams",
        description="""List teams the current user is a member of.

USE THIS WHEN: You want to see available teams for scoping entities or collaboration.

RETURNS: Teams with names, descriptions, and your role in each team.""",
        inputSchema={"type": "object", "properties": {}}
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def list_my_scopes(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List all scopes the current agent can access.

    Returns available scopes (domain, team, personal) with descriptions
    and shows the current default scope.
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    available_scopes = session_state.get("available_scopes", [])
    default_scope = session_state.get("default_scope", {})
    active_team = session_state.get("active_team_key")

    output = "# My Available Scopes\n\n"

    if not available_scopes:
        output += "No scopes available. Try re-identifying to refresh scope data.\n"
        return [types.TextContent(type="text", text=output)]

    # Group scopes by type
    domain_scopes = [s for s in available_scopes if s.get('scope_type') == 'domain']
    team_scopes = [s for s in available_scopes if s.get('scope_type') == 'team']
    user_scopes = [s for s in available_scopes if s.get('scope_type') == 'user']

    if domain_scopes:
        output += "## Domain Scopes\n"
        for s in domain_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            default_marker = " ← **default**" if is_default else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    if team_scopes:
        output += "## Team Scopes\n"
        for s in team_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            is_active = s.get('scope_key') == active_team
            default_marker = " ← **default**" if is_default else ""
            active_marker = " 🎯 **active**" if is_active else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}{active_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    if user_scopes:
        output += "## Personal Scope\n"
        for s in user_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            default_marker = " ← **default**" if is_default else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    output += "---\n\n"
    output += "## Usage\n"
    output += "Use `scope_type` and `scope_key` in `create_entity` to target specific scopes:\n"
    output += "```\n"
    output += 'create_entity(\n'
    output += '    name="My Entity",\n'
    output += '    entity_type="Concept",\n'
    output += '    scope_type="team",\n'
    output += '    scope_key="team-xxx"\n'
    output += ')\n'
    output += "```\n\n"
    output += "Use `set_active_team` to change your default scope for new entities.\n"

    return [types.TextContent(type="text", text=output)]


async def set_active_team(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Set active team for this session.

    New entities will default to this team's scope.

    Args:
        team_key: Team key to set as active (optional - omit to clear active team)
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    team_key = arguments.get("team_key")
    teams = session_state.get("teams", [])

    if team_key:
        # Validate team access
        team = next((t for t in teams if t.get('team_key') == team_key), None)
        if not team:
            output = f"Error: Not a member of team `{team_key}`\n\n"
            if teams:
                output += "Your teams:\n"
                for t in teams:
                    output += f"- **{t.get('name')}** - `{t.get('team_key')}`\n"
            else:
                output += "You are not a member of any teams.\n"
            return [types.TextContent(type="text", text=output)]

        # Set active team
        session_state["active_team_key"] = team_key

        # Update default scope to use this team
        session_state["default_scope"] = {
            "scope_type": "team",
            "scope_key": team_key
        }

        output = f"# Active Team Set\n\n"
        output += f"**Team:** {team.get('name')}\n"
        output += f"**Key:** `{team_key}`\n"
        output += f"**Your Role:** {team.get('role')}\n\n"
        output += "New entities will be created in this team's scope by default.\n"
    else:
        # Clear active team
        previous = session_state.pop("active_team_key", None)

        # Reset default scope
        domain_key = session_state.get("domain_key")
        if domain_key:
            session_state["default_scope"] = {
                "scope_type": "domain",
                "scope_key": domain_key
            }
        else:
            user_key = session_state.get("user_key")
            session_state["default_scope"] = {
                "scope_type": "user",
                "scope_key": user_key
            }

        output = "# Active Team Cleared\n\n"
        if previous:
            output += f"Previously active team `{previous}` has been cleared.\n\n"
        output += "Default scope has been reset to: "
        default_scope = session_state.get("default_scope", {})
        output += f"{default_scope.get('scope_type')} ({default_scope.get('scope_key')})\n"

    return [types.TextContent(type="text", text=output)]


async def list_teams(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List teams the current user is a member of.

    Returns team names, keys, descriptions, and the user's role in each team.
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    teams = session_state.get("teams", [])
    active_team = session_state.get("active_team_key")

    output = "# My Teams\n\n"

    if not teams:
        output += "You are not a member of any teams.\n\n"
        output += "Teams are managed by domain administrators.\n"
        return [types.TextContent(type="text", text=output)]

    output += f"You are a member of **{len(teams)}** team(s):\n\n"

    for t in teams:
        is_active = t.get('team_key') == active_team
        active_marker = " 🎯 **active**" if is_active else ""

        output += f"## {t.get('name')}{active_marker}\n"
        output += f"**Key:** `{t.get('team_key')}`\n"
        output += f"**Your Role:** {t.get('role')}\n"
        if t.get('description'):
            output += f"**Description:** {t.get('description')}\n"
        output += "\n"

    output += "---\n\n"
    output += "Use `set_active_team(team_key=\"...\")` to set your active team.\n"
    output += "Entities created without explicit scope will use the active team's scope.\n"

    return [types.TextContent(type="text", text=output)]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "list_my_scopes": list_my_scopes,
    "set_active_team": set_active_team,
    "list_teams": list_teams,
}
