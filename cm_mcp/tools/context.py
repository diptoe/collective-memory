"""
Context Tools

MCP tools for context and RAG operations.
"""

import json
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


async def get_context(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get RAG context for a query from the knowledge graph.

    Args:
        query: The query to get context for
        max_entities: Maximum entities to include (default 5)
    """
    query = arguments.get("query")
    max_entities = arguments.get("max_entities", 5)

    if not query:
        return [types.TextContent(type="text", text="Error: query is required")]

    try:
        # Search for relevant entities
        params = {"search": query, "limit": max_entities}
        result = await _make_request(config, "GET", "/entities", params=params)

        if result.get("success"):
            entities = result.get("data", {}).get("entities", [])

            if not entities:
                return [types.TextContent(type="text", text=f"No relevant context found for query: {query}")]

            # Build context text
            output = f"## Knowledge Graph Context for: \"{query}\"\n\n"
            output += f"Found {len(entities)} relevant entities:\n\n"

            for entity in entities:
                output += f"### {entity['name']} ({entity['entity_type']})\n"
                props = entity.get('properties', {})
                if props:
                    for key, value in props.items():
                        if isinstance(value, str) and len(value) > 200:
                            value = value[:200] + "..."
                        output += f"- **{key}:** {value}\n"
                output += "\n"

            # Get relationships for these entities
            entity_keys = [e['entity_key'] for e in entities]
            rel_output = "\n## Relationships\n\n"
            has_rels = False

            for entity_key in entity_keys[:3]:  # Limit relationship lookups
                try:
                    rel_result = await _make_request(
                        config, "GET", "/relationships",
                        params={"entity_key": entity_key, "limit": 5}
                    )
                    rels = rel_result.get("data", {}).get("relationships", [])
                    for r in rels:
                        rel_output += f"- {r['from_entity_key']} **{r['relationship_type']}** {r['to_entity_key']}\n"
                        has_rels = True
                except:
                    pass

            if has_rels:
                output += rel_output

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to get context')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting context: {str(e)}")]


async def get_entity_context(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get detailed context around a specific entity.

    Args:
        entity_key: The entity key to get context for
        depth: How many relationship hops to include (default 1)
    """
    entity_key = arguments.get("entity_key")
    depth = arguments.get("depth", 1)

    if not entity_key:
        return [types.TextContent(type="text", text="Error: entity_key is required")]

    try:
        # Get the entity
        entity_result = await _make_request(config, "GET", f"/entities/{entity_key}")

        if not entity_result.get("success"):
            return [types.TextContent(type="text", text=f"Error: Entity not found: {entity_key}")]

        entity = entity_result.get("data", {})

        output = f"## Entity Context: {entity.get('name')}\n\n"
        output += f"**Type:** {entity.get('entity_type')}\n"
        output += f"**Key:** {entity.get('entity_key')}\n\n"

        props = entity.get('properties', {})
        if props:
            output += "### Properties\n"
            output += f"```json\n{json.dumps(props, indent=2)}\n```\n\n"

        # Get relationships
        rel_result = await _make_request(
            config, "GET", "/relationships",
            params={"entity_key": entity_key, "limit": 20}
        )

        if rel_result.get("success"):
            rels = rel_result.get("data", {}).get("relationships", [])

            outgoing = [r for r in rels if r['from_entity_key'] == entity_key]
            incoming = [r for r in rels if r['to_entity_key'] == entity_key]

            if outgoing:
                output += "### Outgoing Relationships\n"
                for r in outgoing:
                    output += f"- **{r['relationship_type']}** → {r['to_entity_key']}\n"
                output += "\n"

            if incoming:
                output += "### Incoming Relationships\n"
                for r in incoming:
                    output += f"- {r['from_entity_key']} → **{r['relationship_type']}**\n"
                output += "\n"

            if not outgoing and not incoming:
                output += "### Relationships\nNo relationships found for this entity.\n"

        return [types.TextContent(type="text", text=output)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting entity context: {str(e)}")]
