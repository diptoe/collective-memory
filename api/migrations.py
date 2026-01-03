"""
Collective Memory Platform - Migrations

Auto-discovery migration system following Jai API patterns.
"""
import logging
from api.models import db, Entity, Relationship, Message, Agent, Persona, Conversation, ChatMessage
from api import config

logger = logging.getLogger(__name__)


def run_migrations():
    """
    Run database migrations and seed default data.

    Called on application startup.
    """
    logger.info("Running migrations...")

    # Ensure all tables exist
    db.create_all()
    logger.info("Database tables created/verified")

    # Seed default personas if none exist
    seed_default_personas()

    # Seed default user entity if none exist
    seed_default_user()

    logger.info("Migrations complete")


def seed_default_personas():
    """Seed default personas from config if none exist."""
    existing_count = Persona.count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing personas, skipping seed")
        return

    logger.info("Seeding default personas...")

    for persona_data in config.DEFAULT_PERSONAS:
        persona = Persona(
            name=persona_data['name'],
            model=persona_data['model'],
            role=persona_data['role'],
            color=persona_data['color'],
            system_prompt=persona_data['system_prompt'],
            personality=persona_data.get('personality', {}),
            capabilities=persona_data.get('capabilities', []),
            status='active'
        )
        persona.save()
        logger.info(f"Created persona: {persona.name}")


def seed_default_user():
    """Seed the default user entity if it doesn't exist."""
    user = config.DEFAULT_USER

    # Check if user entity exists
    existing = Entity.query.filter_by(
        entity_type='Person',
        name=user['name']
    ).first()

    if existing:
        logger.info(f"Default user entity already exists: {user['name']}")
        return

    logger.info(f"Creating default user entity: {user['name']}")

    entity = Entity(
        entity_key=user['user_key'],
        entity_type='Person',
        name=user['name'],
        properties={
            'email': user['email'],
            'role': 'owner'
        },
        context_domain='system',
        confidence=1.0,
        source='system'
    )
    entity.save()
    logger.info(f"Created user entity: {entity.name}")
