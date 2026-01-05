"""
Collective Memory Platform - Commit Model

Stores individual git commits from repositories.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from api.models.base import BaseModel, db, get_key, get_now


class Commit(BaseModel):
    """
    Individual git commit record.

    Stores commit metadata, stats, and AI co-author detection.
    Links to Repository entity via repository_key.
    """
    __tablename__ = 'commits'

    # Primary key - readable format
    commit_key = Column(String(50), primary_key=True, default=get_key)

    # Git identifiers
    sha = Column(String(40), nullable=False, index=True)
    repository_key = Column(String(255), nullable=False, index=True)

    # Commit metadata
    message = Column(Text, nullable=True)
    author_name = Column(String(255), nullable=True, index=True)
    author_email = Column(String(255), nullable=True, index=True)
    committer_name = Column(String(255), nullable=True)
    committer_email = Column(String(255), nullable=True)

    # Timestamps
    committed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    authored_at = Column(DateTime(timezone=True), nullable=True)

    # Stats
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)

    # AI co-authors detected (e.g., ["Claude", "GitHub Copilot"])
    ai_coauthors = Column(JSONB, default=list)

    # Link to Person entity if author matched
    author_entity_key = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes
    __table_args__ = (
        Index('ix_commits_repo_date', 'repository_key', 'committed_at'),
        Index('ix_commits_repo_sha', 'repository_key', 'sha', unique=True),
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'commit_key': self.commit_key,
            'sha': self.sha,
            'repository_key': self.repository_key,
            'message': self.message,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'committer_name': self.committer_name,
            'committer_email': self.committer_email,
            'committed_at': self.committed_at.isoformat() if self.committed_at else None,
            'authored_at': self.authored_at.isoformat() if self.authored_at else None,
            'additions': self.additions,
            'deletions': self.deletions,
            'files_changed': self.files_changed,
            'ai_coauthors': self.ai_coauthors or [],
            'author_entity_key': self.author_entity_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_sha(cls, repository_key: str, sha: str) -> 'Commit':
        """Get commit by repository and SHA."""
        return cls.query.filter_by(repository_key=repository_key, sha=sha).first()

    @classmethod
    def get_by_repository(cls, repository_key: str, limit: int = 100, offset: int = 0) -> list:
        """Get commits for a repository, ordered by date descending."""
        return cls.query.filter_by(repository_key=repository_key)\
            .order_by(cls.committed_at.desc())\
            .limit(limit).offset(offset).all()

    @classmethod
    def get_by_author(cls, author_email: str, limit: int = 100) -> list:
        """Get commits by author email."""
        return cls.query.filter_by(author_email=author_email)\
            .order_by(cls.committed_at.desc())\
            .limit(limit).all()

    @classmethod
    def get_ai_assisted(cls, repository_key: str = None, limit: int = 100) -> list:
        """Get commits with AI co-authors."""
        query = cls.query.filter(cls.ai_coauthors != None, cls.ai_coauthors != [])
        if repository_key:
            query = query.filter_by(repository_key=repository_key)
        return query.order_by(cls.committed_at.desc()).limit(limit).all()
