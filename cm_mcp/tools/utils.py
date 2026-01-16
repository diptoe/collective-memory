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
    agent_id: str = None,
) -> dict:
    """
    Make HTTP request to the Collective Memory API.

    Args:
        config: Configuration object with api_endpoint, timeout, and optional pat
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path (e.g., "/entities")
        json: JSON body data for POST/PUT requests
        params: Query parameters for GET requests
        agent_id: Agent ID to include in X-Agent-Id header for activity tracking

    Returns:
        Parsed JSON response as dict
    """
    headers = {}
    if agent_id:
        headers['X-Agent-Id'] = agent_id

    # Include PAT authentication if configured
    if hasattr(config, 'pat') and config.pat:
        headers['Authorization'] = f'Bearer {config.pat}'

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            url = f"{config.api_endpoint}{endpoint}"
            response = await client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers if headers else None,
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        # Connection/transport issues (DNS, refused port, etc.)
        raise RuntimeError(
            f"Failed to reach CM API at {config.api_endpoint}. "
            "Check CM_API_URL (current value shown) and ensure the API is running and reachable. "
            f"Details: {str(e)}"
        ) from e
    except httpx.HTTPStatusError as e:
        # API returned a non-2xx response
        body_snippet = ""
        if e.response is not None and e.response.text:
            body_snippet = f" Response body: {e.response.text[:300]}"
        raise RuntimeError(
            f"CM API returned {e.response.status_code} for {e.request.url}.{body_snippet}"
        ) from e
