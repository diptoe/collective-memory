"""
Message Tools

MCP tools for inter-agent messaging queue operations in Collective Memory (CM).
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="send_message",
        description="""Send a message to other agents or human coordinators via the message queue.

USE THIS WHEN: You want to communicate with other agents or humans. Messages appear in the Messages UI, NOT the Chat UI.

Use this for:
- Status updates: "I've completed the API refactoring"
- Questions: "Which database should I use for caching?"
- Handoffs: "Frontend is ready, backend team please review"
- Announcements: "New feature deployed to staging"
- Replies: Reply to a specific message to create a threaded conversation
- Autonomous tasks: Request another agent to work on something and reply when done

## AUTONOMOUS COLLABORATION WORKFLOW

The `autonomous` flag enables structured agent-to-agent collaboration:

1. **Request work**: Set `autonomous=true` when asking another agent to work on a task
   - "Please implement X and reply when done"
   - The receiver will see this prominently highlighted as requiring their attention

2. **Acknowledge task**: When you RECEIVE an autonomous task, IMMEDIATELY reply with:
   - Use `message_type: "acknowledged"` to signal you've received the task
   - Include brief plan and ETA in the content
   - Example: `{"reply_to": "msg-abc", "message_type": "acknowledged", "content": "Starting auth API with JWT. ETA ~15 min."}`

3. **Signal waiting**: When you need to ask your operator for console input:
   - Use `message_type: "waiting"` to broadcast that you're paused
   - This lets other agents/observers know you're waiting for LOCAL console input (not a message reply)
   - Include WHY you're waiting and WHAT you're asking your operator
   - Example: `{"reply_to": "msg-abc", "message_type": "waiting", "content": "Asking operator: OAuth or JWT? (waiting for console input)"}`

4. **Signal resumed**: When your operator provides console input and you continue:
   - Use `message_type: "resumed"` to broadcast you're back to work
   - Include WHAT your operator decided/provided
   - Example: `{"reply_to": "msg-abc", "message_type": "resumed", "content": "Operator chose JWT with refresh tokens. Continuing..."}`

5. **Complete work**: Reply with `autonomous=false` (default) when you believe the task is done
   - "I've implemented X, here's what I did..."
   - This signals you believe the task is complete and are handing back control

6. **Operator confirmation**: Human operators can "Confirm" completion in the Messages UI
   - Shows a green "Confirmed" badge on the message
   - Operators can also "Undo" confirmation if more work is needed
   - This provides a human-in-the-loop verification step

5. **Continue collaboration**: Original sender can send a NEW message with `autonomous=true` if more work needed
   - "Thanks, but we also need Y. Please continue and reply when done."
   - This keeps the collaboration loop going

This creates a natural back-and-forth where agents can work independently but stay coordinated, with optional human oversight.

EXAMPLES:
- {"channel": "general", "content": "Starting work on auth module", "message_type": "status"}
- {"channel": "backend", "content": "Need help with database schema", "message_type": "question", "priority": "high"}
- {"to_agent": "claude-backend", "content": "Please implement the auth API and reply when done", "autonomous": true} → Request autonomous work
- {"content": "Acknowledged! I'll implement auth with JWT tokens. ETA ~15 min.", "reply_to": "msg-abc123"} → Acknowledge immediately
- {"content": "Done! I implemented the auth API with JWT tokens.", "reply_to": "msg-abc123"} → Reply when complete (autonomous=false by default)
- {"to_agent": "claude-backend", "content": "Great, but we also need refresh tokens. Please add that.", "autonomous": true} → Continue collaboration

RETURNS: Confirmation with message key.""",
        inputSchema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel name: general, backend, frontend, urgent, or custom", "default": "general"},
                "content": {"type": "string", "description": "Message content"},
                "message_type": {"type": "string", "description": "Type: status, announcement, request, task, message, acknowledged (task received), waiting (blocked/need input), resumed (continuing after input)", "default": "status"},
                "to_agent": {"type": "string", "description": "Optional: specific agent ID (null for broadcast)"},
                "reply_to": {"type": "string", "description": "Optional: message_key to reply to (creates threaded conversation)"},
                "priority": {"type": "string", "description": "Priority: high, normal, low", "default": "normal"},
                "autonomous": {"type": "boolean", "description": "Set true to request autonomous work (receiver works independently and replies when done). Set false (default) when replying to signal task completion. See AUTONOMOUS COLLABORATION WORKFLOW above.", "default": False},
                "entity_keys": {"type": "array", "items": {"type": "string"}, "description": "Optional: entity keys to link this message to in the knowledge graph. Replies auto-inherit parent's entity_keys."},
                "team_key": {"type": "string", "description": "Optional: team key to scope message to a specific team (null = domain-wide)"}
            },
            "required": ["content"]
        }
    ),
    types.Tool(
        name="get_messages",
        description="""Get messages from the message queue.

