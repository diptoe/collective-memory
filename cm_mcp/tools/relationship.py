"""
Relationship Tools

MCP tools for relationship operations on the knowledge graph.
"""

import json
import mcp.types as types
from typing import Any

from .utils import _make_request, is_guest_session, reject_guest_write


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="list_relationships",
        description="""List relationships in the knowledge graph, optionally filtered by entity.

USE THIS WHEN: You want to understand how entities are connected, or explore the graph structure.

EXAMPLES:
- All relationships: {}
- For specific entity: {"entity_key": "ent-abc123"}

COMMON RELATIONSHIP TYPES:
- WORKS_ON: Person → Project
- KNOWS: Person → Person
- USES: Project/Person → Technology
- CREATED: Person/Agent → Any
- BELONGS_TO: Entity → Organization
- RELATED_TO: Generic relationship

RETURNS: Relationships with from/to entity keys, types, and properties.""",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_key": {"type": "string", "description": "Show only relationships involving this entity"},
                "limit": {"type": "integer", "description": "Maximum results (default 20)", "default": 20}
            }
        }
    ),
    types.Tool(
        name="create_relationship",
        description="""Create a relationship between two entities. Your agent ID is recorded as the creator.

USE THIS WHEN: You discover a connection between entities that should be captured in the graph.

RELATIONSHIP TYPES:
- WORKS_ON: Person works on Project
- KNOWS: Person knows Person
- USES: Project/Person uses Technology
- CREATED: Person/Agent created Project/Document
- BELONGS_TO: Entity belongs to Organization
- RELATED_TO: General relationship (use when others don't fit)

EXAMPLES:
- {"from_entity_key": "ent-sarah", "to_entity_key": "ent-dashboard", "relationship_type": "WORKS_ON", "properties": {"role": "Tech Lead"}}
- {"from_entity_key": "ent-dashboard", "to_entity_key": "ent-react", "relationship_type": "USES"}

RETURNS: The created relationship with its assigned relationship_key.""",
        inputSchema={
            "type": "object",
            "properties": {
                "from_entity_key": {"type": "string", "description": "Source entity key (the 'from' side)"},
                "to_entity_key": {"type": "string", "description": "Target entity key (the 'to' side)"},
                "relationship_type": {"type": "string", "description": "WORKS_ON, KNOWS, USES, CREATED, BELONGS_TO, RELATED_TO, or custom"},
                "properties": {"type": "object", "description": "Additional properties for the relationship"}
            },
            "required": ["from_entity_key", "to_entity_key", "relationship_type"]
        }
    ),
    types.Tool(
        name="delete_relationship",
        description="""Delete a relationship from the knowledge graph.

USE THIS WHEN: You need to remove a connection between entities that is no longer valid or was created in error.

EXAMPLE: {"relationship_key": "rel-abc123"}

CAUTION: This permanently removes the relationship. Use list_relationships first to confirm the correct key.

RETURNS: Confirmation of deletion.""",
        inputSchema={
            "type": "object",
            "properties": {
                "relationship_key": {"type": "string", "description": "The unique relationship key to delete"}
            },
            "required": ["relationship_key"]
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

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

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {"limit": limit}
        if entity_key:
            params["entity"] = entity_key  # API expects "entity" not "entity_key"

        result = await _make_request(config, "GET", "/relationships", params=params, agent_id=agent_id)

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
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("create_relationship")

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

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None) or "unknown"

    # Add source to properties for tracking
    if "created_by" not in properties:
        properties["created_by"] = f"agent:{agent_id}"

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
            },
            agent_id=agent_id,
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


async def delete_relationship(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Delete a relationship from the knowledge graph.

    Args:
        relationship_key: The unique key of the relationship to delete
    """
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("delete_relationship")

    relationship_key = arguments.get("relationship_key")

    if not relationship_key:
        return [types.TextContent(type="text", text="Error: relationship_key is required")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        result = await _make_request(
            config,
            "DELETE",
            f"/relationships/{relationship_key}",
            agent_id=agent_id,
        )

        if result.get("success"):
            return [types.TextContent(type="text", text=f"Relationship '{relationship_key}' deleted successfully.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to delete relationship')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error deleting relationship: {str(e)}")]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "list_relationships": list_relationships,
    "create_relationship": create_relationship,
    "delete_relationship": delete_relationship,
}