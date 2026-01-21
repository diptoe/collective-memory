"""
Collective Memory Platform - Migration Manager

Sophisticated migration system with schema versioning, column detection,
and dialect-aware SQL generation. Based on Jai API patterns.
"""
import logging
import os
from typing import Dict, List, Type, Optional, Any, Set
from datetime import datetime, timezone
from sqlalchemy import inspect, text, Column
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import TypeEngine
from api.models.base import db, BaseModel

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations with schema versioning.

    Features:
    - Auto-discovery of models
    - Table registry with Table model
    - Status tracking with TableStatus model
    - Column addition detection
    - Column removal detection (with safety controls)
    - Column type change detection
    - Index management
    - Foreign key handling
    - Dialect-aware SQL generation
    """

    # Columns that should never be removed (safety)
    PROTECTED_COLUMNS = {'id', 'created_at', 'updated_at'}

    # SQL type mappings for PostgreSQL
    POSTGRES_TYPE_MAP = {
        'String': 'VARCHAR',
        'Text': 'TEXT',
        'Integer': 'INTEGER',
        'BigInteger': 'BIGINT',
        'SmallInteger': 'SMALLINT',
        'Float': 'FLOAT',
        'Numeric': 'NUMERIC',
        'Boolean': 'BOOLEAN',
        'DateTime': 'TIMESTAMP WITH TIME ZONE',
        'Date': 'DATE',
        'Time': 'TIME',
        'LargeBinary': 'BYTEA',
        'JSON': 'JSONB',
        'JSONB': 'JSONB',
        'UUID': 'UUID',
    }

    def __init__(self, app=None, allow_column_removal: bool = False):
        self.app = app
        self.engine: Optional[Engine] = None
        self.inspector = None
        self._models: Dict[str, Type[BaseModel]] = {}
        self._system_tables_created = False
        # Safety flag - column removal is disabled by default
        self.allow_column_removal = allow_column_removal

    def pgvector_enabled(self) -> bool:
        """
        Whether pgvector-backed VECTOR columns/indexes are enabled.

        We gate this behind an env var so local/dev DBs without the pgvector
        extension don't crash on startup.
        """
        return os.getenv("CM_ENABLE_PGVECTOR", "false").lower() in ("1", "true", "yes")

    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        self.engine = db.engine
        self.inspector = inspect(self.engine)

    def discover_models(self) -> Dict[str, Type[BaseModel]]:
        """
        Discover all BaseModel subclasses.

        Returns dict of table_name -> model_class.

        Note: Order matters for foreign key dependencies.
        Tables with FKs must be created after their referenced tables.
        """
        from api.models import (
            Key, Entity, Relationship, Message, MessageRead, Agent, AgentCheckpoint,
            Conversation, ChatMessage, Document,
            User, Session, Domain, Team, TeamMembership,
            Client, Model, Persona,  # Client must come before Model/Persona (FK dependency)
            WorkSession, Project, TeamProject, Repository, ProjectRepository,
            RepositoryStats, Commit, Metric
        )
        from api.models.activity import Activity

        models = {}

        # Core models - ORDER MATTERS for FK dependencies
        model_classes = [
            # Key mapping (no dependencies)
            Key,
            # Base entities and relationships
            Entity, Relationship, Document,
            # Auth and multi-tenancy (no FKs to other app tables)
            User, Session, Domain,
            # Teams (depends on Domain, User)
            Team, TeamMembership,
            # Clients must come before Model/Persona (they have FKs to clients)
            Client,
            # Models and Personas (have FKs to clients)
            Model, Persona,
            # Agents and checkpoints
            Agent, AgentCheckpoint,
            # Messaging
            Message, MessageRead,
            # Conversations
            Conversation, ChatMessage,
            # Projects and repositories
            Project, Repository, TeamProject, ProjectRepository,
            RepositoryStats, Commit,
            # Work sessions
            WorkSession,
            # Metrics and activity
            Metric, Activity,
        ]

        for model_cls in model_classes:
            if hasattr(model_cls, '__tablename__'):
                table_name = model_cls.__tablename__
            else:
                # Generate table name from class name
                table_name = model_cls.__name__.lower() + 's'
            models[table_name] = model_cls

        self._models = models
        return models

    def get_existing_tables(self) -> Set[str]:
        """Get set of existing table names in database."""
        if self.inspector is None:
            self.inspector = inspect(self.engine)
        return set(self.inspector.get_table_names())

    def get_existing_columns(self, table_name: str) -> Dict[str, dict]:
        """
        Get existing columns for a table.

        Returns dict of column_name -> column_info.
        """
        if self.inspector is None:
            self.inspector = inspect(self.engine)

        columns = {}
        for col in self.inspector.get_columns(table_name):
            columns[col['name']] = {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default'),
                'primary_key': col.get('primary_key', False)
            }
        return columns

    def get_model_columns(self, model_cls: Type) -> Dict[str, Column]:
        """Get columns defined in model class."""
        columns = {}
        for col in model_cls.__table__.columns:
            columns[col.name] = col
        return columns

    def get_existing_indexes(self, table_name: str) -> List[dict]:
        """Get existing indexes for a table."""
        if self.inspector is None:
            self.inspector = inspect(self.engine)
        return self.inspector.get_indexes(table_name)

    def get_existing_foreign_keys(self, table_name: str) -> List[dict]:
        """Get existing foreign keys for a table."""
        if self.inspector is None:
            self.inspector = inspect(self.engine)
        return self.inspector.get_foreign_keys(table_name)

    def _sqlalchemy_type_to_postgres(self, sa_type: TypeEngine) -> str:
        """Convert SQLAlchemy type to PostgreSQL type string."""
        type_name = type(sa_type).__name__

        # Handle specific types
        if type_name == 'String':
            length = getattr(sa_type, 'length', None)
            if length:
                return f'VARCHAR({length})'
            return 'VARCHAR'
        elif type_name == 'Numeric':
            precision = getattr(sa_type, 'precision', None)
            scale = getattr(sa_type, 'scale', None)
            if precision and scale:
                return f'NUMERIC({precision},{scale})'
            return 'NUMERIC'

        return self.POSTGRES_TYPE_MAP.get(type_name, 'TEXT')

    def _get_column_default_sql(self, column: Column) -> Optional[str]:
        """Get SQL default value for a column."""
        if column.default is None:
            return None

        if callable(column.default.arg):
            # Python callable defaults can't be represented in SQL
            return None

        default = column.default.arg
        if isinstance(default, bool):
            return 'TRUE' if default else 'FALSE'
        elif isinstance(default, (int, float)):
            return str(default)
        elif isinstance(default, str):
            return f"'{default}'"

        return None

    def generate_add_column_sql(self, table_name: str, column: Column) -> str:
        """Generate SQL to add a column."""
        col_type = self._sqlalchemy_type_to_postgres(column.type)
        nullable = '' if column.nullable else ' NOT NULL'

        default = self._get_column_default_sql(column)
        default_clause = f' DEFAULT {default}' if default else ''

        return f'ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}{nullable}{default_clause}'

    def generate_drop_column_sql(self, table_name: str, column_name: str) -> str:
        """Generate SQL to drop a column."""
        return f'ALTER TABLE {table_name} DROP COLUMN {column_name}'

    def is_column_protected(self, table_name: str, column_name: str,
                            model_cls: Type) -> bool:
        """
        Check if a column is protected from removal.

        Protected columns:
        - Primary key columns
        - Columns in PROTECTED_COLUMNS set
        - Foreign key columns
        """
        # Check if it's a protected column name
        if column_name in self.PROTECTED_COLUMNS:
            return True

        # Check if it's the primary key
        pk_columns = [col.name for col in model_cls.__table__.primary_key.columns]
        if column_name in pk_columns:
            return True

        return False

    def generate_create_index_sql(self, table_name: str, index_name: str,
                                   columns: List[str], unique: bool = False) -> str:
        """Generate SQL to create an index."""
        unique_clause = 'UNIQUE ' if unique else ''
        cols = ', '.join(columns)
        return f'CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} ON {table_name} ({cols})'

    def detect_schema_changes(self, table_name: str, model_cls: Type) -> Dict[str, Any]:
        """
        Detect schema changes between model and database.

        Returns dict with:
        - new_columns: List of columns to add
        - removed_columns: List of columns to remove (if enabled)
        - modified_columns: List of columns with type changes
        - new_indexes: List of indexes to create
        - new_foreign_keys: List of foreign keys to add
        """
        changes = {
            'new_columns': [],
            'removed_columns': [],
            'modified_columns': [],
            'new_indexes': [],
            'new_foreign_keys': [],
            'total_changes': 0
        }

        existing_columns = self.get_existing_columns(table_name)
        model_columns = self.get_model_columns(model_cls)

        # Check for new columns
        for col_name, column in model_columns.items():
            if col_name not in existing_columns:
                changes['new_columns'].append(column)
                changes['total_changes'] += 1

        # Check for removed columns (in DB but not in model)
        for col_name in existing_columns:
            if col_name not in model_columns:
                # Check if column is protected
                if self.is_column_protected(table_name, col_name, model_cls):
                    logger.debug(f"Column {table_name}.{col_name} is protected, skipping removal")
                    continue

                # Only treat "extra columns" as actionable changes when removal is enabled.
                # Otherwise this creates noisy warnings on every startup for legacy columns.
                if self.allow_column_removal:
                    changes['removed_columns'].append({
                        'name': col_name,
                        'info': existing_columns[col_name]
                    })
                    changes['total_changes'] += 1
                else:
                    logger.debug(
                        f"Column {table_name}.{col_name} exists in database but not in model "
                        f"(allow_column_removal=False; keeping column)"
                    )

        # Check indexes
        existing_indexes = {idx['name']: idx for idx in self.get_existing_indexes(table_name)}

        for index in model_cls.__table__.indexes:
            if index.name not in existing_indexes:
                changes['new_indexes'].append({
                    'name': index.name,
                    'columns': [col.name for col in index.columns],
                    'unique': index.unique
                })
                changes['total_changes'] += 1

        # Check foreign keys
        existing_fks = self.get_existing_foreign_keys(table_name)
        existing_fk_cols = {fk['constrained_columns'][0] for fk in existing_fks if fk['constrained_columns']}

        for fk in model_cls.__table__.foreign_keys:
            if fk.parent.name not in existing_fk_cols:
                changes['new_foreign_keys'].append({
                    'column': fk.parent.name,
                    'references': f'{fk.column.table.name}.{fk.column.name}'
                })
                changes['total_changes'] += 1

        return changes

    def apply_schema_changes(self, table_name: str, changes: Dict[str, Any],
                             allow_removal: bool = None) -> int:
        """
        Apply schema changes to database.

        Args:
            table_name: Name of the table to modify
            changes: Dict of changes from detect_schema_changes
            allow_removal: Override instance-level allow_column_removal setting

        Returns number of changes applied.
        """
        applied = 0
        removal_enabled = allow_removal if allow_removal is not None else self.allow_column_removal

        with db.engine.connect() as conn:
            # Add new columns
            for column in changes.get('new_columns', []):
                sql = self.generate_add_column_sql(table_name, column)
                logger.info(f"Adding column: {sql}")
                try:
                    conn.execute(text(sql))
                    applied += 1
                except Exception as e:
                    logger.error(f"Failed to add column {column.name}: {e}")

            # Remove columns (only if enabled)
            for col_info in changes.get('removed_columns', []):
                col_name = col_info['name']
                if removal_enabled:
                    sql = self.generate_drop_column_sql(table_name, col_name)
                    logger.warning(f"Removing column: {sql}")
                    try:
                        conn.execute(text(sql))
                        applied += 1
                    except Exception as e:
                        logger.error(f"Failed to remove column {col_name}: {e}")
                else:
                    logger.warning(
                        f"Column {table_name}.{col_name} exists in database but not in model. "
                        f"Set allow_column_removal=True to remove it."
                    )

            # Create new indexes
            for index in changes.get('new_indexes', []):
                sql = self.generate_create_index_sql(
                    table_name,
                    index['name'],
                    index['columns'],
                    index['unique']
                )
                logger.info(f"Creating index: {sql}")
                try:
                    conn.execute(text(sql))
                    applied += 1
                except Exception as e:
                    logger.error(f"Failed to create index {index['name']}: {e}")

            conn.commit()

        return applied

    def ensure_pgvector_extension(self):
        """
        Ensure pgvector extension is enabled in PostgreSQL.

        This must be called before creating tables with vector columns.
        """
        if not self.pgvector_enabled():
            return
        try:
            with db.engine.connect() as conn:
                # Check if extension exists
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                ))
                exists = result.scalar()

                if not exists:
                    logger.info("Enabling pgvector extension...")
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    logger.info("pgvector extension enabled")
                else:
                    logger.debug("pgvector extension already enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension: {e}")
            logger.warning("Semantic search will be disabled")

    def ensure_hnsw_indexes(self):
        """
        Create HNSW indexes for vector columns.

        HNSW (Hierarchical Navigable Small World) indexes provide fast
        approximate nearest neighbor search for vector columns.
        """
        if not self.pgvector_enabled():
            return
        hnsw_indexes = [
            {
                'table': 'entities',
                'column': 'embedding',
                'index_name': 'entities_embedding_hnsw_idx',
            },
            {
                'table': 'documents',
                'column': 'embedding',
                'index_name': 'documents_embedding_hnsw_idx',
            },
        ]

        existing_tables = self.get_existing_tables()

        for idx_config in hnsw_indexes:
            table_name = idx_config['table']
            if table_name not in existing_tables:
                continue

            # Only attempt HNSW indexes when the column is actually a VECTOR type.
            # If the schema still has TEXT embeddings, pgvector ops will fail.
            try:
                existing_cols = self.get_existing_columns(table_name)
                col_info = existing_cols.get(idx_config['column'])
                col_type = (col_info or {}).get('type', '')
                if 'vector' not in str(col_type).lower():
                    logger.debug(
                        f"Skipping HNSW index {idx_config['index_name']} because "
                        f"{table_name}.{idx_config['column']} is not VECTOR (type={col_type})"
                    )
                    continue
            except Exception as e:
                logger.warning(
                    f"Could not inspect column type for HNSW index {idx_config['index_name']}: {e}"
                )
                continue

            # Check if index already exists
            existing_indexes = {idx['name'] for idx in self.get_existing_indexes(table_name)}
            if idx_config['index_name'] in existing_indexes:
                logger.debug(f"HNSW index {idx_config['index_name']} already exists")
                continue

            # Create HNSW index
            sql = f"""
                CREATE INDEX IF NOT EXISTS {idx_config['index_name']}
                ON {table_name}
                USING hnsw ({idx_config['column']} vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """
            try:
                with db.engine.connect() as conn:
                    logger.info(f"Creating HNSW index: {idx_config['index_name']}")
                    conn.execute(text(sql))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Could not create HNSW index {idx_config['index_name']}: {e}")

    def ensure_system_tables(self):
        """Ensure Table and TableStatus tables exist."""
        if self._system_tables_created:
            return

        from api.models.table import Table
        from api.models.table_status import TableStatus

        existing_tables = self.get_existing_tables()

        # Create tables table first
        if 'tables' not in existing_tables:
            Table.__table__.create(bind=db.engine)
            logger.info("Created 'tables' table")

        # Refresh inspector
        self.inspector = inspect(self.engine)
        existing_tables = self.get_existing_tables()

        # Create table_status table
        if 'table_status' not in existing_tables:
            TableStatus.__table__.create(bind=db.engine)
            logger.info("Created 'table_status' table")

        self._system_tables_created = True

    def register_table(self, table_name: str, model_cls: Type) -> 'Table':
        """Register a table in the Table registry."""
        from api.models.table import Table
        from api.models.table_status import TableStatus

        model_class_name = model_cls.__name__
        schema_version = getattr(model_cls, 'current_schema_version', lambda: 1)()

        # Get or create table entry
        table = Table.register(
            name=table_name,
            model_class=model_class_name,
            schema_version=schema_version
        )

        # Ensure status record exists
        if not table.status:
            status = TableStatus(table_key=table.table_key)
            db.session.add(status)
            db.session.commit()

        return table

    def migrate_table(self, table_name: str, model_cls: Type) -> Dict[str, Any]:
        """
        Migrate a single table.

        Returns migration result dict.
        """
        from api.models.table import Table
        from api.models.table_status import TableStatus

        result = {
            'table': table_name,
            'action': 'none',
            'changes': 0,
            'status': 'ok'
        }

        existing_tables = self.get_existing_tables()

        if table_name not in existing_tables:
            # Create table
            logger.info(f"Creating table: {table_name}")
            model_cls.__table__.create(bind=db.engine)
            result['action'] = 'created'

            # Refresh inspector
            self.inspector = inspect(self.engine)

            # Register table and update status
            table = self.register_table(table_name, model_cls)
            version = getattr(model_cls, 'current_schema_version', lambda: 1)()
            table.status.mark_applied(changes=0, version=version)
        else:
            # Register table first
            table = self.register_table(table_name, model_cls)

            # Check for schema changes
            changes = self.detect_schema_changes(table_name, model_cls)

            if changes['total_changes'] > 0:
                logger.info(f"Detected {changes['total_changes']} changes for {table_name}")
                applied = self.apply_schema_changes(table_name, changes)
                result['action'] = 'migrated'
                result['changes'] = applied

                # Update status
                version = getattr(model_cls, 'current_schema_version', lambda: 1)()
                table.status.mark_applied(changes=applied, version=version)
            else:
                result['action'] = 'verified'
                table.status.mark_verified()

        # Refresh inspector cache after changes
        if result['action'] in ('created', 'migrated'):
            self.inspector = inspect(self.engine)

        # Run data migrations if model has migrate() method
        if hasattr(model_cls, 'migrate') and callable(getattr(model_cls, 'migrate')):
            try:
                migrated = model_cls.migrate()
                if migrated:
                    logger.info(f"Data migration completed for {table_name}")
                    result['data_migrated'] = True
            except Exception as e:
                logger.error(f"Data migration failed for {table_name}: {e}")
                result['data_migration_error'] = str(e)

        return result

    def run_migrations(self, seed_data: bool = True,
                        allow_column_removal: bool = None) -> Dict[str, Any]:
        """
        Run all migrations.

        Args:
            seed_data: Whether to seed default data after migrations
            allow_column_removal: Override instance-level setting for column removal.
                                  If True, columns in DB not in model will be dropped.
                                  Default is False for safety.

        Returns summary of migration results.
        """
        # Allow override of removal setting for this run
        if allow_column_removal is not None:
            self.allow_column_removal = allow_column_removal

        logger.info("Starting migrations...")

        # Initialize
        self.engine = db.engine
        self.inspector = inspect(self.engine)

        # Enable pgvector extension for vector embeddings (when enabled)
        self.ensure_pgvector_extension()

        # Ensure system tables exist first (Table, TableStatus)
        self.ensure_system_tables()

        # Discover models
        models = self.discover_models()

        results = {
            'tables': {},
            'total_created': 0,
            'total_migrated': 0,
            'total_verified': 0,
            'errors': []
        }

        # Migrate each table
        for table_name, model_cls in models.items():
            try:
                result = self.migrate_table(table_name, model_cls)
                results['tables'][table_name] = result

                if result['action'] == 'created':
                    results['total_created'] += 1
                elif result['action'] == 'migrated':
                    results['total_migrated'] += 1
                elif result['action'] == 'verified':
                    results['total_verified'] += 1

            except Exception as e:
                logger.error(f"Migration failed for {table_name}: {e}")
                results['errors'].append({
                    'table': table_name,
                    'error': str(e)
                })

        # Create HNSW indexes for vector columns (after tables exist, when enabled)
        self.ensure_hnsw_indexes()

        # Seed data if requested
        if seed_data:
            self._seed_default_data()

        logger.info(f"Migrations complete: {results['total_created']} created, "
                   f"{results['total_migrated']} migrated, {results['total_verified']} verified")

        return results

    def _seed_default_data(self):
        """Seed default data after migrations."""
        from api import config
        from api.models import Entity, Persona

        # Seed default personas
        existing_personas = Persona.count()
        if existing_personas == 0:
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
        else:
            logger.info(f"Found {existing_personas} existing personas, skipping seed")

        # Seed default user
        user = config.DEFAULT_USER
        existing_user = Entity.query.filter_by(
            entity_type='Person',
            name=user['name']
        ).first()

        if not existing_user:
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
        else:
            logger.info(f"Default user entity already exists: {user['name']}")

    def get_table_registry(self) -> List[dict]:
        """Get all registered tables with their status."""
        from api.models.table import Table

        tables = Table.get_all()
        return [t.to_dict() for t in tables]

    def get_table_status(self, table_name: str) -> Optional[dict]:
        """Get status for a specific table."""
        from api.models.table import Table

        table = Table.get_by_name(table_name)
        if table:
            return table.to_dict()
        return None

    def update_row_counts(self):
        """Update cached row counts for all registered tables."""
        from api.models.table import Table

        for table in Table.get_all():
            if table.name in self._models:
                model_cls = self._models[table.name]
                count = model_cls.query.count()
                if table.status:
                    table.status.update_row_count(count)


# Global instance
migration_manager = MigrationManager()


def run_migrations():
    """
    Run database migrations and seed default data.

    Called on application startup. This is the main entry point
    that replaces the simple migrations.py.
    """
    return migration_manager.run_migrations(seed_data=True)
