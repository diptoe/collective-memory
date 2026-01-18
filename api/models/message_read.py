"""
Collective Memory Platform - MessageRead Model

Tracks which agents/users have read which messages.
Enables per-reader read tracking for broadcast/channel messages.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint

from api.models.base import BaseModel, db, get_key, get_now


class MessageRead(BaseModel):
    """
    Tracks when an agent or user has read a message.

    reader_key can be either:
    - An agent_key (e.g., 'swift-bold-keen-lion') for agent readers
    - A user_key (e.g., 'calm-fresh-wild-river') for user readers

    For broadcast messages (to_key is null), each reader creates their own
    MessageRead record when they read the message.

    For direct messages (to_key is set), the recipient creates a record.
    """
    __tablename__ = 'message_reads'

    read_key = Column(String(36), primary_key=True, default=get_key)
    message_key = Column(String(36), ForeignKey('messages.message_key'), nullable=False, index=True)
    reader_key = Column(String(100), nullable=False, index=True)  # agent_key or user_key
    read_at = Column(DateTime(timezone=True), default=get_now)

    # Ensure each reader can only mark a message as read once
    __table_args__ = (
        UniqueConstraint('message_key', 'reader_key', name='uq_message_reader_read'),
    )

    _default_fields = ['read_key', 'message_key', 'reader_key', 'read_at']
    _readonly_fields = ['read_key', 'read_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 2

    @classmethod
    def has_read(cls, message_key: str, reader_key: str) -> bool:
        """Check if a reader (agent or user) has read a message."""
        return cls.query.filter_by(
            message_key=message_key,
            reader_key=reader_key
        ).first() is not None

    @classmethod
    def get_read_record(cls, message_key: str, reader_key: str) -> 'MessageRead':
        """Get the read record for a message/reader combination."""
        return cls.query.filter_by(
            message_key=message_key,
            reader_key=reader_key
        ).first()

    @classmethod
    def mark_read(cls, message_key: str, reader_key: str) -> 'MessageRead':
        """Mark a message as read by a reader. Returns existing record if already read."""
        existing = cls.get_read_record(message_key, reader_key)
        if existing:
            return existing

        read_record = cls(
            message_key=message_key,
            reader_key=reader_key
        )
        read_record.save()
        return read_record

    @classmethod
    def get_readers(cls, message_key: str) -> list['MessageRead']:
        """Get all readers who have read a message."""
        return cls.query.filter_by(message_key=message_key).all()

    @classmethod
    def get_read_count(cls, message_key: str) -> int:
        """Get count of readers who have read a message."""
        return cls.query.filter_by(message_key=message_key).count()

    @classmethod
    def get_unread_messages_for_reader(cls, reader_key: str, message_keys: list[str]) -> list[str]:
        """
        Given a list of message_keys, return those the reader hasn't read.
        """
        read_keys = db.session.query(cls.message_key).filter(
            cls.reader_key == reader_key,
            cls.message_key.in_(message_keys)
        ).all()
        read_keys_set = {r[0] for r in read_keys}
        return [mk for mk in message_keys if mk not in read_keys_set]

    @classmethod
    def mark_all_read_for_reader(cls, reader_key: str, message_keys: list[str]) -> int:
        """
        Mark multiple messages as read by a reader.
        Returns count of newly marked messages.
        """
        count = 0
        for message_key in message_keys:
            if not cls.has_read(message_key, reader_key):
                cls.mark_read(message_key, reader_key)
                count += 1
        return count
