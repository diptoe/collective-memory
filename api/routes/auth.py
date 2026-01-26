"""
Collective Memory Platform - Auth Routes

User authentication endpoints: register, login, logout, session management.
"""
from flask import request, make_response, g, jsonify
from flask_restx import Api, Resource, Namespace, fields

from api.models import User, Session, Domain
from api.services.auth import (
    hash_password, verify_password, is_admin_email,
    set_session_cookie, clear_session_cookie,
    require_auth_strict, require_admin, get_user_from_request
)
from api.services.activity import activity_service
from api.services.scope import scope_service


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


def register_auth_routes(api: Api):
    """Register auth routes with the API."""

    ns = api.namespace(
        'auth',
        description='User authentication',
        path='/auth'
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
        'created_at': fields.DateTime(readonly=True),
    })

    register_model = ns.model('RegisterRequest', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password'),
        'first_name': fields.String(required=True, description='First name'),
        'last_name': fields.String(required=True, description='Last name'),
    })

    login_model = ns.model('LoginRequest', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password'),
        'remember_me': fields.Boolean(description='Remember me for 30 days', default=False),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('/register')
    class Register(Resource):
        @ns.doc('register_user')
        @ns.expect(register_model)
        def post(self):
            """Register a new user account."""
            data = request.json or {}

            # Validate required fields
            if not data.get('email'):
                return {'success': False, 'msg': 'email is required'}, 400
            if not data.get('password'):
                return {'success': False, 'msg': 'password is required'}, 400
            if not data.get('first_name'):
                return {'success': False, 'msg': 'first_name is required'}, 400
            if not data.get('last_name'):
                return {'success': False, 'msg': 'last_name is required'}, 400

            # Validate password strength
            if len(data['password']) < 8:
                return {'success': False, 'msg': 'Password must be at least 8 characters'}, 400

            email = data['email'].lower().strip()

            # Check if email already exists
            if User.get_by_email(email):
                return {'success': False, 'msg': 'Email already registered'}, 409

            try:
                # Determine role based on admin email config
                role = 'admin' if is_admin_email(email) else 'user'

                # Get or create domain based on email (returns None for generic emails)
                domain = Domain.get_or_create_for_email(email)

                # Create user
                user = User(
                    email=email,
                    password_hash=hash_password(data['password']),
                    first_name=data['first_name'].strip(),
                    last_name=data['last_name'].strip(),
                    role=role,
                    status='active',
                    domain_key=domain.domain_key if domain else None,
                )
                user.save()

                # Create session
                session = Session.create_for_user(
                    user_key=user.user_key,
                    remember_me=False,
                    user_agent=request.headers.get('User-Agent'),
                    ip_address=request.remote_addr,
                )

                # Update last login
                user.update_last_login()

                # Ensure user has a linked Person entity in the knowledge graph
                user.ensure_person_entity()

                # Record activity
                activity_service.record_create(
                    actor=user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes={'email': email, 'role': role},
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                # Build response with cookie
                response_data = {
                    'success': True,
                    'msg': 'User registered successfully',
                    'data': {
                        'user': user.to_dict(include_pat=True),
                        'session_expires_at': session.expires_at.isoformat(),
                    }
                }
                response = make_response(jsonify(response_data), 201)
                set_session_cookie(response, session)

                return response

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/login')
    class Login(Resource):
        @ns.doc('login_user')
        @ns.expect(login_model)
        def post(self):
            """Login with email and password."""
            data = request.json or {}

            if not data.get('email'):
                return {'success': False, 'msg': 'email is required'}, 400
            if not data.get('password'):
                return {'success': False, 'msg': 'password is required'}, 400

            email = data['email'].lower().strip()
            remember_me = data.get('remember_me', False)

            # Find user
            user = User.get_by_email(email)
            if not user:
                return {'success': False, 'msg': 'Invalid email or password'}, 401

            # Check status
            if not user.is_active:
                return {'success': False, 'msg': 'Account is suspended'}, 401

            # Verify password
            if not verify_password(data['password'], user.password_hash):
                return {'success': False, 'msg': 'Invalid email or password'}, 401

            try:
                # Check if there's already a valid session cookie for this user
                session_token = request.cookies.get('cm_session')
                existing_session = None
                if session_token:
                    existing_session = Session.get_by_token(session_token)
                    # Only reuse if it belongs to the same user
                    if existing_session and existing_session.user_key == user.user_key:
                        # Extend the existing session instead of creating a new one
                        existing_session.extend()
                        session = existing_session
                    else:
                        # Different user or invalid session - revoke and create new
                        if existing_session:
                            existing_session.revoke()
                        existing_session = None

                if not existing_session:
                    # Create new session
                    session = Session.create_for_user(
                        user_key=user.user_key,
                        remember_me=remember_me,
                        user_agent=request.headers.get('User-Agent'),
                        ip_address=request.remote_addr,
                    )

                # Update last login
                user.update_last_login()

                # Ensure user has a linked Person entity in the knowledge graph
                user.ensure_person_entity()

                # Record activity
                activity_service.record_read(
                    actor=user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    query='login',
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                # Build response with cookie
                response_data = {
                    'success': True,
                    'msg': 'Login successful',
                    'data': {
                        'user': user.to_dict(include_pat=True),
                        'session_expires_at': session.expires_at.isoformat(),
                    }
                }
                response = make_response(jsonify(response_data))
                set_session_cookie(response, session)

                return response

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/logout')
    class Logout(Resource):
        @ns.doc('logout_user')
        def post(self):
            """Logout and destroy session."""
            user, session = get_user_from_request()

            if session:
                try:
                    session.revoke()
                except Exception:
                    pass  # Session may already be deleted

            response_data = {
                'success': True,
                'msg': 'Logged out successfully',
            }
            response = make_response(jsonify(response_data))
            clear_session_cookie(response)

            return response

    @ns.route('/guest')
    class GuestLogin(Resource):
        @ns.doc('guest_login')
        def post(self):
            """Login as guest user for demo access (view-only)."""
            GUEST_EMAIL = 'guest@diptoe.ai'

            guest = User.get_by_email(GUEST_EMAIL)
            if not guest or not guest.is_active:
                return {'success': False, 'msg': 'Guest access not available'}, 404

            try:
                session = Session.create_for_user(
                    user_key=guest.user_key,
                    remember_me=False,
                    user_agent=request.headers.get('User-Agent'),
                    ip_address=request.remote_addr,
                )

                response_data = {
                    'success': True,
                    'msg': 'Guest login successful',
                    'data': {
                        'user': guest.to_dict(),
                        'is_guest': True,
                    }
                }
                response = make_response(jsonify(response_data))
                set_session_cookie(response, session)

                return response

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/me')
    class CurrentUser(Resource):
        @ns.doc('get_current_user')
        @ns.marshal_with(response_model)
        def get(self):
            """Get current authenticated user with teams and scopes."""
            user, session = get_user_from_request()

            if not user:
                return {'success': False, 'msg': 'Not authenticated'}, 401

            # Get user's teams with membership info
            teams_data = []
            for team in user.get_teams():
                membership = user.get_team_memberships()
                team_membership = next(
                    (m for m in membership if m.team_key == team.team_key),
                    None
                )
                teams_data.append({
                    'team_key': team.team_key,
                    'name': team.name,
                    'slug': team.slug,
                    'description': team.description,
                    'role': team_membership.role if team_membership else 'member',
                    'membership_slug': team_membership.slug if team_membership else None,
                })

            # Get available scopes and default scope
            available_scopes = scope_service.get_user_accessible_scopes(user)
            default_scope = scope_service.get_default_scope(user)

            return {
                'success': True,
                'msg': 'User retrieved',
                'data': {
                    'user': user.to_dict(include_pat=True, include_domain=True),
                    'session': session.to_dict() if session else None,
                    'teams': teams_data,
                    'available_scopes': available_scopes,
                    'default_scope': default_scope,
                }
            }

    @ns.route('/pat/regenerate')
    class RegeneratePAT(Resource):
        @ns.doc('regenerate_pat')
        @require_auth_strict
        def post(self):
            """Regenerate Personal Access Token."""
            user = g.current_user

            try:
                new_pat = user.regenerate_pat()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes={'pat': 'regenerated'},
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'PAT regenerated successfully',
                    'data': {
                        'pat': new_pat,
                        'pat_created_at': user.pat_created_at.isoformat(),
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    profile_model = ns.model('ProfileUpdateRequest', {
        'first_name': fields.String(description='First name'),
        'last_name': fields.String(description='Last name'),
    })

    password_model = ns.model('PasswordChangeRequest', {
        'current_password': fields.String(required=True, description='Current password'),
        'new_password': fields.String(required=True, description='New password'),
    })

    @ns.route('/profile')
    class Profile(Resource):
        @ns.doc('update_profile')
        @ns.expect(profile_model)
        @require_auth_strict
        def put(self):
            """Update user profile (name)."""
            user = g.current_user
            data = request.json or {}

            changes = {}

            if 'first_name' in data:
                first_name = data['first_name'].strip() if data['first_name'] else ''
                if first_name:
                    user.first_name = first_name
                    changes['first_name'] = first_name

            if 'last_name' in data:
                last_name = data['last_name'].strip() if data['last_name'] else ''
                if last_name:
                    user.last_name = last_name
                    changes['last_name'] = last_name

            if not changes:
                return {'success': False, 'msg': 'No valid changes provided'}, 400

            try:
                user.save()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes=changes,
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Profile updated successfully',
                    'data': {
                        'user': user.to_dict(include_pat=True)
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/password')
    class PasswordChange(Resource):
        @ns.doc('change_password')
        @ns.expect(password_model)
        @require_auth_strict
        def put(self):
            """Change user password."""
            user = g.current_user
            data = request.json or {}

            if not data.get('current_password'):
                return {'success': False, 'msg': 'current_password is required'}, 400
            if not data.get('new_password'):
                return {'success': False, 'msg': 'new_password is required'}, 400

            # Verify current password
            if not verify_password(data['current_password'], user.password_hash):
                return {'success': False, 'msg': 'Current password is incorrect'}, 401

            # Validate new password strength
            if len(data['new_password']) < 8:
                return {'success': False, 'msg': 'New password must be at least 8 characters'}, 400

            try:
                user.password_hash = hash_password(data['new_password'])
                user.save()

                # Record activity
                activity_service.record_update(
                    actor=user.user_key,
                    entity_type='User',
                    entity_key=user.user_key,
                    entity_name=user.display_name,
                    changes={'password': 'changed'},
                    domain_key=user.domain_key,
                    user_key=user.user_key
                )

                return {
                    'success': True,
                    'msg': 'Password changed successfully',
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/sessions')
    class SessionList(Resource):
        @ns.doc('list_sessions')
        @require_auth_strict
        @ns.marshal_with(response_model)
        def get(self):
            """List all active sessions for current user."""
            user = g.current_user
            current_session = g.current_session

            sessions = Session.get_user_sessions(user.user_key)

            # Mark current session
            session_list = []
            for s in sessions:
                session_dict = s.to_dict()
                if current_session and s.session_key == current_session.session_key:
                    session_dict['is_current'] = True
                session_list.append(session_dict)

            return {
                'success': True,
                'msg': f'Found {len(sessions)} active sessions',
                'data': {
                    'sessions': session_list
                }
            }

    @ns.route('/sessions/<string:session_key>')
    @ns.param('session_key', 'Session identifier')
    class SessionDetail(Resource):
        @ns.doc('revoke_session')
        @require_auth_strict
        def delete(self, session_key):
            """Revoke a specific session."""
            user = g.current_user
            current_session = g.current_session

            # Find session
            session = Session.get_by_key(session_key)
            if not session:
                return {'success': False, 'msg': 'Session not found'}, 404

            # Verify ownership
            if session.user_key != user.user_key:
                return {'success': False, 'msg': 'Session not found'}, 404

            try:
                is_current = current_session and session.session_key == current_session.session_key
                session.revoke()

                response_data = {
                    'success': True,
                    'msg': 'Session revoked',
                    'data': {'was_current': is_current}
                }

                # If revoking current session, clear cookie
                if is_current:
                    response = make_response(jsonify(response_data))
                    clear_session_cookie(response)
                    return response

                return response_data

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/sessions/all')
    class RevokeAllSessions(Resource):
        @ns.doc('revoke_all_sessions')
        @require_auth_strict
        def delete(self):
            """Revoke all sessions for current user (logout everywhere)."""
            user = g.current_user

            try:
                count = Session.revoke_all_for_user(user.user_key)

                response_data = {
                    'success': True,
                    'msg': f'Revoked {count} sessions',
                    'data': {'revoked_count': count}
                }
                response = make_response(jsonify(response_data))
                clear_session_cookie(response)

                return response

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    # ===================
    # Admin Routes
    # ===================

    @ns.route('/admin/sessions')
    class AdminSessionList(Resource):
        @ns.doc('admin_list_sessions')
        @require_admin
        @ns.param('include_expired', 'Include expired sessions', type=bool, default=False)
        @ns.param('limit', 'Maximum sessions to return', type=int, default=100)
        @ns.marshal_with(response_model)
        def get(self):
            """[Admin] List all sessions with user and agent details."""
            include_expired = request.args.get('include_expired', 'false').lower() == 'true'
            limit = request.args.get('limit', 100, type=int)

            sessions = Session.get_all_sessions(include_expired=include_expired, limit=limit)

            session_list = []
            for s in sessions:
                session_list.append(s.to_dict(include_user=True, include_agent=True))

            return {
                'success': True,
                'msg': f'Found {len(sessions)} sessions',
                'data': {
                    'sessions': session_list
                }
            }

    @ns.route('/admin/sessions/<string:session_key>')
    @ns.param('session_key', 'Session identifier')
    class AdminSessionDetail(Resource):
        @ns.doc('admin_revoke_session')
        @require_admin
        def delete(self, session_key):
            """[Admin] Revoke any session."""
            session = Session.get_by_key(session_key)
            if not session:
                return {'success': False, 'msg': 'Session not found'}, 404

            try:
                # Get user info before deletion
                user_key = session.user_key
                session.revoke()

                # Record activity
                activity_service.record_delete(
                    actor=g.current_user.user_key,
                    entity_type='Session',
                    entity_key=session_key,
                    entity_name=f'Session for user {user_key}',
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                return {
                    'success': True,
                    'msg': 'Session revoked',
                    'data': {'user_key': user_key}
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/admin/sessions/cleanup')
    class AdminSessionCleanup(Resource):
        @ns.doc('admin_cleanup_sessions')
        @require_admin
        def post(self):
            """[Admin] Delete all expired sessions."""
            try:
                count = Session.cleanup_expired()

                return {
                    'success': True,
                    'msg': f'Cleaned up {count} expired sessions',
                    'data': {'deleted_count': count}
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    # ===================
    # Guest Settings
    # ===================

    @ns.route('/guest/settings')
    class GuestSettings(Resource):
        GUEST_EMAIL = 'guest@diptoe.ai'

        @ns.doc('get_guest_settings')
        @require_admin
        def get(self):
            """[Admin] Get guest access settings."""
            guest = User.get_by_email(self.GUEST_EMAIL)

            if not guest:
                return {
                    'success': True,
                    'msg': 'Guest user not configured',
                    'data': {
                        'exists': False,
                        'enabled': False,
                        'email': self.GUEST_EMAIL,
                    }
                }

            return {
                'success': True,
                'msg': 'Guest settings retrieved',
                'data': {
                    'exists': True,
                    'enabled': guest.is_active,
                    'email': guest.email,
                    'user_key': guest.user_key,
                    'created_at': guest.created_at.isoformat() if guest.created_at else None,
                }
            }

        @ns.doc('update_guest_settings')
        @require_admin
        def put(self):
            """[Admin] Enable or disable guest access."""
            data = request.json or {}
            enabled = data.get('enabled')

            if enabled is None:
                return {'success': False, 'msg': 'enabled field is required'}, 400

            guest = User.get_by_email(self.GUEST_EMAIL)

            if not guest:
                if enabled:
                    # Create guest user if enabling and doesn't exist
                    from api.services.seeding import seed_guest_user
                    result = seed_guest_user()
                    if result.get('status') == 'error':
                        return {'success': False, 'msg': result.get('msg', 'Failed to create guest user')}, 500
                    return {
                        'success': True,
                        'msg': 'Guest access enabled',
                        'data': {'enabled': True, 'user_key': result.get('user_key')}
                    }
                else:
                    return {
                        'success': True,
                        'msg': 'Guest user does not exist',
                        'data': {'enabled': False}
                    }

            # Toggle guest user status
            guest.status = 'active' if enabled else 'inactive'
            guest.save()

            # Record activity
            activity_service.record_update(
                actor=g.current_user.user_key,
                entity_type='User',
                entity_key=guest.user_key,
                entity_name='Guest User',
                changes={'status': guest.status, 'guest_access': 'enabled' if enabled else 'disabled'},
                domain_key=get_user_domain_key(),
                user_key=get_user_key()
            )

            return {
                'success': True,
                'msg': f'Guest access {"enabled" if enabled else "disabled"}',
                'data': {'enabled': enabled, 'user_key': guest.user_key}
            }
