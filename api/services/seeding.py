"""
Collective Memory Platform - Seeding Service

Handles seeding of default clients, models, and personas on startup.
Checks for new entries in config and adds them if they don't exist.
"""
import logging
from typing import List, Dict, Any

from api.models import Model, Persona, Client, db
from api import config

logger = logging.getLogger(__name__)

# Map providers to client keys
PROVIDER_CLIENT_MAP = {
    'anthropic': 'client-claude-code',
    'openai': 'client-codex',
    'google': 'client-gemini-cli',
}

# Map suggested_clients to client keys
CLIENT_TYPE_MAP = {
    'claude-code': 'client-claude-code',
    'claude-desktop': 'client-claude-desktop',
    'codex': 'client-codex',
    'gemini-cli': 'client-gemini-cli',
    'cursor': 'client-cursor',
    'vscode': 'client-vscode',
}


def seed_clients() -> Dict[str, Any]:
    """
    Seed default clients from the Client model.

    Creates clients if they don't exist, and ensures each has a knowledge graph entity.
    Returns summary of actions taken.
    """
    from api.models.client import DEFAULT_CLIENTS

    created = []
    skipped = []
    entities_created = []

    for client_data in DEFAULT_CLIENTS:
        client_key = client_data.get('client_key')
        if not client_key:
            logger.warning(f"Skipping client without client_key: {client_data}")
            continue

        # Check if client already exists
        existing = Client.get_by_key(client_key)
        if existing:
            # Ensure entity exists for existing client
            if not existing.entity_key:
                try:
                    existing.ensure_entity()
                    entities_created.append(client_key)
                    logger.info(f"Created entity for existing client: {client_key}")
                except Exception as e:
                    logger.error(f"Failed to create entity for client {client_key}: {e}")
            skipped.append(client_key)
            continue

        # Create new client
        client = Client(**client_data)
        try:
            client.save()
            # Create knowledge graph entity for the client
            client.ensure_entity()
            created.append(client_key)
            entities_created.append(client_key)
            logger.info(f"Created client: {client.name} with entity")
        except Exception as e:
            logger.error(f"Failed to create client {client_key}: {e}")

    return {
        'created': created,
        'skipped': skipped,
        'entities_created': entities_created,
        'created_count': len(created),
        'skipped_count': len(skipped),
        'entities_count': len(entities_created)
    }


def seed_models() -> Dict[str, Any]:
    """
    Seed default models from config.

    Checks each model in DEFAULT_MODELS and creates it if it doesn't exist.
    Links models to clients based on provider mapping.
    Returns summary of actions taken.
    """
    created = []
    skipped = []
    linked = []

    for model_data in config.DEFAULT_MODELS:
        model_id = model_data.get('model_id')
        if not model_id:
            logger.warning(f"Skipping model without model_id: {model_data}")
            continue

        # Check if model already exists by model_id
        existing = Model.get_by_model_id(model_id)
        if existing:
            # Check if we need to link to a client
            if not existing.client_key:
                provider = model_data.get('provider')
                client_key = PROVIDER_CLIENT_MAP.get(provider)
                if client_key:
                    existing.client_key = client_key
                    existing.save()
                    linked.append(model_id)
                    logger.info(f"Linked model {model_id} to client {client_key}")
            skipped.append(model_id)
            continue

        # Get client_key from provider mapping
        provider = model_data.get('provider')
        client_key = PROVIDER_CLIENT_MAP.get(provider)

        # Create new model
        model = Model(
            name=model_data['name'],
            provider=model_data['provider'],
            model_id=model_id,
            capabilities=model_data.get('capabilities', []),
            context_window=model_data.get('context_window'),
            max_output_tokens=model_data.get('max_output_tokens'),
            description=model_data.get('description'),
            status=model_data.get('status', 'active'),
            client_key=client_key
        )

        try:
            model.save()
            created.append(model_id)
            logger.info(f"Created model: {model_id}" + (f" linked to {client_key}" if client_key else ""))
        except Exception as e:
            logger.error(f"Failed to create model {model_id}: {e}")

    return {
        'created': created,
        'skipped': skipped,
        'linked': linked,
        'created_count': len(created),
        'skipped_count': len(skipped),
        'linked_count': len(linked)
    }


