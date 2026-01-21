"""
Collective Memory Platform - Database Routes

Admin endpoints for database statistics, health monitoring, and entity consistency checks.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields
from sqlalchemy import text, inspect

from api.models.base import db
from api.models.entity import Entity
from api.models.relationship import Relationship
from api.models.work_session import WorkSession
from api.models.project import Project
from api.models.team import Team
from api.models.user import User
from api.models.client import Client
from api.models.agent import Agent
from api.services.auth import require_auth


def register_database_routes(api: Api):
    """Register database admin routes with the API."""

    ns = api.namespace(
        'database',
        description='Database administration and statistics',
        path='/database'
    )

    # Response models
    table_stats_model = ns.model('TableStats', {
        'table_name': fields.String(description='Database table name'),
        'row_count': fields.Integer(description='Number of rows'),
        'has_domain_key': fields.Boolean(description='Whether table has domain_key column'),
        'domain_filtered_count': fields.Integer(description='Count filtered by domain (if applicable)'),
    })

    response_model = ns.model('DatabaseStatsResponse', {
        'success': fields.Boolean(),
        'msg': fields.String(),
        'data': fields.Raw(),
    })

    @ns.route('/stats')
    class DatabaseStats(Resource):
        @ns.doc('get_database_stats')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Get database table statistics.

            System admins see all tables with total counts.
            Domain admins see domain-filtered counts for tables with domain_key.

            Query params:
            - domain_key: Filter counts by domain (system admin only)
            """
            from flask import g

            # Check authorization
            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            # Get domain filter
            domain_key = request.args.get('domain_key')

            # Domain admins can only see their own domain
            if user.role == 'domain_admin':
                domain_key = user.domain_key

            # Get all table names from the database
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()

            stats = []
            total_rows = 0
            total_domain_rows = 0

            for table_name in sorted(table_names):
                # Skip internal/system tables
                if table_name.startswith('pg_') or table_name.startswith('sql_'):
                    continue

                # Get columns to check for domain_key
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                has_domain_key = 'domain_key' in columns

                # Get total count
                try:
                    result = db.session.execute(
                        text(f'SELECT COUNT(*) FROM "{table_name}"')
                    )
                    row_count = result.scalar() or 0
                except Exception:
                    row_count = -1  # Error reading table

                # Get domain-filtered count if applicable
                domain_filtered_count = None
                if has_domain_key and domain_key:
                    try:
                        result = db.session.execute(
                            text(f'SELECT COUNT(*) FROM "{table_name}" WHERE domain_key = :dk'),
                            {'dk': domain_key}
                        )
                        domain_filtered_count = result.scalar() or 0
                    except Exception:
                        domain_filtered_count = -1

                stats.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'has_domain_key': has_domain_key,
                    'domain_filtered_count': domain_filtered_count,
                })

                if row_count > 0:
                    total_rows += row_count
                if domain_filtered_count and domain_filtered_count > 0:
                    total_domain_rows += domain_filtered_count

            return {
                'success': True,
                'msg': 'Database statistics retrieved',
                'data': {
                    'tables': stats,
                    'total_tables': len(stats),
                    'total_rows': total_rows,
                    'total_domain_rows': total_domain_rows if domain_key else None,
                    'domain_key': domain_key,
                    'scope': 'domain' if domain_key else 'all',
                }
            }

    @ns.route('/health')
    class DatabaseHealth(Resource):
        @ns.doc('get_database_health')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Check database connectivity and basic health.
            """
            from flask import g

            # Check authorization - admin only
            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            try:
                # Test database connection
                result = db.session.execute(text('SELECT 1'))
                result.scalar()

                # Get database version
                version_result = db.session.execute(text('SELECT version()'))
                db_version = version_result.scalar()

                # Get database size (PostgreSQL specific)
                size_result = db.session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                db_size = size_result.scalar()

                # Get connection info
                conn_result = db.session.execute(
                    text("SELECT current_database(), current_user")
                )
                conn_info = conn_result.fetchone()

                return {
                    'success': True,
                    'msg': 'Database is healthy',
                    'data': {
                        'status': 'healthy',
                        'database': conn_info[0] if conn_info else None,
                        'user': conn_info[1] if conn_info else None,
                        'version': db_version,
                        'size': db_size,
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'msg': f'Database health check failed: {str(e)}',
                    'data': {
                        'status': 'unhealthy',
                        'error': str(e),
                    }
                }, 500

    @ns.route('/consistency')
    class EntityConsistency(Resource):
        @ns.doc('check_entity_consistency')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Check entity consistency issues.

            Checks for:
            - Milestones with incorrect scope (should be project > team > domain based on session)
            - Projects without strongly linked Project entities (entity_key = project_key)
            - Teams without strongly linked Team entities (entity_key = team_key)
            - Users without strongly linked Person entities (entity_key = user_key)
            - Clients without strongly linked Client entities (entity_key = client_key)
            - Milestones missing relationships to Project/Team entities (BELONGS_TO)
            - Milestones missing relationships to Person entities (CREATED_BY)
            - Milestones missing relationships to Client entities (EXECUTED_BY)

            Query params:
            - domain_key: Filter by domain (system admin only)
            """
            from flask import g

            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            domain_key = request.args.get('domain_key')
            if user.role == 'domain_admin':
                domain_key = user.domain_key

            issues = {
                'projects': [],
                'teams': [],
                'users': [],
                'clients': [],
                'milestones': [],
                'summary': {
                    'project_entity_issues': 0,
                    'team_entity_issues': 0,
                    'user_entity_issues': 0,
                    'client_entity_issues': 0,
                    'milestone_scope_issues': 0,
                    'milestone_relationship_issues': 0,
                    'milestone_client_issues': 0,
                }
            }

            # ========================================
            # PARENT ENTITY CHECKS (must come first)
            # ========================================

            # Check Project entity strong links
            project_query = Project.query
            if domain_key:
                project_query = project_query.filter(Project.domain_key == domain_key)

            projects = project_query.all()

            for project in projects:
                # Check if entity exists with entity_key = project_key
                project_entity = Entity.get_by_key(project.project_key)

                if not project_entity:
                    issues['projects'].append({
                        'project_key': project.project_key,
                        'name': project.name,
                        'issue_type': 'missing_entity',
                        'description': 'No Project entity exists with entity_key = project_key',
                    })
                    issues['summary']['project_entity_issues'] += 1
                elif project_entity.entity_type != 'Project':
                    issues['projects'].append({
                        'project_key': project.project_key,
                        'name': project.name,
                        'issue_type': 'wrong_entity_type',
                        'current_type': project_entity.entity_type,
                        'expected_type': 'Project',
                    })
                    issues['summary']['project_entity_issues'] += 1

            # Check Team entity strong links
            team_query = Team.query
            if domain_key:
                team_query = team_query.filter(Team.domain_key == domain_key)

            teams = team_query.all()

            for team in teams:
                # Check if entity exists with entity_key = team_key
                team_entity = Entity.get_by_key(team.team_key)

                if not team_entity:
                    issues['teams'].append({
                        'team_key': team.team_key,
                        'name': team.name,
                        'issue_type': 'missing_entity',
                        'description': 'No Team entity exists with entity_key = team_key',
                    })
                    issues['summary']['team_entity_issues'] += 1
                elif team_entity.entity_type != 'Team':
                    issues['teams'].append({
                        'team_key': team.team_key,
                        'name': team.name,
                        'issue_type': 'wrong_entity_type',
                        'current_type': team_entity.entity_type,
                        'expected_type': 'Team',
                    })
                    issues['summary']['team_entity_issues'] += 1

            # Check User entity strong links (User should have linked Person entity)
            user_query = User.query.filter(User.status == 'active')
            if domain_key:
                user_query = user_query.filter(User.domain_key == domain_key)

            users = user_query.all()

            for user in users:
                # Check if entity exists with entity_key = user_key (strong link)
                user_entity = Entity.get_by_key(user.user_key)

                if not user_entity:
                    issues['users'].append({
                        'user_key': user.user_key,
                        'email': user.email,
                        'display_name': user.display_name,
                        'issue_type': 'missing_entity',
                        'description': 'No Person entity exists with entity_key = user_key',
                    })
                    issues['summary']['user_entity_issues'] += 1
                elif user_entity.entity_type != 'Person':
                    issues['users'].append({
                        'user_key': user.user_key,
                        'email': user.email,
                        'display_name': user.display_name,
                        'issue_type': 'wrong_entity_type',
                        'current_type': user_entity.entity_type,
                        'expected_type': 'Person',
                    })
                    issues['summary']['user_entity_issues'] += 1
                elif user.entity_key != user.user_key:
                    # User has entity but link is not the strong link pattern
                    issues['users'].append({
                        'user_key': user.user_key,
                        'email': user.email,
                        'display_name': user.display_name,
                        'issue_type': 'weak_link',
                        'current_entity_key': user.entity_key,
                        'expected_entity_key': user.user_key,
                        'description': 'User.entity_key should equal user_key for strong link',
                    })
                    issues['summary']['user_entity_issues'] += 1

            # Check Client entity strong links (Client should have linked Client entity)
            clients = Client.get_all()

            for client in clients:
                # Check if entity exists with entity_key = client_key (strong link)
                client_entity = Entity.get_by_key(client.client_key)

                if not client_entity:
                    issues['clients'].append({
                        'client_key': client.client_key,
                        'name': client.name,
                        'issue_type': 'missing_entity',
                        'description': 'No Client entity exists with entity_key = client_key',
                    })
                    issues['summary']['client_entity_issues'] += 1
                elif client_entity.entity_type != 'Client':
                    issues['clients'].append({
                        'client_key': client.client_key,
                        'name': client.name,
                        'issue_type': 'wrong_entity_type',
                        'current_type': client_entity.entity_type,
                        'expected_type': 'Client',
                    })
                    issues['summary']['client_entity_issues'] += 1
                elif client.entity_key != client.client_key:
                    # Client has entity but link is not the strong link pattern
                    issues['clients'].append({
                        'client_key': client.client_key,
                        'name': client.name,
                        'issue_type': 'weak_link',
                        'current_entity_key': client.entity_key,
                        'expected_entity_key': client.client_key,
                        'description': 'Client.entity_key should equal client_key for strong link',
                    })
                    issues['summary']['client_entity_issues'] += 1

            # ========================================
            # MILESTONE CHECKS (after parent entities)
            # ========================================

            # Check Milestone scope consistency
            milestone_query = Entity.query.filter(Entity.entity_type == 'Milestone')
            if domain_key:
                milestone_query = milestone_query.filter(Entity.domain_key == domain_key)

            milestones = milestone_query.all()

            for milestone in milestones:
                if not milestone.work_session_key:
                    continue

                # Get the work session to check scope
                session = WorkSession.get_by_key(milestone.work_session_key)
                if not session:
                    continue

                # Determine expected scope based on session (project > team > domain)
                expected_scope_type = None
                expected_scope_key = None

                if session.project_key:
                    expected_scope_type = 'project'
                    expected_scope_key = session.project_key
                elif session.team_key:
                    expected_scope_type = 'team'
                    expected_scope_key = session.team_key
                elif session.domain_key:
                    expected_scope_type = 'domain'
                    expected_scope_key = session.domain_key

                # Check if scope matches
                if milestone.scope_type != expected_scope_type or milestone.scope_key != expected_scope_key:
                    issues['milestones'].append({
                        'entity_key': milestone.entity_key,
                        'name': milestone.name,
                        'issue_type': 'scope_mismatch',
                        'current_scope_type': milestone.scope_type,
                        'current_scope_key': milestone.scope_key,
                        'expected_scope_type': expected_scope_type,
                        'expected_scope_key': expected_scope_key,
                        'work_session_key': milestone.work_session_key,
                    })
                    issues['summary']['milestone_scope_issues'] += 1

                # Check for BELONGS_TO relationship to Project/Team entity
                # Milestones with project scope should have relationship to project entity
                # Milestones with team scope should have relationship to team entity
                target_entity_key = None
                if session.project_key:
                    target_entity_key = session.project_key
                elif session.team_key:
                    target_entity_key = session.team_key

                if target_entity_key:
                    # Check if BELONGS_TO relationship exists
                    existing_rel = Relationship.query.filter_by(
                        from_entity_key=milestone.entity_key,
                        to_entity_key=target_entity_key,
                        relationship_type='BELONGS_TO'
                    ).first()

                    if not existing_rel:
                        issues['milestones'].append({
                            'entity_key': milestone.entity_key,
                            'name': milestone.name,
                            'issue_type': 'missing_relationship',
                            'target_entity_key': target_entity_key,
                            'target_type': 'project' if session.project_key else 'team',
                            'work_session_key': milestone.work_session_key,
                        })
                        issues['summary']['milestone_relationship_issues'] += 1

                # Check for CREATED_BY relationship to Person entity
                # Get agent_id from milestone properties to find the user
                props = milestone.properties or {}
                agent_id_str = props.get('agent_id')
                if agent_id_str:
                    # Look up the agent to get user_key
                    agent = Agent.query.filter_by(agent_id=agent_id_str).first()
                    if agent and agent.user_key:
                        # Check if CREATED_BY relationship exists to Person entity
                        created_by_rel = Relationship.query.filter_by(
                            from_entity_key=milestone.entity_key,
                            to_entity_key=agent.user_key,  # Person entity uses user_key
                            relationship_type='CREATED_BY'
                        ).first()

                        if not created_by_rel:
                            issues['milestones'].append({
                                'entity_key': milestone.entity_key,
                                'name': milestone.name,
                                'issue_type': 'missing_created_by',
                                'target_entity_key': agent.user_key,
                                'target_type': 'person',
                                'work_session_key': milestone.work_session_key,
                            })
                            issues['summary']['milestone_relationship_issues'] += 1

            # Check Milestone → Client relationships (EXECUTED_BY)
            # Milestones should have EXECUTED_BY relationship to the Client that recorded them
            for milestone in milestones:
                props = milestone.properties or {}
                agent_id_str = props.get('agent_id')

                if agent_id_str:
                    # Look up the agent to get client_key
                    agent = Agent.query.filter_by(agent_id=agent_id_str).first()
                    if agent and agent.client_key:
                        # Check if EXECUTED_BY relationship exists to Client entity
                        executed_by_rel = Relationship.query.filter_by(
                            from_entity_key=milestone.entity_key,
                            to_entity_key=agent.client_key,
                            relationship_type='EXECUTED_BY'
                        ).first()

                        if not executed_by_rel:
                            issues['milestones'].append({
                                'entity_key': milestone.entity_key,
                                'name': milestone.name,
                                'issue_type': 'missing_executed_by',
                                'target_entity_key': agent.client_key,
                                'target_type': 'client',
                                'work_session_key': milestone.work_session_key,
                            })
                            issues['summary']['milestone_client_issues'] += 1

            total_issues = sum(issues['summary'].values())

            return {
                'success': True,
                'msg': f'Found {total_issues} consistency issues' if total_issues > 0 else 'No consistency issues found',
                'data': {
                    'issues': issues,
                    'total_issues': total_issues,
                    'domain_key': domain_key,
                }
            }

        @ns.doc('fix_entity_consistency')
        @ns.marshal_with(response_model)
        @require_auth
        def post(self):
            """
            Fix entity consistency issues.

            Request body:
            - fix_types: List of issue types to fix (processed in this order):
                PARENT ENTITIES (processed first):
                - 'project_entities': Create missing Project entities
                - 'team_entities': Create missing Team entities
                - 'user_entities': Create missing Person entities for users
                - 'client_entities': Create missing Client entities
                MILESTONE FIXES (processed after parent entities exist):
                - 'milestone_scopes': Fix milestone scope mismatches
                - 'milestone_relationships': Fix missing BELONGS_TO and CREATED_BY relationships
                - 'milestone_clients': Create missing EXECUTED_BY relationships to Clients
            - domain_key: Filter by domain (system admin only)
            - dry_run: If true, only report what would be fixed (default: true)
            """
            from flask import g

            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            data = request.get_json() or {}
            fix_types = data.get('fix_types', [])
            domain_key = data.get('domain_key')
            dry_run = data.get('dry_run', True)

            if user.role == 'domain_admin':
                domain_key = user.domain_key

            if not fix_types:
                return {'success': False, 'msg': 'fix_types is required'}, 400

            results = {
                'fixed': [],
                'errors': [],
                'dry_run': dry_run,
            }

            # ========================================
            # PARENT ENTITY FIXES (must come first)
            # ========================================

            # Fix Project entities - create missing or update wrong type
            if 'project_entities' in fix_types:
                project_query = Project.query
                if domain_key:
                    project_query = project_query.filter(Project.domain_key == domain_key)

                projects = project_query.all()

                for project in projects:
                    project_entity = Entity.get_by_key(project.project_key)

                    if not project_entity:
                        # Create new entity with entity_key = project_key
                        if not dry_run:
                            try:
                                new_entity = Entity(
                                    entity_key=project.project_key,
                                    name=project.name,
                                    entity_type='Project',
                                    domain_key=project.domain_key,
                                    scope_type='domain',
                                    scope_key=project.domain_key,
                                    properties={
                                        'description': project.description,
                                        'status': project.status,
                                        'auto_created': True,
                                        'source': 'consistency_fix',
                                    }
                                )
                                new_entity.save()
                                results['fixed'].append({
                                    'type': 'project_entity_created',
                                    'project_key': project.project_key,
                                    'name': project.name,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'project_entity_created',
                                    'project_key': project.project_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'project_entity_created',
                                'project_key': project.project_key,
                                'name': project.name,
                                'dry_run': True,
                            })

            # Fix Team entities - create missing or update wrong type
            if 'team_entities' in fix_types:
                team_query = Team.query
                if domain_key:
                    team_query = team_query.filter(Team.domain_key == domain_key)

                teams = team_query.all()

                for team in teams:
                    team_entity = Entity.get_by_key(team.team_key)

                    if not team_entity:
                        # Create new entity with entity_key = team_key
                        if not dry_run:
                            try:
                                new_entity = Entity(
                                    entity_key=team.team_key,
                                    name=team.name,
                                    entity_type='Team',
                                    domain_key=team.domain_key,
                                    scope_type='domain',
                                    scope_key=team.domain_key,
                                    properties={
                                        'description': team.description,
                                        'status': team.status,
                                        'auto_created': True,
                                        'source': 'consistency_fix',
                                    }
                                )
                                new_entity.save()
                                results['fixed'].append({
                                    'type': 'team_entity_created',
                                    'team_key': team.team_key,
                                    'name': team.name,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'team_entity_created',
                                    'team_key': team.team_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'team_entity_created',
                                'team_key': team.team_key,
                                'name': team.name,
                                'dry_run': True,
                            })

            # Fix User entities - create missing Person entities or fix weak links
            if 'user_entities' in fix_types:
                user_query = User.query.filter(User.status == 'active')
                if domain_key:
                    user_query = user_query.filter(User.domain_key == domain_key)

                users = user_query.all()

                for user in users:
                    user_entity = Entity.get_by_key(user.user_key)

                    if not user_entity:
                        # Create new Person entity using ensure_person_entity
                        if not dry_run:
                            try:
                                user.ensure_person_entity()
                                results['fixed'].append({
                                    'type': 'user_entity_created',
                                    'user_key': user.user_key,
                                    'display_name': user.display_name,
                                    'email': user.email,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'user_entity_created',
                                    'user_key': user.user_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'user_entity_created',
                                'user_key': user.user_key,
                                'display_name': user.display_name,
                                'email': user.email,
                                'dry_run': True,
                            })
                    elif user_entity.entity_type != 'Person':
                        # Update entity type to Person
                        if not dry_run:
                            try:
                                user_entity.entity_type = 'Person'
                                user_entity.save()
                                results['fixed'].append({
                                    'type': 'user_entity_type_fixed',
                                    'user_key': user.user_key,
                                    'display_name': user.display_name,
                                    'old_type': user_entity.entity_type,
                                    'new_type': 'Person',
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'user_entity_type_fixed',
                                    'user_key': user.user_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'user_entity_type_fixed',
                                'user_key': user.user_key,
                                'display_name': user.display_name,
                                'would_change_type': 'Person',
                                'dry_run': True,
                            })
                    elif user.entity_key != user.user_key:
                        # Fix weak link - update user.entity_key to match user_key
                        if not dry_run:
                            try:
                                old_entity_key = user.entity_key
                                user.entity_key = user.user_key
                                user.save()
                                results['fixed'].append({
                                    'type': 'user_entity_link_fixed',
                                    'user_key': user.user_key,
                                    'display_name': user.display_name,
                                    'old_entity_key': old_entity_key,
                                    'new_entity_key': user.user_key,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'user_entity_link_fixed',
                                    'user_key': user.user_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'user_entity_link_fixed',
                                'user_key': user.user_key,
                                'display_name': user.display_name,
                                'would_update_entity_key': user.user_key,
                                'dry_run': True,
                            })

            # Fix Client entities - create missing or fix links
            if 'client_entities' in fix_types:
                clients = Client.get_all()

                for client in clients:
                    client_entity = Entity.get_by_key(client.client_key)

                    if not client_entity:
                        # Create new Client entity using ensure_entity
                        if not dry_run:
                            try:
                                client.ensure_entity()
                                results['fixed'].append({
                                    'type': 'client_entity_created',
                                    'client_key': client.client_key,
                                    'name': client.name,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'client_entity_created',
                                    'client_key': client.client_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'client_entity_created',
                                'client_key': client.client_key,
                                'name': client.name,
                                'dry_run': True,
                            })
                    elif client_entity.entity_type != 'Client':
                        # Update entity type to Client
                        if not dry_run:
                            try:
                                old_type = client_entity.entity_type
                                client_entity.entity_type = 'Client'
                                client_entity.save()
                                results['fixed'].append({
                                    'type': 'client_entity_type_fixed',
                                    'client_key': client.client_key,
                                    'name': client.name,
                                    'old_type': old_type,
                                    'new_type': 'Client',
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'client_entity_type_fixed',
                                    'client_key': client.client_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'client_entity_type_fixed',
                                'client_key': client.client_key,
                                'name': client.name,
                                'would_change_type': 'Client',
                                'dry_run': True,
                            })
                    elif client.entity_key != client.client_key:
                        # Fix weak link - update client.entity_key to match client_key
                        if not dry_run:
                            try:
                                old_entity_key = client.entity_key
                                client.entity_key = client.client_key
                                client.save()
                                results['fixed'].append({
                                    'type': 'client_entity_link_fixed',
                                    'client_key': client.client_key,
                                    'name': client.name,
                                    'old_entity_key': old_entity_key,
                                    'new_entity_key': client.client_key,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'client_entity_link_fixed',
                                    'client_key': client.client_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'client_entity_link_fixed',
                                'client_key': client.client_key,
                                'name': client.name,
                                'would_update_entity_key': client.client_key,
                                'dry_run': True,
                            })

            # ========================================
            # MILESTONE FIXES (after parent entities)
            # ========================================

            # Fix Milestone scopes based on session's project/team/domain
            if 'milestone_scopes' in fix_types:
                milestone_query = Entity.query.filter(Entity.entity_type == 'Milestone')
                if domain_key:
                    milestone_query = milestone_query.filter(Entity.domain_key == domain_key)

                milestones = milestone_query.all()

                for milestone in milestones:
                    if not milestone.work_session_key:
                        continue

                    session = WorkSession.get_by_key(milestone.work_session_key)
                    if not session:
                        continue

                    # Determine expected scope (project > team > domain)
                    expected_scope_type = None
                    expected_scope_key = None

                    if session.project_key:
                        expected_scope_type = 'project'
                        expected_scope_key = session.project_key
                    elif session.team_key:
                        expected_scope_type = 'team'
                        expected_scope_key = session.team_key
                    elif session.domain_key:
                        expected_scope_type = 'domain'
                        expected_scope_key = session.domain_key

                    # Fix if scope doesn't match
                    if milestone.scope_type != expected_scope_type or milestone.scope_key != expected_scope_key:
                        if not dry_run:
                            try:
                                old_scope_type = milestone.scope_type
                                old_scope_key = milestone.scope_key
                                milestone.scope_type = expected_scope_type
                                milestone.scope_key = expected_scope_key
                                milestone.save()
                                results['fixed'].append({
                                    'type': 'milestone_scope_fixed',
                                    'entity_key': milestone.entity_key,
                                    'name': milestone.name,
                                    'old_scope_type': old_scope_type,
                                    'old_scope_key': old_scope_key,
                                    'new_scope_type': expected_scope_type,
                                    'new_scope_key': expected_scope_key,
                                })
                            except Exception as e:
                                results['errors'].append({
                                    'type': 'milestone_scope_fixed',
                                    'entity_key': milestone.entity_key,
                                    'error': str(e),
                                })
                        else:
                            results['fixed'].append({
                                'type': 'milestone_scope_fixed',
                                'entity_key': milestone.entity_key,
                                'name': milestone.name,
                                'would_change_scope_type': expected_scope_type,
                                'would_change_scope_key': expected_scope_key,
                                'dry_run': True,
                            })

            # Fix Milestone relationships (BELONGS_TO project/team, CREATED_BY person)
            if 'milestone_relationships' in fix_types:
                milestone_query = Entity.query.filter(Entity.entity_type == 'Milestone')
                if domain_key:
                    milestone_query = milestone_query.filter(Entity.domain_key == domain_key)

                milestones = milestone_query.all()

                for milestone in milestones:
                    if not milestone.work_session_key:
                        continue

                    session = WorkSession.get_by_key(milestone.work_session_key)
                    if not session:
                        continue

                    # Determine target entity for BELONGS_TO relationship
                    target_entity_key = None
                    target_type = None
                    if session.project_key:
                        target_entity_key = session.project_key
                        target_type = 'project'
                    elif session.team_key:
                        target_entity_key = session.team_key
                        target_type = 'team'

                    if target_entity_key:
                        # Check if BELONGS_TO relationship exists
                        existing_rel = Relationship.query.filter_by(
                            from_entity_key=milestone.entity_key,
                            to_entity_key=target_entity_key,
                            relationship_type='BELONGS_TO'
                        ).first()

                        if not existing_rel:
                            if not dry_run:
                                try:
                                    new_rel = Relationship(
                                        from_entity_key=milestone.entity_key,
                                        to_entity_key=target_entity_key,
                                        relationship_type='BELONGS_TO',
                                        properties={
                                            'auto_created': True,
                                            'source': 'consistency_fix'
                                        }
                                    )
                                    new_rel.save()
                                    results['fixed'].append({
                                        'type': 'milestone_belongs_to',
                                        'entity_key': milestone.entity_key,
                                        'name': milestone.name,
                                        'target_entity_key': target_entity_key,
                                        'target_type': target_type,
                                    })
                                except Exception as e:
                                    results['errors'].append({
                                        'type': 'milestone_belongs_to',
                                        'entity_key': milestone.entity_key,
                                        'error': str(e),
                                    })
                            else:
                                results['fixed'].append({
                                    'type': 'milestone_belongs_to',
                                    'entity_key': milestone.entity_key,
                                    'name': milestone.name,
                                    'would_link_to': target_entity_key,
                                    'target_type': target_type,
                                    'dry_run': True,
                                })

                    # Check for missing CREATED_BY relationship to Person
                    props = milestone.properties or {}
                    agent_id_str = props.get('agent_id')
                    if agent_id_str:
                        agent = Agent.query.filter_by(agent_id=agent_id_str).first()
                        if agent and agent.user_key:
                            created_by_rel = Relationship.query.filter_by(
                                from_entity_key=milestone.entity_key,
                                to_entity_key=agent.user_key,
                                relationship_type='CREATED_BY'
                            ).first()

                            if not created_by_rel:
                                if not dry_run:
                                    try:
                                        new_rel = Relationship(
                                            from_entity_key=milestone.entity_key,
                                            to_entity_key=agent.user_key,
                                            relationship_type='CREATED_BY',
                                            properties={
                                                'auto_created': True,
                                                'source': 'consistency_fix'
                                            }
                                        )
                                        new_rel.save()
                                        results['fixed'].append({
                                            'type': 'milestone_created_by',
                                            'entity_key': milestone.entity_key,
                                            'name': milestone.name,
                                            'target_entity_key': agent.user_key,
                                            'target_type': 'person',
                                        })
                                    except Exception as e:
                                        results['errors'].append({
                                            'type': 'milestone_created_by',
                                            'entity_key': milestone.entity_key,
                                            'error': str(e),
                                        })
                                else:
                                    results['fixed'].append({
                                        'type': 'milestone_created_by',
                                        'entity_key': milestone.entity_key,
                                        'name': milestone.name,
                                        'would_link_to': agent.user_key,
                                        'target_type': 'person',
                                        'dry_run': True,
                                    })

            # Fix Milestone → Client relationships (EXECUTED_BY)
            if 'milestone_clients' in fix_types:
                milestone_query = Entity.query.filter(Entity.entity_type == 'Milestone')
                if domain_key:
                    milestone_query = milestone_query.filter(Entity.domain_key == domain_key)

                milestones = milestone_query.all()

                for milestone in milestones:
                    props = milestone.properties or {}
                    agent_id_str = props.get('agent_id')

                    if agent_id_str:
                        agent = Agent.query.filter_by(agent_id=agent_id_str).first()
                        if agent and agent.client_key:
                            # Check if EXECUTED_BY relationship exists
                            executed_by_rel = Relationship.query.filter_by(
                                from_entity_key=milestone.entity_key,
                                to_entity_key=agent.client_key,
                                relationship_type='EXECUTED_BY'
                            ).first()

                            if not executed_by_rel:
                                if not dry_run:
                                    try:
                                        new_rel = Relationship(
                                            from_entity_key=milestone.entity_key,
                                            to_entity_key=agent.client_key,
                                            relationship_type='EXECUTED_BY',
                                            properties={
                                                'auto_created': True,
                                                'source': 'consistency_fix',
                                                'agent_id': agent_id_str,
                                            }
                                        )
                                        new_rel.save()
                                        results['fixed'].append({
                                            'type': 'milestone_executed_by',
                                            'entity_key': milestone.entity_key,
                                            'name': milestone.name,
                                            'target_entity_key': agent.client_key,
                                            'target_type': 'client',
                                        })
                                    except Exception as e:
                                        results['errors'].append({
                                            'type': 'milestone_executed_by',
                                            'entity_key': milestone.entity_key,
                                            'error': str(e),
                                        })
                                else:
                                    results['fixed'].append({
                                        'type': 'milestone_executed_by',
                                        'entity_key': milestone.entity_key,
                                        'name': milestone.name,
                                        'would_link_to': agent.client_key,
                                        'target_type': 'client',
                                        'dry_run': True,
                                    })

            return {
                'success': True,
                'msg': f"{'Would fix' if dry_run else 'Fixed'} {len(results['fixed'])} issues with {len(results['errors'])} errors",
                'data': results,
            }
