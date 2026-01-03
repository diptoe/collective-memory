"""
Collective Memory Platform - Route Registration

Following Jai API patterns for Flask-RestX route registration.
"""
from flask_restx import Api

from api.routes.entities import register_entity_routes
from api.routes.relationships import register_relationship_routes
from api.routes.messages import register_message_routes
from api.routes.agents import register_agent_routes
from api.routes.personas import register_persona_routes
from api.routes.conversations import register_conversation_routes
from api.routes.context import register_context_routes


def register_routes(api: Api):
    """Register all API routes with the Flask-RestX API."""
    register_entity_routes(api)
    register_relationship_routes(api)
    register_message_routes(api)
    register_agent_routes(api)
    register_persona_routes(api)
    register_conversation_routes(api)
    register_context_routes(api)
