"""
Message Tools

MCP tools for inter-agent messaging queue operations in Collective Memory (CM).
"""

import mcp.types as types
from typing import Any

from .utils import _make_request


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
        message_type: Type of message: 'status', 'announcement', 'request', 'task', 'message'
        to_agent: Optional specific agent ID to send to (null for broadcast to channel)
        reply_to: Optional message_key to reply to (creates a threaded conversation)
        priority: Priority level: 'normal', 'high', 'urgent' (default: 'normal')
    """
    channel = arguments.get("channel", "general")
    content = arguments.get("content")
    message_type = arguments.get("message_type", "message")
    to_agent = arguments.get("to_agent")
    reply_to = arguments.get("reply_to")
    priority = arguments.get("priority", "normal")

    if not content:
        return [types.TextContent(type="text", text="Error: content is required")]

    # Get sender agent ID from session
    from_agent = session_state.get("agent_id")
    if not from_agent:
        return [types.TextContent(
            type="text",
            text="Error: Not registered as an agent. Cannot send messages.\n\n"
                 "Set CM_AGENT_ID environment variable to establish identity."
        )]

    try:
        payload = {
            "channel": channel,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": {"text": content} if isinstance(content, str) else content,
            "priority": priority,
        }

        if reply_to:
            payload["reply_to_key"] = reply_to

        result = await _make_request(
            config,
            "POST",
            "/messages",
            json=payload
        )

        if result.get("success"):
            msg_data = result.get("data", {})
            output = f"## Message Sent\n\n"
            output += f"**Channel:** {channel}\n"
            output += f"**Type:** {message_type}\n"
            if reply_to:
                output += f"**Reply to:** {reply_to}\n"
            if to_agent:
                output += f"**To:** {to_agent}\n"
            else:
                output += f"**To:** (broadcast)\n"
            output += f"**Priority:** {priority}\n"
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
    Messages are filtered to show those directed to you + all broadcasts.
    Retrieved messages are automatically marked as read.

    Args:
        channel: Channel to read from (optional, reads all if not specified)
        unread_only: Only get unread messages (default: True)
        limit: Maximum messages to retrieve (default: 20)
    """
    channel = arguments.get("channel")
    unread_only = arguments.get("unread_only", True)
    limit = arguments.get("limit", 20)

    # Get agent ID for per-agent read tracking
    my_agent_id = session_state.get("agent_id")

    try:
        if channel:
            endpoint = f"/messages/{channel}"
        else:
            endpoint = "/messages"

        params = {
            "unread_only": str(unread_only).lower(),
            "limit": str(limit),
        }

        # Use per-agent tracking if we have an agent ID
        if my_agent_id:
            params["for_agent"] = my_agent_id

        result = await _make_request(config, "GET", endpoint, params=params)

        if result.get("success"):
            messages = result.get("data", {}).get("messages", [])
            unread_count = result.get("data", {}).get("unread_count", 0)

            if not messages:
                return [types.TextContent(type="text", text="No messages found.")]

            # Auto-mark retrieved messages as read (if we have an agent ID)
            marked_count = 0
            if my_agent_id:
                for msg in messages:
                    if not msg.get("is_read", False):
                        try:
                            await _make_request(
                                config,
                                "POST",
                                f"/messages/mark-read/{msg.get('message_key')}",
                                params={"agent_id": my_agent_id}
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
                is_mine = msg.get("from_agent") == my_agent_id
                is_to_me = msg.get("to_agent") == my_agent_id

                # Status indicators (all now read since we just marked them)
                status = "📭"  # Read
                if msg.get("priority") == "high":
                    status = "🚨"
                elif msg.get("priority") == "urgent":
                    status = "⚠️"

                output += f"{status} **{msg.get('from_agent')}**"
                if is_mine:
                    output += " (you)"
                if msg.get("to_agent"):
                    output += f" → {msg.get('to_agent')}"
                    if is_to_me:
                        output += " (you)"
                output += f"\n"

                output += f"   *{msg.get('message_type')}* in #{msg.get('channel')}\n"

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

    # Get agent ID for per-agent read tracking
    agent_id = session_state.get("agent_id")
    if not agent_id:
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
            params={"agent_id": agent_id}
        )

        if result.get("success"):
            return [types.TextContent(type="text", text=f"Message {message_key} marked as read.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to mark message read')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error marking message read: {str(e)}")]


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
    """
    channel = arguments.get("channel")

    # Get agent ID for per-agent read tracking (required)
    agent_id = session_state.get("agent_id")
    if not agent_id:
        return [types.TextContent(
            type="text",
            text="Error: Not registered as an agent. Cannot mark messages read.\n\n"
                 "Use the identify tool to establish your identity."
        )]

    try:
        params = {"agent_id": agent_id}
        if channel:
            params["channel"] = channel

        result = await _make_request(
            config,
            "POST",
            "/messages/mark-all-read",
            params=params
        )

        if result.get("success"):
            count = result.get("data", {}).get("marked_count", 0)
            filter_str = f" in #{channel}" if channel else ""
            return [types.TextContent(type="text", text=f"Marked {count} messages as read{filter_str}.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to mark messages read')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error marking messages read: {str(e)}")]
