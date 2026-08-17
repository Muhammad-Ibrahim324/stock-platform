"""Centralized application settings.

Never hardcode secrets or provider keys anywhere else in the codebase —
everything provider- or deployment-specific belongs here, sourced from
the environment. See `.env.example` for every variable this reads.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_name: str = "Stock Market Research & Analytics Platform API"
    environment: str = "development"
    cors_allow_origins: list[str] = ["http://localhost:3000"]

    # --- Data provider ---
    primary_provider: str = "yfinance"  # yfinance | synthetic
    # If the primary provider fails (no network, rate limited, etc.), fall
    # back to synthetic demo data instead of erroring. Every response is
    # tagged is_synthetic=True when this path is taken. Set to False to
    # have the API return a clean error instead of ever serving demo data.
    enable_synthetic_fallback: bool = True

    # --- Database ---
    # SQLite by default (zero-config, file-based, fine for local dev/demo).
    # Point this at Postgres in production, e.g.
    # "postgresql+asyncpg://user:pass@host:5432/dbname" — every model here
    # is plain SQLAlchemy with no SQLite-specific types, so no code changes
    # are needed to switch, only this URL.
    database_url: str = "sqlite+aiosqlite:///./stock_platform.db"

    # --- Auth ---
    # MUST be overridden in any real deployment — this default only exists
    # so the app runs out of the box for local demo purposes.
    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- Caching ---
    redis_url: str | None = None  # if unset, falls back to in-memory cache
    cache_ttl_intraday_seconds: int = 60
    cache_ttl_daily_seconds: int = 3600 * 6
    cache_ttl_fundamentals_seconds: int = 3600 * 24

    # --- Risk model defaults ---
    default_risk_free_rate: float = 0.04  # annualized, used for Sharpe/Sortino

    # --- Rate limiting ---
    rate_limit_per_minute: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
