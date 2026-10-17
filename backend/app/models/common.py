from datetime import datetime, timezone


def utcnow():
    """Naive UTC timestamp used as the default for every created_at column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
