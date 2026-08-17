from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rate_limiter_blocks_after_the_configured_limit(client):
    limit = get_settings().rate_limit_per_minute
    statuses = [client.get("/api/stocks/AAPL/overview").status_code for _ in range(limit + 5)]
    assert 200 in statuses
    assert 429 in statuses, "expected at least one request to be rate-limited past the configured limit"
    # Once limited, the response should say so in a way a client can surface.
    last = client.get("/api/stocks/AAPL/overview")
    if last.status_code == 429:
        assert "rate limit" in last.json()["detail"].lower()
