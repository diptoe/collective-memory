"""
Collective Memory Platform - Work Session Routes

Endpoints for managing work sessions - focused work periods on projects.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import WorkSession, Entity, db
from api.services.auth import require_auth_strict
from api.services.activity import activity_service


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


def register_work_session_routes(api: Api):
    """Register work session routes with the API."""

    ns = api.namespace(
        'work-sessions',
        description='Work session management for focused project work',
        path='/work-sessions'
    )

    # Define models for OpenAPI documentation
    session_model = ns.model('WorkSession', {
        'session_key': fields.String(readonly=True, description='Unique session identifier'),
        'user_key': fields.String(description='User who owns the session'),
        'project_key': fields.String(description='Project entity key'),
        'team_key': fields.String(description='Team scope (optional)'),
        'name': fields.String(description='Session name'),
        'status': fields.String(description='Status: active, closed, expired'),
        'started_at': fields.DateTime(readonly=True),
        'ended_at': fields.DateTime(readonly=True),
        'last_activity_at': fields.DateTime(readonly=True),
        'auto_close_at': fields.DateTime(readonly=True),
        'closed_by': fields.String(description='Who closed: user, agent, system'),
        'summary': fields.String(description='Session summary'),
        'time_remaining_seconds': fields.Integer(readonly=True, description='Seconds until auto-close'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    create_session_model = ns.model('CreateWorkSessionRequest', {
        'project_key': fields.String(required=True, description='Project entity key (required)'),
        'name': fields.String(description='Session name (optional)'),
        'team_key': fields.String(description='Team scope (optional)'),
    })

    update_session_model = ns.model('UpdateWorkSessionRequest', {
        'name': fields.String(description='Session name'),
        'summary': fields.String(description='Session summary'),
    })

    extend_session_model = ns.model('ExtendWorkSessionRequest', {
        'hours': fields.Float(description='Hours to extend (default: 1.0)'),
    })

    close_session_model = ns.model('CloseWorkSessionRequest', {
        'summary': fields.String(description='Session summary'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class WorkSessionList(Resource):
        @ns.doc('list_work_sessions')
        @require_auth_strict
        def get(self):
            """
            List work sessions for the current user.

            Query params:
            - status: Filter by status ('active', 'closed', 'expired', or omit for all)
            - project_key: Filter by project
            - limit: Maximum results (default: 50)
            - offset: Pagination offset (default: 0)
            """
            user = g.current_user
            status_filter = request.args.get('status')
            project_filter = request.args.get('project_key')
            limit = min(int(request.args.get('limit', 50)), 100)
            offset = int(request.args.get('offset', 0))

            query = WorkSession.query.filter_by(user_key=user.user_key)

            if status_filter:
                query = query.filter_by(status=status_filter)

            if project_filter:
                query = query.filter_by(project_key=project_filter)

            total = query.count()
            sessions = query.order_by(WorkSession.started_at.desc()).offset(offset).limit(limit).all()

            return {
                'success': True,
                'msg': f'Found {len(sessions)} work sessions',
                'data': {
                    'sessions': [s.to_dict() for s in sessions],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

        @ns.doc('start_work_session')
        @ns.expect(create_session_model)
        @require_auth_strict
        def post(self):
            """
            Start a new work session.

            Requires a project_key. Only one active session per user per project is allowed.
            """
            user = g.current_user
            data = request.json or {}

            if not data.get('project_key'):
                return {'success': False, 'msg': 'project_key is required'}, 400

            project_key = data['project_key']

            # Verify project exists
            project = Entity.get_by_key(project_key)
            if not project:
                return {'success': False, 'msg': 'Project not found'}, 404

            if project.entity_type != 'Project':
                return {'success': False, 'msg': 'Entity must be a Project type'}, 400

            # Check for existing active session
            existing = WorkSession.get_active_for_user(user.user_key, project_key)
            if existing:
                return {
                    'success': False,
                    'msg': 'An active session already exists for this project',
                    'data': {'existing_session': existing.to_dict()}
                }, 409

            try:
                session = WorkSession(
                    user_key=user.user_key,
                    project_key=project_key,
                    team_key=data.get('team_key'),
                    domain_key=user.domain_key,
                    name=data.get('name'),
                    status='active'
                )
                session.save()

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='WorkSession',
                    entity_key=session.session_key,
                    entity_name=session.name or f'Session for {project.name}',
                    changes={'project_key': project_key},
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Work session started',
                    'data': {
                        'session': session.to_dict()
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/active')
    class ActiveWorkSession(Resource):
        @ns.doc('get_active_work_session')
        @require_auth_strict
        def get(self):
            """
            Get the active work session for the current user.

            Query params:
            - project_key: Filter by project (optional)
            """
            user = g.current_user
            project_filter = request.args.get('project_key')

            session = WorkSession.get_active_for_user(user.user_key, project_filter)

            if not session:
                return {
                    'success': True,
                    'msg': 'No active session found',
                    'data': {'session': None}
                }

            # Check if session should be expired
            if session.is_expired():
                session.expire()
                session.save()
                return {
                    'success': True,
                    'msg': 'No active session found (previous session expired)',
                    'data': {'session': None}
                }

            return {
                'success': True,
                'msg': 'Active session found',
                'data': {
                    'session': session.to_dict()
                }
            }

    @ns.route('/<string:session_key>')
    @ns.param('session_key', 'Work session identifier')
    class WorkSessionDetail(Resource):
        @ns.doc('get_work_session')
        @require_auth_strict
        def get(self, session_key):
            """Get work session details."""
            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access - users can only see their own sessions
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            # Include counts of linked entities and messages
            include_stats = request.args.get('include_stats', 'false').lower() == 'true'
            result = session.to_dict()

            if include_stats:
                from api.models import Entity, Message
                # Get categorized entity counts
                entities = Entity.query.filter_by(work_session_key=session_key).all()
                milestone_count = sum(1 for e in entities if e.entity_type == 'Milestone')
                other_entity_count = sum(1 for e in entities if e.entity_type != 'Milestone')
                total_entity_count = len(entities)
                message_count = Message.query.filter_by(work_session_key=session_key).count()
                result['stats'] = {
                    'milestone_count': milestone_count,
                    'message_count': message_count,
                    'other_entity_count': other_entity_count,
                    'total_entity_count': total_entity_count,
                    # Legacy fields for backwards compatibility
                    'entity_count': total_entity_count
                }

            return {
                'success': True,
                'msg': 'Work session retrieved',
                'data': {
                    'session': result
                }
            }

        @ns.doc('update_work_session')
        @ns.expect(update_session_model)
        @require_auth_strict
        def put(self, session_key):
            """Update work session (name, summary)."""
            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            data = request.json or {}
            changes = {}

            if 'name' in data:
                changes['name'] = {'old': session.name, 'new': data['name']}
                session.name = data['name']

            if 'summary' in data:
                changes['summary'] = {'old': session.summary, 'new': data['summary']}
                session.summary = data['summary']

            # Update activity timestamp if session is active
            if session.status == 'active':
                session.update_activity()

            try:
                session.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=user.user_key,
                        entity_type='WorkSession',
                        entity_key=session.session_key,
                        entity_name=session.name or session.session_key,
                        changes=changes,
                        domain_key=get_user_domain_key(),
                        user_key=user.user_key
                    )

                return {
                    'success': True,
                    'msg': 'Work session updated',
                    'data': {
                        'session': session.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:session_key>/extend')
    @ns.param('session_key', 'Work session identifier')
    class ExtendWorkSession(Resource):
        @ns.doc('extend_work_session')
        @ns.expect(extend_session_model)
        @require_auth_strict
        def post(self, session_key):
            """Extend the auto-close time for an active session."""
            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            if session.status != 'active':
                return {'success': False, 'msg': 'Can only extend active sessions'}, 400

            data = request.json or {}
            hours = float(data.get('hours', 1.0))

            if hours <= 0 or hours > 8:
                return {'success': False, 'msg': 'Hours must be between 0 and 8'}, 400

            try:
                session.extend(hours)
                session.save()

                return {
                    'success': True,
                    'msg': f'Session extended by {hours} hours',
                    'data': {
                        'session': session.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:session_key>/close')
    @ns.param('session_key', 'Work session identifier')
    class CloseWorkSession(Resource):
        @ns.doc('close_work_session')
        @ns.expect(close_session_model)
        @require_auth_strict
        def post(self, session_key):
            """Close a work session."""
            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            if session.status != 'active':
                return {'success': False, 'msg': 'Session is already closed'}, 400

            data = request.json or {}

            try:
                session.close(closed_by='user', summary=data.get('summary'))
                session.save()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='WorkSession',
                    entity_key=session.session_key,
                    entity_name=session.name or session.session_key,
                    changes={'status': {'old': 'active', 'new': 'closed'}},
                    domain_key=get_user_domain_key(),
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Work session closed',
                    'data': {
                        'session': session.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:session_key>/activity')
    @ns.param('session_key', 'Work session identifier')
    class WorkSessionActivity(Resource):
        @ns.doc('record_work_session_activity')
        @require_auth_strict
        def post(self, session_key):
            """
            Record activity in a work session (updates last_activity_at and auto_close_at).

            Call this endpoint when work is done within a session to prevent auto-close.
            """
            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            if session.status != 'active':
                return {'success': False, 'msg': 'Session is not active'}, 400

            try:
                session.update_activity()
                session.save()

                return {
                    'success': True,
                    'msg': 'Activity recorded',
                    'data': {
                        'session': session.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:session_key>/entities')
    @ns.param('session_key', 'Work session identifier')
    class WorkSessionEntities(Resource):
        @ns.doc('list_work_session_entities')
        @require_auth_strict
        def get(self, session_key):
            """
            List entities created during this work session.

            Query params:
            - include_metrics: Include metrics for Milestone entities (default: true)
            - limit: Maximum results (default: 50)
            - offset: Pagination offset (default: 0)
            """
            from api.models import Metric

            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            limit = min(int(request.args.get('limit', 50)), 100)
            offset = int(request.args.get('offset', 0))
            include_metrics = request.args.get('include_metrics', 'true').lower() == 'true'

            query = Entity.query.filter_by(work_session_key=session_key)
            total = query.count()
            entities = query.order_by(Entity.created_at.desc()).offset(offset).limit(limit).all()

            # Build entity dicts, including metrics for Milestone entities
            entity_dicts = []
            for entity in entities:
                entity_dict = entity.to_dict()
                if include_metrics and entity.entity_type == 'Milestone':
                    # Fetch metrics for this milestone
                    metrics = Metric.query.filter_by(entity_key=entity.entity_key).all()
                    entity_dict['metrics'] = [m.to_dict() for m in metrics]
                entity_dicts.append(entity_dict)

            return {
                'success': True,
                'msg': f'Found {len(entities)} entities',
                'data': {
                    'entities': entity_dicts,
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

    @ns.route('/<string:session_key>/messages')
    @ns.param('session_key', 'Work session identifier')
    class WorkSessionMessages(Resource):
        @ns.doc('list_work_session_messages')
        @require_auth_strict
        def get(self, session_key):
            """List messages sent during this work session."""
            from api.models import Message

            user = g.current_user
            session = WorkSession.get_by_key(session_key)

            if not session:
                return {'success': False, 'msg': 'Work session not found'}, 404

            # Check access
            if session.user_key != user.user_key and not user.is_admin:
                return {'success': False, 'msg': 'Access denied'}, 403

            limit = min(int(request.args.get('limit', 50)), 100)
            offset = int(request.args.get('offset', 0))

            query = Message.query.filter_by(work_session_key=session_key)
            total = query.count()
            messages = query.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()

            return {
                'success': True,
                'msg': f'Found {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict() for m in messages],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

    @ns.route('/cleanup-expired')
    class CleanupExpiredSessions(Resource):
        @ns.doc('cleanup_expired_sessions')
        @require_auth_strict
        def post(self):
            """
            Close all expired sessions (admin only).

            This endpoint marks all sessions past their auto_close_at time as expired.
            """
            user = g.current_user

            if not user.is_admin:
                return {'success': False, 'msg': 'Admin access required'}, 403

            try:
                count = WorkSession.close_expired_sessions()

                return {
                    'success': True,
                    'msg': f'Closed {count} expired sessions',
                    'data': {
                        'closed_count': count
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
