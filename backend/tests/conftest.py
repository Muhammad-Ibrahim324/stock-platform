from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio

# Set once, before any test module imports app.main (which reads settings
# at import time) — mirrors the pattern in test_api.py for provider config.
_TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "stock_platform_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB_PATH}")
os.environ.setdefault("PRIMARY_PROVIDER", "synthetic")
os.environ.setdefault("ENABLE_SYNTHETIC_FALLBACK", "true")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")


@pytest_asyncio.fixture(autouse=True)
async def _fresh_db():
    """Reset the cached engine/session-factory and give every test a clean
    schema (drop + recreate), so tests can't leak state into each other via
    the shared temp SQLite file — e.g. two tests both signing up the same
    email would otherwise collide."""
    import app.db.base as db_base

    db_base._engine = None
    db_base._session_factory = None
    engine = db_base.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.drop_all)
        await conn.run_sync(db_base.Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def _fresh_rate_limiter():
    """The in-process rate limiter (app/api/deps.py) is a module-level
    singleton keyed by client IP, which TestClient always reports the same
    for. Left unreset, a long test run legitimately trips it — every test
    after the ~60th request in the process would start seeing 429s that
    have nothing to do with what that individual test is checking. Reset
    it before every test so rate-limit *behavior* stays testable (see
    tests that specifically exercise it) without leaking across tests
    that aren't about rate limiting at all."""
    import app.api.deps as deps_module
    from collections import defaultdict

    deps_module._limiter._hits = defaultdict(list)
    yield


@pytest.fixture
def flat_prices() -> pd.Series:
    """A constant-price series: every derived metric has a known, exact answer."""
    dates = pd.bdate_range("2024-01-01", periods=60)
    return pd.Series([100.0] * 60, index=dates, name="close")


@pytest.fixture
def monotonic_up_prices() -> pd.Series:
    """Strictly increasing prices: max drawdown must be exactly zero."""
    dates = pd.bdate_range("2024-01-01", periods=100)
    values = np.linspace(100, 200, 100)
    return pd.Series(values, index=dates, name="close")


@pytest.fixture
def known_drawdown_prices() -> pd.Series:
    """Rises to 120, falls to 90 (a known -25% drawdown from the 120 peak),
    then partially recovers. Used to check exact drawdown math."""
    dates = pd.bdate_range("2024-01-01", periods=10)
    values = [100, 110, 120, 115, 100, 90, 95, 100, 105, 108]
    return pd.Series(values, index=dates, name="close")


@pytest.fixture
def random_walk_prices() -> pd.Series:
    """A realistic seeded random walk for statistical sanity checks
    (e.g. RSI/ATR staying in bounds) rather than exact-value checks."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2022-01-01", periods=500)
    daily_returns = rng.normal(0.0005, 0.015, len(dates))
    prices = 150 * np.exp(np.cumsum(daily_returns))
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def random_walk_ohlc(random_walk_prices: pd.Series) -> pd.DataFrame:
    """Derive a plausible OHLC frame from the close-only random walk,
    for indicators that need high/low (ATR, ADX)."""
    rng = np.random.default_rng(7)
    close = random_walk_prices
    spread = close * 0.01
    high = close + spread.abs() * rng.uniform(0.2, 1.0, len(close))
    low = close - spread.abs() * rng.uniform(0.2, 1.0, len(close))
    open_ = close.shift(1).fillna(close.iloc[0])
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


@pytest.fixture
def benchmark_prices() -> pd.Series:
    """A second seeded random walk, correlated-ish with random_walk_prices
    only by sharing market noise structure loosely (used for beta tests
    where we construct an exact relationship instead — see test_risk.py)."""
    rng = np.random.default_rng(99)
    dates = pd.bdate_range("2022-01-01", periods=500)
    daily_returns = rng.normal(0.0003, 0.011, len(dates))
    prices = 4000 * np.exp(np.cumsum(daily_returns))
    return pd.Series(prices, index=dates, name="close")
