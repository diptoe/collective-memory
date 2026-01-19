"""
Session Tools

MCP tools for managing work sessions - session lifecycle (start, end, extend, get active).
"""

import mcp.types as types
from typing import Any
from datetime import datetime

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="get_active_session",
        description="""Check for an active work session for the current user.

USE THIS WHEN: You want to see if there's already an active work session, especially before starting a new one.

EXAMPLES:
- {} → Check for any active session
- {"project_key": "ent-project-xyz"} → Check for session on specific project

RETURNS: Active session details including time remaining, or message that no session is active.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_key": {"type": "string", "description": "Optional: Filter by specific project entity key"}
            }
        }
    ),
    types.Tool(
        name="start_session",
        description="""Start a new work session for a project.

USE THIS WHEN: You're beginning focused work on a project and want to track entities/messages created during the session.

WHAT IT DOES:
- Creates a work session tied to a Project entity
- Entities and messages created while session is active are automatically linked
- Session auto-closes after 1 hour of inactivity
- Only one active session per project allowed

EXAMPLES:
- {"project_key": "ent-project-xyz"}
- {"project_key": "ent-dashboard", "name": "Implementing auth feature"}
- {"project_key": "ent-api", "name": "Bug fixes", "team_key": "team-backend"}

RETURNS: Session details including session_key and auto-close time.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_key": {"type": "string", "description": "REQUIRED: The Project entity key to work on"},
                "name": {"type": "string", "description": "Optional: Descriptive name for the session"},
                "team_key": {"type": "string", "description": "Optional: Team scope for the session"}
            },
            "required": ["project_key"]
        }
    ),
    types.Tool(
        name="end_session",
        description="""End (close) a work session.

USE THIS WHEN: You've finished your focused work and want to close the session.

EXAMPLES:
- {} → Close active session
- {"summary": "Completed auth feature implementation"}
- {"session_key": "sess-xyz", "summary": "Fixed 3 bugs"}

RETURNS: Closed session details including duration.""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_key": {"type": "string", "description": "Optional: Specific session to close (defaults to active session)"},
                "summary": {"type": "string", "description": "Optional: Summary of work done in the session"}
            }
        }
    ),
    types.Tool(
        name="extend_session",
        description="""Extend the auto-close timer for a work session.

USE THIS WHEN: You need more time and want to prevent the session from auto-closing.

EXAMPLES:
- {} → Extend active session by 1 hour (default)
- {"hours": 2} → Extend by 2 hours
- {"session_key": "sess-xyz", "hours": 0.5} → Extend specific session by 30 minutes

RETURNS: Updated session with new auto-close time.""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_key": {"type": "string", "description": "Optional: Specific session to extend (defaults to active session)"},
                "hours": {"type": "number", "description": "Hours to extend (default: 1.0, max: 8.0)", "default": 1.0}
            }
        }
    ),
    types.Tool(
        name="update_session",
        description="""Update a work session's name or summary.

USE THIS WHEN:
- You want to name an unnamed session (sessions should always have descriptive names!)
- The work focus has evolved and the session name should reflect that
- You want to add or update the session summary

IMPORTANT: Sessions should ALWAYS have a descriptive name that reflects the work being done.
If you start a session without a name, update it as soon as the work focus becomes clear.

EXAMPLES:
- {"name": "Implementing authentication system"}
- {"name": "Bug fixes for checkout flow", "summary": "Addressing 3 critical bugs reported by QA"}
- {"session_key": "sess-xyz", "name": "Updated focus: refactoring auth"}

RETURNS: Updated session details.""",
        inputSchema={
            "type": "object",
            "properties": {
                "session_key": {"type": "string", "description": "Optional: Specific session to update (defaults to active session)"},
                "name": {"type": "string", "description": "New name for the session (descriptive of the work being done)"},
                "summary": {"type": "string", "description": "Optional: Summary or notes about the session"}
            }
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def get_active_session(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Check for an active work session for the current user.

    Args:
        project_key: Optional - filter by specific project
    """
    project_key = arguments.get("project_key")

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {}
        if project_key:
            params["project_key"] = project_key

        result = await _make_request(config, "GET", "/work-sessions/active", params=params, agent_id=agent_id)

        if result.get("success"):
            session = result.get("data", {}).get("session")

            if not session:
                output = "## No Active Work Session\n\n"
                output += "You don't have an active work session"
                if project_key:
                    output += f" for project `{project_key}`"
                output += ".\n\n"
                output += "Use `start_session` to begin a new work session."
                return [types.TextContent(type="text", text=output)]

            # Format session details
            output = "## Active Work Session\n\n"
            output += f"**Session:** `{session.get('session_key')}`\n"
            if session.get('name'):
                output += f"**Name:** {session.get('name')}\n"
            else:
                output += f"**Name:** _(unnamed - use `update_session` to name it!)_\n"
            output += f"**Project:** `{session.get('project_key')}`\n"

            # Time info
            started = session.get('started_at')
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    output += f"**Started:** {dt.strftime('%Y-%m-%d %H:%M')}\n"
                except:
                    output += f"**Started:** {started}\n"

            # Time remaining
            remaining = session.get('time_remaining_seconds')
            if remaining is not None:
                if remaining > 3600:
                    hours = remaining // 3600
                    mins = (remaining % 3600) // 60
                    output += f"**Time Remaining:** {hours}h {mins}m\n"
                elif remaining > 60:
                    mins = remaining // 60
                    output += f"**Time Remaining:** {mins} minutes\n"
                else:
                    output += f"**Time Remaining:** {remaining} seconds ⚠️\n"

            auto_close = session.get('auto_close_at')
            if auto_close:
                try:
                    dt = datetime.fromisoformat(auto_close.replace('Z', '+00:00'))
                    output += f"**Auto-closes:** {dt.strftime('%Y-%m-%d %H:%M')}\n"
                except:
                    pass

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to get active session')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error checking active session: {str(e)}")]


async def start_session(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Start a new work session for a project.

    Args:
        project_key: Required - the Project entity key to work on
        name: Optional - a descriptive name for the session
        team_key: Optional - team scope for the session
    """
    project_key = arguments.get("project_key")
    name = arguments.get("name")
    team_key = arguments.get("team_key")

    if not project_key:
        return [types.TextContent(type="text", text="Error: `project_key` is required. Provide the key of a Project entity to work on.")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        body = {"project_key": project_key}
        if name:
            body["name"] = name
        if team_key:
            body["team_key"] = team_key

        result = await _make_request(config, "POST", "/work-sessions", json=body, agent_id=agent_id)

        if result.get("success"):
            session = result.get("data", {}).get("session", {})

            output = "## Work Session Started\n\n"
            output += f"**Session Key:** `{session.get('session_key')}`\n"
            if session.get('name'):
                output += f"**Name:** {session.get('name')}\n"
            else:
                output += f"**Name:** _(unnamed - please name this session!)_\n"
            output += f"**Project:** `{session.get('project_key')}`\n"
            output += f"**Status:** {session.get('status')}\n"

            remaining = session.get('time_remaining_seconds')
            if remaining:
                mins = remaining // 60
                output += f"**Auto-closes in:** {mins} minutes\n"

            # Add prompt to name the session if unnamed
            if not session.get('name'):
                output += "\n### ⚠️ Session Naming Required\n"
                output += "This session doesn't have a name yet. As the work focus becomes clear, "
                output += "use `update_session` to give it a descriptive name like:\n"
                output += "- \"Implementing authentication system\"\n"
                output += "- \"Bug fixes for checkout flow\"\n"
                output += "- \"Refactoring database queries\"\n"

            output += "\n### Tips\n"
            output += "- Entities and messages created will be linked to this session\n"
            output += "- Use `update_session` to name or update the session\n"
            output += "- Use `extend_session` if you need more time\n"
            output += "- Use `end_session` when you're done\n"
            output += "- The session will auto-close after 1 hour of inactivity\n"

            return [types.TextContent(type="text", text=output)]
        else:
            error_msg = result.get('msg', 'Failed to start session')
            existing = result.get('data', {}).get('existing_session')

            if existing:
                output = f"## Session Already Exists\n\n"
                output += f"You already have an active session for this project:\n\n"
                output += f"**Session Key:** `{existing.get('session_key')}`\n"
                if existing.get('name'):
                    output += f"**Name:** {existing.get('name')}\n"
                remaining = existing.get('time_remaining_seconds')
                if remaining:
                    mins = remaining // 60
                    output += f"**Time Remaining:** {mins} minutes\n"
                output += "\nClose the existing session first with `end_session`."
                return [types.TextContent(type="text", text=output)]

            return [types.TextContent(type="text", text=f"Error: {error_msg}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error starting session: {str(e)}")]


async def end_session(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    End (close) a work session.

    Args:
        session_key: Optional - specific session to close (defaults to active session)
        summary: Optional - summary of work done in the session
    """
    session_key = arguments.get("session_key")
    summary = arguments.get("summary")

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no session_key provided, get the active session first
        if not session_key:
            active_result = await _make_request(config, "GET", "/work-sessions/active", agent_id=agent_id)
            if active_result.get("success"):
                active_session = active_result.get("data", {}).get("session")
                if active_session:
                    session_key = active_session.get("session_key")
                else:
                    return [types.TextContent(type="text", text="No active session to close.")]
            else:
                return [types.TextContent(type="text", text=f"Error finding active session: {active_result.get('msg')}")]

        body = {}
        if summary:
            body["summary"] = summary

        result = await _make_request(config, "POST", f"/work-sessions/{session_key}/close", json=body, agent_id=agent_id)

        if result.get("success"):
            session = result.get("data", {}).get("session", {})

            output = "## Work Session Closed\n\n"
            output += f"**Session:** `{session.get('session_key')}`\n"
            if session.get('name'):
                output += f"**Name:** {session.get('name')}\n"
            output += f"**Project:** `{session.get('project_key')}`\n"

            # Duration
            started = session.get('started_at')
            ended = session.get('ended_at')
            if started and ended:
                try:
                    start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(ended.replace('Z', '+00:00'))
                    duration = end_dt - start_dt
                    hours = int(duration.total_seconds() // 3600)
                    mins = int((duration.total_seconds() % 3600) // 60)
                    if hours > 0:
                        output += f"**Duration:** {hours}h {mins}m\n"
                    else:
                        output += f"**Duration:** {mins} minutes\n"
                except:
                    pass

            if session.get('summary'):
                output += f"**Summary:** {session.get('summary')}\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to close session')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error closing session: {str(e)}")]


async def extend_session(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Extend the auto-close timer for a work session.

    Args:
        session_key: Optional - specific session to extend (defaults to active session)
        hours: Optional - hours to extend (default: 1.0, max: 8.0)
    """
    session_key = arguments.get("session_key")
    hours = arguments.get("hours", 1.0)

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no session_key provided, get the active session first
        if not session_key:
            active_result = await _make_request(config, "GET", "/work-sessions/active", agent_id=agent_id)
            if active_result.get("success"):
                active_session = active_result.get("data", {}).get("session")
                if active_session:
                    session_key = active_session.get("session_key")
                else:
                    return [types.TextContent(type="text", text="No active session to extend.")]
            else:
                return [types.TextContent(type="text", text=f"Error finding active session: {active_result.get('msg')}")]

        body = {"hours": hours}
        result = await _make_request(config, "POST", f"/work-sessions/{session_key}/extend", json=body, agent_id=agent_id)

        if result.get("success"):
            session = result.get("data", {}).get("session", {})

            output = f"## Session Extended by {hours} hours\n\n"
            output += f"**Session:** `{session.get('session_key')}`\n"

            remaining = session.get('time_remaining_seconds')
            if remaining:
                if remaining > 3600:
                    hrs = remaining // 3600
                    mins = (remaining % 3600) // 60
                    output += f"**New Time Remaining:** {hrs}h {mins}m\n"
                else:
                    mins = remaining // 60
                    output += f"**New Time Remaining:** {mins} minutes\n"

            auto_close = session.get('auto_close_at')
            if auto_close:
                try:
                    dt = datetime.fromisoformat(auto_close.replace('Z', '+00:00'))
                    output += f"**Auto-closes at:** {dt.strftime('%Y-%m-%d %H:%M')}\n"
                except:
                    pass

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to extend session')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error extending session: {str(e)}")]


async def update_session(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update a work session's name or summary.

    Args:
        session_key: Optional - specific session to update (defaults to active session)
        name: Optional - new name for the session
        summary: Optional - summary or notes about the session
    """
    session_key = arguments.get("session_key")
    name = arguments.get("name")
    summary = arguments.get("summary")

    if not name and not summary:
        return [types.TextContent(type="text", text="Error: Provide at least `name` or `summary` to update.")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no session_key provided, get the active session first
        if not session_key:
            active_result = await _make_request(config, "GET", "/work-sessions/active", agent_id=agent_id)
            if active_result.get("success"):
                active_session = active_result.get("data", {}).get("session")
                if active_session:
                    session_key = active_session.get("session_key")
                else:
                    return [types.TextContent(type="text", text="No active session to update.")]
            else:
                return [types.TextContent(type="text", text=f"Error finding active session: {active_result.get('msg')}")]

        body = {}
        if name:
            body["name"] = name
        if summary:
            body["summary"] = summary

        result = await _make_request(config, "PUT", f"/work-sessions/{session_key}", json=body, agent_id=agent_id)

        if result.get("success"):
            session = result.get("data", {}).get("session", {})

            output = "## Work Session Updated\n\n"
            output += f"**Session:** `{session.get('session_key')}`\n"
            output += f"**Name:** {session.get('name') or '(unnamed)'}\n"
            output += f"**Project:** `{session.get('project_key')}`\n"

            if session.get('summary'):
                output += f"**Summary:** {session.get('summary')}\n"

            remaining = session.get('time_remaining_seconds')
            if remaining:
                if remaining > 3600:
                    hours = remaining // 3600
                    mins = (remaining % 3600) // 60
                    output += f"**Time Remaining:** {hours}h {mins}m\n"
                else:
                    mins = remaining // 60
                    output += f"**Time Remaining:** {mins} minutes\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to update session')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error updating session: {str(e)}")]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "get_active_session": get_active_session,
    "start_session": start_session,
    "end_session": end_session,
    "extend_session": extend_session,
    "update_session": update_session,
}
