"""
Collective Memory Platform - Team Routes

Endpoints for team management within domains.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Team, TeamMembership, User, db
from api.services.auth import require_auth_strict, require_domain_admin
from api.services.activity import activity_service


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


def is_team_admin(user: User, team: Team) -> bool:
    """Check if user has admin rights for a team."""
    if user.is_admin or user.is_domain_admin:
        return True
    membership = TeamMembership.get_user_membership(user.user_key, team.team_key)
    return membership and membership.is_admin


def is_team_member(user: User, team: Team) -> bool:
    """Check if user is a member of the team."""
    if user.is_admin:
        return True
    return user.is_team_member(team.team_key)


def register_team_routes(api: Api):
    """Register team routes with the API."""

    ns = api.namespace(
        'teams',
        description='Team management within domains',
        path='/teams'
    )

    # Define models for OpenAPI documentation
    team_model = ns.model('Team', {
        'team_key': fields.String(readonly=True, description='Unique team identifier'),
        'domain_key': fields.String(description='Domain this team belongs to'),
        'name': fields.String(description='Team display name'),
        'slug': fields.String(description='Team slug (URL-friendly)'),
        'description': fields.String(description='Team description'),
        'status': fields.String(description='Team status: active, archived'),
        'member_count': fields.Integer(readonly=True, description='Number of team members'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    create_team_model = ns.model('CreateTeamRequest', {
        'name': fields.String(required=True, description='Team display name'),
        'slug': fields.String(description='Team slug (auto-generated if not provided)'),
        'description': fields.String(description='Team description'),
        'domain_key': fields.String(description='Domain key (admin only, defaults to user domain)'),
    })

    update_team_model = ns.model('UpdateTeamRequest', {
        'name': fields.String(description='Team display name'),
        'description': fields.String(description='Team description'),
        'status': fields.String(description='Team status: active, archived'),
    })

    membership_model = ns.model('TeamMembership', {
        'membership_key': fields.String(readonly=True, description='Unique membership identifier'),
        'team_key': fields.String(description='Team key'),
        'user_key': fields.String(description='User key'),
        'role': fields.String(description='Role: owner, admin, member, viewer'),
        'joined_at': fields.DateTime(readonly=True),
    })

    add_member_model = ns.model('AddMemberRequest', {
        'user_key': fields.String(required=True, description='User key to add'),
        'role': fields.String(description='Role: owner, admin, member, viewer (default: member)'),
        'slug': fields.String(description='Custom identifier (2-10 chars, alphanumeric). Defaults to user initials.'),
    })

    update_member_model = ns.model('UpdateMemberRequest', {
        'role': fields.String(description='Role: owner, admin, member, viewer'),
        'slug': fields.String(description='Custom identifier (2-10 chars, alphanumeric with hyphens)'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    move_domain_model = ns.model('MoveTeamToDomainRequest', {
        'target_domain_key': fields.String(required=True, description='Domain key to move the team to'),
    })

    @ns.route('')
    class TeamList(Resource):
        @ns.doc('list_teams')
        @require_auth_strict
        def get(self):
            """
            List teams.

            System admins see all teams (optionally filtered by domain).
            Domain admins see all teams in their domain.
            Regular users see only teams they are members of.

            Query params:
            - status: Filter by status ('active', 'archived', or omit for all)
            - domain_key: Filter by domain (admin only)
            """
            user = g.current_user
            status_filter = request.args.get('status')
            domain_filter = request.args.get('domain_key')

            if user.is_admin:
                # System admin can see all teams, optionally filtered by domain
                include_archived = status_filter != 'active'
                if domain_filter:
                    teams = Team.get_for_domain(domain_filter, include_archived=include_archived)
                else:
                    # Get all teams across all domains
                    query = Team.query
                    if not include_archived:
                        query = query.filter_by(status='active')
                    teams = query.order_by(Team.name).all()

                # Apply status filter if specified
                if status_filter:
                    teams = [t for t in teams if t.status == status_filter]
            elif user.is_domain_admin and user.domain_key:
                # Domain admins see all teams in their domain
                include_archived = status_filter != 'active'
                teams = Team.get_for_domain(user.domain_key, include_archived=include_archived)

                # Apply status filter if specified
                if status_filter:
                    teams = [t for t in teams if t.status == status_filter]
            else:
                # Regular users see only their teams
                teams = user.get_teams()
                if status_filter:
                    teams = [t for t in teams if t.status == status_filter]

            return {
                'success': True,
                'msg': f'Found {len(teams)} teams',
                'data': {
                    'teams': [t.to_dict() for t in teams],
                    'total': len(teams)
                }
            }

        @ns.doc('create_team')
        @ns.expect(create_team_model)
        @require_domain_admin
        def post(self):
            """Create a new team. Admins can specify domain_key, others use their own domain."""
            from api.models import Domain
            user = g.current_user
            data = request.json or {}

            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400

            # Determine domain_key
            if data.get('domain_key') and user.is_admin:
                # System admin can specify any domain
                domain = Domain.get_by_key(data['domain_key'])
                if not domain:
                    return {'success': False, 'msg': 'Domain not found'}, 404
                domain_key = data['domain_key']
            elif user.domain_key:
                # Use user's domain
                domain_key = user.domain_key
            else:
                return {'success': False, 'msg': 'Domain is required'}, 400

            try:
                from api.models import Entity

                team = Team.create_team(
                    domain_key=domain_key,
                    name=data['name'].strip(),
                    slug=data.get('slug'),
                    description=data.get('description'),
                )

                # Create a Team entity with entity_key = team_key (strong link)
                existing_entity = Entity.get_by_key(team.team_key)
                if not existing_entity:
                    team_entity = Entity(
                        entity_key=team.team_key,  # Strong link: entity_key matches team_key
                        entity_type='Team',
                        name=team.name,
                        domain_key=domain_key,
                        scope_type='domain',
                        scope_key=domain_key,
                        properties={
                            'description': data.get('description'),
                            'slug': team.slug,
                        },
                        source=Entity.create_source_bridge('team', team.team_key),
                        confidence=1.0,
                    )
                    team_entity.save()

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='Team',
                    entity_key=team.team_key,
                    entity_name=team.name,
                    changes={'slug': team.slug, 'domain_key': team.domain_key},
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team created successfully',
                    'data': {
                        'team': team.to_dict()
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:team_key>')
    @ns.param('team_key', 'Team identifier')
    class TeamDetail(Resource):
        @ns.doc('get_team')
        @require_auth_strict
        def get(self, team_key):
            """Get team details. Requires team membership."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_member(user, team):
                return {'success': False, 'msg': 'Access denied'}, 403

            include_members = request.args.get('include_members', 'false').lower() == 'true'

            return {
                'success': True,
                'msg': 'Team retrieved',
                'data': {
                    'team': team.to_dict(include_members=include_members)
                }
            }

        @ns.doc('update_team')
        @ns.expect(update_team_model)
        @require_auth_strict
        def put(self, team_key):
            """Update team. Requires team admin role."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_admin(user, team):
                return {'success': False, 'msg': 'Team admin access required'}, 403

            data = request.json or {}
            changes = {}

            if 'name' in data:
                changes['name'] = {'old': team.name, 'new': data['name']}
                team.name = data['name'].strip()

            if 'description' in data:
                changes['description'] = {'old': team.description, 'new': data['description']}
                team.description = data['description']

            if 'status' in data:
                if data['status'] not in ('active', 'archived'):
                    return {'success': False, 'msg': 'Invalid status'}, 400
                changes['status'] = {'old': team.status, 'new': data['status']}
                team.status = data['status']

            try:
                team.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=user.user_key,
                        entity_type='Team',
                        entity_key=team.team_key,
                        entity_name=team.name,
                        changes=changes,
                        domain_key=get_user_domain_key(),
                        user_key=user.user_key
                    )

                return {
                    'success': True,
                    'msg': 'Team updated',
                    'data': {
                        'team': team.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_team')
        @require_domain_admin
        def delete(self, team_key):
            """Archive a team. Requires domain admin role."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Ensure team belongs to user's domain
            if team.domain_key != user.domain_key:
                return {'success': False, 'msg': 'Access denied'}, 403

            try:
                team.archive()

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='Team',
                    entity_key=team.team_key,
                    entity_name=team.name,
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team archived',
                    'data': {
                        'team': team.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:team_key>/move-domain')
    @ns.param('team_key', 'Team identifier')
    class TeamMoveDomain(Resource):
        @ns.doc('move_team_to_domain')
        @ns.expect(move_domain_model)
        @require_domain_admin
        def post(self, team_key):
            """
            Move a team to a different domain.

            This operation:
            - Updates the team's domain_key
            - Removes all project associations (projects are domain-specific)
            - Ensures slug uniqueness in target domain
            - Keeps team memberships (users can be in teams across domains)

            Requires system admin role.
            """
            user = g.current_user

            # Only system admins can move teams between domains
            if not user.is_admin:
                return {'success': False, 'msg': 'Only system administrators can move teams between domains'}, 403

            team = Team.get_by_key(team_key)
            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            data = request.json or {}
            target_domain_key = data.get('target_domain_key')

            if not target_domain_key:
                return {'success': False, 'msg': 'target_domain_key is required'}, 400

            try:
                summary = team.move_to_domain(target_domain_key)

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='Team',
                    entity_key=team.team_key,
                    entity_name=team.name,
                    changes={
                        'domain_key': {'old': summary['source_domain'], 'new': summary['target_domain']},
                        'action': 'move_to_domain',
                        'project_associations_removed': summary['project_associations_removed'],
                    },
                    domain_key=target_domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team moved to new domain successfully',
                    'data': {
                        'team': team.to_dict(),
                        'summary': summary
                    }
                }

            except ValueError as e:
                return {'success': False, 'msg': str(e)}, 400
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:team_key>/members')
    @ns.param('team_key', 'Team identifier')
    class TeamMembers(Resource):
        @ns.doc('list_members')
        @require_auth_strict
        def get(self, team_key):
            """List team members. Requires team membership."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_member(user, team):
                return {'success': False, 'msg': 'Access denied'}, 403

            memberships = team.get_members()

            return {
                'success': True,
                'msg': f'Found {len(memberships)} members',
                'data': {
                    'team': {'team_key': team.team_key, 'name': team.name},
                    'members': [m.to_dict(include_user=True) for m in memberships]
                }
            }

        @ns.doc('add_member')
        @ns.expect(add_member_model)
        @require_auth_strict
        def post(self, team_key):
            """Add a member to the team. Requires team admin role."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_admin(user, team):
                return {'success': False, 'msg': 'Team admin access required'}, 403

            data = request.json or {}

            if not data.get('user_key'):
                return {'success': False, 'msg': 'user_key is required'}, 400

            new_member = User.get_by_key(data['user_key'])
            if not new_member:
                return {'success': False, 'msg': 'User not found'}, 404

            # Ensure user is in the same domain
            if new_member.domain_key != team.domain_key:
                return {'success': False, 'msg': 'User must be in the same domain as the team'}, 400

            role = data.get('role', 'member')
            if role not in ('owner', 'admin', 'member', 'viewer'):
                return {'success': False, 'msg': 'Invalid role'}, 400

            # Validate slug if provided
            slug = data.get('slug')
            if slug:
                import re
                slug = slug.strip().lower()
                if len(slug) < 2 or len(slug) > 10:
                    return {'success': False, 'msg': 'Slug must be 2-10 characters'}, 400
                if not re.match(r'^[a-z0-9-]+$', slug):
                    return {'success': False, 'msg': 'Slug must be alphanumeric with hyphens only'}, 400

            try:
                membership = team.add_member(new_member.user_key, role, slug=slug)

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='TeamMembership',
                    entity_key=membership.membership_key,
                    entity_name=f'{new_member.display_name} -> {team.name}',
                    changes={'role': role, 'user_key': new_member.user_key, 'team_key': team.team_key},
                    domain_key=team.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Member added to team',
                    'data': {
                        'membership': membership.to_dict(include_user=True)
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:team_key>/members/<string:user_key>')
    @ns.param('team_key', 'Team identifier')
    @ns.param('user_key', 'User identifier')
    class TeamMemberDetail(Resource):
        @ns.doc('update_member')
        @ns.expect(update_member_model)
        @require_auth_strict
        def put(self, team_key, user_key):
            """Update a member's role. Requires team admin role."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_admin(user, team):
                return {'success': False, 'msg': 'Team admin access required'}, 403

            membership = TeamMembership.get_user_membership(user_key, team_key)
            if not membership:
                return {'success': False, 'msg': 'Membership not found'}, 404

            data = request.json or {}

            if not data.get('role') and 'slug' not in data:
                return {'success': False, 'msg': 'role or slug is required'}, 400

            changes = {}
            old_role = membership.role
            old_slug = membership.slug

            try:
                import re

                # Handle role update
                if data.get('role'):
                    new_role = data['role']
                    if new_role not in ('owner', 'admin', 'member', 'viewer'):
                        return {'success': False, 'msg': 'Invalid role'}, 400
                    membership.role = new_role
                    changes['role'] = {'old': old_role, 'new': new_role}

                # Handle slug update
                if 'slug' in data:
                    slug = data['slug']
                    if slug:
                        slug = slug.strip().lower()
                        if len(slug) < 2 or len(slug) > 10:
                            return {'success': False, 'msg': 'Slug must be 2-10 characters'}, 400
                        if not re.match(r'^[a-z0-9-]+$', slug):
                            return {'success': False, 'msg': 'Slug must be alphanumeric with hyphens only'}, 400
                    membership.slug = slug if slug else None
                    changes['slug'] = {'old': old_slug, 'new': membership.slug}

                membership.save()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='TeamMembership',
                    entity_key=membership.membership_key,
                    entity_name=f'{membership.user.display_name} -> {team.name}',
                    changes=changes,
                    domain_key=team.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Member updated',
                    'data': {
                        'membership': membership.to_dict(include_user=True)
                    }
                }

            except ValueError as e:
                return {'success': False, 'msg': str(e)}, 400
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('remove_member')
        @require_auth_strict
        def delete(self, team_key, user_key):
            """Remove a member from the team. Requires team admin role."""
            user = g.current_user
            team = Team.get_by_key(team_key)

            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Check access
            if not is_team_admin(user, team):
                return {'success': False, 'msg': 'Team admin access required'}, 403

            membership = TeamMembership.get_user_membership(user_key, team_key)
            if not membership:
                return {'success': False, 'msg': 'Membership not found'}, 404

            member_name = membership.user.display_name if membership.user else user_key

            try:
                team.remove_member(user_key)

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='TeamMembership',
                    entity_key=membership.membership_key,
                    entity_name=f'{member_name} -> {team.name}',
                    domain_key=team.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Member removed from team'
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/my')
    class MyTeams(Resource):
        @ns.doc('get_my_teams')
        @require_auth_strict
        def get(self):
            """Get all teams the current user is a member of."""
            user = g.current_user
            teams = user.get_teams()
            memberships = user.get_team_memberships()

            # Build response with membership info
            team_data = []
            for team in teams:
                membership = next((m for m in memberships if m.team_key == team.team_key), None)
                t = team.to_dict()
                t['my_role'] = membership.role if membership else None
                team_data.append(t)

            return {
                'success': True,
                'msg': f'Found {len(teams)} teams',
                'data': {
                    'teams': team_data
                }
            }

    @ns.route('/stats')
    class TeamStats(Resource):
        @ns.doc('get_team_stats')
        @require_domain_admin
        def get(self):
            """Get team statistics for the user's domain."""
            user = g.current_user

            if not user.domain_key:
                return {'success': False, 'msg': 'User must belong to a domain'}, 400

            # Get counts
            all_teams = Team.get_for_domain(user.domain_key, include_archived=True)
            active_count = sum(1 for t in all_teams if t.status == 'active')
            archived_count = sum(1 for t in all_teams if t.status == 'archived')

            return {
                'success': True,
                'msg': 'Team stats retrieved',
                'data': {
                    'total': len(all_teams),
                    'active': active_count,
                    'archived': archived_count
                }
            }