USE THIS WHEN: You want to check for messages from other agents or human coordinators.

EXAMPLES:
- {} → Get all unread messages
- {"channel": "backend"} → Messages from backend channel
- {"unread_only": false, "limit": 50} → Get recent messages including read ones
- {"since": "2025-01-06T10:00:00Z"} → Messages after a specific time

RETURNS: List of messages with sender, content, type, and read status.""",
        inputSchema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Filter by channel (optional)"},
                "unread_only": {"type": "boolean", "description": "Only unread messages", "default": True},
                "limit": {"type": "integer", "description": "Maximum messages to retrieve", "default": 20},
                "since": {"type": "string", "description": "Only return messages created after this ISO8601 timestamp (optional)"},
                "team_key": {"type": "string", "description": "Filter to a specific team's messages (optional, uses active team if set)"}
            }
        }
    ),
    types.Tool(
        name="mark_message_read",
        description="""Mark a message as read by you.

Uses per-agent read tracking - marks the message as read by YOU specifically.
Other agents will still see the message as unread until they mark it.

USE THIS WHEN: You've processed a message and want to mark it as handled.

EXAMPLE: {"message_key": "msg-abc123"}

RETURNS: Confirmation.""",
        inputSchema={
            "type": "object",
            "properties": {
                "message_key": {"type": "string", "description": "The message key to mark as read"}
            },
            "required": ["message_key"]
        }
    ),
    types.Tool(
        name="mark_all_messages_read",
        description="""Mark all unread messages as read for you.

Uses per-agent read tracking - marks messages as read by YOU specifically.
Other agents will still see the messages as unread until they mark them.

USE THIS WHEN: You want to clear your unread messages.

EXAMPLES:
- {} → Mark all your unread messages as read
- {"channel": "backend"} → Mark only backend channel messages as read

RETURNS: Number of messages marked as read.""",
        inputSchema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Only mark messages in this channel as read (optional)"},
                "team_key": {"type": "string", "description": "Only mark messages in this team as read (optional)"}
            }
        }
    ),
    types.Tool(
        name="link_message_entities",
        description="""Link entities to an existing message.

USE THIS WHEN: You want to connect a message to relevant entities in the knowledge graph after it was created.

MODES:
- add (default): Add entities to existing links
- replace: Replace all entity links with the new ones
- remove: Remove specified entities from links

EXAMPLES:
- {"message_key": "msg-abc123", "entity_keys": ["ent-xyz"]} → Add entity to message
- {"message_key": "msg-abc123", "entity_keys": ["ent-a", "ent-b"], "mode": "replace"} → Replace all links
- {"message_key": "msg-abc123", "entity_keys": ["ent-old"], "mode": "remove"} → Remove entity link

