"""
Collective Memory Platform - Table Status Model

Tracks dynamic state for database tables including migration status.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from api.models.base import db


def get_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TableStatus(db.Model):
    """
    Tracks status and state for each table.

    Includes migration tracking, health status, and cached metrics.
    One status record per table.
    """
    __tablename__ = 'table_status'

    # Foreign key to Table (also serves as primary key)
    table_key = Column(String(36), ForeignKey('tables.table_key', ondelete='CASCADE'),
                       primary_key=True)

    # Schema version currently in database
    db_version = Column(Integer, nullable=False, default=0)

    # Migration timestamps
    applied_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    migrated_at = Column(DateTime(timezone=True), nullable=True)

    # Number of changes in last migration
    changes = Column(Integer, nullable=True, default=0)

    # Current status (ok, migrating, error, etc.)
    status = Column(String(64), nullable=True, default='pending')

    # Detailed status message or error
    status_message = Column(Text, nullable=True)

    # Cached row count (updated periodically)
    row_count = Column(Integer, nullable=True)

    # Last time row count was updated
    row_count_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to Table
    table = db.relationship('Table', back_populates='status')

    @classmethod
    def get_for_table(cls, table_key: str) -> 'TableStatus | None':
        """Get status for a table."""
        return cls.query.get(table_key)

    @classmethod
    def get_or_create(cls, table_key: str) -> 'TableStatus':
        """Get existing status or create new one."""
        status = cls.query.get(table_key)
        if not status:
            status = cls(table_key=table_key)
            db.session.add(status)
            db.session.commit()
        return status

    def mark_applied(self, changes: int = 0, version: int = None):
        """Mark migration as applied."""
        self.applied_at = get_now()
        self.changes = changes
        if version is not None:
            self.db_version = version
        self.status = 'applied'
        self.status_message = f'Applied {changes} changes'
        db.session.commit()

    def mark_verified(self):
        """Mark schema as verified (no changes needed)."""
        self.verified_at = get_now()
        self.status = 'verified'
        self.status_message = 'Schema verified, no changes needed'
        db.session.commit()

    def mark_migrated(self):
        """Mark data migration as complete."""
        self.migrated_at = get_now()
        self.status = 'migrated'
        self.status_message = 'Data migration complete'
        db.session.commit()

    def mark_error(self, error_message: str):
        """Mark as error state."""
        self.status = 'error'
        self.status_message = error_message
        db.session.commit()

    def mark_pending(self):
        """Mark as pending migration."""
        self.status = 'pending'
        self.status_message = 'Awaiting migration'
        db.session.commit()

    def update_row_count(self, count: int):
        """Update cached row count."""
        self.row_count = count
        self.row_count_at = get_now()
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'table_key': self.table_key,
            'db_version': self.db_version,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'migrated_at': self.migrated_at.isoformat() if self.migrated_at else None,
            'changes': self.changes,
            'status': self.status,
            'status_message': self.status_message,
            'row_count': self.row_count,
            'row_count_at': self.row_count_at.isoformat() if self.row_count_at else None,
        }

    def __repr__(self) -> str:
        return f'<TableStatus {self.table_key} v{self.db_version} ({self.status})>'
