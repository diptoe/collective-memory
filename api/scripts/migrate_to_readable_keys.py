#!/usr/bin/env python3
"""
Migration Script: UUID to Human-Readable Keys
==============================================

This script migrates existing UUID-based keys to human-readable four-word keys.

Tables migrated:
- entities (entity_key)
- relationships (relationship_key, from_entity_key, to_entity_key)
- documents (document_key)
- messages (message_key)
- agents (agent_key)
- personas (persona_key)
- conversations (conversation_key)
- chat_messages (chat_message_key)

The migration:
1. Creates a Key record mapping old UUID -> new four-word key
2. Updates the record with the new key
3. Updates any foreign key references

Usage:
    python -m api.scripts.migrate_to_readable_keys [--dry-run] [--table TABLE]

Options:
    --dry-run       Show what would be changed without making changes
    --table TABLE   Only migrate a specific table
    --limit N       Limit number of records to migrate (for testing)
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from api import config
from api.models import db, Key
from api.utils.readable_keys import generate_readable_key, is_uuid, is_readable_key


def create_app():
    """Create Flask app for migration context."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def get_existing_readable_keys() -> set:
    """Get all existing readable keys to avoid collisions."""
    keys = set()
    for key_record in Key.query.all():
        keys.add(key_record.four_words)
    return keys


def generate_unique_key(existing_keys: set) -> str:
    """Generate a unique readable key."""
    key = generate_readable_key(existing_keys)
    existing_keys.add(key)
    return key


def migrate_table(
    model_class,
    key_column: str,
    existing_keys: set,
    dry_run: bool = False,
    limit: int = None,
    verbose: bool = True
) -> dict:
    """
    Migrate a single table's keys from UUID to readable format.

    Args:
        model_class: SQLAlchemy model class
        key_column: Name of the key column to migrate
        existing_keys: Set of existing readable keys
        dry_run: If True, don't commit changes
        limit: Maximum number of records to migrate
        verbose: Print progress

    Returns:
        Dict with migration stats
    """
    stats = {
        'table': model_class.__tablename__,
        'total': 0,
        'migrated': 0,
        'skipped': 0,
        'errors': []
    }

    query = model_class.query
    if limit:
        query = query.limit(limit)

    records = query.all()
    stats['total'] = len(records)

    for record in records:
        old_key = getattr(record, key_column)

        # Skip if already a readable key
        if is_readable_key(old_key):
            stats['skipped'] += 1
            continue

        # Skip if not a UUID
        if not is_uuid(old_key):
            stats['skipped'] += 1
            if verbose:
                print(f"  Skipping non-UUID key: {old_key[:20]}...")
            continue

        # Generate new readable key
        new_key = generate_unique_key(existing_keys)

        if verbose:
            print(f"  {old_key} -> {new_key}")

        if not dry_run:
            # Create Key mapping record
            key_record = Key(
                four_words=new_key,
                uuid=old_key
            )
            db.session.add(key_record)

            # Update the record
            setattr(record, key_column, new_key)

        stats['migrated'] += 1

    if not dry_run:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            stats['errors'].append(str(e))
            print(f"  ERROR: {e}")

    return stats


def migrate_relationship_references(dry_run: bool = False, verbose: bool = True) -> dict:
    """
    Update relationship foreign key references after entity keys are migrated.

    This updates from_entity_key and to_entity_key in relationships table.
    """
    from api.models import Relationship

    stats = {
        'table': 'relationships (references)',
        'total': 0,
        'migrated': 0,
        'skipped': 0,
        'errors': []
    }

    relationships = Relationship.query.all()
    stats['total'] = len(relationships)

    for rel in relationships:
        updated = False

        # Check from_entity_key
        if is_uuid(rel.from_entity_key):
            key_record = Key.query.filter_by(uuid=rel.from_entity_key).first()
            if key_record:
                if verbose:
                    print(f"  from: {rel.from_entity_key} -> {key_record.four_words}")
                if not dry_run:
                    rel.from_entity_key = key_record.four_words
                updated = True

        # Check to_entity_key
        if is_uuid(rel.to_entity_key):
            key_record = Key.query.filter_by(uuid=rel.to_entity_key).first()
            if key_record:
                if verbose:
                    print(f"  to: {rel.to_entity_key} -> {key_record.four_words}")
                if not dry_run:
                    rel.to_entity_key = key_record.four_words
                updated = True

        if updated:
            stats['migrated'] += 1
        else:
            stats['skipped'] += 1

    if not dry_run:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            stats['errors'].append(str(e))
            print(f"  ERROR: {e}")

    return stats


def run_migration(dry_run: bool = False, table: str = None, limit: int = None):
    """Run the full migration."""
    from api.models import (
        Entity, Relationship, Document, Message,
        Agent, Persona, Conversation, ChatMessage
    )

    print("=" * 60)
    print("UUID to Human-Readable Keys Migration")
    print("=" * 60)
    if dry_run:
        print("DRY RUN - No changes will be made")
    print()

    # Get existing readable keys
    print("Loading existing keys...")
    existing_keys = get_existing_readable_keys()
    print(f"  Found {len(existing_keys)} existing readable keys")
    print()

    # Define tables to migrate
    tables = [
        (Entity, 'entity_key'),
        (Relationship, 'relationship_key'),
        (Document, 'document_key'),
        (Message, 'message_key'),
        (Agent, 'agent_key'),
        (Persona, 'persona_key'),
        (Conversation, 'conversation_key'),
        (ChatMessage, 'message_key'),  # ChatMessage uses message_key, not chat_message_key
    ]

    all_stats = []

    for model_class, key_column in tables:
        table_name = model_class.__tablename__

        # Skip if specific table requested and this isn't it
        if table and table != table_name:
            continue

        print(f"Migrating {table_name}.{key_column}...")
        stats = migrate_table(
            model_class,
            key_column,
            existing_keys,
            dry_run=dry_run,
            limit=limit
        )
        all_stats.append(stats)
        print(f"  Total: {stats['total']}, Migrated: {stats['migrated']}, Skipped: {stats['skipped']}")
        if stats['errors']:
            print(f"  Errors: {stats['errors']}")
        print()

    # Update relationship references (after entities are migrated)
    if not table or table == 'relationships':
        print("Updating relationship references...")
        ref_stats = migrate_relationship_references(dry_run=dry_run)
        all_stats.append(ref_stats)
        print(f"  Total: {ref_stats['total']}, Migrated: {ref_stats['migrated']}, Skipped: {ref_stats['skipped']}")
        print()

    # Summary
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    total_migrated = sum(s['migrated'] for s in all_stats)
    total_skipped = sum(s['skipped'] for s in all_stats)
    total_errors = sum(len(s['errors']) for s in all_stats)
    print(f"Total migrated: {total_migrated}")
    print(f"Total skipped: {total_skipped}")
    print(f"Total errors: {total_errors}")

    if dry_run:
        print()
        print("This was a dry run. Run without --dry-run to apply changes.")

    return all_stats


def main():
    parser = argparse.ArgumentParser(
        description='Migrate UUID keys to human-readable keys'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--table',
        type=str,
        help='Only migrate a specific table'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of records to migrate'
    )

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # Create keys table if it doesn't exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'keys' not in inspector.get_table_names():
            print("Creating keys table...")
            Key.__table__.create(db.engine, checkfirst=True)

        run_migration(
            dry_run=args.dry_run,
            table=args.table,
            limit=args.limit
        )


if __name__ == '__main__':
    main()
