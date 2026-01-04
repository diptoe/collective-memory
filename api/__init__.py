"""
Collective Memory Platform - Flask Application Factory

Following Jai API patterns for Flask app initialization.
"""
from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from api import config
from api.models import db


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

    # Initialize Flask-RestX API with Swagger UI
    api = Api(
        app,
        version='1.0',
        title='Collective Memory API',
        description='Knowledge graph and multi-agent collaboration platform',
        doc='/api/docs',
        prefix='/api'
    )

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

    return app
