"""
Collective Memory Platform - Migrations

Auto-discovery migration system following Jai API patterns.

This module provides backward compatibility with the original simple
migrations interface while delegating to the enhanced MigrationManager.
"""
import logging
from api.migration_manager import (
    run_migrations as _run_migrations,
    migration_manager
)

logger = logging.getLogger(__name__)


def _run_custom_migrations():
    """Run custom migrations that can't be handled by auto-migration."""
    from api.models import db
    from sqlalchemy import text, inspect

    inspector = inspect(db.engine)

    # Migration: Rename message_reads.agent_id to reader_key
    if 'message_reads' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('message_reads')]
        if 'agent_id' in columns and 'reader_key' not in columns:
            logger.info("Migrating message_reads: renaming agent_id to reader_key")
            try:
                db.session.execute(text(
                    'ALTER TABLE message_reads RENAME COLUMN agent_id TO reader_key'
                ))
                # Also update the unique constraint name if it exists
                db.session.execute(text(
                    'ALTER INDEX IF EXISTS uq_message_agent_read RENAME TO uq_message_reader_read'
                ))
                db.session.commit()
                logger.info("Migration complete: message_reads.agent_id -> reader_key")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Migration warning (may already be done): {e}")

    # Migration: Backfill team_memberships.slug with user initials
    if 'team_memberships' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('team_memberships')]
        if 'slug' in columns:
            # Check if any memberships have null slug that should be backfilled
            try:
                result = db.session.execute(text(
                    '''
                    SELECT COUNT(*) FROM team_memberships tm
                    JOIN users u ON tm.user_key = u.user_key
                    WHERE tm.slug IS NULL AND u.initials IS NOT NULL
                    '''
                ))
                null_count = result.scalar()
                if null_count and null_count > 0:
                    logger.info(f"Backfilling {null_count} team_memberships.slug with user initials")
                    db.session.execute(text(
                        '''
                        UPDATE team_memberships tm
                        SET slug = LOWER(u.initials)
                        FROM users u
                        WHERE tm.user_key = u.user_key
                        AND tm.slug IS NULL
                        AND u.initials IS NOT NULL
                        '''
                    ))
                    db.session.commit()
                    logger.info("Migration complete: team_memberships.slug backfilled")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Migration warning (slug backfill): {e}")


def run_migrations(allow_column_removal: bool = False):
    """
    Run database migrations and seed default data.

    Called on application startup.

    Args:
        allow_column_removal: If True, columns in database that are not
                              in the model will be dropped. Default False
                              for safety - use with caution!

    This is the main entry point that wraps the MigrationManager
    for backward compatibility with existing code.
    """
    # Run custom migrations first (column renames, etc.)
    _run_custom_migrations()

    return migration_manager.run_migrations(
        seed_data=True,
        allow_column_removal=allow_column_removal
    )


def get_table_registry():
    """Get all registered tables with their status."""
    return migration_manager.get_table_registry()


def get_table_status(table_name: str):
    """Get status for a specific table."""
    return migration_manager.get_table_status(table_name)


def update_row_counts():
    """Update cached row counts for all registered tables."""
    return migration_manager.update_row_counts()


# Backward compatibility exports
__all__ = [
    'run_migrations',
    'get_table_registry',
    'get_table_status',
    'update_row_counts',
    'migration_manager'
]
