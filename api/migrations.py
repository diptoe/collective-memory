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
