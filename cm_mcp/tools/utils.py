"""
Collective Memory MCP Tools - Shared Utilities

Common utilities for MCP tool implementations.
"""

import httpx
from typing import Any, Optional


async def _make_request(
    config: Any,
    method: str,
    endpoint: str,
    json: dict = None,
    params: dict = None,
) -> dict:
    """
    Make HTTP request to the Collective Memory API.

    Args:
        config: Configuration object with api_endpoint and timeout
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path (e.g., "/entities")
        json: JSON body data for POST/PUT requests
        params: Query parameters for GET requests

    Returns:
        Parsed JSON response as dict
    """
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        url = f"{config.api_endpoint}{endpoint}"
        response = await client.request(
            method=method,
            url=url,
            json=json,
            params=params,
        )
        response.raise_for_status()
        return response.json()
