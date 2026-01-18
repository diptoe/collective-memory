"""
Collective Memory Platform - Flask Application Factory

Following Jai API patterns for Flask app initialization.
"""
import logging
import traceback

from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api

from api import config
from api.models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('api')


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Following Jai pattern:
    1. Create Flask instance
    2. Load configuration
    3. Initialize extensions (db, CORS)
    4. Initialize Flask-RestX API
    5. Register routes
    6. Run migrations if enabled
    """
    # Create Flask instance
    app = Flask(__name__)

    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config.SQLALCHEMY_ENGINE_OPTIONS
    app.config['DEBUG'] = config.DEBUG

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "supports_credentials": True,
    }})

    # Global exception handler for unhandled errors
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log full traceback for all unhandled exceptions."""
        # Get request details for context
        method = request.method
        path = request.path
        remote_addr = request.remote_addr

        # Log the full traceback
        logger.error(
            f"Unhandled exception on {method} {path} from {remote_addr}:\n"
            f"Exception: {type(e).__name__}: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # Return a generic error response
        return {
            'success': False,
            'msg': f'Internal server error: {str(e)}',
            'error_type': type(e).__name__
        }, 500

    # Initialize Flask-RestX API with Swagger UI
    api = Api(
        app,
        version='1.0',
        title='Collective Memory API',
        description='Knowledge graph and multi-agent collaboration platform',
        doc='/api/docs',
        prefix='/api'
    )

    # Flask-RestX error handler
    @api.errorhandler(Exception)
    def api_error_handler(e):
        """Log errors caught by Flask-RestX."""
        method = request.method
        path = request.path
        remote_addr = request.remote_addr

        logger.error(
            f"API exception on {method} {path} from {remote_addr}:\n"
            f"Exception: {type(e).__name__}: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        return {
            'success': False,
            'msg': f'Internal server error: {str(e)}',
            'error_type': type(e).__name__
        }, 500

    # Register routes
    from api.routes import register_routes
    register_routes(api)

    # Create database tables on first request
    with app.app_context():
        db.create_all()

        # Run migrations
        from api.migrations import run_migrations
        run_migrations()

        # Seed default models and personas (creates any missing defaults)
        from api.services.seeding import seed_all
        seed_all()

        # Ensure default domain exists and migrate existing data
        from api.models.domain import ensure_default_domain
        ensure_default_domain()

    return app
