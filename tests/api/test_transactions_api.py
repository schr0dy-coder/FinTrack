"""API Tests for Transactions Endpoints and Role Isolation."""

from fastapi.testclient import TestClient


def test_submit_valid_transaction(client: TestClient, user_headers: dict):
    payload = {
        "amount": 1499.0,
        "merchant": "Swiggy Food",
        "category": "Food & Dining",
        "location": "Mumbai, IN",
        "device_id": "device-iphone-1",
    }
    resp = client.post("/api/v1/transactions", json=payload, headers=user_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["amount"] == 1499.0
    assert data["merchant"] == "Swiggy Food"
    assert data["status"] == "APPROVED"
    assert "risk_assessment" in data
    assert data["risk_assessment"]["risk_level"] == "LOW"


def test_submit_invalid_negative_amount(client: TestClient, user_headers: dict):
    payload = {
        "amount": -500.0,
        "merchant": "Invalid Merchant",
        "location": "Mumbai, IN",
        "device_id": "device-1",
    }
    resp = client.post("/api/v1/transactions", json=payload, headers=user_headers)
    assert resp.status_code == 422


def test_submit_invalid_zero_amount(client: TestClient, user_headers: dict):
    payload = {
        "amount": 0.0,
        "merchant": "Invalid Merchant",
        "location": "Mumbai, IN",
        "device_id": "device-1",
    }
    resp = client.post("/api/v1/transactions", json=payload, headers=user_headers)
    assert resp.status_code == 422


def test_submit_missing_mandatory_fields(client: TestClient, user_headers: dict):
    payload = {
        "amount": 100.0,
        # missing merchant, location, device_id
    }
    resp = client.post("/api/v1/transactions", json=payload, headers=user_headers)
    assert resp.status_code == 422


def test_list_transactions_with_pagination(client: TestClient, user_headers: dict):
    # Submit 3 transactions
    for i in range(3):
        client.post(
            "/api/v1/transactions",
            json={
                "amount": 100.0 * (i + 1),
                "merchant": f"Store {i}",
                "location": "Mumbai, IN",
                "device_id": "device-1",
            },
            headers=user_headers,
        )

    resp = client.get("/api/v1/transactions?page=1&limit=2", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["total_pages"] == 2


def test_get_transaction_by_id_and_not_found(client: TestClient, user_headers: dict):
    create_resp = client.post(
        "/api/v1/transactions",
        json={
            "amount": 450.0,
            "merchant": "Starbucks",
            "location": "Mumbai, IN",
            "device_id": "device-1",
        },
        headers=user_headers,
    )
    tx_id = create_resp.json()["id"]

    # Valid ID
    get_resp = client.get(f"/api/v1/transactions/{tx_id}", headers=user_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tx_id
    assert get_resp.json()["merchant"] == "Starbucks"

    # Non-existent ID
    missing_resp = client.get("/api/v1/transactions/non-existent-uuid", headers=user_headers)
    assert missing_resp.status_code == 404


def test_cross_user_transaction_authorization(
    client: TestClient, user_headers: dict, admin_headers: dict
):
    # Register another regular user
    client.post(
        "/api/v1/auth/register",
        json={"name": "User Two", "email": "user2@test.com", "password": "Password123"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user2@test.com", "password": "Password123"},
    )
    user2_token = login_resp.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User 1 creates a transaction
    tx_resp = client.post(
        "/api/v1/transactions",
        json={
            "amount": 800.0,
            "merchant": "Uber",
            "location": "Mumbai, IN",
            "device_id": "phone-1",
        },
        headers=user_headers,
    )
    tx_id = tx_resp.json()["id"]

    # User 2 tries to access User 1's transaction -> should get 403 Forbidden
    forbidden_resp = client.get(f"/api/v1/transactions/{tx_id}", headers=user2_headers)
    assert forbidden_resp.status_code == 403

    # Admin accesses User 1's transaction -> should succeed (200 OK)
    admin_resp = client.get(f"/api/v1/transactions/{tx_id}", headers=admin_headers)
    assert admin_resp.status_code == 200
    assert admin_resp.json()["id"] == tx_id


def test_health_endpoint(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "ml_model" in data
