"""
Collective Memory Platform - Activity Model

Tracks system activities for the activity dashboard.
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class ActivityType(str, Enum):
    """Activity types tracked by the system."""
    MESSAGE_SENT = 'message_sent'
    AGENT_HEARTBEAT = 'agent_heartbeat'
    AGENT_REGISTERED = 'agent_registered'
    SEARCH_PERFORMED = 'search_performed'
    ENTITY_CREATED = 'entity_created'
    ENTITY_UPDATED = 'entity_updated'
    ENTITY_DELETED = 'entity_deleted'
    ENTITY_READ = 'entity_read'
    RELATIONSHIP_CREATED = 'relationship_created'
    RELATIONSHIP_DELETED = 'relationship_deleted'


class Activity(BaseModel):
    """
    Activity log entry for tracking system events.

    Used to power the activity dashboard with real-time visualization.
    Activities are auto-purged after RETENTION_DAYS.
    """
    __tablename__ = 'activities'

    RETENTION_DAYS = 7

    activity_key = Column(String(36), primary_key=True, default=get_key)
    activity_type = Column(String(50), nullable=False, index=True)
    actor = Column(String(100), nullable=False, index=True)  # agent_id or user_key or "system"
    user_key = Column(String(36), nullable=True, index=True)  # user who performed the action
    target_key = Column(String(100), nullable=True)  # entity_key, message_key, etc.
    target_type = Column(String(50), nullable=True)  # 'entity', 'message', 'agent'
    extra_data = Column(JSONB, default=dict)  # extra info like entity_type, name, channel
    domain_key = Column(String(36), nullable=True, index=True)  # domain for multi-tenancy
    created_at = Column(DateTime(timezone=True), default=get_now, index=True)

    __table_args__ = (
        Index('ix_activities_created_type', 'created_at', 'activity_type'),
        Index('ix_activities_actor_created', 'actor', 'created_at'),
        Index('ix_activities_domain_created', 'domain_key', 'created_at'),
    )

    _default_fields = ['activity_key', 'activity_type', 'actor', 'user_key', 'target_key', 'target_type', 'extra_data', 'domain_key']
    _readonly_fields = ['activity_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 2

    @classmethod
    def migrate(cls) -> bool:
        """
        Migrate existing Activity records to include domain_key and user_key.

        For activities created before multi-tenancy, attempts to set domain_key
        based on the actor's (agent's) owning user's domain. Activities with
        actor='system' or unrecognized actors remain without a domain.
        """
        from api.models.agent import Agent
        from api.models.user import User

        migrated = False
        # Only migrate records that have NULL domain_key
        records = cls.query.filter(cls.domain_key.is_(None)).all()

        for r in records:
            # Try to get domain from the actor (agent) -> user -> domain
            if r.actor and r.actor != 'system':
                agent = Agent.query.filter_by(agent_id=r.actor).first()
                if agent and agent.user_key:
                    user = User.query.get(agent.user_key)
                    if user:
                        if user.domain_key:
                            r.domain_key = user.domain_key
                        if not r.user_key:
                            r.user_key = user.user_key
                        db.session.add(r)
                        migrated = True

        if migrated:
            db.session.commit()

        return migrated

    @classmethod
    def get_recent(
        cls,
        limit: int = 50,
        activity_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        actor: Optional[str] = None,
        domain_key: Optional[str] = None,
        user_key: Optional[str] = None
    ) -> List['Activity']:
        """
        Get recent activities with optional filtering.

        Args:
            limit: Maximum number of results
            activity_type: Filter by activity type
            since: Only activities after this time
            until: Only activities before this time
            actor: Filter by actor (agent_id)
            domain_key: Filter by domain (for multi-tenancy)
            user_key: Filter by user

        Returns:
            List of Activity objects ordered by created_at desc
        """
        query = cls.query

        if activity_type:
            query = query.filter(cls.activity_type == activity_type)
        if since:
            query = query.filter(cls.created_at >= since)
        if until:
            query = query.filter(cls.created_at <= until)
        if actor:
            query = query.filter(cls.actor == actor)
        if domain_key:
            query = query.filter(cls.domain_key == domain_key)
        if user_key:
            query = query.filter(cls.user_key == user_key)

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_summary(
        cls,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        domain_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated activity counts by type.

        Args:
            since: Only count activities after this time
            until: Only count activities before this time
            domain_key: Filter by domain (for multi-tenancy)

        Returns:
            Dict with 'summary' (type -> count) and 'total' count
        """
        query = db.session.query(
            cls.activity_type,
            func.count(cls.activity_key).label('count')
        )

        if since:
            query = query.filter(cls.created_at >= since)
        if until:
            query = query.filter(cls.created_at <= until)
        if domain_key:
            query = query.filter(cls.domain_key == domain_key)

        results = query.group_by(cls.activity_type).all()

        summary = {r.activity_type: r.count for r in results}
        total = sum(summary.values())

        return {
            'summary': summary,
            'total': total
        }

    @classmethod
    def get_timeline(
        cls,
        hours: int = 24,
        bucket_minutes: int = 60,
        since: Optional[datetime] = None,
        domain_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time-bucketed activity data for charts.

        Args:
            hours: Number of hours to look back
            bucket_minutes: Size of each time bucket in minutes
            since: Override start time (defaults to hours ago)
            domain_key: Filter by domain (for multi-tenancy)

        Returns:
            List of dicts with timestamp, total, and per-type counts
        """
        if since is None:
            since = get_now() - timedelta(hours=hours)

        # Use PostgreSQL to bucket by arbitrary minutes
        # Formula: floor epoch to nearest bucket_minutes interval, then convert back
        bucket_seconds = bucket_minutes * 60
        bucket_expr = func.to_timestamp(
            func.floor(
                func.extract('epoch', cls.created_at) / bucket_seconds
            ) * bucket_seconds
        ).label('bucket')

        query = db.session.query(
            bucket_expr,
            cls.activity_type,
            func.count(cls.activity_key).label('count')
        ).filter(
            cls.created_at >= since
        )

        if domain_key:
            query = query.filter(cls.domain_key == domain_key)

        query = query.group_by(
            text("1"),  # bucket
            cls.activity_type
        ).order_by(
            text("1")
        )

        results = query.all()

        # Organize by timestamp
        timeline: Dict[datetime, Dict[str, int]] = {}
        for r in results:
            bucket = r.bucket
            if bucket not in timeline:
                timeline[bucket] = {'total': 0}
            timeline[bucket][r.activity_type] = r.count
            timeline[bucket]['total'] += r.count

        # Convert to list format
        return [
            {
                'timestamp': ts.isoformat(),
                **counts
            }
            for ts, counts in sorted(timeline.items())
        ]

    @classmethod
    def purge_old(cls) -> int:
        """
        Delete activities older than RETENTION_DAYS.

        Returns:
            Number of records deleted
        """
        cutoff = get_now() - timedelta(days=cls.RETENTION_DAYS)

        result = cls.query.filter(cls.created_at < cutoff).delete()
        db.session.commit()

        return result

    @classmethod
    def get_activity_types(cls) -> List[str]:
        """Get list of available activity types."""
        return [t.value for t in ActivityType]

    def to_dict(self, include_relationships: bool = False) -> dict:
        """Convert to dictionary."""
        return {
            'activity_key': self.activity_key,
            'activity_type': self.activity_type,
            'actor': self.actor,
            'user_key': self.user_key,
            'target_key': self.target_key,
            'target_type': self.target_type,
            'extra_data': self.extra_data or {},
            'domain_key': self.domain_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
