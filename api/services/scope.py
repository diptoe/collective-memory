"""
Collective Memory Platform - Scope Service

Centralized scope and access control logic for team-based visibility.
"""
from typing import TYPE_CHECKING
from sqlalchemy import or_, and_

if TYPE_CHECKING:
    from api.models.user import User
    from api.models.team import Team, TeamMembership


class ScopeService:
    """
    Centralized scope and access control logic.

    Handles:
    - Determining which scopes a user can access
    - Filtering queries by user's accessible scopes
    - Default scope selection for new entities
    """

    @staticmethod
    def get_user_accessible_scopes(user: 'User') -> list[dict]:
        """
        Return all scopes a user can access.

        Returns a list of scope dictionaries with:
        - scope_type: 'domain', 'team', 'user', or 'system'
        - scope_key: The corresponding key (None for system scope)
        - name: Human-readable name
        - access_level: 'admin', 'owner', 'member', or 'viewer'
        """
        from api.models.team import TeamMembership

        scopes = []

        # System scope (always accessible to everyone)
        scopes.append({
            'scope_type': 'system',
            'scope_key': None,
            'name': 'System',
            'access_level': 'viewer'
        })

        # Domain scope (if user has domain)
        if user.domain_key:
            domain_name = user.domain.name if user.domain else 'Domain'
            scopes.append({
                'scope_type': 'domain',
                'scope_key': user.domain_key,
                'name': domain_name,
                'access_level': 'admin' if user.is_domain_admin else 'member'
            })

        # Team scopes
        for team in user.get_teams():
            membership = TeamMembership.query.filter_by(
                team_key=team.team_key, user_key=user.user_key
            ).first()
            scopes.append({
                'scope_type': 'team',
                'scope_key': team.team_key,
                'name': team.name,
                'access_level': membership.role if membership else 'member'
            })

        # Personal scope
        scopes.append({
            'scope_type': 'user',
            'scope_key': user.user_key,
            'name': 'Personal',
            'access_level': 'owner'
        })

        return scopes

    @staticmethod
    def filter_query_by_scope(query, user: 'User', model_class):
        """
        Filter SQLAlchemy query by user's accessible scopes.

        Args:
            query: SQLAlchemy query object
            user: The user making the request
            model_class: The model class being queried (must have scope_type, scope_key, domain_key)

        Returns:
            Filtered query
        """
        if user.is_admin:
            return query  # Admins see everything

        conditions = []

        # System-scoped entities are visible to everyone (e.g., Client entities)
        conditions.append(
            and_(model_class.scope_type == 'system', model_class.scope_key.is_(None))
        )

        # Domain-scoped (NULL scope_type or explicit domain)
        if user.domain_key:
            conditions.append(
                and_(
                    or_(model_class.scope_type.is_(None), model_class.scope_type == 'domain'),
                    model_class.domain_key == user.domain_key
                )
            )

        # Team-scoped
        team_keys = [t.team_key for t in user.get_teams()]
        if team_keys:
            conditions.append(
                and_(model_class.scope_type == 'team', model_class.scope_key.in_(team_keys))
            )

        # User-scoped (own items)
        conditions.append(
            and_(model_class.scope_type == 'user', model_class.scope_key == user.user_key)
        )

        if conditions:
            return query.filter(or_(*conditions))
        return query

    @staticmethod
    def can_access_scope(user: 'User', scope_type: str, scope_key: str) -> bool:
        """
        Check if user can access a specific scope.

        Args:
            user: The user to check
            scope_type: 'domain', 'team', 'user', or 'system'
            scope_key: The key for the scope

        Returns:
            True if user can access the scope
        """
        if user.is_admin:
            return True

        # System scope is accessible to everyone (read-only)
        if scope_type == 'system':
            return True

        if scope_type == 'domain':
            return user.domain_key == scope_key
        elif scope_type == 'team':
            return any(t.team_key == scope_key for t in user.get_teams())
        elif scope_type == 'user':
            return user.user_key == scope_key

        # NULL or unknown scope_type - check domain
        return user.domain_key == scope_key if scope_key else True

    @staticmethod
    def can_write_to_scope(user: 'User', scope_type: str, scope_key: str) -> bool:
        """
        Check if user can write (create/update) in a specific scope.

        Args:
            user: The user to check
            scope_type: 'domain', 'team', or 'user'
            scope_key: The key for the scope

        Returns:
            True if user can write in the scope
        """
        from api.models.team import TeamMembership

        if user.is_admin:
            return True

        if scope_type == 'domain':
            # Domain admins can write to domain scope
            return user.domain_key == scope_key and user.is_domain_admin
        elif scope_type == 'team':
            # Check team membership and role
            membership = TeamMembership.query.filter_by(
                team_key=scope_key,
                user_key=user.user_key
            ).first()
            return membership and membership.can_write
        elif scope_type == 'user':
            # Only the user can write to their personal scope
            return user.user_key == scope_key

        # NULL scope_type - domain admins can write
        return user.is_domain_admin

    @staticmethod
    def get_default_scope(user: 'User', session_state: dict = None) -> dict:
        """
        Determine default scope for new entities.

        Priority:
        1. Active team from session state
        2. If user is in exactly one team, use that team
        3. Fall back to domain scope
        4. Personal scope as last resort

        Args:
            user: The user creating the entity
            session_state: Optional session state with active_team_key

        Returns:
            dict with 'scope_type' and 'scope_key'
        """
        # Check session for active team
        if session_state and session_state.get('active_team_key'):
            team_key = session_state['active_team_key']
            if any(t.team_key == team_key for t in user.get_teams()):
                return {'scope_type': 'team', 'scope_key': team_key}

        # Single team? Use it
        teams = user.get_teams()
        if len(teams) == 1:
            return {'scope_type': 'team', 'scope_key': teams[0].team_key}

        # Fall back to domain
        if user.domain_key:
            return {'scope_type': 'domain', 'scope_key': user.domain_key}

        # Personal scope as last resort
        return {'scope_type': 'user', 'scope_key': user.user_key}

    @staticmethod
    def validate_scope_params(scope_type: str, scope_key: str) -> tuple[bool, str]:
        """
        Validate scope parameters.

        Args:
            scope_type: The scope type to validate
            scope_key: The scope key to validate

        Returns:
            tuple of (is_valid, error_message)
        """
        valid_scope_types = ('domain', 'team', 'user', 'system', None)

        if scope_type and scope_type not in valid_scope_types:
            return False, f"Invalid scope_type: {scope_type}. Must be one of: domain, team, user, system"

        # System scope has null scope_key, other types require scope_key
        if scope_type == 'system':
            return True, ""  # System scope doesn't need scope_key

        if scope_type and not scope_key:
            return False, f"scope_key is required when scope_type is set"

        if scope_key and not scope_type:
            return False, f"scope_type is required when scope_key is set"

        return True, ""


# Singleton instance for convenience
scope_service = ScopeService()
