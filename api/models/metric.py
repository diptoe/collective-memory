"""
Collective Memory Platform - Metric Model

Generic time-series metrics storage for any entity.
"""

from sqlalchemy import Column, String, Float, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from api.models.base import BaseModel, db, get_key, get_now


class Metric(BaseModel):
    """
    Generic time-series metric record.

    Stores any numeric metric for any entity over time.
    Useful for tracking: stars, forks, issues, size, performance metrics, etc.
    """
    __tablename__ = 'metrics'

    # Primary key - readable format
    metric_key = Column(String(50), primary_key=True, default=get_key)

    # Links to any entity
    entity_key = Column(String(255), nullable=False, index=True)

    # Metric identification
    metric_type = Column(String(100), nullable=False, index=True)
    # Examples: stars, forks, open_issues, closed_issues, size_kb,
    #           watchers, contributors, releases, response_time_ms

    # Value and timestamp
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Optional extra context
    extra = Column(JSONB, default=dict)
    # Can store additional context like: {"source": "github_api", "branch": "main"}

    # Optional tags for filtering
    tags = Column(JSONB, default=list)
    # Examples: ["production", "daily_snapshot"]

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Indexes and constraints
    __table_args__ = (
        Index('ix_metrics_entity_type_date', 'entity_key', 'metric_type', 'recorded_at'),
        Index('ix_metrics_type_date', 'metric_type', 'recorded_at'),
        # Allow multiple metrics of same type per entity per timestamp (no unique constraint)
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'metric_key': self.metric_key,
            'entity_key': self.entity_key,
            'metric_type': self.metric_type,
            'value': self.value,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'extra': self.extra or {},
            'tags': self.tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_for_entity(cls, entity_key: str, metric_type: str = None,
                       limit: int = 100, offset: int = 0) -> list:
        """Get metrics for an entity, optionally filtered by type."""
        query = cls.query.filter_by(entity_key=entity_key)
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        return query.order_by(cls.recorded_at.desc()).limit(limit).offset(offset).all()

    @classmethod
    def get_time_series(cls, entity_key: str, metric_type: str,
                        start_date: DateTime = None, end_date: DateTime = None) -> list:
        """Get time series data for charting."""
        query = cls.query.filter_by(entity_key=entity_key, metric_type=metric_type)
        if start_date:
            query = query.filter(cls.recorded_at >= start_date)
        if end_date:
            query = query.filter(cls.recorded_at <= end_date)
        return query.order_by(cls.recorded_at.asc()).all()

    @classmethod
    def get_latest(cls, entity_key: str, metric_type: str) -> 'Metric':
        """Get the most recent metric of a type for an entity."""
        return cls.query.filter_by(entity_key=entity_key, metric_type=metric_type)\
            .order_by(cls.recorded_at.desc()).first()

    @classmethod
    def record(cls, entity_key: str, metric_type: str, value: float,
               recorded_at: DateTime = None, extra: dict = None, tags: list = None) -> 'Metric':
        """
        Record a new metric value.

        Args:
            entity_key: The entity this metric belongs to
            metric_type: Type of metric (e.g., 'stars', 'forks')
            value: The numeric value
            recorded_at: When the metric was recorded (defaults to now)
            extra: Optional additional context
            tags: Optional tags for filtering

        Returns:
            The created Metric instance
        """
        metric = cls(
            entity_key=entity_key,
            metric_type=metric_type,
            value=value,
            recorded_at=recorded_at or get_now(),
            extra=extra or {},
            tags=tags or []
        )
        db.session.add(metric)
        return metric


# Common metric types as constants
class MetricTypes:
    """Standard metric type constants."""
    # GitHub repository metrics
    STARS = 'stars'
    FORKS = 'forks'
    WATCHERS = 'watchers'
    OPEN_ISSUES = 'open_issues'
    CLOSED_ISSUES = 'closed_issues'
    SIZE_KB = 'size_kb'
    CONTRIBUTORS = 'contributors'
    RELEASES = 'releases'

    # Commit metrics (aggregated)
    COMMITS_TOTAL = 'commits_total'
    COMMITS_DAILY = 'commits_daily'
    ADDITIONS_DAILY = 'additions_daily'
    DELETIONS_DAILY = 'deletions_daily'

    # Performance metrics
    RESPONSE_TIME_MS = 'response_time_ms'
    UPTIME_PERCENT = 'uptime_percent'

    # Usage metrics
    API_CALLS = 'api_calls'
    ACTIVE_USERS = 'active_users'

    # Milestone auto-capture metrics
    MILESTONE_TOOL_CALLS = 'milestone_tool_calls'
    MILESTONE_FILES_TOUCHED = 'milestone_files_touched'
    MILESTONE_LINES_ADDED = 'milestone_lines_added'
    MILESTONE_LINES_REMOVED = 'milestone_lines_removed'
    MILESTONE_COMMITS_MADE = 'milestone_commits_made'
    MILESTONE_DURATION_MINUTES = 'milestone_duration_minutes'

    # Milestone self-assessment metrics (1-5 scale)
    MILESTONE_HUMAN_GUIDANCE = 'milestone_human_guidance'       # 1=fully autonomous, 5=heavy guidance
    MILESTONE_MODEL_UNDERSTANDING = 'milestone_model_understanding'  # 1=low, 5=high
    MILESTONE_MODEL_ACCURACY = 'milestone_model_accuracy'       # 1=low, 5=high
    MILESTONE_COLLABORATION_RATING = 'milestone_collaboration_rating'  # 1=poor, 5=excellent
    MILESTONE_COMPLEXITY_RATING = 'milestone_complexity_rating'  # 1=trivial, 5=very complex
