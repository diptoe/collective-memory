"""
Collective Memory Platform - Seeding Service

Handles seeding of default models and personas on startup.
Checks for new entries in config and adds them if they don't exist.
"""
import logging
from typing import List, Dict, Any

from api.models import Model, Persona, db
from api import config

logger = logging.getLogger(__name__)


def seed_models() -> Dict[str, Any]:
    """
    Seed default models from config.

    Checks each model in DEFAULT_MODELS and creates it if it doesn't exist.
    Returns summary of actions taken.
    """
    created = []
    skipped = []

    for model_data in config.DEFAULT_MODELS:
        model_id = model_data.get('model_id')
        if not model_id:
            logger.warning(f"Skipping model without model_id: {model_data}")
            continue

        # Check if model already exists by model_id
        existing = Model.get_by_model_id(model_id)
        if existing:
            skipped.append(model_id)
            continue

        # Create new model
        model = Model(
            name=model_data['name'],
            provider=model_data['provider'],
            model_id=model_id,
            capabilities=model_data.get('capabilities', []),
            context_window=model_data.get('context_window'),
            max_output_tokens=model_data.get('max_output_tokens'),
            description=model_data.get('description'),
            status=model_data.get('status', 'active')
        )

        try:
            model.save()
            created.append(model_id)
            logger.info(f"Created model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to create model {model_id}: {e}")

    return {
        'created': created,
        'skipped': skipped,
        'created_count': len(created),
        'skipped_count': len(skipped)
    }


def seed_personas() -> Dict[str, Any]:
    """
    Seed default personas from config.

    Checks each persona in DEFAULT_PERSONAS and creates it if it doesn't exist.
    Uses 'role' as the unique identifier.
    Returns summary of actions taken.
    """
    created = []
    skipped = []

    for persona_data in config.DEFAULT_PERSONAS:
        role = persona_data.get('role')
        if not role:
            logger.warning(f"Skipping persona without role: {persona_data}")
            continue

        # Check if persona already exists by role
        existing = Persona.get_by_role(role)
        if existing:
            skipped.append(role)
            continue

        # Create new persona
        persona = Persona(
            name=persona_data['name'],
            role=role,
            system_prompt=persona_data.get('system_prompt'),
            personality=persona_data.get('personality', {}),
            capabilities=persona_data.get('capabilities', []),
            suggested_clients=persona_data.get('suggested_clients', []),
            color=persona_data.get('color', '#d97757'),
            status='active'
        )

        try:
            persona.save()
            created.append(role)
            logger.info(f"Created persona: {role}")
        except Exception as e:
            logger.error(f"Failed to create persona {role}: {e}")

    return {
        'created': created,
        'skipped': skipped,
        'created_count': len(created),
        'skipped_count': len(skipped)
    }


def seed_all() -> Dict[str, Any]:
    """
    Seed all default data (models and personas).

    Call this on application startup to ensure all defaults exist.
    """
    logger.info("Starting seed process...")

    models_result = seed_models()
    personas_result = seed_personas()

    summary = {
        'models': models_result,
        'personas': personas_result
    }

    total_created = models_result['created_count'] + personas_result['created_count']
    total_skipped = models_result['skipped_count'] + personas_result['skipped_count']

    if total_created > 0:
        logger.info(f"Seed complete: {total_created} created, {total_skipped} already existed")
    else:
        logger.info(f"Seed complete: All {total_skipped} items already exist")

    return summary


# Service instance for easy import
class SeedingService:
    """Service class for seeding operations."""

    def seed_models(self) -> Dict[str, Any]:
        return seed_models()

    def seed_personas(self) -> Dict[str, Any]:
        return seed_personas()

    def seed_all(self) -> Dict[str, Any]:
        return seed_all()


seeding_service = SeedingService()
