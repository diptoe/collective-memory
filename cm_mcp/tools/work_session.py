"""
Work Session Tools

MCP tools for managing work sessions - focused work periods on projects.
"""

import mcp.types as types
from typing import Any
from datetime import datetime

from .utils import _make_request


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
            output += f"**Project:** `{session.get('project_key')}`\n"
            output += f"**Status:** {session.get('status')}\n"

            remaining = session.get('time_remaining_seconds')
            if remaining:
                mins = remaining // 60
                output += f"**Auto-closes in:** {mins} minutes\n"

            output += "\n### Tips\n"
            output += "- Entities and messages created will be linked to this session\n"
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


async def record_milestone(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Record a milestone during a work session.

    Creates a 'Milestone' entity linked to the current work session.
    Also updates the session's activity timestamp.

    Args:
        name: Required - name/description of the milestone
        status: Optional - milestone status: 'started', 'completed', or 'blocked' (default: 'completed')
        properties: Optional - additional properties (e.g., blocker reason, files changed)
        session_key: Optional - specific session (defaults to active session)
    """
    name = arguments.get("name")
    status = arguments.get("status", "completed")
    properties = arguments.get("properties", {})
    session_key = arguments.get("session_key")

    if not name:
        return [types.TextContent(type="text", text="Error: `name` is required for the milestone.")]

    # Validate status
    valid_statuses = ["started", "completed", "blocked"]
    if status not in valid_statuses:
        return [types.TextContent(type="text", text=f"Error: `status` must be one of: {', '.join(valid_statuses)}")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no session_key provided, get the active session first
        active_session = None  # Initialize for scope lookup later
        if not session_key:
            active_result = await _make_request(config, "GET", "/work-sessions/active", agent_id=agent_id)
            if active_result.get("success"):
                active_session = active_result.get("data", {}).get("session")
                if active_session:
                    session_key = active_session.get("session_key")
                else:
                    return [types.TextContent(type="text", text="No active session. Start a session first with `start_session`.")]
            else:
                return [types.TextContent(type="text", text=f"Error finding active session: {active_result.get('msg')}")]

        # Update session activity
        await _make_request(config, "POST", f"/work-sessions/{session_key}/activity", agent_id=agent_id)

        # Get scope from the active session (need to fetch it if we don't have it)
        scope_type = None
        scope_key = None
        if active_session:
            # Use team scope if session has a team, otherwise domain scope
            if active_session.get("team_key"):
                scope_type = "team"
                scope_key = active_session.get("team_key")
            elif active_session.get("domain_key"):
                scope_type = "domain"
                scope_key = active_session.get("domain_key")

        # If we didn't have active_session details, fetch the session
        if not scope_type and session_key:
            try:
                session_result = await _make_request(config, "GET", f"/work-sessions/{session_key}", agent_id=agent_id)
                if session_result.get("success"):
                    session_data = session_result.get("data", {}).get("session", {})
                    if session_data.get("team_key"):
                        scope_type = "team"
                        scope_key = session_data.get("team_key")
                    elif session_data.get("domain_key"):
                        scope_type = "domain"
                        scope_key = session_data.get("domain_key")
            except Exception:
                pass  # Fall back to no scope

        # Create the Milestone entity with proper scope and work_session_key
        entity_body = {
            "name": name,
            "entity_type": "Milestone",
            "work_session_key": session_key,  # Top-level field, not in properties
            "properties": {
                **properties,
                "status": status,
            }
        }

        # Add scope if determined
        if scope_type and scope_key:
            entity_body["scope_type"] = scope_type
            entity_body["scope_key"] = scope_key

        result = await _make_request(config, "POST", "/entities", json=entity_body, agent_id=agent_id)

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})

            # Status emoji for visual feedback
            status_emoji = {"started": "🚀", "completed": "✅", "blocked": "🚫"}.get(status, "📍")

            output = f"## {status_emoji} Milestone Recorded\n\n"
            output += f"**Name:** {entity.get('name')}\n"
            output += f"**Status:** {status}\n"
            output += f"**Entity Key:** `{entity.get('entity_key')}`\n"
            output += f"**Session:** `{session_key}`\n"

            if properties:
                output += f"**Properties:** {properties}\n"

            output += "\nSession activity timestamp updated."

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to create milestone')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error recording milestone: {str(e)}")]


# Legacy alias for backward compatibility
async def record_interaction(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """Legacy alias for record_milestone. Use record_milestone instead."""
    return await record_milestone(arguments, config, session_state)
