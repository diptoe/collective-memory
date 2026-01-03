"""
Collective Memory Platform - Base Model

Following Jai API patterns for SQLAlchemy model base class.
"""
from datetime import datetime, timezone
from typing import Optional, Type, TypeVar
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
    """
    __abstract__ = True

    # Default and readonly field lists (override in subclasses)
    _default_fields: list = []
    _readonly_fields: list = ['created_at', 'updated_at']

    @classmethod
    def current_schema_version(cls) -> int:
        """Override in subclasses to track schema versions."""
        return 1

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