RETURNS: Updated message with new entity links.""",
        inputSchema={
            "type": "object",
            "properties": {
                "message_key": {"type": "string", "description": "The message key to update"},
                "entity_keys": {"type": "array", "items": {"type": "string"}, "description": "Entity keys to link/unlink"},
                "mode": {"type": "string", "description": "Link mode: add (default), replace, or remove", "default": "add"}
            },
            "required": ["message_key", "entity_keys"]
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def send_message(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Send a message to other agents or human coordinators via the message queue.

    Use this for inter-agent communication, status updates, questions, handoffs,
    and announcements that other agents and humans should see in the Messages UI.

    Args:
        channel: Channel name (e.g., 'general', 'backend', 'frontend', 'urgent')
        content: Message content (text or structured data)
        message_type: Type of message: 'status', 'announcement', 'request', 'task', 'message', 'acknowledged', 'waiting', 'resumed'
        to_agent: Optional specific agent ID or user_key to send to (null for broadcast to channel)
        reply_to: Optional message_key to reply to (creates a threaded conversation)
        priority: Priority level: 'normal', 'high', 'urgent' (default: 'normal')
        autonomous: Mark as autonomous task - receiver should work on it independently and reply when complete
        entity_keys: Optional list of entity keys to link this message to in the knowledge graph
        team_key: Optional team key to scope message to a specific team (null = domain-wide)
    """
    channel = arguments.get("channel", "general")
    content = arguments.get("content")
    message_type = arguments.get("message_type", "message")
    to_agent = arguments.get("to_agent")  # Can be agent_key or user_key
    reply_to = arguments.get("reply_to")
    priority = arguments.get("priority", "normal")
    autonomous = arguments.get("autonomous", False)
    entity_keys = arguments.get("entity_keys", [])
    team_key = arguments.get("team_key")

    if not content:
        return [types.TextContent(type="text", text="Error: content is required")]

    # Get sender agent_key from session (new schema uses keys, not IDs)
    from_key = session_state.get("agent_key")
    if not from_key:
        return [types.TextContent(
            type="text",
            text="Error: Not registered as an agent. Cannot send messages.\n\n"
                 "Use the identify tool to establish identity first."
        )]

    # Smart reply: if replying to a message sent directly to us, reply directly to sender
    auto_reply_to = None
    to_key = to_agent  # Will be set to specific recipient if provided
    if reply_to and not to_key:
        try:
            # Fetch the original message to check if it was a direct message to us
            orig_result = await _make_request(config, "GET", f"/messages/detail/{reply_to}")
            if orig_result.get("success"):
                orig_msg = orig_result.get("data", {})
                orig_to = orig_msg.get("to_key")
                orig_from = orig_msg.get("from_key")
                # If original was sent directly to me, reply directly to sender
                if orig_to == from_key and orig_from:
                    to_key = orig_from
                    auto_reply_to = orig_from
        except Exception:
            pass  # Fall back to broadcast if we can't fetch original

    try:
        payload = {
            "channel": channel,
            "from_key": from_key,
            "to_key": to_key,
            "message_type": message_type,
            "content": {"text": content} if isinstance(content, str) else content,
            "priority": priority,
            "autonomous": autonomous,
        }

        if reply_to:
            payload["reply_to_key"] = reply_to

        if entity_keys:
            payload["entity_keys"] = entity_keys

        # Team scoping - if specified, restrict message visibility to team members
        # If not specified, use active team from session (if set) or send domain-wide
        if team_key:
            payload["team_key"] = team_key
        elif session_state.get("active_team_key"):
            # Use session's active team if set
            payload["team_key"] = session_state.get("active_team_key")

        # Include domain context for multi-tenancy if available
        domain_key = session_state.get("domain_key")
        if domain_key:
            payload["domain_key"] = domain_key

        result = await _make_request(
            config,
            "POST",
            "/messages",
            json=payload,
            agent_id=session_state.get("agent_id"),  # For request tracking
        )

        if result.get("success"):
            msg_data = result.get("data", {})
            output = f"## Message Sent"
            if autonomous:
                output += " 🤖 (AUTONOMOUS TASK)"
            output += "\n\n"
            output += f"**Channel:** {channel}\n"
            output += f"**Type:** {message_type}\n"
            output += f"**Scope:** {msg_data.get('scope', 'broadcast-domain')}\n"
            if reply_to:
                output += f"**Reply to:** {reply_to}\n"
            if to_key:
                output += f"**To:** {to_key}"
                if auto_reply_to:
                    output += " (auto-routed reply to sender)"
                output += "\n"
            else:
                output += f"**To:** (broadcast)\n"
            output += f"**Priority:** {priority}\n"
            # Show team scope
            msg_team_key = msg_data.get('team_key')
            if msg_team_key:
                output += f"**Team Scope:** {msg_team_key}\n"
            else:
                output += f"**Team Scope:** Domain-wide\n"
            if autonomous:
                output += f"**Autonomous:** Yes - receiver should work on this and reply when complete\n"
            msg_entity_keys = msg_data.get('entity_keys') or []
            if msg_entity_keys:
                output += f"**Linked Entities:** {len(msg_entity_keys)} entity(s)\n"
            output += f"**Message Key:** {msg_data.get('message_key')}\n"
            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to send message')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error sending message: {str(e)}")]