def seed_personas() -> Dict[str, Any]:
    """
    Seed default personas from config.

    Checks each persona in DEFAULT_PERSONAS and creates it if it doesn't exist.
    Links personas to their first suggested client.
    Uses 'role' as the unique identifier.
    Returns summary of actions taken.
    """
    created = []
    skipped = []
    linked = []

    for persona_data in config.DEFAULT_PERSONAS:
        role = persona_data.get('role')
        if not role:
            logger.warning(f"Skipping persona without role: {persona_data}")
            continue

        # Check if persona already exists by role (get_by_role returns a list)
        existing_list = Persona.get_by_role(role)
        if existing_list:
            existing = existing_list[0]  # Role is unique, so take first
            # Check if we need to link to a client
            if not existing.client_key:
                suggested = persona_data.get('suggested_clients', [])
                if suggested:
                    client_type = suggested[0]  # Use first suggested client
                    client_key = CLIENT_TYPE_MAP.get(client_type)
                    if client_key:
                        existing.client_key = client_key
                        existing.save()
                        linked.append(role)
                        logger.info(f"Linked persona {role} to client {client_key}")
            skipped.append(role)
            continue

        # Get client_key from first suggested client
        suggested = persona_data.get('suggested_clients', [])
        client_key = None
        if suggested:
            client_type = suggested[0]
            client_key = CLIENT_TYPE_MAP.get(client_type)

        # Create new persona
        persona = Persona(
            name=persona_data['name'],
            role=role,
            system_prompt=persona_data.get('system_prompt'),
            personality=persona_data.get('personality', {}),
            capabilities=persona_data.get('capabilities', []),
            suggested_clients=persona_data.get('suggested_clients', []),
            color=persona_data.get('color', '#d97757'),
            status='active',
            client_key=client_key
        )

        try:
            persona.save()
            created.append(role)
            logger.info(f"Created persona: {role}" + (f" linked to {client_key}" if client_key else ""))
        except Exception as e:
            logger.error(f"Failed to create persona {role}: {e}")

    return {
        'created': created,
        'skipped': skipped,
        'linked': linked,
        'created_count': len(created),
        'skipped_count': len(skipped),
        'linked_count': len(linked)
    }


def seed_guest_user() -> Dict[str, Any]:
    """
    Seed guest user for demo access.

    Creates a guest user with view-only permissions if it doesn't exist.
    The guest user is added to the collective-memory team as a viewer.
    """
    from api.models import User, Team, TeamMembership, Domain
    from api.services.auth import hash_password

    GUEST_EMAIL = 'guest@diptoe.ai'
    GUEST_DOMAIN = 'diptoe.ai'

    # Check if exists
    existing = User.get_by_email(GUEST_EMAIL)
    if existing:
        logger.info(f"Guest user already exists: {GUEST_EMAIL}")
        return {'status': 'skipped', 'user_key': existing.user_key}

    # Get diptoe.ai domain
    domain = Domain.get_by_slug(GUEST_DOMAIN)
    if not domain:
        logger.warning(f"Domain '{GUEST_DOMAIN}' not found - cannot create guest user")
        return {'status': 'error', 'msg': f'Domain {GUEST_DOMAIN} not found'}

    # Create guest user
    guest = User(
        email=GUEST_EMAIL,
        password_hash=hash_password('guest-demo-2024'),
        first_name='Guest',
        last_name='User',
        role='guest',
        status='active',
        domain_key=domain.domain_key,
    )
    guest.save()

    # Add to collective-memory team as viewer
    team = Team.query.filter_by(slug='collective-memory').first()
    if team:
        membership = TeamMembership(
            team_key=team.team_key,
            user_key=guest.user_key,
            role='viewer',
        )
        membership.save()
        logger.info(f"Guest user created and added to team: {team.slug}")
    else:
        logger.info(f"Guest user created (no collective-memory team found)")

    return {'status': 'created', 'user_key': guest.user_key}


def seed_all() -> Dict[str, Any]:
    """
    Seed all default data (clients, models, personas, and guest user).

    Clients must be seeded first as models and personas reference them.
    Call this on application startup to ensure all defaults exist.
    """
    logger.info("Starting seed process...")

    # Seed clients first (models and personas have FKs to clients)
    clients_result = seed_clients()
    models_result = seed_models()
    personas_result = seed_personas()
    guest_result = seed_guest_user()

    summary = {
        'clients': clients_result,
        'models': models_result,
        'personas': personas_result,
        'guest_user': guest_result,
    }

    total_created = (
        clients_result['created_count'] +
        models_result['created_count'] +
        personas_result['created_count']
    )
    total_skipped = (
        clients_result['skipped_count'] +
        models_result['skipped_count'] +
        personas_result['skipped_count']
    )
    total_linked = (
        models_result.get('linked_count', 0) +
        personas_result.get('linked_count', 0)
    )

    if total_created > 0 or total_linked > 0:
        logger.info(f"Seed complete: {total_created} created, {total_linked} linked, {total_skipped} already existed")
    else:
        logger.info(f"Seed complete: All {total_skipped} items already exist")

    return summary


# Service instance for easy import
class SeedingService:
    """Service class for seeding operations."""

    def seed_clients(self) -> Dict[str, Any]:
        return seed_clients()

    def seed_models(self) -> Dict[str, Any]:
        return seed_models()

    def seed_personas(self) -> Dict[str, Any]:
        return seed_personas()

    def seed_all(self) -> Dict[str, Any]:
        return seed_all()


seeding_service = SeedingService()
