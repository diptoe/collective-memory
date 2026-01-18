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
            params["type"] = entity_type  # API expects "type" not "entity_type"

        # Add domain filter for multi-tenancy
        domain_key = session_state.get("domain_key")
        if domain_key:
            params["domain"] = domain_key

        result = await _make_request(config, "GET", "/entities", params=params, agent_id=agent_id)

        if result.get("success"):
            entities = result.get("data", {}).get("entities", [])
            if entities:
                output = f"Found {len(entities)} entities"
                if domain_key:
                    output += f" (domain: {domain_key})"
                output += ":\n\n"
                for e in entities:
                    output += f"- **{e['name']}** ({e['entity_type']})\n"
                    output += f"  Key: {e['entity_key']}\n"
                    if e.get('properties'):
                        output += f"  Properties: {json.dumps(e['properties'])}\n"
                return [types.TextContent(type="text", text=output)]
            else:
                msg = "No entities found matching your query"
                if domain_key:
                    msg += f" (domain: {domain_key})"
                msg += "."
                return [types.TextContent(type="text", text=msg)]
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

            # Show domain and source attribution
            if entity.get('domain_key'):
                output += f"**Domain:** {entity.get('domain_key')}\n"
            if entity.get('source'):
                output += f"**Source:** {entity.get('source')}\n"

            # Show scope information
            scope_type = entity.get('scope_type')
            scope_key = entity.get('scope_key')
            scope_name = entity.get('scope_name')
            if scope_type:
                scope_display = f"{scope_type}"
                if scope_name:
                    scope_display += f" ({scope_name})"
                elif scope_key:
                    scope_display += f" ({scope_key})"
                output += f"**Scope:** {scope_display}\n"
            else:
                output += f"**Scope:** domain (default)\n"

            props = entity.get('properties', {})
            if props:
                output += f"\n**Properties:**\n```json\n{json.dumps(props, indent=2)}\n```\n"

            output += f"\n**Created:** {entity.get('created_at', 'Unknown')}\n"

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
        scope_type: Optional scope type ('domain', 'team', 'user')
        scope_key: Optional scope key (team_key or user_key)
    """
    name = arguments.get("name")
    entity_type = arguments.get("entity_type")
    properties = arguments.get("properties", {})
    scope_type = arguments.get("scope_type")
    scope_key = arguments.get("scope_key")

    if not name:
        return [types.TextContent(type="text", text="Error: name is required")]
    if not entity_type:
        return [types.TextContent(type="text", text="Error: entity_type is required")]

    # Track which agent created this entity
    agent_id = session_state.get("agent_id") or "unknown"
    domain_key = session_state.get("domain_key")

    # Validate scope parameters
    if scope_type and not scope_key:
        return [types.TextContent(type="text", text="Error: scope_key is required when scope_type is set")]
    if scope_key and not scope_type:
        return [types.TextContent(type="text", text="Error: scope_type is required when scope_key is set")]

    valid_scope_types = ('domain', 'team', 'user')
    if scope_type and scope_type not in valid_scope_types:
        return [types.TextContent(
            type="text",
            text=f"Error: Invalid scope_type '{scope_type}'. Must be one of: {', '.join(valid_scope_types)}"
        )]

    # Validate scope access if specified
    if scope_type and scope_key:
        available_scopes = session_state.get("available_scopes", [])
        has_access = any(
            s.get("scope_type") == scope_type and s.get("scope_key") == scope_key
            for s in available_scopes
        )
        if not has_access and available_scopes:
            return [types.TextContent(
                type="text",
                text=f"Error: You don't have access to scope ({scope_type}: {scope_key})"
            )]
    else:
        # Use default scope from session if not specified
        default_scope = session_state.get("default_scope", {})
        if default_scope:
            scope_type = default_scope.get("scope_type")
            scope_key = default_scope.get("scope_key")

    try:
        payload = {
            "name": name,
            "entity_type": entity_type,
            "properties": properties,
            "source": f"agent:{agent_id}",
        }

        # Include domain context for multi-tenancy if available
        if domain_key:
            payload["domain_key"] = domain_key

        # Include scope information
        if scope_type and scope_key:
            payload["scope_type"] = scope_type
            payload["scope_key"] = scope_key

        result = await _make_request(
            config,
            "POST",
            "/entities",
            json=payload,
            agent_id=agent_id,
        )

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})
            output = f"Entity created successfully!\n\n"
            output += f"**Name:** {entity.get('name')}\n"
            output += f"**Type:** {entity.get('entity_type')}\n"
            output += f"**Key:** {entity.get('entity_key')}\n"
            if entity.get('domain_key'):
                output += f"**Domain:** {entity.get('domain_key')}\n"
            # Show scope info
            if entity.get('scope_type') or scope_type:
                output += f"**Scope:** {entity.get('scope_type') or scope_type}"
                if entity.get('scope_key') or scope_key:
                    output += f" ({entity.get('scope_key') or scope_key})"
                output += "\n"
            if entity.get('source'):
                output += f"**Source:** {entity.get('source')}\n"
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
        scope_type: New scope type - 'domain', 'team', or 'user' (optional)
        scope_key: New scope key - team_key or user_key (optional)
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

    # Handle scope updates
    scope_type = arguments.get("scope_type")
    scope_key = arguments.get("scope_key")

    if scope_type is not None or scope_key is not None:
        # Both must be provided together, or both must be None/empty to clear scope
        if scope_type and not scope_key:
            return [types.TextContent(type="text", text="Error: scope_key is required when scope_type is set")]
        if scope_key and not scope_type:
            return [types.TextContent(type="text", text="Error: scope_type is required when scope_key is set")]

        valid_scope_types = ('domain', 'team', 'user')
        if scope_type and scope_type not in valid_scope_types:
            return [types.TextContent(
                type="text",
                text=f"Error: Invalid scope_type '{scope_type}'. Must be one of: {', '.join(valid_scope_types)}"
            )]

        # Validate scope access
        if scope_type and scope_key:
            available_scopes = session_state.get("available_scopes", [])
            has_access = any(
                s.get("scope_type") == scope_type and s.get("scope_key") == scope_key
                for s in available_scopes
            )
            if not has_access and available_scopes:
                return [types.TextContent(
                    type="text",
                    text=f"Error: You don't have access to scope ({scope_type}: {scope_key})"
                )]

        update_data["scope_type"] = scope_type
        update_data["scope_key"] = scope_key

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
            # Show scope info
            ent_scope_type = entity.get('scope_type')
            ent_scope_key = entity.get('scope_key')
            ent_scope_name = entity.get('scope_name')
            if ent_scope_type:
                scope_display = f"{ent_scope_type}"
                if ent_scope_name:
                    scope_display += f" ({ent_scope_name})"
                elif ent_scope_key:
                    scope_display += f" ({ent_scope_key})"
                output += f"**Scope:** {scope_display}\n"
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

        # Add domain filter for multi-tenancy
        domain_key = session_state.get("domain_key")
        if domain_key:
            params["domain"] = domain_key

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


async def move_entity_scope(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Move an entity and its related entities to a different scope.

    Requires domain_admin or admin role. When include_related is True, also moves
    entities that are:
    - Connected via OUTGOING relationships (where this entity is the source)
    - Currently in the SAME scope as this entity

    This prevents accidentally moving unrelated entities that share common
    connections (like technologies used by multiple projects).

    Args:
        entity_key: The entity key to move
        scope_type: Target scope type ('domain', 'team', 'user')
        scope_key: Target scope key (domain_key, team_key, or user_key)
        include_related: Include related entities (default True, but conservative)
    """
    entity_key = arguments.get("entity_key")
    scope_type = arguments.get("scope_type")
    scope_key = arguments.get("scope_key")
    include_related = arguments.get("include_related", True)

    if not entity_key:
        return [types.TextContent(type="text", text="Error: entity_key is required")]
    if not scope_type:
        return [types.TextContent(type="text", text="Error: scope_type is required")]
    if not scope_key:
        return [types.TextContent(type="text", text="Error: scope_key is required")]

    valid_scope_types = ('domain', 'team', 'user')
    if scope_type not in valid_scope_types:
        return [types.TextContent(
            type="text",
            text=f"Error: Invalid scope_type '{scope_type}'. Must be one of: {', '.join(valid_scope_types)}"
        )]

    # Validate scope access
    available_scopes = session_state.get("available_scopes", [])
    has_access = any(
        s.get("scope_type") == scope_type and s.get("scope_key") == scope_key
        for s in available_scopes
    )
    if not has_access and available_scopes:
        return [types.TextContent(
            type="text",
            text=f"Error: You don't have access to scope ({scope_type}: {scope_key})"
        )]

    # Check if user is domain_admin
    user_role = session_state.get("user_role")
    if user_role not in ('admin', 'domain_admin'):
        return [types.TextContent(
            type="text",
            text="Error: This operation requires domain_admin or admin role"
        )]

    agent_id = session_state.get("agent_id")

    try:
        result = await _make_request(
            config,
            "POST",
            f"/entities/{entity_key}/move-scope",
            json={
                "scope_type": scope_type,
                "scope_key": scope_key,
                "include_related": include_related,
            },
            agent_id=agent_id,
        )

        if result.get("success"):
            data = result.get("data", {})
            updated_count = data.get("total_updated", 0)
            updated_keys = data.get("updated_entities", [])

            output = f"# Entity Scope Move Successful\n\n"
            output += f"**Target Entity:** {entity_key}\n"
            output += f"**New Scope:** {scope_type} ({scope_key})\n"
            output += f"**Entities Updated:** {updated_count}\n\n"

            if updated_keys and len(updated_keys) <= 20:
                output += "## Updated Entities\n"
                for key in updated_keys:
                    output += f"- {key}\n"
            elif updated_keys:
                output += "## Updated Entities (first 20)\n"
                for key in updated_keys[:20]:
                    output += f"- {key}\n"
                output += f"\n... and {len(updated_keys) - 20} more\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to move entity scope')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error moving entity scope: {str(e)}")]
