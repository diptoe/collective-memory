"""
Activity Tools

MCP tools for querying system activity data.
"""

import json
import mcp.types as types
from typing import Any
from datetime import datetime

from .utils import _make_request


async def list_activities(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List recent system activities with optional filtering.

    Args:
        hours: Number of hours to look back (default 24)
        activity_type: Filter by activity type (message_sent, agent_heartbeat, etc.)
        actor: Filter by actor (agent_id)
        limit: Maximum results (default 50)
    """
    hours = arguments.get("hours", 24)
    activity_type = arguments.get("activity_type")
    actor = arguments.get("actor")
    limit = arguments.get("limit", 50)

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {
            "hours": hours,
            "limit": limit
        }
        if activity_type:
            params["type"] = activity_type
        if actor:
            params["actor"] = actor

        result = await _make_request(config, "GET", "/activities", params=params, agent_id=agent_id)

        if result.get("success"):
            activities = result.get("data", {}).get("activities", [])
            total = result.get("data", {}).get("total", len(activities))

            if not activities:
                return [types.TextContent(type="text", text=f"No activities found in the last {hours} hours.")]

            # Build output
            output = f"## System Activities (last {hours} hours)\n\n"
            output += f"Found {total} activities"
            if activity_type:
                output += f" of type '{activity_type}'"
            if actor:
                output += f" by actor '{actor}'"
            output += f" (showing {len(activities)}):\n\n"

            # Group by type for readability
            by_type = {}
            for act in activities:
                t = act.get('activity_type', 'unknown')
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(act)

            for activity_type_name, type_activities in sorted(by_type.items()):
                output += f"### {activity_type_name} ({len(type_activities)})\n"
                for act in type_activities[:10]:  # Limit per type
                    timestamp = act.get('created_at', '')
                    if timestamp:
                        # Format timestamp nicely
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass

                    actor_name = act.get('actor', 'unknown')
                    extra = act.get('extra_data', {})

                    # Build description based on type
                    desc = ""
                    if activity_type_name == 'agent_registered':
                        is_reconnect = extra.get('is_reconnect', False)
                        client = extra.get('client', '')
                        action = "reconnected" if is_reconnect else "registered"
                        desc = f"{action} ({client})"
                    elif activity_type_name == 'message_sent':
                        channel = extra.get('channel', 'general')
                        desc = f"to #{channel}"
                    elif activity_type_name in ('entity_created', 'entity_updated', 'entity_deleted', 'entity_read'):
                        entity_name = extra.get('entity_name', act.get('target_key', ''))
                        entity_type = extra.get('entity_type', '')
                        desc = f"{entity_name} ({entity_type})"
                    elif activity_type_name in ('relationship_created', 'relationship_deleted'):
                        rel_type = extra.get('relationship_type', '')
                        from_name = extra.get('from_entity_name', extra.get('from_entity_key', ''))
                        to_name = extra.get('to_entity_name', extra.get('to_entity_key', ''))
                        desc = f"{from_name} → {rel_type} → {to_name}"
                    elif activity_type_name == 'search_performed':
                        query = extra.get('query', '')
                        search_type = extra.get('search_type', 'entity')
                        result_count = extra.get('result_count', 0)
                        desc = f"'{query}' ({search_type}, {result_count} results)"
                    elif activity_type_name == 'agent_heartbeat':
                        desc = "heartbeat"

                    output += f"- **{timestamp}** | {actor_name}: {desc}\n"

                if len(type_activities) > 10:
                    output += f"  ... and {len(type_activities) - 10} more\n"
                output += "\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to get activities')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing activities: {str(e)}")]


async def get_activity_summary(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get activity summary with counts by type.

    Args:
        hours: Number of hours to summarize (default 24)
    """
    hours = arguments.get("hours", 24)

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {"hours": hours}
        result = await _make_request(config, "GET", "/activities/summary", params=params, agent_id=agent_id)

        if result.get("success"):
            data = result.get("data", {})
            summary = data.get("summary", {})
            total = data.get("total", 0)

            if not summary:
                return [types.TextContent(type="text", text=f"No activities in the last {hours} hours.")]

            output = f"## Activity Summary (last {hours} hours)\n\n"
            output += f"**Total activities:** {total}\n\n"
            output += "| Activity Type | Count | % |\n"
            output += "|---------------|-------|---|\n"

            for activity_type, count in sorted(summary.items(), key=lambda x: -x[1]):
                pct = (count / total * 100) if total > 0 else 0
                output += f"| {activity_type} | {count} | {pct:.1f}% |\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to get summary')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting activity summary: {str(e)}")]
