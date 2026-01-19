"""
Collective Memory Platform - Project Routes

Endpoints for project management with team associations.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Project, TeamProject, Team, db
from api.services.auth import require_auth_strict, require_domain_admin
from api.services.activity import activity_service


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def register_project_routes(api: Api):
    """Register project routes with the API."""

    ns = api.namespace(
        'projects',
        description='Project management with team associations',
        path='/projects'
    )

    # Define models for OpenAPI documentation
    project_model = ns.model('Project', {
        'project_key': fields.String(readonly=True, description='Unique project identifier'),
        'name': fields.String(description='Project name'),
        'description': fields.String(description='Project description'),
        'repository_type': fields.String(description='Repository type: github, gitlab, bitbucket, azure, codecommit'),
        'repository_url': fields.String(description='Repository URL'),
        'repository_owner': fields.String(readonly=True, description='Repository owner/org'),
        'repository_name': fields.String(readonly=True, description='Repository name'),
        'domain_key': fields.String(description='Domain the project belongs to'),
        'entity_key': fields.String(description='Linked knowledge graph entity'),
        'status': fields.String(description='Project status: active, archived'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    create_project_model = ns.model('CreateProjectRequest', {
        'name': fields.String(required=True, description='Project name'),
        'description': fields.String(description='Project description'),
        'repository_url': fields.String(description='Repository URL (will be parsed)'),
        'entity_key': fields.String(description='Link to knowledge graph entity'),
        'domain_key': fields.String(description='Domain key (admin only, defaults to user domain)'),
    })

    update_project_model = ns.model('UpdateProjectRequest', {
        'name': fields.String(description='Project name'),
        'description': fields.String(description='Project description'),
        'repository_url': fields.String(description='Repository URL (will be parsed)'),
        'entity_key': fields.String(description='Link to knowledge graph entity'),
        'status': fields.String(description='Project status: active, archived'),
    })

    team_project_model = ns.model('TeamProject', {
        'team_project_key': fields.String(readonly=True, description='Association identifier'),
        'team_key': fields.String(description='Team key'),
        'project_key': fields.String(description='Project key'),
        'role': fields.String(description='Role: owner, contributor, viewer'),
        'created_at': fields.DateTime(readonly=True),
    })

    add_team_model = ns.model('AddTeamRequest', {
        'team_key': fields.String(required=True, description='Team key to add'),
        'role': fields.String(description='Role: owner, contributor, viewer (default: contributor)'),
    })

    update_team_role_model = ns.model('UpdateTeamRoleRequest', {
        'role': fields.String(required=True, description='New role: owner, contributor, viewer'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class ProjectList(Resource):
        @ns.doc('list_projects')
        @require_auth_strict
        def get(self):
            """
            List projects.

            Query params:
            - status: Filter by status ('active', 'archived', or omit for all)
            - team_key: Filter by team association
            - domain_key: Filter by domain (admin only)
            - include_teams: Include team associations (default: false)
            """
            user = g.current_user
            status_filter = request.args.get('status')
            team_filter = request.args.get('team_key')
            domain_filter = request.args.get('domain_key')
            include_teams = request.args.get('include_teams', 'false').lower() == 'true'

            # Get domain key for filtering
            domain_key = user.domain_key if user.domain_key else None

            if not domain_key and not user.is_admin:
                return {'success': False, 'msg': 'User must belong to a domain'}, 400

            # Build query
            if user.is_admin:
                # System admin can filter by domain or see all
                if domain_filter:
                    query = Project.query.filter_by(domain_key=domain_filter)
                elif domain_key:
                    query = Project.query.filter_by(domain_key=domain_key)
                else:
                    # No filter - see all projects
                    query = Project.query
            else:
                query = Project.query.filter_by(domain_key=domain_key)

            # Apply status filter
            if status_filter:
                query = query.filter_by(status=status_filter)
            else:
                # Default to active only
                query = query.filter_by(status='active')

            # Apply team filter
            if team_filter:
                # Get project keys for this team
                associations = TeamProject.get_projects_for_team(team_filter)
                project_keys = [a.project_key for a in associations]
                query = query.filter(Project.project_key.in_(project_keys))

            projects = query.order_by(Project.name).all()

            return {
                'success': True,
                'msg': f'Found {len(projects)} projects',
                'data': {
                    'projects': [p.to_dict(include_teams=include_teams) for p in projects],
                    'total': len(projects)
                }
            }

        @ns.doc('create_project')
        @ns.expect(create_project_model)
        @require_domain_admin
        def post(self):
            """Create a new project. Admins can specify domain_key, others use their own domain."""
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

            # Check for duplicate repository URL
            if data.get('repository_url'):
                existing = Project.find_by_repository(data['repository_url'])
                if existing:
                    return {
                        'success': False,
                        'msg': f'A project with this repository URL already exists: {existing.name}'
                    }, 409

            try:
                from api.models import Entity

                # Check for existing entity with same name in domain
                existing_entity = None
                entity_key = data.get('entity_key')

                if not entity_key:
                    # Search for existing Project entity with same name in domain
                    existing_entities = Entity.query.filter_by(
                        domain_key=domain_key,
                        entity_type='Project',
                        name=data['name'].strip()
                    ).all()

                    if existing_entities:
                        existing_entity = existing_entities[0]
                        entity_key = existing_entity.entity_key

                # Create the project
                project = Project.create_project(
                    domain_key=domain_key,
                    name=data['name'].strip(),
                    description=data.get('description'),
                    repository_url=data.get('repository_url'),
                    entity_key=entity_key,
                    extra_data=data.get('extra_data')
                )

                # If we found an existing entity, update its source bridge
                if existing_entity:
                    existing_entity.source = Entity.create_source_bridge('project', project.project_key)
                    existing_entity.save()
                elif not entity_key:
                    # Create a new Project entity and link it
                    new_entity = Entity(
                        entity_type='Project',
                        name=data['name'].strip(),
                        domain_key=domain_key,
                        properties={
                            'description': data.get('description'),
                            'repository_url': data.get('repository_url'),
                        },
                        source=Entity.create_source_bridge('project', project.project_key),
                        confidence=1.0,
                    )
                    new_entity.save()
                    project.entity_key = new_entity.entity_key
                    project.save()

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='Project',
                    entity_key=project.project_key,
                    entity_name=project.name,
                    changes={
                        'repository_url': project.repository_url,
                        'domain_key': project.domain_key,
                        'linked_entity_key': project.entity_key,
                    },
                    domain_key=domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Project created successfully',
                    'data': {
                        'project': project.to_dict()
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/lookup')
    class ProjectLookup(Resource):
        @ns.doc('lookup_project')
        @require_auth_strict
        def get(self):
            """
            Find a project by repository URL.

            Query params:
            - repository_url: The repository URL to look up (required)

            Returns the project with its team associations.
            """
            repository_url = request.args.get('repository_url')

            if not repository_url:
                return {'success': False, 'msg': 'repository_url is required'}, 400

            project = Project.find_by_repository(repository_url)

            if not project:
                return {
                    'success': True,
                    'msg': 'No project found for this repository URL',
                    'data': {
                        'project': None,
                        'teams': []
                    }
                }

            # Get team associations
            associations = TeamProject.get_teams_for_project(project.project_key)

            return {
                'success': True,
                'msg': 'Project found',
                'data': {
                    'project': project.to_dict(),
                    'teams': [a.to_dict(include_team=True) for a in associations]
                }
            }

    @ns.route('/from-entity/<string:entity_key>')
    @ns.param('entity_key', 'Entity key to create project from')
    class ProjectFromEntity(Resource):
        @ns.doc('create_project_from_entity')
        @require_domain_admin
        def post(self, entity_key):
            """
            Create a project from an existing entity.

            This creates a new Project database record linked to the entity,
            sets the entity's source bridge, and returns the created project.
            """
            from api.models import Entity

            user = g.current_user
            entity = Entity.query.filter_by(entity_key=entity_key).first()

            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Check domain access
            if entity.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            # Check if entity already has a source bridge to a project
            bridge = Entity.parse_source_bridge(entity.source)
            if bridge and bridge['type'] == 'project':
                existing_project = Project.get_by_key(bridge['key'])
                if existing_project:
                    return {
                        'success': False,
                        'msg': f'Entity is already linked to project: {existing_project.name}'
                    }, 409

            # Get optional parameters from request
            data = request.json or {}
            repository_url = data.get('repository_url') or entity.properties.get('repository_url') if entity.properties else None
            description = data.get('description') or entity.properties.get('description') if entity.properties else None

            try:
                # Create the project
                project = Project.create_project(
                    domain_key=entity.domain_key,
                    name=entity.name,
                    description=description,
                    repository_url=repository_url,
                    entity_key=entity.entity_key,
                    extra_data=data.get('extra_data')
                )

                # Update the entity's source bridge
                entity.source = Entity.create_source_bridge('project', project.project_key)
                entity.save()

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='Project',
                    entity_key=project.project_key,
                    entity_name=project.name,
                    changes={
                        'repository_url': project.repository_url,
                        'domain_key': project.domain_key,
                        'linked_entity_key': entity.entity_key,
                        'created_from_entity': True,
                    },
                    domain_key=entity.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Project created from entity',
                    'data': {
                        'project': project.to_dict(),
                        'entity_key': entity.entity_key
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:project_key>')
    @ns.param('project_key', 'Project identifier')
    class ProjectDetail(Resource):
        @ns.doc('get_project')
        @require_auth_strict
        def get(self, project_key):
            """Get project details."""
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            include_teams = request.args.get('include_teams', 'true').lower() == 'true'

            return {
                'success': True,
                'msg': 'Project retrieved',
                'data': {
                    'project': project.to_dict(include_teams=include_teams)
                }
            }

        @ns.doc('update_project')
        @ns.expect(update_project_model)
        @require_domain_admin
        def put(self, project_key):
            """Update project details."""
            user = g.current_user
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Check domain access
            if project.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            data = request.json or {}
            changes = {}

            if 'name' in data:
                changes['name'] = {'old': project.name, 'new': data['name']}
                project.name = data['name'].strip()

            if 'description' in data:
                changes['description'] = {'old': project.description, 'new': data['description']}
                project.description = data['description']

            if 'repository_url' in data:
                # Check for duplicate if changing URL
                if data['repository_url'] and data['repository_url'] != project.repository_url:
                    existing = Project.find_by_repository(data['repository_url'])
                    if existing and existing.project_key != project.project_key:
                        return {
                            'success': False,
                            'msg': f'A project with this repository URL already exists: {existing.name}'
                        }, 409

                changes['repository_url'] = {'old': project.repository_url, 'new': data['repository_url']}
                project.update_repository(data['repository_url'])

            if 'entity_key' in data:
                changes['entity_key'] = {'old': project.entity_key, 'new': data['entity_key']}
                project.entity_key = data['entity_key']

            if 'status' in data:
                if data['status'] not in ('active', 'archived'):
                    return {'success': False, 'msg': 'Invalid status'}, 400
                changes['status'] = {'old': project.status, 'new': data['status']}
                project.status = data['status']

            try:
                project.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=user.user_key,
                        entity_type='Project',
                        entity_key=project.project_key,
                        entity_name=project.name,
                        changes=changes,
                        domain_key=get_user_domain_key(),
                        user_key=user.user_key
                    )

                return {
                    'success': True,
                    'msg': 'Project updated',
                    'data': {
                        'project': project.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('archive_project')
        @require_domain_admin
        def delete(self, project_key):
            """Archive a project (soft delete)."""
            user = g.current_user
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Check domain access
            if project.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            try:
                project.archive()

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='Project',
                    entity_key=project.project_key,
                    entity_name=project.name,
                    domain_key=get_user_domain_key(),
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Project archived',
                    'data': {
                        'project': project.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:project_key>/teams')
    @ns.param('project_key', 'Project identifier')
    class ProjectTeams(Resource):
        @ns.doc('list_project_teams')
        @require_auth_strict
        def get(self, project_key):
            """List teams associated with a project."""
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            associations = TeamProject.get_teams_for_project(project_key)

            return {
                'success': True,
                'msg': f'Found {len(associations)} team associations',
                'data': {
                    'project': {'project_key': project.project_key, 'name': project.name},
                    'teams': [a.to_dict(include_team=True) for a in associations]
                }
            }

        @ns.doc('add_team_to_project')
        @ns.expect(add_team_model)
        @require_domain_admin
        def post(self, project_key):
            """Add a team to a project."""
            user = g.current_user
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Check domain access
            if project.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            data = request.json or {}

            if not data.get('team_key'):
                return {'success': False, 'msg': 'team_key is required'}, 400

            team = Team.get_by_key(data['team_key'])
            if not team:
                return {'success': False, 'msg': 'Team not found'}, 404

            # Ensure team is in the same domain
            if team.domain_key != project.domain_key:
                return {'success': False, 'msg': 'Team must be in the same domain as the project'}, 400

            role = data.get('role', 'contributor')
            if role not in ('owner', 'contributor', 'viewer'):
                return {'success': False, 'msg': 'Invalid role'}, 400

            try:
                association = TeamProject.create_association(
                    team_key=team.team_key,
                    project_key=project.project_key,
                    role=role
                )

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='TeamProject',
                    entity_key=association.team_project_key,
                    entity_name=f'{team.name} -> {project.name}',
                    changes={'role': role, 'team_key': team.team_key, 'project_key': project.project_key},
                    domain_key=project.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team added to project',
                    'data': {
                        'association': association.to_dict(include_team=True)
                    }
                }, 201

            except ValueError as e:
                return {'success': False, 'msg': str(e)}, 409
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:project_key>/teams/<string:team_key>')
    @ns.param('project_key', 'Project identifier')
    @ns.param('team_key', 'Team identifier')
    class ProjectTeamDetail(Resource):
        @ns.doc('update_team_role')
        @ns.expect(update_team_role_model)
        @require_domain_admin
        def put(self, project_key, team_key):
            """Update a team's role in a project."""
            user = g.current_user
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Check domain access
            if project.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            association = TeamProject.get_association(team_key, project_key)
            if not association:
                return {'success': False, 'msg': 'Team association not found'}, 404

            data = request.json or {}

            if not data.get('role'):
                return {'success': False, 'msg': 'role is required'}, 400

            new_role = data['role']
            if new_role not in ('owner', 'contributor', 'viewer'):
                return {'success': False, 'msg': 'Invalid role'}, 400

            old_role = association.role

            try:
                association.role = new_role
                association.save()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='TeamProject',
                    entity_key=association.team_project_key,
                    entity_name=f'{team_key} -> {project.name}',
                    changes={'role': {'old': old_role, 'new': new_role}},
                    domain_key=project.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team role updated',
                    'data': {
                        'association': association.to_dict(include_team=True)
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('remove_team_from_project')
        @require_domain_admin
        def delete(self, project_key, team_key):
            """Remove a team from a project."""
            user = g.current_user
            project = Project.get_by_key(project_key)

            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Check domain access
            if project.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            association = TeamProject.get_association(team_key, project_key)
            if not association:
                return {'success': False, 'msg': 'Team association not found'}, 404

            try:
                team = Team.get_by_key(team_key)
                team_name = team.name if team else team_key

                association.delete()

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='TeamProject',
                    entity_key=association.team_project_key,
                    entity_name=f'{team_name} -> {project.name}',
                    domain_key=project.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Team removed from project'
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
