"""
Collective Memory Platform - Base Model

Following Jai API patterns for SQLAlchemy model base class.
Enhanced with schema versioning and migration support.
"""
from datetime import datetime, timezone
from typing import Optional, Type, TypeVar, List, Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
import uuid

db = SQLAlchemy()

T = TypeVar('T', bound='BaseModel')


def get_key() -> str:
    """Generate a new UUID key."""
    return str(uuid.uuid4())


def get_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class BaseModel(db.Model):
    """
    Base model class with common functionality.

    Provides:
    - UUID primary key generation
    - Timestamp management
    - Common CRUD operations
    - Schema versioning support
    - Migration hooks

    Schema Versioning:
    - Override _schema_version in subclasses to track schema changes
    - Override _schema_migrations() to define migration steps
    - Each version increment should correspond to a schema change
    """
    __abstract__ = True

    # Schema version - increment when model schema changes
    _schema_version: int = 1

    # Default and readonly field lists (override in subclasses)
    _default_fields: list = []
    _readonly_fields: list = ['created_at', 'updated_at']

    @classmethod
    def current_schema_version(cls) -> int:
        """
        Get current schema version for this model.

        Override _schema_version class attribute to change version.
        """
        return cls._schema_version

    @classmethod
    def _schema_migrations(cls) -> Dict[int, str]:
        """
        Define schema migrations for each version.

        Override in subclasses to provide migration descriptions.

        Returns dict of version -> migration description.

        Example:
            @classmethod
            def _schema_migrations(cls):
                return {
                    1: "Initial schema",
                    2: "Added status column",
                    3: "Added index on name column"
                }
        """
        return {1: "Initial schema"}

    @classmethod
    def pre_migrate(cls, from_version: int, to_version: int) -> None:
        """
        Hook called before migration.

        Override in subclasses to run pre-migration logic.

        Args:
            from_version: Current database schema version
            to_version: Target schema version
        """
        pass

    @classmethod
    def post_migrate(cls, from_version: int, to_version: int) -> None:
        """
        Hook called after migration.

        Override in subclasses to run post-migration logic
        like data transformations.

        Args:
            from_version: Previous database schema version
            to_version: New schema version
        """
        pass

    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model."""
        if hasattr(cls, '__tablename__'):
            return cls.__tablename__
        return cls.__name__.lower() + 's'

    @classmethod
    def get_by_key(cls: Type[T], key: str) -> Optional[T]:
        """Get a record by its primary key."""
        pk_column = list(cls.__table__.primary_key.columns)[0].name
        return cls.query.filter_by(**{pk_column: key}).first()

    @classmethod
    def get_all(cls: Type[T], limit: int = 100, offset: int = 0) -> list[T]:
        """Get all records with pagination."""
        return cls.query.limit(limit).offset(offset).all()

    @classmethod
    def count(cls: Type[T]) -> int:
        """Get total count of records."""
        return cls.query.count()

    def save(self) -> bool:
        """Save the current record to the database."""
        try:
            if hasattr(self, 'updated_at'):
                self.updated_at = get_now()
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self) -> bool:
        """Delete the current record from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def to_dict(self, include_relationships: bool = False) -> dict:
        """
        Convert the model to a dictionary.

        Override in subclasses for custom serialization.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_from_dict(self, data: dict) -> None:
        """
        Update model fields from a dictionary.

        Respects _readonly_fields.
        """
        for key, value in data.items():
            if key in self._readonly_fields:
                continue
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def create_from_dict(cls: Type[T], data: dict) -> T:
        """Create a new instance from a dictionary."""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    def __repr__(self) -> str:
        pk_column = list(self.__table__.primary_key.columns)[0].name
        pk_value = getattr(self, pk_column)
        return f'<{self.__class__.__name__} {pk_value}>'
