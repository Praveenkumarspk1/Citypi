"""
Shared Utilities - Validation helpers
"""
import re
from typing import Any

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_REGEX.match(email))


def is_valid_uuid(value: str) -> bool:
    """Validate UUID format."""
    from uuid import UUID
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> list[str]:
    """Validate that required fields are present and not empty."""
    missing = []
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """sanitize string input by stripping and truncating."""
    return value.strip()[:max_length]
