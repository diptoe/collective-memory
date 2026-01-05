"""
Collective Memory Platform - Repository Stats Model

Time-series metrics for repository activity tracking.
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Index, UniqueConstraint
from api.models.base import BaseModel, db, get_key, get_now


class RepositoryStats(BaseModel):
    """
    Daily statistics snapshot for a repository.

    Tracks metrics like commits, additions, deletions per day
    to enable time-series analysis and charting.
    """
    __tablename__ = 'repository_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_key = Column(String(255), nullable=False, index=True)  # Links to Repository entity
    date = Column(Date, nullable=False, index=True)

    # Commit metrics
    commits_count = Column(Integer, default=0)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)

    # Author metrics
    unique_authors = Column(Integer, default=0)
    ai_assisted_commits = Column(Integer, default=0)  # Commits with AI co-authors

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Ensure one record per entity per day
    __table_args__ = (
        UniqueConstraint('entity_key', 'date', name='uq_repository_stats_entity_date'),
        Index('ix_repository_stats_entity_date', 'entity_key', 'date'),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'entity_key': self.entity_key,
            'date': self.date.isoformat() if self.date else None,
            'commits_count': self.commits_count,
            'additions': self.additions,
            'deletions': self.deletions,
            'files_changed': self.files_changed,
            'unique_authors': self.unique_authors,
            'ai_assisted_commits': self.ai_assisted_commits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
