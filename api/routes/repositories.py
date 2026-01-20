"""
Collective Memory Platform - Repository Routes

Endpoints for repository management with project associations.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Repository, ProjectRepository, Project, Team, db
from api.services.auth import require_auth_strict, require_domain_admin
from api.services.activity import activity_service


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def register_repository_routes(api: Api):
    """Register repository routes with the API."""

    ns = api.namespace(
        'repositories',
        description='Repository management with project associations',
        path='/repositories'
    )

    # Define models for OpenAPI documentation
    repository_model = ns.model('Repository', {
        'repository_key': fields.String(readonly=True, description='Unique repository identifier'),
        'name': fields.String(description='Repository name'),
        'description': fields.String(description='Repository description'),
        'repository_type': fields.String(description='Repository type: github, gitlab, bitbucket, azure, codecommit'),
        'repository_url': fields.String(description='Repository URL'),
        'repository_owner': fields.String(readonly=True, description='Repository owner/org'),
        'repository_name': fields.String(readonly=True, description='Repository name from URL'),
        'domain_key': fields.String(description='Domain the repository belongs to'),
        'status': fields.String(description='Repository status: active, archived'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    create_repository_model = ns.model('CreateRepositoryRequest', {
        'repository_url': fields.String(required=True, description='Repository URL (will be parsed)'),
        'name': fields.String(description='Repository name (defaults to parsed name from URL)'),
        'description': fields.String(description='Repository description'),
        'domain_key': fields.String(description='Domain key (admin only, defaults to user domain)'),
    })

    update_repository_model = ns.model('UpdateRepositoryRequest', {
        'name': fields.String(description='Repository name'),
        'description': fields.String(description='Repository description'),
        'repository_url': fields.String(description='Repository URL (will be re-parsed)'),
        'status': fields.String(description='Repository status: active, archived'),
    })

    project_repository_model = ns.model('ProjectRepository', {
        'project_repository_key': fields.String(readonly=True, description='Association identifier'),
        'project_key': fields.String(description='Project key'),
        'repository_key': fields.String(description='Repository key'),
        'created_at': fields.DateTime(readonly=True),
    })

    link_project_model = ns.model('LinkProjectRequest', {
        'project_key': fields.String(required=True, description='Project key to link'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class RepositoryList(Resource):
        @ns.doc('list_repositories')
        @require_auth_strict
        def get(self):
            """
            List repositories.

            Query params:
            - status: Filter by status ('active', 'archived', or omit for all active)
            - domain_key: Filter by domain (admin only)
            - include_projects: Include project associations (default: false)
            """
            user = g.current_user
            status_filter = request.args.get('status')
            domain_filter = request.args.get('domain_key')
            include_projects = request.args.get('include_projects', 'false').lower() == 'true'

            # Get domain key for filtering
            domain_key = user.domain_key if user.domain_key else None

            if not domain_key and not user.is_admin:
                return {'success': False, 'msg': 'User must belong to a domain'}, 400

            # Build query
            if user.is_admin:
                if domain_filter and domain_filter != 'all':
                    query = Repository.query.filter_by(domain_key=domain_filter)
                elif domain_filter == 'all':
                    query = Repository.query
                else:
                    query = Repository.query
            else:
                query = Repository.query.filter_by(domain_key=domain_key)

            # Apply status filter
            if status_filter:
                query = query.filter_by(status=status_filter)
            else:
                # Default to active only
                query = query.filter_by(status='active')

            repositories = query.order_by(Repository.name).all()

            return {
                'success': True,
                'msg': f'Found {len(repositories)} repositories',
                'data': {
                    'repositories': [r.to_dict(include_projects=include_projects) for r in repositories],
                    'total': len(repositories)
                }
            }

        @ns.doc('create_repository')
        @ns.expect(create_repository_model)
        @require_domain_admin
        def post(self):
            """Create a new repository. Admins can specify domain_key, others use their own domain."""
            from api.models import Domain
            user = g.current_user
            data = request.json or {}

            if not data.get('repository_url'):
                return {'success': False, 'msg': 'repository_url is required'}, 400

            # Determine domain_key
            if data.get('domain_key') and user.is_admin:
                domain = Domain.get_by_key(data['domain_key'])
                if not domain:
                    return {'success': False, 'msg': 'Domain not found'}, 404
                domain_key = data['domain_key']
            elif user.domain_key:
                domain_key = user.domain_key
            else:
                return {'success': False, 'msg': 'Domain is required'}, 400

            # Check for duplicate repository URL
            existing = Repository.find_by_url(data['repository_url'])
            if existing:
                return {
                    'success': False,
                    'msg': f'A repository with this URL already exists: {existing.name}'
                }, 409

            try:
                repository = Repository.create_repository(
                    domain_key=domain_key,
                    repository_url=data['repository_url'],
                    name=data.get('name'),
                    description=data.get('description'),
                    extra_data=data.get('extra_data')
                )

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='Repository',
                    entity_key=repository.repository_key,
                    entity_name=repository.name,
                    changes={
                        'repository_url': repository.repository_url,
                        'domain_key': repository.domain_key,
                    },
                    domain_key=domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Repository created successfully',
                    'data': {
                        'repository': repository.to_dict()
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/lookup')
    class RepositoryLookup(Resource):
        @ns.doc('lookup_repository')
        @require_auth_strict
        def get(self):
            """
            Find a repository by URL and return with linked projects.

            Query params:
            - url: The repository URL to look up (required)

            Returns the repository with its project associations.
            This is the KEY endpoint for MCP detection.
            """
            repository_url = request.args.get('url')

            if not repository_url:
                return {'success': False, 'msg': 'url is required'}, 400

            repository = Repository.find_by_url(repository_url)

            if not repository:
                return {
                    'success': True,
                    'msg': 'No repository found for this URL',
                    'data': {
                        'repository': None,
                        'projects': []
                    }
                }

            # Get project associations with full project data
            associations = ProjectRepository.get_projects_for_repository(repository.repository_key)
            projects = []
            for assoc in associations:
                project = Project.get_by_key(assoc.project_key)
                if project:
                    # Include team associations with each project
                    projects.append(project.to_dict(include_teams=True))

            return {
                'success': True,
                'msg': 'Repository found',
                'data': {
                    'repository': repository.to_dict(),
                    'projects': projects
                }
            }

    @ns.route('/<string:repository_key>')
    @ns.param('repository_key', 'Repository identifier')
    class RepositoryDetail(Resource):
        @ns.doc('get_repository')
        @require_auth_strict
        def get(self, repository_key):
            """Get repository details."""
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            include_projects = request.args.get('include_projects', 'true').lower() == 'true'

            return {
                'success': True,
                'msg': 'Repository retrieved',
                'data': {
                    'repository': repository.to_dict(include_projects=include_projects)
                }
            }

        @ns.doc('update_repository')
        @ns.expect(update_repository_model)
        @require_domain_admin
        def put(self, repository_key):
            """Update repository details."""
            user = g.current_user
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            # Check domain access
            if repository.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            data = request.json or {}
            changes = {}

            if 'name' in data:
                changes['name'] = {'old': repository.name, 'new': data['name']}
                repository.name = data['name'].strip()

            if 'description' in data:
                changes['description'] = {'old': repository.description, 'new': data['description']}
                repository.description = data['description']

            if 'repository_url' in data:
                # Check for duplicate if changing URL
                if data['repository_url'] and data['repository_url'] != repository.repository_url:
                    existing = Repository.find_by_url(data['repository_url'])
                    if existing and existing.repository_key != repository.repository_key:
                        return {
                            'success': False,
                            'msg': f'A repository with this URL already exists: {existing.name}'
                        }, 409

                changes['repository_url'] = {'old': repository.repository_url, 'new': data['repository_url']}
                repository.update_url(data['repository_url'])

            if 'status' in data:
                if data['status'] not in ('active', 'archived'):
                    return {'success': False, 'msg': 'Invalid status'}, 400
                changes['status'] = {'old': repository.status, 'new': data['status']}
                repository.status = data['status']

            try:
                repository.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=user.user_key,
                        entity_type='Repository',
                        entity_key=repository.repository_key,
                        entity_name=repository.name,
                        changes=changes,
                        domain_key=get_user_domain_key(),
                        user_key=user.user_key
                    )

                return {
                    'success': True,
                    'msg': 'Repository updated',
                    'data': {
                        'repository': repository.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('archive_repository')
        @require_domain_admin
        def delete(self, repository_key):
            """Archive a repository (soft delete)."""
            user = g.current_user
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            # Check domain access
            if repository.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            try:
                repository.archive()

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='Repository',
                    entity_key=repository.repository_key,
                    entity_name=repository.name,
                    domain_key=get_user_domain_key(),
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Repository archived',
                    'data': {
                        'repository': repository.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:repository_key>/projects')
    @ns.param('repository_key', 'Repository identifier')
    class RepositoryProjects(Resource):
        @ns.doc('list_repository_projects')
        @require_auth_strict
        def get(self, repository_key):
            """List projects linked to a repository."""
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            associations = ProjectRepository.get_projects_for_repository(repository_key)
            projects = []
            for assoc in associations:
                project = Project.get_by_key(assoc.project_key)
                if project:
                    projects.append({
                        'project_repository_key': assoc.project_repository_key,
                        'project': project.to_dict(include_teams=True),
                        'created_at': assoc.created_at.isoformat() if assoc.created_at else None
                    })

            return {
                'success': True,
                'msg': f'Found {len(projects)} linked projects',
                'data': {
                    'repository': {'repository_key': repository.repository_key, 'name': repository.name},
                    'projects': projects
                }
            }

        @ns.doc('link_project_to_repository')
        @ns.expect(link_project_model)
        @require_domain_admin
        def post(self, repository_key):
            """Link a project to a repository."""
            user = g.current_user
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            # Check domain access
            if repository.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            data = request.json or {}

            if not data.get('project_key'):
                return {'success': False, 'msg': 'project_key is required'}, 400

            project = Project.get_by_key(data['project_key'])
            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            # Ensure project is in the same domain
            if project.domain_key != repository.domain_key:
                return {'success': False, 'msg': 'Project must be in the same domain as the repository'}, 400

            try:
                association = ProjectRepository.create_association(
                    project_key=project.project_key,
                    repository_key=repository.repository_key
                )

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='ProjectRepository',
                    entity_key=association.project_repository_key,
                    entity_name=f'{project.name} -> {repository.name}',
                    changes={'project_key': project.project_key, 'repository_key': repository.repository_key},
                    domain_key=repository.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Project linked to repository',
                    'data': {
                        'association': association.to_dict(include_project=True)
                    }
                }, 201

            except ValueError as e:
                return {'success': False, 'msg': str(e)}, 409
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:repository_key>/projects/<string:project_key>')
    @ns.param('repository_key', 'Repository identifier')
    @ns.param('project_key', 'Project identifier')
    class RepositoryProjectDetail(Resource):
        @ns.doc('unlink_project_from_repository')
        @require_domain_admin
        def delete(self, repository_key, project_key):
            """Unlink a project from a repository."""
            user = g.current_user
            repository = Repository.get_by_key(repository_key)

            if not repository:
                return {'success': False, 'msg': 'Repository not found'}, 404

            # Check domain access
            if repository.domain_key != user.domain_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            association = ProjectRepository.get_association(project_key, repository_key)
            if not association:
                return {'success': False, 'msg': 'Project-repository association not found'}, 404

            try:
                project = Project.get_by_key(project_key)
                project_name = project.name if project else project_key

                association.delete()

                # Record activity
                activity_service.record_delete(
                    actor=user.user_key,
                    entity_type='ProjectRepository',
                    entity_key=association.project_repository_key,
                    entity_name=f'{project_name} -> {repository.name}',
                    domain_key=repository.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Project unlinked from repository'
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
