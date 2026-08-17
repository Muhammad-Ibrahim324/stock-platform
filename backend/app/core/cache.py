"""A tiny async cache abstraction.

Financial data doesn't need a full caching framework: we need "don't
re-fetch the same historical bars on every page reload" (PRD §40). This
gives an in-memory TTL cache that works with zero setup, and transparently
switches to Redis when `REDIS_URL` is configured — same interface either way.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

from app.core.config import get_settings


class Cache(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...


class InMemoryTTLCache:
    """Process-local cache. Fine for a single dev/demo instance; a
    multi-worker production deployment should set REDIS_URL instead so
    all workers share one cache."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)


class RedisCache:
    """Thin wrapper around redis.asyncio, used only if REDIS_URL is set."""

    def __init__(self, url: str) -> None:
        import redis.asyncio as redis  # imported lazily so redis stays optional

        self._client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Any | None:
        import json

        raw = await self._client.get(key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        import json

        await self._client.set(key, json.dumps(value), ex=ttl_seconds)


_cache_instance: Cache | None = None


def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is None:
        settings = get_settings()
        if settings.redis_url:
            _cache_instance = RedisCache(settings.redis_url)
        else:
            _cache_instance = InMemoryTTLCache()
    return _cache_instance
