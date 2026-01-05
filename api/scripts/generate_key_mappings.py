#!/usr/bin/env python3
"""
Generate Key Mappings (Step 1 of migration)
============================================

This script creates Key records mapping existing UUIDs to new readable keys,
WITHOUT modifying the source tables.

After running this, inspect the keys table to verify the mappings look correct.
Then run migrate_to_readable_keys.py to apply the changes.

Usage:
    python -m api.scripts.generate_key_mappings
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from api import config
from api.models import db, Key
from api.models import Entity, Relationship, Document, Message, Agent, Persona, Conversation, ChatMessage
from api.utils.readable_keys import generate_readable_key, is_uuid, is_readable_key


def create_app():
    """Create Flask app for migration context."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def get_existing_keys() -> set:
    """Get all existing four_words keys."""
    return {k.four_words for k in Key.query.all()}


def get_existing_uuids() -> set:
    """Get all UUIDs already in keys table."""
    return {k.uuid for k in Key.query.all()}


def generate_mappings():
    """Generate Key mappings for all UUID keys without modifying source tables."""

    print("=" * 60)
    print("Generate Key Mappings (Step 1)")
    print("=" * 60)
    print()

    # Get existing keys to avoid collisions
    existing_keys = get_existing_keys()
    existing_uuids = get_existing_uuids()
    print(f"Existing readable keys: {len(existing_keys)}")
    print(f"Existing UUID mappings: {len(existing_uuids)}")
    print()

    # Tables and their key columns
    tables = [
        (Entity, 'entity_key'),
        (Relationship, 'relationship_key'),
        (Document, 'document_key'),
        (Message, 'message_key'),
        (Agent, 'agent_key'),
        (Persona, 'persona_key'),
        (Conversation, 'conversation_key'),
        (ChatMessage, 'message_key'),
    ]

    total_created = 0
    total_skipped = 0

    for model_class, key_column in tables:
        table_name = model_class.__tablename__
        print(f"Processing {table_name}.{key_column}...")

        created = 0
        skipped = 0

        for record in model_class.query.all():
            uuid_key = getattr(record, key_column)

            # Skip if not a UUID
            if not is_uuid(uuid_key):
                skipped += 1
                continue

            # Skip if already mapped
            if uuid_key in existing_uuids:
                skipped += 1
                continue

            # Generate new readable key
            new_key = generate_readable_key(existing_keys)
            existing_keys.add(new_key)
            existing_uuids.add(uuid_key)

            # Create Key record
            key_record = Key(
                four_words=new_key,
                uuid=uuid_key
            )
            db.session.add(key_record)
            created += 1

            print(f"  {uuid_key} -> {new_key}")

        print(f"  Created: {created}, Skipped: {skipped}")
        print()

        total_created += created
        total_skipped += skipped

    # Commit all Key records
    db.session.commit()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total mappings created: {total_created}")
    print(f"Total skipped: {total_skipped}")
    print()
    print("Now inspect the 'keys' table to verify the mappings.")
    print("Then run: python -m api.scripts.apply_key_mappings")


def main():
    app = create_app()
    with app.app_context():
        # Create keys table if needed
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'keys' not in inspector.get_table_names():
            print("Creating keys table...")
            Key.__table__.create(db.engine, checkfirst=True)

        generate_mappings()


if __name__ == '__main__':
    main()
