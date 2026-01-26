"""
Collective Memory Platform - Auth Service

Authentication service for session management, password hashing, and decorators.
"""
import bcrypt
from functools import wraps
from flask import request, g, current_app

from api.models.base import db


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def get_user_from_request():
    """
    Extract and validate user from request.

    Checks in order:
    1. Session cookie (cm_session) - for web UI
    2. Authorization header with Bearer token - for PAT/API access

    Returns:
        tuple: (User | None, Session | None)
    """
    # Import here to avoid circular imports
    from api.models import User, Session

    # 1. Check session cookie (web UI)
    session_token = request.cookies.get('cm_session')
    if session_token:
        session = Session.get_by_token(session_token)
        if session:
            user = User.get_by_key(session.user_key)
            if user and user.is_active:
                # Touch session to update last activity
                session.touch()
                return user, session

    # 2. Check Authorization header with PAT (MCP/API)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        pat = auth_header[7:]
        user = User.get_by_pat(pat)
        if user:
            return user, None

    return None, None


def get_current_user():
    """
    Get the current authenticated user.

    Returns:
        User | None: The authenticated user or None
    """
    if hasattr(g, 'current_user'):
        return g.current_user

    user, session = get_user_from_request()
    g.current_user = user
    g.current_session = session
    return user


def is_auth_required() -> bool:
    """Check if authentication is required based on config."""
    from api import config
    return getattr(config, 'CM_REQUIRE_AUTH', False)


def require_auth(f):
    """
    Decorator to require authentication.

    If CM_REQUIRE_AUTH is False, allows anonymous access.
    Sets g.current_user and g.current_session if authenticated.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user, session = get_user_from_request()
        g.current_user = user
        g.current_session = session

        # Check if auth is required
        if is_auth_required() and not user:
            return {'success': False, 'msg': 'Authentication required'}, 401

        return f(*args, **kwargs)

    return decorated


def require_auth_strict(f):
    """
    Decorator to strictly require authentication (ignores CM_REQUIRE_AUTH).

    Always requires a valid session or PAT.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user, session = get_user_from_request()

        if not user:
            return {'success': False, 'msg': 'Authentication required'}, 401

        g.current_user = user
        g.current_session = session
        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """
    Decorator to require admin role.

    Implies require_auth_strict.
    """
    @wraps(f)
    @require_auth_strict
    def decorated(*args, **kwargs):
        if not g.current_user.is_admin:
            return {'success': False, 'msg': 'Admin access required'}, 403
        return f(*args, **kwargs)

    return decorated


def require_domain_admin(f):
    """
    Decorator to require domain_admin or admin role.

    Use this for operations that should be restricted to domain administrators,
    such as managing teams within a domain.

    Implies require_auth_strict.
    """
    @wraps(f)
    @require_auth_strict
    def decorated(*args, **kwargs):
        if not g.current_user.is_domain_admin:
            return {'success': False, 'msg': 'Domain admin access required'}, 403
        return f(*args, **kwargs)

    return decorated


def require_write_access(f):
    """
    Decorator to require write access (non-guest users).

    Blocks guest users from performing write operations.
    Use this for POST/PUT/DELETE operations that modify data.

    Implies require_auth_strict.
    """
    @wraps(f)
    @require_auth_strict
    def decorated(*args, **kwargs):
        if g.current_user.is_guest:
            return {
                'success': False,
                'msg': 'Guest users have view-only access. Create an account to make changes.'
            }, 403
        return f(*args, **kwargs)

    return decorated


def set_session_cookie(response, session, secure: bool = None):
    """
    Set session cookie on response.

    Args:
        response: Flask response object
        session: Session model instance
        secure: Force secure flag (defaults to checking request scheme)
    """
    is_https = request.scheme == 'https'

    if secure is None:
        secure = is_https

    # Use SameSite=Lax for both dev and prod
    # localhost:3000 -> localhost:5001 is same-site (same registrable domain)
    # SameSite=Lax allows cookies on same-site requests and top-level navigations
    response.set_cookie(
        'cm_session',
        session.token,
        httponly=True,
        secure=secure,
        samesite='Lax',
        expires=session.expires_at,
        path='/'
    )


def clear_session_cookie(response):
    """Clear session cookie from response."""
    response.delete_cookie('cm_session', path='/')


def get_admin_email() -> str | None:
    """Get the configured admin email from environment."""
    from api import config
    return getattr(config, 'CM_ADMIN_EMAIL', None)


def is_admin_email(email: str) -> bool:
    """Check if email matches the configured admin email."""
    admin_email = get_admin_email()
    if not admin_email:
        return False
    return email.lower() == admin_email.lower()


# Singleton-like auth service for convenience
class AuthService:
    """Auth service with helper methods."""

    @staticmethod
    def hash_password(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return verify_password(password, password_hash)

    @staticmethod
    def get_user_from_request():
        return get_user_from_request()

    @staticmethod
    def get_current_user():
        return get_current_user()

    @staticmethod
    def is_admin_email(email: str) -> bool:
        return is_admin_email(email)

    @staticmethod
    def set_session_cookie(response, session, secure: bool = None):
        return set_session_cookie(response, session, secure)

    @staticmethod
    def clear_session_cookie(response):
        return clear_session_cookie(response)


auth_service = AuthService()
