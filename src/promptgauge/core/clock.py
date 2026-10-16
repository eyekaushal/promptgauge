"""Timestamps for SQLite rows: one format everywhere so sorting by text equals sorting by time."""

from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Current time as an ISO 8601 string in UTC with second precision."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()
