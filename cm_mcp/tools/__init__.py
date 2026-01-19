"""
Collective Memory MCP Tools

All tool definitions and implementations for the MCP server.

Tool files export:
- TOOL_DEFINITIONS: List of types.Tool objects
- TOOL_HANDLERS: Dict mapping tool name to handler function
- Individual functions (for backwards compatibility during migration)
"""

# Entity tools - REFACTORED (definitions + handlers)
from .entity import (
    TOOL_DEFINITIONS as ENTITY_DEFINITIONS,
    TOOL_HANDLERS as ENTITY_HANDLERS,
    search_entities,
    get_entity,
    create_entity,
    update_entity,
    search_entities_semantic,
    extract_entities_from_text,
    move_entity_scope,
)

# Relationship tools - REFACTORED (definitions + handlers)
from .relationship import (
    TOOL_DEFINITIONS as RELATIONSHIP_DEFINITIONS,
    TOOL_HANDLERS as RELATIONSHIP_HANDLERS,
    list_relationships,
    create_relationship,
    delete_relationship,
)

# Context tools - REFACTORED (definitions + handlers)
from .context import (
    TOOL_DEFINITIONS as CONTEXT_DEFINITIONS,
    TOOL_HANDLERS as CONTEXT_HANDLERS,
    get_context,
    get_entity_context,
)

# Persona tools - REFACTORED (definitions + handlers)
from .persona import (
    TOOL_DEFINITIONS as PERSONA_DEFINITIONS,
    TOOL_HANDLERS as PERSONA_HANDLERS,
    list_personas,
    chat_with_persona,
)

# Agent tools - REFACTORED (split into agent.py, identity.py, team.py)
from .agent import (
    TOOL_DEFINITIONS as AGENT_DEFINITIONS,
    TOOL_HANDLERS as AGENT_HANDLERS,
    list_agents,
)

# Identity tools - REFACTORED (definitions + handlers)
from .identity import (
    TOOL_DEFINITIONS as IDENTITY_DEFINITIONS,
    TOOL_HANDLERS as IDENTITY_HANDLERS,
    identify,
    get_my_identity,
    update_my_identity,
)

# Team tools - REFACTORED (definitions + handlers)
from .team import (
    TOOL_DEFINITIONS as TEAM_DEFINITIONS,
    TOOL_HANDLERS as TEAM_HANDLERS,
    list_my_scopes,
    set_active_team,
    list_teams,
)

# Message tools - REFACTORED (definitions + handlers)
from .message import (
    TOOL_DEFINITIONS as MESSAGE_DEFINITIONS,
    TOOL_HANDLERS as MESSAGE_HANDLERS,
    send_message,
    get_messages,
    mark_message_read,
    mark_all_messages_read,
    link_message_entities,
)

# Model tools - REFACTORED (definitions + handlers)
from .model import (
    TOOL_DEFINITIONS as MODEL_DEFINITIONS,
    TOOL_HANDLERS as MODEL_HANDLERS,
    list_models,
    list_clients,
    update_focus,
    set_focused_mode,
)

# GitHub tools - REFACTORED (split into github_repo.py, github_sync.py, github_entities.py)
from .github_repo import (
    TOOL_DEFINITIONS as GITHUB_REPO_DEFINITIONS,
    TOOL_HANDLERS as GITHUB_REPO_HANDLERS,
    sync_repository,
    get_repo_issues,
    get_repo_commits,
    get_repo_contributors,
)

from .github_sync import (
    TOOL_DEFINITIONS as GITHUB_SYNC_DEFINITIONS,
    TOOL_HANDLERS as GITHUB_SYNC_HANDLERS,
    sync_repository_history,
    sync_repository_updates,
)

from .github_entities import (
    TOOL_DEFINITIONS as GITHUB_ENTITIES_DEFINITIONS,
    TOOL_HANDLERS as GITHUB_ENTITIES_HANDLERS,
    create_commit_entity,
    create_issue_entity,
    link_work_item,
)

# Activity tools - REFACTORED (definitions + handlers)
from .activity import (
    TOOL_DEFINITIONS as ACTIVITY_DEFINITIONS,
    TOOL_HANDLERS as ACTIVITY_HANDLERS,
    list_activities,
    get_activity_summary,
)

# Work session tools - REFACTORED (split into session.py, milestone.py)
from .session import (
    TOOL_DEFINITIONS as SESSION_DEFINITIONS,
    TOOL_HANDLERS as SESSION_HANDLERS,
    get_active_session,
    start_session,
    end_session,
    extend_session,
)

from .milestone import (
    TOOL_DEFINITIONS as MILESTONE_DEFINITIONS,
    TOOL_HANDLERS as MILESTONE_HANDLERS,
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
    # Aggregated exports
    'TOOL_DEFINITIONS',
    'TOOL_HANDLERS',
]


# ============================================================
# AGGREGATED TOOL DEFINITIONS AND HANDLERS
# ============================================================
# All tool definitions and handlers are now aggregated here.
# server.py can import these to use all tools.

TOOL_DEFINITIONS = (
    ENTITY_DEFINITIONS
    + RELATIONSHIP_DEFINITIONS
    + CONTEXT_DEFINITIONS
    + PERSONA_DEFINITIONS
    + AGENT_DEFINITIONS
    + IDENTITY_DEFINITIONS
    + TEAM_DEFINITIONS
    + MESSAGE_DEFINITIONS
    + MODEL_DEFINITIONS
    + GITHUB_REPO_DEFINITIONS
    + GITHUB_SYNC_DEFINITIONS
    + GITHUB_ENTITIES_DEFINITIONS
    + ACTIVITY_DEFINITIONS
    + SESSION_DEFINITIONS
    + MILESTONE_DEFINITIONS
)

TOOL_HANDLERS = {
    **ENTITY_HANDLERS,
    **RELATIONSHIP_HANDLERS,
    **CONTEXT_HANDLERS,
    **PERSONA_HANDLERS,
    **AGENT_HANDLERS,
    **IDENTITY_HANDLERS,
    **TEAM_HANDLERS,
    **MESSAGE_HANDLERS,
    **MODEL_HANDLERS,
    **GITHUB_REPO_HANDLERS,
    **GITHUB_SYNC_HANDLERS,
    **GITHUB_ENTITIES_HANDLERS,
    **ACTIVITY_HANDLERS,
    **SESSION_HANDLERS,
    **MILESTONE_HANDLERS,
}
