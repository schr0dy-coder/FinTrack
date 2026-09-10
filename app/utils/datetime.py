"""Datetime utilities."""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Return current UTC timezone-aware datetime."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safely parse an ISO format datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None
