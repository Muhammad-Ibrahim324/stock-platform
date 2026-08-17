"""Shared FastAPI dependencies."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import InvalidTokenError, decode_access_token
from app.data.service import DataService, get_data_service
from app.db.base import get_db
from app.db.models import User

__all__ = ["get_service", "rate_limiter", "get_db", "get_current_user", "get_current_user_optional"]

_bearer_scheme = HTTPBearer(auto_error=False)


def get_service() -> DataService:
    return get_data_service()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")
    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session.") from exc
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account no longer exists.")
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        return None
    return await db.get(User, user_id)


class _SlidingWindowRateLimiter:
    """Minimal per-IP rate limiter. Good enough for a single-instance
    demo deployment; a multi-instance production deployment should move
    this to Redis (same pattern as the cache) so limits are shared."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit_per_minute: int) -> bool:
        now = time.monotonic()
        window_start = now - 60
        hits = [t for t in self._hits[key] if t > window_start]
        hits.append(now)
        self._hits[key] = hits
        return len(hits) <= limit_per_minute


_limiter = _SlidingWindowRateLimiter()


async def rate_limiter(request: Request) -> None:
    settings = get_settings()
    client_key = request.client.host if request.client else "unknown"
    if not _limiter.check(client_key, settings.rate_limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
        )
