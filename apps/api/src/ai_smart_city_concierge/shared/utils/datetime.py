"""
Shared Utilities - DateTime helpers
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def format_iso(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.isoformat()


def parse_iso(iso_string: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
