"""API Tests for Authentication and Authorization."""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.security import create_access_token


def test_register_user_success(client: TestClient):
    payload = {
        "name": "Alice Tester",
        "email": "alice@example.com",
        "password": "Password123",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice Tester"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "USER"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_fails(client: TestClient):
    payload = {
        "name": "Bob Tester",
        "email": "bob@example.com",
        "password": "Password123",
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


def test_login_success_returns_jwt(client: TestClient):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"name": "Charlie", "email": "charlie@example.com", "password": "SecretPassword123"},
    )

    # Login
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "SecretPassword123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "charlie@example.com"


def test_login_invalid_credentials_fails(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


def test_get_me_protected_endpoint(client: TestClient, user_headers: dict):
    resp = client.get("/api/v1/auth/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user_test@fintrack.com"


def test_malformed_jwt_token_fails(client: TestClient):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert resp.status_code == 401


def test_expired_jwt_token_fails(client: TestClient):
    # Create expired token (-10 minutes)
    expired_token = create_access_token(subject=1, expires_delta=timedelta(minutes=-10))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_admin_endpoint_forbidden_for_standard_user(client: TestClient, user_headers: dict):
    resp = client.get("/api/v1/admin/statistics", headers=user_headers)
    assert resp.status_code == 403
    assert "Admin privileges required" in resp.json()["detail"]


def test_admin_endpoint_allowed_for_admin_user(client: TestClient, admin_headers: dict):
    resp = client.get("/api/v1/admin/statistics", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_transactions" in data
    assert "total_volume" in data
