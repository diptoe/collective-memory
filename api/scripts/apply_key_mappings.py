#!/usr/bin/env python3
"""
Apply Key Mappings (Step 2 of migration)
=========================================

This script applies the Key mappings created by generate_key_mappings.py
to the actual source tables.

Prerequisites:
    1. Run generate_key_mappings.py first
    2. Review the 'keys' table to verify mappings look correct
    3. Then run this script to apply the changes

Usage:
    python -m api.scripts.apply_key_mappings [--dry-run]

Options:
    --dry-run   Show what would be changed without making changes
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from api import config
from api.models import db, Key
from api.models import Entity, Relationship, Document, Message, Agent, Persona, Conversation, ChatMessage
from api.utils.readable_keys import is_uuid


def create_app():
    """Create Flask app for migration context."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def get_key_mappings() -> dict:
    """Get all UUID -> four_words mappings."""
    return {k.uuid: k.four_words for k in Key.query.all()}


def apply_mappings(dry_run: bool = False):
    """Apply Key mappings to source tables."""

    print("=" * 60)
    print("Apply Key Mappings (Step 2)")
    print("=" * 60)
    if dry_run:
        print("DRY RUN - No changes will be made")
    print()

    # Get all mappings
    mappings = get_key_mappings()
    print(f"Loaded {len(mappings)} key mappings")
    print()

    if not mappings:
        print("No mappings found! Run generate_key_mappings.py first.")
        return

    # Use raw SQL to bypass foreign key constraints
    # Order matters: update in a way that avoids FK violations

    if not dry_run:
        # Disable autoflush to control when changes are sent to DB
        db.session.autoflush = False

        # Use raw SQL to update tables in correct order
        from sqlalchemy import text

        # Disable all FK constraint checking (requires superuser)
        print("Disabling foreign key constraint checking...")
        db.session.execute(text("SET session_replication_role = 'replica'"))

    # Tables and their key columns (entities first, then referencing tables)
    tables = [
        (Entity, 'entity_key'),
        (Document, 'document_key'),
        (Message, 'message_key'),
        (Agent, 'agent_key'),
        (Persona, 'persona_key'),
        (Conversation, 'conversation_key'),
        (ChatMessage, 'message_key'),
    ]

    total_updated = 0
    total_skipped = 0

    # Step 1: Update all primary keys using raw SQL
    print("Step 1: Updating primary keys...")
    for model_class, key_column in tables:
        table_name = model_class.__tablename__
        print(f"  {table_name}.{key_column}...")

        updated = 0
        for old_key, new_key in mappings.items():
            if not dry_run:
                from sqlalchemy import text
                result = db.session.execute(
                    text(f"UPDATE {table_name} SET {key_column} = :new_key WHERE {key_column} = :old_key"),
                    {"new_key": new_key, "old_key": old_key}
                )
                if result.rowcount > 0:
                    print(f"    {old_key[:8]}... -> {new_key}")
                    updated += result.rowcount
            else:
                # Dry run - just count
                record = model_class.query.filter_by(**{key_column: old_key}).first()
                if record:
                    print(f"    {old_key[:8]}... -> {new_key}")
                    updated += 1

        total_updated += updated
        print(f"    Updated: {updated}")
    print()

    # Step 2: Update relationship primary keys
    print("Step 2: Updating relationship primary keys...")
    rel_updated = 0
    for old_key, new_key in mappings.items():
        if not dry_run:
            from sqlalchemy import text
            result = db.session.execute(
                text("UPDATE relationships SET relationship_key = :new_key WHERE relationship_key = :old_key"),
                {"new_key": new_key, "old_key": old_key}
            )
            if result.rowcount > 0:
                print(f"  {old_key[:8]}... -> {new_key}")
                rel_updated += result.rowcount
        else:
            rel = Relationship.query.filter_by(relationship_key=old_key).first()
            if rel:
                print(f"  {old_key[:8]}... -> {new_key}")
                rel_updated += 1
    print(f"  Updated: {rel_updated}")
    total_updated += rel_updated
    print()

    # Step 3: Update relationship foreign key references
    print("Step 3: Updating relationship references (from_entity_key, to_entity_key)...")
    ref_updated = 0
    for old_key, new_key in mappings.items():
        if not dry_run:
            from sqlalchemy import text
            # Update from_entity_key
            result1 = db.session.execute(
                text("UPDATE relationships SET from_entity_key = :new_key WHERE from_entity_key = :old_key"),
                {"new_key": new_key, "old_key": old_key}
            )
            # Update to_entity_key
            result2 = db.session.execute(
                text("UPDATE relationships SET to_entity_key = :new_key WHERE to_entity_key = :old_key"),
                {"new_key": new_key, "old_key": old_key}
            )
            count = result1.rowcount + result2.rowcount
            if count > 0:
                ref_updated += count
        else:
            # Dry run
            rels = Relationship.query.filter(
                (Relationship.from_entity_key == old_key) | (Relationship.to_entity_key == old_key)
            ).all()
            ref_updated += len(rels)
    print(f"  Updated: {ref_updated}")
    print()

    # Re-enable constraints and commit all changes
    if not dry_run:
        from sqlalchemy import text
        print("Re-enabling foreign key constraint checking...")
        db.session.execute(text("SET session_replication_role = 'origin'"))
        db.session.commit()
        print("Changes committed successfully!")

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total keys updated: {total_updated}")
    print(f"Relationship references updated: {ref_updated}")
    print()

    if dry_run:
        print("This was a dry run. Run without --dry-run to apply changes.")
    else:
        print("Migration complete! All UUIDs have been replaced with readable keys.")


def main():
    parser = argparse.ArgumentParser(
        description='Apply key mappings to source tables'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        apply_mappings(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
