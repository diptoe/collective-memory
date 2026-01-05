"""
Collective Memory Platform - Key Model

Maps human-readable four-word keys to UUIDs for backwards compatibility.
The four_words key is the primary key used throughout the system.
The uuid provides a fallback lookup for legacy references.
"""

from sqlalchemy import Column, String, DateTime
from api.models.base import BaseModel, db, get_now


class Key(BaseModel):
    """
    Key mapping table for human-readable keys.

    Primary key: four_words (e.g., "swift-bold-keen-lion")
    Also stores: uuid for backwards compatibility lookup

    This table ensures:
    1. All four-word keys are globally unique
    2. Legacy UUID lookups still work during migration
    3. Fast lookup by either key format
    """
    __tablename__ = 'keys'

    # Primary key: the human-readable four-word key
    four_words = Column(String(50), primary_key=True)

    # UUID for backwards compatibility (unique, indexed)
    uuid = Column(String(36), unique=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)

    def __repr__(self):
        return f"<Key {self.four_words} -> {self.uuid[:8]}...>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'four_words': self.four_words,
            'uuid': self.uuid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_by_any(cls, key: str) -> 'Key':
        """
        Look up a Key by either four_words or uuid.

        Args:
            key: Either a four-word key or UUID

        Returns:
            Key instance or None
        """
        # Try four_words first (primary key lookup is fast)
        result = cls.query.get(key)
        if result:
            return result

        # Try UUID lookup
        return cls.query.filter_by(uuid=key).first()

    @classmethod
    def exists(cls, four_words: str) -> bool:
        """Check if a four-word key already exists."""
        return cls.query.get(four_words) is not None

    @classmethod
    def create_key(cls) -> str:
        """
        Generate a new unique four-word key and register it.

        Returns:
            The new four-word key
        """
        import uuid as uuid_module
        from api.utils.readable_keys import generate_readable_key_with_check

        # Generate unique four-word key
        four_words = generate_readable_key_with_check(cls.exists)

        # Generate UUID for backwards compat
        new_uuid = str(uuid_module.uuid4())

        # Create and save key mapping
        key_record = cls(
            four_words=four_words,
            uuid=new_uuid
        )
        db.session.add(key_record)
        # Note: caller should commit

        return four_words

    @classmethod
    def resolve(cls, key: str) -> str:
        """
        Resolve any key format to four-word format.

        If given a UUID, looks up the corresponding four-word key.
        If given a four-word key, returns it as-is (after validation).

        Args:
            key: Either a four-word key or UUID

        Returns:
            The four-word key

        Raises:
            ValueError: If key not found
        """
        from api.utils.readable_keys import is_uuid, is_readable_key

        if is_readable_key(key):
            # Already a readable key - verify it exists
            if cls.query.get(key):
                return key
            raise ValueError(f"Key not found: {key}")

        if is_uuid(key):
            # Look up by UUID
            record = cls.query.filter_by(uuid=key).first()
            if record:
                return record.four_words
            raise ValueError(f"UUID not found: {key}")

        raise ValueError(f"Invalid key format: {key}")
