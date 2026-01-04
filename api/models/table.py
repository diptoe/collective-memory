"""
Collective Memory Platform - Table Model

Registry of database tables with metadata.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text
from api.models.base import db, get_key, get_now


class Table(db.Model):
    """
    Registry of database tables.

    Tracks all tables managed by the system with their metadata.
    This is a special model that doesn't inherit from BaseModel
    to avoid circular dependencies.
    """
    __tablename__ = 'tables'

    # Primary key
    table_key = Column(String(36), primary_key=True, default=get_key)

    # Table identifier (matches __tablename__)
    name = Column(String(128), nullable=False, unique=True, index=True)

    # SQLAlchemy model class name
    model_class = Column(String(128), nullable=True)

    # Human-readable description
    description = Column(Text, nullable=True)

    # Current schema version defined in model
    schema_version = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=get_now, onupdate=get_now)

    # Relationship to status
    status = db.relationship('TableStatus', back_populates='table', uselist=False, cascade='all, delete-orphan')

    @classmethod
    def get_by_name(cls, name: str) -> 'Table | None':
        """Get table by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_or_create(cls, name: str, model_class: str = None, schema_version: int = 1) -> 'Table':
        """Get existing table or create new one."""
        table = cls.get_by_name(name)
        if not table:
            table = cls(
                name=name,
                model_class=model_class,
                schema_version=schema_version
            )
            db.session.add(table)
            db.session.commit()
        return table

    @classmethod
    def register(cls, name: str, model_class: str, description: str = None,
                 schema_version: int = 1) -> 'Table':
        """Register a table, updating if it exists."""
        table = cls.get_by_name(name)
        if table:
            table.model_class = model_class
            table.schema_version = schema_version
            if description:
                table.description = description
            table.updated_at = get_now()
        else:
            table = cls(
                name=name,
                model_class=model_class,
                description=description,
                schema_version=schema_version
            )
            db.session.add(table)
        db.session.commit()
        return table

    @classmethod
    def get_all(cls) -> list['Table']:
        """Get all registered tables."""
        return cls.query.order_by(cls.name).all()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            'table_key': self.table_key,
            'name': self.name,
            'model_class': self.model_class,
            'description': self.description,
            'schema_version': self.schema_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if self.status:
            result['status'] = self.status.to_dict()
        return result

    def __repr__(self) -> str:
        return f'<Table {self.name} v{self.schema_version}>'
