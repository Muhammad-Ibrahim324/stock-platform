from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    resp = client.post(
        "/api/auth/signup",
        json={"email": "watcher@example.com", "password": "correcthorse123", "display_name": "Watcher"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_watchlist_requires_auth(client):
    resp = client.get("/api/watchlist")
    assert resp.status_code == 401


def test_watchlist_starts_empty(client, auth_headers):
    resp = client.get("/api/watchlist", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_to_watchlist(client, auth_headers):
    resp = client.post("/api/watchlist", json={"ticker": "aapl"}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["price"] is not None

    resp = client.get("/api/watchlist", headers=auth_headers)
    tickers = [item["ticker"] for item in resp.json()]
    assert tickers == ["AAPL"]


def test_add_duplicate_ticker_conflicts(client, auth_headers):
    client.post("/api/watchlist", json={"ticker": "AAPL"}, headers=auth_headers)
    resp = client.post("/api/watchlist", json={"ticker": "AAPL"}, headers=auth_headers)
    assert resp.status_code == 409


def test_add_invalid_ticker_rejected(client, auth_headers):
    resp = client.post("/api/watchlist", json={"ticker": "not-a-ticker!!"}, headers=auth_headers)
    assert resp.status_code == 400


def test_remove_from_watchlist(client, auth_headers):
    client.post("/api/watchlist", json={"ticker": "MSFT"}, headers=auth_headers)
    resp = client.delete("/api/watchlist/MSFT", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get("/api/watchlist", headers=auth_headers)
    assert resp.json() == []


def test_remove_nonexistent_ticker_returns_404(client, auth_headers):
    resp = client.delete("/api/watchlist/GOOGL", headers=auth_headers)
    assert resp.status_code == 404


def test_watchlists_are_isolated_per_user(client):
    token_a = client.post(
        "/api/auth/signup", json={"email": "a@example.com", "password": "correcthorse123", "display_name": "A"}
    ).json()["access_token"]
    token_b = client.post(
        "/api/auth/signup", json={"email": "b@example.com", "password": "correcthorse123", "display_name": "B"}
    ).json()["access_token"]

    client.post("/api/watchlist", json={"ticker": "AAPL"}, headers={"Authorization": f"Bearer {token_a}"})

    resp_a = client.get("/api/watchlist", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/api/watchlist", headers={"Authorization": f"Bearer {token_b}"})
    assert [i["ticker"] for i in resp_a.json()] == ["AAPL"]
    assert resp_b.json() == []
