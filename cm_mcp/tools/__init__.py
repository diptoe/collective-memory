"""
Collective Memory MCP Tools

All tool functions for the MCP server.
"""

from .entity import (
    search_entities,
    get_entity,
    create_entity,
    update_entity,
    search_entities_semantic,
    extract_entities_from_text,
)

from .relationship import (
    list_relationships,
    create_relationship,
)

from .context import (
    get_context,
    get_entity_context,
)

from .persona import (
    list_personas,
    chat_with_persona,
)

from .agent import (
    list_agents,
    get_my_identity,
    update_my_identity,
)

from .message import (
    send_message,
    get_messages,
    mark_message_read,
)

__all__ = [
    # Entity tools
    'search_entities',
    'get_entity',
    'create_entity',
    'update_entity',
    'search_entities_semantic',
    'extract_entities_from_text',
    # Relationship tools
    'list_relationships',
    'create_relationship',
    # Context tools
    'get_context',
    'get_entity_context',
    # Persona tools
    'list_personas',
    'chat_with_persona',
    # Agent collaboration tools
    'list_agents',
    'get_my_identity',
    'update_my_identity',
    # Message queue tools
    'send_message',
    'get_messages',
    'mark_message_read',
]
