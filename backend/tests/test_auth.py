from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _signup(client, email="jane@example.com", password="correcthorse123", name="Jane"):
    return client.post("/api/auth/signup", json={"email": email, "password": password, "display_name": name})


def test_signup_creates_account_and_returns_token(client):
    resp = _signup(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "jane@example.com"
    assert body["user"]["display_name"] == "Jane"
    # Password must never be echoed back.
    assert "password" not in body["user"]
    assert "hashed_password" not in body["user"]


def test_signup_rejects_duplicate_email(client):
    _signup(client)
    resp = _signup(client)
    assert resp.status_code == 409


def test_signup_rejects_short_password(client):
    resp = client.post(
        "/api/auth/signup", json={"email": "x@example.com", "password": "short", "display_name": "X"}
    )
    assert resp.status_code == 422


def test_signup_rejects_invalid_email(client):
    resp = client.post(
        "/api/auth/signup", json={"email": "not-an-email", "password": "correcthorse123", "display_name": "X"}
    )
    assert resp.status_code == 422


def test_login_succeeds_with_correct_credentials(client):
    _signup(client)
    resp = client.post("/api/auth/login", json={"email": "jane@example.com", "password": "correcthorse123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_fails_with_wrong_password(client):
    _signup(client)
    resp = client.post("/api/auth/login", json={"email": "jane@example.com", "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_fails_for_unknown_email(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    token = _signup(client).json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "jane@example.com"


def test_me_rejects_garbage_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_passwords_are_hashed_not_stored_in_plaintext():
    from app.core.security import hash_password, verify_password

    hashed = hash_password("correcthorse123")
    assert hashed != "correcthorse123"
    assert verify_password("correcthorse123", hashed) is True
    assert verify_password("wrong", hashed) is False
