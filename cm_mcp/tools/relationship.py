"""
Relationship Tools

MCP tools for relationship operations on the knowledge graph.
"""

import json
import mcp.types as types
from typing import Any

from .utils import _make_request


async def list_relationships(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List relationships, optionally filtered by entity.

    Args:
        entity_key: Optional entity key to filter relationships
        limit: Maximum results (default 20)
    """
    entity_key = arguments.get("entity_key")
    limit = arguments.get("limit", 20)

    try:
        params = {"limit": limit}
        if entity_key:
            params["entity"] = entity_key  # API expects "entity" not "entity_key"

        result = await _make_request(config, "GET", "/relationships", params=params)

        if result.get("success"):
            relationships = result.get("data", {}).get("relationships", [])
            if relationships:
                output = f"Found {len(relationships)} relationships:\n\n"
                for r in relationships:
                    output += f"- **{r['relationship_type']}**\n"
                    output += f"  From: {r['from_entity_key']} → To: {r['to_entity_key']}\n"
                    output += f"  Key: {r['relationship_key']}\n"
                    if r.get('properties'):
                        output += f"  Properties: {json.dumps(r['properties'])}\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No relationships found.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing relationships: {str(e)}")]


async def create_relationship(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Create a relationship between two entities.

    Args:
        from_entity_key: Source entity key
        to_entity_key: Target entity key
        relationship_type: Type of relationship (e.g., WORKS_ON, KNOWS, USES)
        properties: Optional properties dictionary
    """
    from_entity_key = arguments.get("from_entity_key")
    to_entity_key = arguments.get("to_entity_key")
    relationship_type = arguments.get("relationship_type")
    properties = arguments.get("properties", {})

    if not from_entity_key:
        return [types.TextContent(type="text", text="Error: from_entity_key is required")]
    if not to_entity_key:
        return [types.TextContent(type="text", text="Error: to_entity_key is required")]
    if not relationship_type:
        return [types.TextContent(type="text", text="Error: relationship_type is required")]

    # Track which agent created this relationship
    source = session_state.get("agent_id") or "unknown"

    # Add source to properties for tracking
    if "created_by" not in properties:
        properties["created_by"] = f"agent:{source}"

    try:
        result = await _make_request(
            config,
            "POST",
            "/relationships",
            json={
                "from_entity_key": from_entity_key,
                "to_entity_key": to_entity_key,
                "relationship_type": relationship_type,
                "properties": properties,
            }
        )

        if result.get("success"):
            rel = result.get("data", {})
            output = f"Relationship created successfully!\n\n"
            output += f"**Type:** {rel.get('relationship_type')}\n"
            output += f"**From:** {rel.get('from_entity_key')}\n"
            output += f"**To:** {rel.get('to_entity_key')}\n"
            output += f"**Key:** {rel.get('relationship_key')}\n"
            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to create relationship')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error creating relationship: {str(e)}")]
