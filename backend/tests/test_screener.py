from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_screener_default_scan(client):
    resp = client.get("/api/screener")
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidates_scanned"] > 0
    assert body["candidates_available"] > body["candidates_scanned"] or body["candidates_scanned"] == body[
        "candidates_available"
    ]
    assert "note" in body and len(body["note"]) > 0


def test_screener_sector_filter_narrows_universe(client):
    resp = client.get("/api/screener", params={"sector": "Technology", "candidate_limit": 100})
    assert resp.status_code == 200
    body = resp.json()
    for r in body["results"]:
        assert r["sector"] == "Technology"


def test_screener_invalid_sector_returns_no_candidates(client):
    resp = client.get("/api/screener", params={"sector": "Not A Real Sector"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidates_available"] == 0
    assert body["results"] == []


def test_screener_price_filter_is_respected(client):
    resp = client.get("/api/screener", params={"candidate_limit": 40, "min_price": 0, "max_price": 1_000_000})
    assert resp.status_code == 200
    for r in resp.json()["results"]:
        assert r["price"] is not None
        assert 0 <= r["price"] <= 1_000_000


def test_screener_impossible_price_range_returns_empty(client):
    resp = client.get("/api/screener", params={"candidate_limit": 30, "min_price": 999_999_999})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_screener_candidate_limit_is_enforced(client):
    resp = client.get("/api/screener", params={"candidate_limit": 500})
    assert resp.status_code == 422  # exceeds MAX_CANDIDATE_LIMIT


def test_screener_result_limit_caps_output(client):
    resp = client.get("/api/screener", params={"candidate_limit": 60, "result_limit": 5})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) <= 5


def test_screener_flags_synthetic_data(client):
    resp = client.get("/api/screener", params={"candidate_limit": 10})
    body = resp.json()
    if body["results"]:
        assert body["is_synthetic"] is True  # synthetic provider is forced on in tests
