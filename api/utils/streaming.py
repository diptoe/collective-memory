"""
Collective Memory Platform - SSE Streaming Utilities

Server-Sent Events (SSE) utilities for streaming AI responses.
"""

import json
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any


def sse_format(data: Dict[str, Any]) -> str:
    """
    Format data as an SSE message.

    Args:
        data: Dictionary to serialize as JSON

    Returns:
        SSE-formatted string
    """
    return f"data: {json.dumps(data)}\n\n"


def sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format data as a named SSE event.

    Args:
        event_type: Event type name
        data: Dictionary to serialize as JSON

    Returns:
        SSE-formatted string with event type
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def sse_error(message: str) -> str:
    """Format an error as an SSE message."""
    return sse_format({
        'type': 'error',
        'content': message,
        'done': True
    })


def sse_done(message_key: str = None, usage: Dict[str, int] = None) -> str:
    """Format a completion message as SSE."""
    data = {'type': 'done', 'done': True}
    if message_key:
        data['message_key'] = message_key
    if usage:
        data['usage'] = usage
    return sse_format(data)


async def async_to_sync_generator(
    async_gen: AsyncGenerator
) -> Generator:
    """
    Convert an async generator to a sync generator.

    Used to bridge async streaming with Flask's sync Response.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while True:
            try:
                item = loop.run_until_complete(async_gen.__anext__())
                yield item
            except StopAsyncIteration:
                break
    finally:
        loop.close()


def create_streaming_response(headers: Dict[str, str] = None) -> Dict[str, str]:
    """
    Create headers for an SSE streaming response.

    Returns:
        Dictionary of response headers
    """
    default_headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',  # Disable nginx buffering
    }
    if headers:
        default_headers.update(headers)
    return default_headers
