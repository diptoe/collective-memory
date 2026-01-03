"""
Collective Memory Platform - Key Generation Utilities

Following Jai API patterns for UUID and timestamp generation.
"""
import uuid
from datetime import datetime, timezone


def get_key() -> str:
    """Generate a new UUID key."""
    return str(uuid.uuid4())


def get_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
