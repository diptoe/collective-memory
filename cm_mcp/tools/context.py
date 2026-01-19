"""
Context Tools

MCP tools for context and RAG operations.
"""

import json
import mcp.types as types
from typing import Any

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="get_context",
        description="""Get relevant context from the knowledge graph for answering a question or completing a task.

USE THIS WHEN: You need background knowledge from the graph to inform your response. This is the primary RAG tool.

HOW IT WORKS: Searches for relevant entities and their relationships, returning a structured context package.

EXAMPLES:
- {"query": "What technologies does the dashboard project use?"}
- {"query": "Who is working on authentication?", "max_entities": 10}

RETURNS: Relevant entities, their relationships, and a formatted context summary.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or topic you need context for"},
                "max_entities": {"type": "integer", "description": "Maximum entities to include (default 5)", "default": 5}
            },
            "required": ["query"]
        }
    ),
    types.Tool(
        name="get_entity_context",
        description="""Get detailed context around a specific entity, including all its relationships.

USE THIS WHEN: You have a specific entity and want to understand its full context - what it's connected to.

EXAMPLES:
- {"entity_key": "ent-sarah"} → Sarah's projects, technologies, colleagues
- {"entity_key": "ent-dashboard", "depth": 2} → Dashboard's tech stack AND what uses those technologies

RETURNS: The entity, all related entities, and the relationships connecting them.""",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_key": {"type": "string", "description": "The entity to get context for"},
                "depth": {"type": "integer", "description": "How many relationship hops to follow (1=direct, 2=includes neighbors' neighbors)", "default": 1}
            },
            "required": ["entity_key"]
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

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

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # Search for relevant entities
        params = {"search": query, "limit": max_entities}

        # Add domain filter for multi-tenancy
        domain_key = session_state.get("domain_key")
        if domain_key:
            params["domain"] = domain_key

        result = await _make_request(config, "GET", "/entities", params=params, agent_id=agent_id)

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
                        params={"entity": entity_key, "limit": 5},  # API expects "entity"
                        agent_id=agent_id,
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

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # Get the entity
        entity_result = await _make_request(config, "GET", f"/entities/{entity_key}", agent_id=agent_id)

        if not entity_result.get("success"):
            return [types.TextContent(type="text", text=f"Error: Entity not found: {entity_key}")]

        entity = entity_result.get("data", {}).get("entity", {})

        output = f"## Entity Context: {entity.get('name')}\n\n"
        output += f"**Type:** {entity.get('entity_type')}\n"
        output += f"**Key:** {entity.get('entity_key')}\n\n"

        props = entity.get('properties', {})
        if props:
            output += "### Properties\n"
            output += f"```json\n{json.dumps(props, indent=2)}\n```\n\n"

        # Use the neighbors endpoint for proper depth traversal
        neighbors_result = await _make_request(
            config, "POST", "/context/neighbors",
            json={"entity_key": entity_key, "max_hops": depth},
            agent_id=agent_id,
        )

        if neighbors_result.get("success"):
            data = neighbors_result.get("data", {})
            neighbor_entities = data.get("entities", [])
            relationships = data.get("relationships", [])

            # Show related entities
            if neighbor_entities:
                output += f"### Related Entities (depth={depth})\n"
                for e in neighbor_entities:
                    output += f"- **{e['name']}** ({e['entity_type']})\n"
                output += "\n"

            # Categorize relationships
            outgoing = [r for r in relationships if r['from_entity_key'] == entity_key]
            incoming = [r for r in relationships if r['to_entity_key'] == entity_key]
            other = [r for r in relationships if r['from_entity_key'] != entity_key and r['to_entity_key'] != entity_key]

            if outgoing:
                output += "### Outgoing Relationships\n"
                for r in outgoing:
                    # Find target entity name
                    target = next((e for e in neighbor_entities if e['entity_key'] == r['to_entity_key']), None)
                    target_name = target['name'] if target else r['to_entity_key']
                    output += f"- **{r['relationship_type']}** → {target_name}\n"
                output += "\n"

            if incoming:
                output += "### Incoming Relationships\n"
                for r in incoming:
                    # Find source entity name
                    source = next((e for e in neighbor_entities if e['entity_key'] == r['from_entity_key']), None)
                    source_name = source['name'] if source else r['from_entity_key']
                    output += f"- {source_name} → **{r['relationship_type']}**\n"
                output += "\n"

            if other and depth > 1:
                output += "### Extended Graph Relationships\n"
                for r in other:
                    # Find both entity names
                    source = next((e for e in neighbor_entities if e['entity_key'] == r['from_entity_key']), None)
                    target = next((e for e in neighbor_entities if e['entity_key'] == r['to_entity_key']), None)
                    source_name = source['name'] if source else r['from_entity_key']
                    target_name = target['name'] if target else r['to_entity_key']
                    output += f"- {source_name} **{r['relationship_type']}** → {target_name}\n"
                output += "\n"

            if not relationships:
                output += "### Relationships\nNo relationships found for this entity.\n"
        else:
            # Fallback to simple relationship lookup if neighbors endpoint fails
            rel_result = await _make_request(
                config, "GET", "/relationships",
                params={"entity": entity_key, "limit": 20},  # API expects "entity"
                agent_id=agent_id,
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

        # Fetch linked messages
        try:
            msg_params = {"entity_key": entity_key, "limit": 10}
            # Add domain filter for multi-tenancy
            domain_key = session_state.get("domain_key")
            if domain_key:
                msg_params["domain_key"] = domain_key

            messages_result = await _make_request(
                config, "GET", "/messages",
                params=msg_params,
                agent_id=agent_id,
            )
            if messages_result.get("success"):
                messages = messages_result.get("data", {}).get("messages", [])
                if messages:
                    output += f"\n### Linked Messages ({len(messages)})\n"
                    for msg in messages:
                        from_agent = msg.get('from_agent', 'unknown')
                        content = msg.get('content', '')
                        if isinstance(content, dict):
                            content = content.get('text', str(content))
                        content = str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
                        output += f"- [{msg.get('message_key')}] {from_agent}: {content}\n"
        except Exception:
            pass  # Don't fail if messages can't be fetched

        return [types.TextContent(type="text", text=output)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting entity context: {str(e)}")]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "get_context": get_context,
    "get_entity_context": get_entity_context,
}