"""
Entity Tools

MCP tools for entity operations on the knowledge graph.
"""

import json
import mcp.types as types
from typing import Any

from .utils import _make_request


async def search_entities(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Search entities in the knowledge graph.

    Args:
        query: Search query string
        entity_type: Optional filter by entity type
        limit: Maximum results (default 10)
    """
    query = arguments.get("query", "")
    entity_type = arguments.get("entity_type")
    limit = arguments.get("limit", 10)

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {"limit": limit}
        if query:
            params["search"] = query
        if entity_type:
            params["entity_type"] = entity_type

        result = await _make_request(config, "GET", "/entities", params=params, agent_id=agent_id)

        if result.get("success"):
            entities = result.get("data", {}).get("entities", [])
            if entities:
                output = f"Found {len(entities)} entities:\n\n"
                for e in entities:
                    output += f"- **{e['name']}** ({e['entity_type']})\n"
                    output += f"  Key: {e['entity_key']}\n"
                    if e.get('properties'):
                        output += f"  Properties: {json.dumps(e['properties'])}\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No entities found matching your query.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error searching entities: {str(e)}")]


async def get_entity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get a specific entity by key.

    Args:
        entity_key: The entity key to retrieve
    """
    entity_key = arguments.get("entity_key")

    if not entity_key:
        return [types.TextContent(type="text", text="Error: entity_key is required")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        result = await _make_request(config, "GET", f"/entities/{entity_key}", agent_id=agent_id)

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})
            output = f"# {entity.get('name', 'Unknown')}\n\n"
            output += f"**Type:** {entity.get('entity_type', 'Unknown')}\n"
            output += f"**Key:** {entity.get('entity_key')}\n"

            props = entity.get('properties', {})
            if props:
                output += f"\n**Properties:**\n```json\n{json.dumps(props, indent=2)}\n```\n"

            output += f"\n**Created:** {entity.get('created_at', 'Unknown')}\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Entity not found')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting entity: {str(e)}")]


async def create_entity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Create a new entity in the knowledge graph.

    Args:
        name: Entity name
        entity_type: Type (Person, Project, Technology, etc.)
        properties: Optional properties dictionary
    """
    name = arguments.get("name")
    entity_type = arguments.get("entity_type")
    properties = arguments.get("properties", {})

    if not name:
        return [types.TextContent(type="text", text="Error: name is required")]
    if not entity_type:
        return [types.TextContent(type="text", text="Error: entity_type is required")]

    # Track which agent created this entity
    agent_id = session_state.get("agent_id") or "unknown"

    try:
        result = await _make_request(
            config,
            "POST",
            "/entities",
            json={
                "name": name,
                "entity_type": entity_type,
                "properties": properties,
                "source": f"agent:{agent_id}",
            },
            agent_id=agent_id,
        )

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})
            output = f"Entity created successfully!\n\n"
            output += f"**Name:** {entity.get('name')}\n"
            output += f"**Type:** {entity.get('entity_type')}\n"
            output += f"**Key:** {entity.get('entity_key')}\n"
            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to create entity')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error creating entity: {str(e)}")]


async def update_entity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update an existing entity.

    Args:
        entity_key: The entity key to update
        name: New name (optional)
        entity_type: New type (optional)
        properties: New properties (optional)
    """
    entity_key = arguments.get("entity_key")

    if not entity_key:
        return [types.TextContent(type="text", text="Error: entity_key is required")]

    update_data = {}
    if "name" in arguments:
        update_data["name"] = arguments["name"]
    if "entity_type" in arguments:
        update_data["entity_type"] = arguments["entity_type"]
    if "properties" in arguments:
        update_data["properties"] = arguments["properties"]

    if not update_data:
        return [types.TextContent(type="text", text="Error: No update fields provided")]

    agent_id = session_state.get("agent_id")

    try:
        result = await _make_request(
            config,
            "PUT",
            f"/entities/{entity_key}",
            json=update_data,
            agent_id=agent_id,
        )

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})
            output = f"Entity updated successfully!\n\n"
            output += f"**Name:** {entity.get('name')}\n"
            output += f"**Type:** {entity.get('entity_type')}\n"
            output += f"**Key:** {entity.get('entity_key')}\n"
            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to update entity')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error updating entity: {str(e)}")]


async def search_entities_semantic(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Semantic search for entities using natural language.

    Uses OpenAI embeddings for semantic similarity matching.

    Args:
        query: Natural language search query
        entity_type: Optional filter by entity type
        limit: Maximum results (default 10)
    """
    query = arguments.get("query")
    entity_type = arguments.get("entity_type")
    limit = arguments.get("limit", 10)

    if not query:
        return [types.TextContent(type="text", text="Error: query is required")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        params = {"query": query, "limit": limit}
        if entity_type:
            params["type"] = entity_type

        result = await _make_request(config, "GET", "/search/semantic", params=params, agent_id=agent_id)

        if result.get("success"):
            data = result.get("data", {})
            entities = data.get("entities", [])
            documents = data.get("documents", [])

            output = f"# Semantic Search Results for: \"{query}\"\n\n"

            if entities:
                output += f"## Entities ({len(entities)})\n\n"
                for e in entities:
                    output += f"- **{e['name']}** ({e['entity_type']})\n"
                    output += f"  Key: {e['entity_key']}\n"
            else:
                output += "No matching entities found.\n"

            if documents:
                output += f"\n## Documents ({len(documents)})\n\n"
                for d in documents:
                    output += f"- **{d['title']}**\n"
                    output += f"  Key: {d['document_key']}\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Search failed')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error in semantic search: {str(e)}")]


async def extract_entities_from_text(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Extract named entities from text using NER.

    Uses spaCy for Named Entity Recognition.

    Args:
        text: Text to extract entities from
        auto_create: Whether to automatically create extracted entities (default False)
    """
    text = arguments.get("text")
    auto_create = arguments.get("auto_create", False)

    if not text:
        return [types.TextContent(type="text", text="Error: text is required")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        result = await _make_request(
            config,
            "POST",
            "/ner/extract",
            json={
                "text": text,
                "auto_create": auto_create,
            },
            agent_id=agent_id,
        )

        if result.get("success"):
            data = result.get("data", {})
            extracted = data.get("extracted", [])
            existing = data.get("existing", [])
            created = data.get("created", [])
            suggestions = data.get("suggestions", [])

            output = f"# Entity Extraction Results\n\n"
            output += f"**Total extracted:** {len(extracted)}\n\n"

            if existing:
                output += f"## Existing Entities ({len(existing)})\n"
                for e in existing:
                    output += f"- **{e['name']}** ({e['entity_type']}) - Key: {e['entity_key']}\n"
                output += "\n"

            if created:
                output += f"## Created Entities ({len(created)})\n"
                for e in created:
                    output += f"- **{e['name']}** ({e['entity_type']})\n"
                output += "\n"

            if suggestions:
                output += f"## Suggested Entities ({len(suggestions)})\n"
                output += "These entities were found but not created:\n"
                for e in suggestions:
                    output += f"- **{e['name']}** ({e['entity_type']}) - spaCy label: {e['original_label']}\n"
                output += "\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Extraction failed')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error extracting entities: {str(e)}")]
