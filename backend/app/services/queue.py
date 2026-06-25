from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _redis_client() -> Any | None:
    """Return a Redis client if REDIS_URL is configured, else None. Imported lazily so the app
    runs without redis installed/configured (local/dev uses the in-process fallback)."""
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        from redis import Redis

        return Redis.from_url(settings.redis_url)
    except Exception:
        return None


def redis_ready() -> bool:
    client = _redis_client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        return False


def enqueue_call_dispatch(attempt_id: int) -> bool:
    """Enqueue a call dispatch onto the durable RQ queue.

    Returns True if it was enqueued to Redis, False if Redis is not configured/available
    (so the caller can fall back to an in-process background task).
    """
    client = _redis_client()
    if client is None:
        return False
    try:
        from rq import Queue

        settings = get_settings()
        queue = Queue(settings.redis_queue_name, connection=client)
        # reference by dotted path so the RQ worker imports it independently
        queue.enqueue("app.services.calls.dispatch_call_attempt_job", attempt_id)
        return True
    except Exception:
        return False
