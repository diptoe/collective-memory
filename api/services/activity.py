"""
Collective Memory Platform - Activity Service

Service for recording and querying system activities.
"""
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from api.models.base import db, get_key, get_now
from api.models.activity import Activity, ActivityType


class ActivityService:
    """
    Service for recording system activities.

    Provides convenience methods for recording different activity types
    and includes opportunistic purging of old records.
    """

    # Purge check probability (1 in N requests will trigger purge check)
    PURGE_CHECK_PROBABILITY = 100

    def __init__(self):
        self._last_purge_check: Optional[datetime] = None

    def record(
        self,
        activity_type: str,
        actor: str,
        target_key: Optional[str] = None,
        target_type: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Activity:
        """
        Record a new activity.

        Args:
            activity_type: Type of activity (from ActivityType enum)
            actor: Agent key or "system"
            target_key: Key of the target object
            target_type: Type of target ('entity', 'message', 'agent')
            extra_data: Additional data

        Returns:
            The created Activity record
        """
        activity = Activity(
            activity_key=get_key(),
            activity_type=activity_type,
            actor=actor,
            target_key=target_key,
            target_type=target_type,
            extra_data=extra_data or {},
            created_at=get_now()
        )

        db.session.add(activity)
        db.session.commit()

        # Opportunistic purge check
        self._maybe_purge()

        return activity

    def record_message_sent(
        self,
        actor: str,
        message_key: str,
        channel: Optional[str] = None,
        recipient: Optional[str] = None
    ) -> Activity:
        """Record a message_sent activity."""
        return self.record(
            activity_type=ActivityType.MESSAGE_SENT.value,
            actor=actor,
            target_key=message_key,
            target_type='message',
            extra_data={
                'channel': channel,
                'recipient': recipient
            }
        )

    def record_agent_heartbeat(
        self,
        actor: str,
        agent_key: str,
        status: Optional[str] = None,
        unread_messages: int = 0,
        autonomous_tasks: int = 0
    ) -> Activity:
        """Record an agent_heartbeat activity."""
        return self.record(
            activity_type=ActivityType.AGENT_HEARTBEAT.value,
            actor=actor,
            target_key=agent_key,
            target_type='agent',
            extra_data={
                'status': status,
                'unread_messages': unread_messages,
                'autonomous_tasks': autonomous_tasks
            }
        )

    def record_agent_registered(
        self,
        actor: str,
        agent_key: str,
        client: Optional[str] = None,
        persona: Optional[str] = None,
        model: Optional[str] = None,
        is_reconnect: bool = False
    ) -> Activity:
        """Record an agent_registered activity."""
        return self.record(
            activity_type=ActivityType.AGENT_REGISTERED.value,
            actor=actor,
            target_key=agent_key,
            target_type='agent',
            extra_data={
                'client': client,
                'persona': persona,
                'model': model,
                'is_reconnect': is_reconnect
            }
        )

    def record_entity_created(
        self,
        actor: str,
        entity_key: str,
        entity_type: str,
        entity_name: str
    ) -> Activity:
        """Record an entity_created activity."""
        return self.record(
            activity_type=ActivityType.ENTITY_CREATED.value,
            actor=actor,
            target_key=entity_key,
            target_type='entity',
            extra_data={
                'entity_type': entity_type,
                'entity_name': entity_name
            }
        )

    def record_entity_updated(
        self,
        actor: str,
        entity_key: str,
        entity_type: str,
        entity_name: str
    ) -> Activity:
        """Record an entity_updated activity."""
        return self.record(
            activity_type=ActivityType.ENTITY_UPDATED.value,
            actor=actor,
            target_key=entity_key,
            target_type='entity',
            extra_data={
                'entity_type': entity_type,
                'entity_name': entity_name
            }
        )

    def record_entity_deleted(
        self,
        actor: str,
        entity_key: str,
        entity_type: str,
        entity_name: str
    ) -> Activity:
        """Record an entity_deleted activity."""
        return self.record(
            activity_type=ActivityType.ENTITY_DELETED.value,
            actor=actor,
            target_key=entity_key,
            target_type='entity',
            extra_data={
                'entity_type': entity_type,
                'entity_name': entity_name
            }
        )

    def record_entity_read(
        self,
        actor: str,
        entity_key: str,
        entity_type: str,
        entity_name: str
    ) -> Activity:
        """Record an entity_read activity."""
        return self.record(
            activity_type=ActivityType.ENTITY_READ.value,
            actor=actor,
            target_key=entity_key,
            target_type='entity',
            extra_data={
                'entity_type': entity_type,
                'entity_name': entity_name
            }
        )

    def record_search(
        self,
        actor: str,
        query: Optional[str] = None,
        search_type: str = 'entity',
        entity_type: Optional[str] = None,
        result_count: int = 0
    ) -> Activity:
        """Record a search_performed activity."""
        return self.record(
            activity_type=ActivityType.SEARCH_PERFORMED.value,
            actor=actor,
            target_key=None,
            target_type='search',
            extra_data={
                'query': query,
                'search_type': search_type,
                'entity_type': entity_type,
                'result_count': result_count
            }
        )

    def record_relationship_created(
        self,
        actor: str,
        relationship_key: str,
        from_entity_key: str,
        from_entity_name: str,
        to_entity_key: str,
        to_entity_name: str,
        relationship_type: str
    ) -> Activity:
        """Record a relationship_created activity."""
        return self.record(
            activity_type=ActivityType.RELATIONSHIP_CREATED.value,
            actor=actor,
            target_key=relationship_key,
            target_type='relationship',
            extra_data={
                'from_entity_key': from_entity_key,
                'from_entity_name': from_entity_name,
                'to_entity_key': to_entity_key,
                'to_entity_name': to_entity_name,
                'relationship_type': relationship_type
            }
        )

    def record_relationship_deleted(
        self,
        actor: str,
        relationship_key: str,
        from_entity_key: Optional[str] = None,
        to_entity_key: Optional[str] = None,
        relationship_type: Optional[str] = None
    ) -> Activity:
        """Record a relationship_deleted activity."""
        return self.record(
            activity_type=ActivityType.RELATIONSHIP_DELETED.value,
            actor=actor,
            target_key=relationship_key,
            target_type='relationship',
            extra_data={
                'from_entity_key': from_entity_key,
                'to_entity_key': to_entity_key,
                'relationship_type': relationship_type
            }
        )

    def get_recent(
        self,
        limit: int = 50,
        activity_type: Optional[str] = None,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        actor: Optional[str] = None
    ) -> List[Activity]:
        """
        Get recent activities with filtering.

        Args:
            limit: Maximum results
            activity_type: Filter by type
            hours: Look back this many hours
            since: Start time (overrides hours)
            until: End time
            actor: Filter by actor

        Returns:
            List of Activity objects
        """
        if hours and not since:
            from datetime import timedelta
            since = get_now() - timedelta(hours=hours)

        return Activity.get_recent(
            limit=limit,
            activity_type=activity_type,
            since=since,
            until=until,
            actor=actor
        )

    def get_summary(
        self,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get activity summary by type.

        Args:
            hours: Look back this many hours
            since: Start time (overrides hours)
            until: End time

        Returns:
            Dict with summary and total
        """
        if hours and not since:
            from datetime import timedelta
            since = get_now() - timedelta(hours=hours)

        return Activity.get_summary(since=since, until=until)

    def get_timeline(
        self,
        hours: int = 24,
        bucket_minutes: int = 60,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time-bucketed activity data.

        Args:
            hours: Number of hours to look back
            bucket_minutes: Bucket size in minutes
            since: Override start time

        Returns:
            List of timeline data points
        """
        return Activity.get_timeline(
            hours=hours,
            bucket_minutes=bucket_minutes,
            since=since
        )

    def purge_old(self) -> int:
        """
        Purge activities older than retention period.

        Returns:
            Number of records deleted
        """
        return Activity.purge_old()

    def _maybe_purge(self) -> None:
        """
        Opportunistically purge old records.

        Runs approximately once per PURGE_CHECK_PROBABILITY calls,
        and only if enough time has passed since last purge.
        """
        # Random check to avoid purging on every request
        if random.randint(1, self.PURGE_CHECK_PROBABILITY) != 1:
            return

        # Don't purge more than once per hour
        now = get_now()
        if self._last_purge_check:
            from datetime import timedelta
            if now - self._last_purge_check < timedelta(hours=1):
                return

        self._last_purge_check = now

        try:
            deleted = self.purge_old()
            if deleted > 0:
                print(f"[ActivityService] Purged {deleted} old activity records")
        except Exception as e:
            print(f"[ActivityService] Purge failed: {e}")


# Global service instance
activity_service = ActivityService()
