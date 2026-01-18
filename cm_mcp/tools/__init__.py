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
    move_entity_scope,
)

from .relationship import (
    list_relationships,
    create_relationship,
    delete_relationship,
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
    identify,
    list_agents,
    get_my_identity,
    update_my_identity,
    list_my_scopes,
    set_active_team,
    list_teams,
)

from .message import (
    send_message,
    get_messages,
    mark_message_read,
    mark_all_messages_read,
    link_message_entities,
)

from .model import (
    list_models,
    list_clients,
    update_focus,
    set_focused_mode,
)

from .github import (
    sync_repository,
    get_repo_issues,
    get_repo_commits,
    get_repo_contributors,
    sync_repository_history,
    sync_repository_updates,
    create_commit_entity,
    create_issue_entity,
    link_work_item,
)

from .activity import (
    list_activities,
    get_activity_summary,
)

from .work_session import (
    get_active_session,
    start_session,
    end_session,
    extend_session,
    record_milestone,
    record_interaction,  # Legacy alias
)

__all__ = [
    # Entity tools
    'search_entities',
    'get_entity',
    'create_entity',
    'update_entity',
    'search_entities_semantic',
    'extract_entities_from_text',
    'move_entity_scope',
    # Relationship tools
    'list_relationships',
    'create_relationship',
    'delete_relationship',
    # Context tools
    'get_context',
    'get_entity_context',
    # Persona tools
    'list_personas',
    'chat_with_persona',
    # Agent collaboration tools
    'identify',
    'list_agents',
    'get_my_identity',
    'update_my_identity',
    # Team and scope tools
    'list_my_scopes',
    'set_active_team',
    'list_teams',
    # Message queue tools
    'send_message',
    'get_messages',
    'mark_message_read',
    'mark_all_messages_read',
    'link_message_entities',
    # Model and client tools
    'list_models',
    'list_clients',
    'update_focus',
    'set_focused_mode',
    # GitHub integration tools
    'sync_repository',
    'get_repo_issues',
    'get_repo_commits',
    'get_repo_contributors',
    'sync_repository_history',
    'sync_repository_updates',
    'create_commit_entity',
    'create_issue_entity',
    'link_work_item',
    # Activity tools
    'list_activities',
    'get_activity_summary',
    # Work session tools
    'get_active_session',
    'start_session',
    'end_session',
    'extend_session',
    'record_milestone',
    'record_interaction',  # Legacy alias
]
