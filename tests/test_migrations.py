"""
Collective Memory Platform - Migration Tests

Tests for the MigrationManager and schema change detection.
"""
import pytest
from sqlalchemy import text


class TestMigrationManager:
    """Tests for MigrationManager functionality."""

    @pytest.fixture
    def migration_manager(self, app, db):
        """Provide configured MigrationManager."""
        from api.migration_manager import MigrationManager

        with app.app_context():
            mm = MigrationManager()
            mm.engine = db.engine
            yield mm

    @pytest.mark.integration
    def test_detect_new_column(self, app, db, migration_manager):
        """Test detection of new columns in model."""
        from api.models import Entity

        with app.app_context():
            # Get current columns
            existing = migration_manager.get_existing_columns('entities')

            # Get model columns
            model_cols = migration_manager.get_model_columns(Entity)

            # All model columns should exist in database
            for col_name in model_cols:
                assert col_name in existing, f"Column {col_name} missing from database"

    @pytest.mark.integration
    def test_detect_removed_column(self, app, db, migration_manager):
        """Test detection of columns that exist in DB but not in model."""
        from api.models import Entity

        with app.app_context():
            # Add a test column
            with db.engine.connect() as conn:
                try:
                    conn.execute(text('ALTER TABLE entities ADD COLUMN orphan_test_col VARCHAR(50)'))
                    conn.commit()
                except Exception:
                    pass  # Column might already exist

            # Reset inspector cache
            migration_manager.inspector = None

            # Detect changes
            changes = migration_manager.detect_schema_changes('entities', Entity)

            # Should detect the orphan column
            removed_names = [c['name'] for c in changes['removed_columns']]
            assert 'orphan_test_col' in removed_names

            # Clean up
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE entities DROP COLUMN IF EXISTS orphan_test_col'))
                conn.commit()

    @pytest.mark.integration
    def test_column_removal_disabled_by_default(self, app, db, migration_manager):
        """Test that column removal is disabled by default."""
        from api.models import Entity

        with app.app_context():
            # Add a test column
            with db.engine.connect() as conn:
                try:
                    conn.execute(text('ALTER TABLE entities ADD COLUMN safe_test_col VARCHAR(50)'))
                    conn.commit()
                except Exception:
                    pass

            # Reset inspector
            migration_manager.inspector = None

            # Detect and apply with removal disabled
            changes = migration_manager.detect_schema_changes('entities', Entity)
            applied = migration_manager.apply_schema_changes('entities', changes, allow_removal=False)

            # Column should NOT be removed
            migration_manager.inspector = None
            cols = migration_manager.get_existing_columns('entities')
            assert 'safe_test_col' in cols, "Column should not be removed when disabled"

            # Clean up
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE entities DROP COLUMN IF EXISTS safe_test_col'))
                conn.commit()

    @pytest.mark.integration
    def test_column_removal_when_enabled(self, app, db, migration_manager):
        """Test that columns are removed when enabled."""
        from api.models import Entity

        with app.app_context():
            # Add a test column
            with db.engine.connect() as conn:
                try:
                    conn.execute(text('ALTER TABLE entities ADD COLUMN remove_test_col VARCHAR(50)'))
                    conn.commit()
                except Exception:
                    pass

            # Reset inspector
            migration_manager.inspector = None

            # Detect and apply with removal enabled
            changes = migration_manager.detect_schema_changes('entities', Entity)
            applied = migration_manager.apply_schema_changes('entities', changes, allow_removal=True)

            # Column should be removed
            migration_manager.inspector = None
            cols = migration_manager.get_existing_columns('entities')
            assert 'remove_test_col' not in cols, "Column should be removed when enabled"

    @pytest.mark.integration
    def test_protected_columns_not_removed(self, app, db, migration_manager):
        """Test that protected columns (like primary key) are never removed."""
        from api.models import Entity

        with app.app_context():
            # entity_key is the primary key and should be protected
            changes = migration_manager.detect_schema_changes('entities', Entity)

            removed_names = [c['name'] for c in changes['removed_columns']]
            assert 'entity_key' not in removed_names, "Primary key should be protected"
            assert 'created_at' not in removed_names, "created_at should be protected"

    @pytest.mark.integration
    def test_table_registry(self, app, db, migration_manager):
        """Test that tables are registered correctly."""
        from api.models.table import Table

        with app.app_context():
            # Run migrations to ensure registry is populated
            from api.migrations import run_migrations
            run_migrations()

            # Check tables are registered
            tables = Table.get_all()
            table_names = [t.name for t in tables]

            assert 'entities' in table_names
            assert 'relationships' in table_names
            assert 'personas' in table_names

    @pytest.mark.integration
    def test_sql_generation(self, migration_manager):
        """Test SQL generation methods."""
        from sqlalchemy import Column, String, Integer

        # Test add column SQL
        col = Column('test_col', String(100), nullable=True)
        col.name = 'test_col'
        col.type = String(100)
        col.nullable = True

        sql = migration_manager.generate_add_column_sql('test_table', col)
        assert 'ALTER TABLE test_table ADD COLUMN test_col' in sql
        assert 'VARCHAR' in sql

        # Test drop column SQL
        sql = migration_manager.generate_drop_column_sql('test_table', 'old_col')
        assert sql == 'ALTER TABLE test_table DROP COLUMN old_col'

        # Test create index SQL
        sql = migration_manager.generate_create_index_sql('test_table', 'idx_test', ['col1', 'col2'])
        assert 'CREATE INDEX IF NOT EXISTS idx_test ON test_table (col1, col2)' in sql

        # Test unique index
        sql = migration_manager.generate_create_index_sql('test_table', 'idx_unique', ['col1'], unique=True)
        assert 'UNIQUE INDEX' in sql
