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
        json={"email": "investor@example.com", "password": "correcthorse123", "display_name": "Investor"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _add_holding(client, headers, ticker="AAPL", shares=10, cost=100.0, purchase_date="2024-01-15"):
    return client.post(
        "/api/portfolio/holdings",
        json={"ticker": ticker, "shares": shares, "cost_basis_per_share": cost, "purchase_date": purchase_date},
        headers=headers,
    )


def test_portfolio_requires_auth(client):
    resp = client.get("/api/portfolio/holdings")
    assert resp.status_code == 401


def test_analytics_with_no_holdings(client, auth_headers):
    resp = client.get("/api/portfolio/analytics", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["holdings"] == []
    assert body["total_current_value"] == 0.0
    assert body["risk"] is None


def test_add_holding(client, auth_headers):
    resp = _add_holding(client, auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["shares"] == 10
    assert body["cost_basis_per_share"] == 100.0


def test_add_holding_rejects_zero_shares(client, auth_headers):
    resp = _add_holding(client, auth_headers, shares=0)
    assert resp.status_code == 422


def test_add_holding_rejects_negative_cost_basis(client, auth_headers):
    resp = _add_holding(client, auth_headers, cost=-5)
    assert resp.status_code == 422


def test_update_holding(client, auth_headers):
    holding_id = _add_holding(client, auth_headers).json()["id"]
    resp = client.put(f"/api/portfolio/holdings/{holding_id}", json={"shares": 25}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["shares"] == 25
    # Untouched fields survive a partial update.
    assert resp.json()["cost_basis_per_share"] == 100.0


def test_update_nonexistent_holding_404(client, auth_headers):
    resp = client.put("/api/portfolio/holdings/does-not-exist", json={"shares": 1}, headers=auth_headers)
    assert resp.status_code == 404


def test_delete_holding(client, auth_headers):
    holding_id = _add_holding(client, auth_headers).json()["id"]
    resp = client.delete(f"/api/portfolio/holdings/{holding_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/api/portfolio/holdings", headers=auth_headers).json() == []


def test_users_cannot_modify_each_others_holdings(client):
    token_a = client.post(
        "/api/auth/signup", json={"email": "a2@example.com", "password": "correcthorse123", "display_name": "A"}
    ).json()["access_token"]
    token_b = client.post(
        "/api/auth/signup", json={"email": "b2@example.com", "password": "correcthorse123", "display_name": "B"}
    ).json()["access_token"]

    holding_id = _add_holding(client, {"Authorization": f"Bearer {token_a}"}).json()["id"]

    resp = client.delete(f"/api/portfolio/holdings/{holding_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404  # not "403 forbidden" — user B shouldn't even learn it exists


def test_analytics_gain_loss_math_is_exact(client, auth_headers):
    # Synthetic provider prices are seeded/deterministic per ticker, so we
    # can't predict the exact current price here — but cost-basis math is
    # independent of the live price and must be exact regardless.
    _add_holding(client, auth_headers, ticker="AAPL", shares=10, cost=50.0)
    resp = client.get("/api/portfolio/analytics", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["holdings"]) == 1
    h = body["holdings"][0]
    assert h["cost_basis_total"] == 500.0  # 10 * 50
    if h["current_value"] is not None:
        expected_gain_loss = h["current_value"] - 500.0
        assert abs(h["gain_loss"] - expected_gain_loss) < 1e-6
        expected_pct = expected_gain_loss / 500.0 * 100
        assert abs(h["gain_loss_pct"] - expected_pct) < 1e-6


def test_analytics_allocation_sums_to_one(client, auth_headers):
    _add_holding(client, auth_headers, ticker="AAPL", shares=10, cost=100.0)
    _add_holding(client, auth_headers, ticker="MSFT", shares=5, cost=200.0)
    resp = client.get("/api/portfolio/analytics", headers=auth_headers)
    body = resp.json()
    total_weight = sum(body["allocation_by_ticker"].values())
    assert abs(total_weight - 1.0) < 1e-6


def test_analytics_includes_risk_note_disclosure(client, auth_headers):
    _add_holding(client, auth_headers, ticker="AAPL", shares=10, cost=100.0)
    resp = client.get("/api/portfolio/analytics", headers=auth_headers)
    body = resp.json()
    assert "risk_note" in body
    assert len(body["risk_note"]) > 0
    if body["risk"] is not None:
        # The disclosure must actually say this is hypothetical, not realized history.
        assert "hypothetical" in body["risk_note"].lower()


def test_analytics_multiple_lots_same_ticker_aggregate_correctly(client, auth_headers):
    _add_holding(client, auth_headers, ticker="AAPL", shares=10, cost=100.0, purchase_date="2024-01-01")
    _add_holding(client, auth_headers, ticker="AAPL", shares=5, cost=150.0, purchase_date="2024-06-01")
    resp = client.get("/api/portfolio/analytics", headers=auth_headers)
    body = resp.json()
    assert len(body["holdings"]) == 2  # each lot shown separately
    assert body["total_cost_basis"] == 10 * 100.0 + 5 * 150.0
    # Both lots roll into a single AAPL allocation bucket.
    assert set(body["allocation_by_ticker"].keys()) == {"AAPL"}
