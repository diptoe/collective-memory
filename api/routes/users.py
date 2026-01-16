"""
Collective Memory Platform - Users Admin Routes

Admin-only user management endpoints.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import User, Session, Domain
from api.services.auth import require_admin, hash_password
from api.services.activity import activity_service


def register_user_routes(api: Api):
    """Register user admin routes with the API."""

    ns = api.namespace(
        'users',
        description='User management (admin only)',
        path='/users'
    )

    # Define models for OpenAPI documentation
    user_model = ns.model('User', {
        'user_key': fields.String(readonly=True, description='Unique user identifier'),
        'email': fields.String(description='User email'),
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'display_name': fields.String(readonly=True, description='Display name'),
        'role': fields.String(description='User role: admin, user'),
        'status': fields.String(description='User status: active, suspended'),
        'last_login_at': fields.DateTime(description='Last login timestamp'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    user_update_model = ns.model('UserUpdate', {
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
        'status': fields.String(description='User status: active, suspended'),
    })

    role_change_model = ns.model('RoleChange', {
        'role': fields.String(required=True, description='New role: admin, user'),
    })

    domain_change_model = ns.model('DomainChange', {
        'domain_key': fields.String(description='Domain key to assign (null to unassign)'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class UserList(Resource):
        @ns.doc('list_users')
        @ns.param('role', 'Filter by role')
        @ns.param('status', 'Filter by status')
        @ns.param('limit', 'Limit results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @require_admin
        @ns.marshal_with(response_model)
        def get(self):
            """List all users (admin only)."""
            role = request.args.get('role')
            status = request.args.get('status')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))

            query = User.query

            if role:
                query = query.filter_by(role=role)
            if status:
                query = query.filter_by(status=status)

            total = query.count()
            users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()

            return {
                'success': True,
                'msg': f'Found {len(users)} users',
                'data': {
                    'users': [u.to_dict() for u in users],
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                }
            }

    @ns.route('/<string:user_key>')
    @ns.param('user_key', 'User identifier')
    class UserDetail(Resource):
        @ns.doc('get_user')
        @require_admin
        @ns.marshal_with(response_model)
        def get(self, user_key):
            """Get user details (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            # Get session count
            sessions = Session.get_user_sessions(user.user_key)

            return {
                'success': True,
                'msg': 'User retrieved',
                'data': {
                    'user': user.to_dict(),
                    'session_count': len(sessions),
                }
            }

        @ns.doc('update_user')
        @ns.expect(user_update_model)
        @require_admin
        @ns.marshal_with(response_model)
        def put(self, user_key):
            """Update user details (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            data = request.json or {}
            changes = {}

            # Update allowed fields
            if 'first_name' in data and data['first_name']:
                changes['first_name'] = {'from': user.first_name, 'to': data['first_name']}
                user.first_name = data['first_name'].strip()

            if 'last_name' in data and data['last_name']:
                changes['last_name'] = {'from': user.last_name, 'to': data['last_name']}
                user.last_name = data['last_name'].strip()

            if 'status' in data and data['status'] in ('active', 'suspended'):
                if data['status'] != user.status:
                    changes['status'] = {'from': user.status, 'to': data['status']}
                    user.status = data['status']

                    # If suspending, revoke all sessions
                    if data['status'] == 'suspended':
                        Session.revoke_all_for_user(user.user_key)

            try:
                user.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=g.current_user.user_key,
                        entity_type='User',
                        entity_key=user.user_key,
                        entity_name=user.display_name,
                        changes=changes
                    )

                return {
                    'success': True,
                    'msg': 'User updated',
                    'data': {'user': user.to_dict()}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_user')
        @require_admin
        @ns.marshal_with(response_model)
        def delete(self, user_key):
            """Suspend a user (admin only). Use PUT with status='suspended' for soft delete."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            # Prevent self-suspension
            if user.user_key == g.current_user.user_key:
                return {'success': False, 'msg': 'Cannot suspend yourself'}, 400

            try:
                # Soft delete - suspend the user
                user.suspend()

                # Revoke all sessions
                Session.revoke_all_for_user(user.user_key)

                # Record activity
                activity_service.record_delete(
                    actor=g.current_user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name
                )

                return {
                    'success': True,
                    'msg': 'User suspended',
                    'data': {'user': user.to_dict()}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:user_key>/role')
    @ns.param('user_key', 'User identifier')
    class UserRole(Resource):
        @ns.doc('change_user_role')
        @ns.expect(role_change_model)
        @require_admin
        @ns.marshal_with(response_model)
        def post(self, user_key):
            """Change user role (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            data = request.json or {}
            new_role = data.get('role')

            if new_role not in ('admin', 'user'):
                return {'success': False, 'msg': 'Invalid role. Must be admin or user'}, 400

            # Prevent self-demotion (last admin check)
            if user.user_key == g.current_user.user_key and new_role != 'admin':
                admins = User.get_admins()
                if len(admins) <= 1:
                    return {'success': False, 'msg': 'Cannot remove the last admin'}, 400

            old_role = user.role
            if old_role == new_role:
                return {
                    'success': True,
                    'msg': 'Role unchanged',
                    'data': {'user': user.to_dict()}
                }

            try:
                user.set_role(new_role)

                # Record activity
                activity_service.record_update(
                    actor=g.current_user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes={'role': {'from': old_role, 'to': new_role}}
                )

                return {
                    'success': True,
                    'msg': f'User role changed to {new_role}',
                    'data': {'user': user.to_dict()}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:user_key>/domain')
    @ns.param('user_key', 'User identifier')
    class UserDomain(Resource):
        @ns.doc('change_user_domain')
        @ns.expect(domain_change_model)
        @require_admin
        @ns.marshal_with(response_model)
        def put(self, user_key):
            """Change user domain assignment (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            data = request.json or {}
            new_domain_key = data.get('domain_key')

            # Validate domain if provided
            if new_domain_key:
                domain = Domain.get_by_key(new_domain_key)
                if not domain:
                    return {'success': False, 'msg': 'Domain not found'}, 404
                if domain.status != 'active':
                    return {'success': False, 'msg': 'Cannot assign to suspended domain'}, 400

            old_domain_key = user.domain_key

            if old_domain_key == new_domain_key:
                return {
                    'success': True,
                    'msg': 'Domain unchanged',
                    'data': {'user': user.to_dict()}
                }

            try:
                user.domain_key = new_domain_key
                user.save()

                # Record activity
                activity_service.record_update(
                    actor=g.current_user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes={'domain_key': {'from': old_domain_key, 'to': new_domain_key}}
                )

                return {
                    'success': True,
                    'msg': f'User domain {"assigned" if new_domain_key else "unassigned"}',
                    'data': {'user': user.to_dict()}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:user_key>/sessions')
    @ns.param('user_key', 'User identifier')
    class UserSessions(Resource):
        @ns.doc('list_user_sessions')
        @require_admin
        @ns.marshal_with(response_model)
        def get(self, user_key):
            """List all sessions for a user (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            sessions = Session.get_user_sessions(user.user_key)

            return {
                'success': True,
                'msg': f'Found {len(sessions)} sessions',
                'data': {
                    'sessions': [s.to_dict() for s in sessions]
                }
            }

        @ns.doc('revoke_user_sessions')
        @require_admin
        @ns.marshal_with(response_model)
        def delete(self, user_key):
            """Revoke all sessions for a user (admin only)."""
            user = User.get_by_key(user_key)
            if not user:
                return {'success': False, 'msg': 'User not found'}, 404

            try:
                count = Session.revoke_all_for_user(user.user_key)

                # Record activity
                activity_service.record_delete(
                    actor=g.current_user.user_key,
                    entity_type='Session',
                    entity_key=user.user_key,
                    entity_name=f'{count} sessions for {user.display_name}'
                )

                return {
                    'success': True,
                    'msg': f'Revoked {count} sessions',
                    'data': {'revoked_count': count}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/stats')
    class UserStats(Resource):
        @ns.doc('get_user_stats')
        @require_admin
        @ns.marshal_with(response_model)
        def get(self):
            """Get user statistics (admin only)."""
            total = User.count()
            active = User.query.filter_by(status='active').count()
            suspended = User.query.filter_by(status='suspended').count()
            admins = User.query.filter_by(role='admin', status='active').count()

            return {
                'success': True,
                'msg': 'User stats retrieved',
                'data': {
                    'total': total,
                    'active': active,
                    'suspended': suspended,
                    'admins': admins,
                    'users': active - admins,
                }
            }