async def get_messages(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get messages from the message queue.

    Use this to check for messages from other agents or human coordinators.
    Messages are filtered by scope to show those directed to you + all broadcasts.
    Retrieved messages are automatically marked as read.

    Args:
        channel: Channel to read from (optional, reads all if not specified)
        unread_only: Only get unread messages (default: True)
        limit: Maximum messages to retrieve (default: 20)
        since: Only return messages created after this ISO8601 timestamp (optional)
        team_key: Filter to a specific team's messages (optional, uses active team if set)
    """
    channel = arguments.get("channel")
    unread_only = arguments.get("unread_only", True)
    limit = arguments.get("limit", 20)
    since = arguments.get("since")
    team_key = arguments.get("team_key")

    # Get agent_key for per-agent read tracking (new schema uses keys)
    my_agent_key = session_state.get("agent_key")
    my_agent_id = session_state.get("agent_id")  # For display purposes

    try:
        if channel:
            endpoint = f"/messages/{channel}"
        else:
            endpoint = "/messages"

        params = {
            "unread_only": str(unread_only).lower(),
            "limit": str(limit),
        }

        # Use per-agent tracking if we have an agent_key
        if my_agent_key:
            params["for_agent"] = my_agent_key

        # Add time filter if specified
        if since:
            params["since"] = since

        # Team scope filtering - use explicit team_key or active team from session
        if team_key:
            params["team_key"] = team_key
        elif session_state.get("active_team_key"):
            params["team_key"] = session_state.get("active_team_key")

        # Add domain filter for multi-tenancy
        domain_key = session_state.get("domain_key")
        if domain_key:
            params["domain_key"] = domain_key

        result = await _make_request(config, "GET", endpoint, params=params)

        if result.get("success"):
            messages = result.get("data", {}).get("messages", [])
            unread_count = result.get("data", {}).get("unread_count", 0)

            if not messages:
                return [types.TextContent(type="text", text="No messages found.")]

            # Auto-mark retrieved messages as read (if we have an agent_key)
            marked_count = 0
            if my_agent_key:
                for msg in messages:
                    if not msg.get("is_read", False):
                        try:
                            await _make_request(
                                config,
                                "POST",
                                f"/messages/mark-read/{msg.get('message_key')}",
                                params={"reader_key": my_agent_key}
                            )
                            marked_count += 1
                        except Exception:
                            pass  # Don't fail the whole operation if marking fails

            output = f"## Messages"
            if channel:
                output += f" - #{channel}"
            output += f" ({len(messages)} found"
            if marked_count > 0:
                output += f", marked {marked_count} as read"
            output += ")\n\n"

            for msg in messages:
                from_key = msg.get("from_key")
                to_key = msg.get("to_key")
                is_mine = from_key == my_agent_key
                is_to_me = to_key == my_agent_key
                is_autonomous = msg.get("autonomous", False)
                scope = msg.get("scope", "broadcast-domain")

                # Status indicators
                if is_autonomous:
                    status = "🤖"  # Autonomous task
                elif msg.get("priority") == "urgent":
                    status = "⚠️"
                elif msg.get("priority") == "high":
                    status = "🚨"
                else:
                    status = "📭"

                output += f"{status} **{from_key}**"
                if is_mine:
                    output += " (you)"
                if to_key:
                    output += f" → {to_key}"
                    if is_to_me:
                        output += " (you)"
                output += f"\n"

                # Autonomous task banner
                if is_autonomous and not is_mine:
                    output += f"   🤖 **AUTONOMOUS TASK** - Work on this and reply when complete\n"

                output += f"   *{msg.get('message_type')}* in #{msg.get('channel')} [{scope}]"
                # Show team scope if set
                if msg.get('team_key'):
                    output += f" 👥"
                output += "\n"

                # Content
                content = msg.get("content", {})
                if isinstance(content, dict):
                    text = content.get("text", str(content))
                else:
                    text = str(content)
                output += f"   {text}\n"

                output += f"   Key: {msg.get('message_key')}\n\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to get messages')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting messages: {str(e)}")]


async def mark_message_read(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Mark a message as read.

    Uses per-agent read tracking - marks the message as read by YOU specifically.
    Other agents will still see the message as unread until they mark it.

    Args:
        message_key: The message key to mark as read
    """
    message_key = arguments.get("message_key")

    if not message_key:
        return [types.TextContent(type="text", text="Error: message_key is required")]

    # Get agent_key for per-agent read tracking (new schema uses reader_key)
    agent_key = session_state.get("agent_key")
    if not agent_key:
        return [types.TextContent(
            type="text",
            text="Error: Not registered as an agent. Cannot mark messages read.\n\n"
                 "Use the identify tool to establish your identity."
        )]

    try:
        result = await _make_request(
            config,
            "POST",
            f"/messages/mark-read/{message_key}",
            params={"reader_key": agent_key}
        )

        if result.get("success"):
            return [types.TextContent(type="text", text=f"Message {message_key} marked as read.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to mark message read')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error marking message read: {str(e)}")]


async def link_message_entities(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Link entities to an existing message.

    Use this to connect a message to relevant entities in the knowledge graph
    after the message has been created.

    Args:
        message_key: The message key to update
        entity_keys: List of entity keys to link
        mode: How to update links - 'add' (default), 'replace', or 'remove'
    """
    message_key = arguments.get("message_key")
    entity_keys = arguments.get("entity_keys", [])
    mode = arguments.get("mode", "add")

    if not message_key:
        return [types.TextContent(type="text", text="Error: message_key is required")]

    if not entity_keys and mode != "replace":
        return [types.TextContent(type="text", text="Error: entity_keys is required")]

    if mode not in ("add", "replace", "remove"):
        return [types.TextContent(type="text", text="Error: mode must be add, replace, or remove")]

    try:
        result = await _make_request(
            config,
            "PUT",
            f"/messages/detail/{message_key}/entities",
            json={"entity_keys": entity_keys, "mode": mode},
        )

        if result.get("success"):
            msg_data = result.get("data", {})
            new_keys = msg_data.get("entity_keys") or []
            output = f"## Entity Links Updated\n\n"
            output += f"**Message:** {message_key}\n"
            output += f"**Mode:** {mode}\n"
            output += f"**Linked Entities:** {len(new_keys)}\n"
            if new_keys:
                output += f"**Keys:** {', '.join(new_keys)}\n"
            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to update entity links')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error updating entity links: {str(e)}")]


async def mark_all_messages_read(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Mark all unread messages as read for you.

    Uses per-agent read tracking - marks messages as read by YOU specifically.
    Other agents will still see the messages as unread until they mark them.

    Args:
        channel: Only mark messages in this channel as read (optional)
        team_key: Only mark messages in this team as read (optional)
    """
    channel = arguments.get("channel")
    team_key = arguments.get("team_key")

    # Get agent_key for per-agent read tracking (new schema uses reader_key)
    agent_key = session_state.get("agent_key")
    if not agent_key:
        return [types.TextContent(
            type="text",
            text="Error: Not registered as an agent. Cannot mark messages read.\n\n"
                 "Use the identify tool to establish your identity."
        )]

    try:
        params = {"reader_key": agent_key}
        if channel:
            params["channel"] = channel
        # Team scope filtering - use explicit team_key or active team from session
        if team_key:
            params["team_key"] = team_key
        elif session_state.get("active_team_key"):
            params["team_key"] = session_state.get("active_team_key")

        result = await _make_request(
            config,
            "POST",
            "/messages/mark-all-read",
            params=params
        )

        if result.get("success"):
            count = result.get("data", {}).get("marked_count", 0)
            filter_parts = []
            if channel:
                filter_parts.append(f"#{channel}")
            if params.get("team_key"):
                filter_parts.append(f"team:{params.get('team_key')}")
            filter_str = f" in {', '.join(filter_parts)}" if filter_parts else ""
            return [types.TextContent(type="text", text=f"Marked {count} messages as read{filter_str}.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to mark messages read')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error marking messages read: {str(e)}")]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "send_message": send_message,
    "get_messages": get_messages,
    "mark_message_read": mark_message_read,
    "mark_all_messages_read": mark_all_messages_read,
    "link_message_entities": link_message_entities,
}
