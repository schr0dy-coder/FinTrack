# FinTrack API Examples & Reference

## Base URL
```text
http://localhost:8000/api/v1
```

---

## 1. Authentication

### Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Connor",
    "email": "sarah@example.com",
    "password": "SecurePassword123"
  }'
```

**Response (201 Created):**
```json
{
  "id": 4,
  "name": "Sarah Connor",
  "email": "sarah@example.com",
  "role": "USER",
  "created_at": "2026-09-10T12:00:00Z",
  "updated_at": "2026-09-10T12:00:00Z"
}
```

### Login & Obtain JWT Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@fintrack.com",
    "password": "Admin@123"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "name": "FinTrack Administrator",
  "email": "admin@fintrack.com",
  "role": "ADMIN"
}
```

---

## 2. Transactions & Risk Evaluation

### Submit a Normal Transaction
```bash
curl -X POST "http://localhost:8000/api/v1/transactions" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 750.00,
    "merchant": "DMart Supermarket",
    "category": "Groceries",
    "location": "Mumbai, IN",
    "device_id": "device-iphone-john"
  }'
```

**Response (201 Created):**
```json
{
  "id": "7b8f9e21-0a4c-4e31-a8b2-5f6a7b8c9d0e",
  "user_id": 2,
  "amount": 750.0,
  "merchant": "DMart Supermarket",
  "category": "Groceries",
  "location": "Mumbai, IN",
  "device_id": "device-iphone-john",
  "timestamp": "2026-09-10T12:00:00Z",
  "status": "APPROVED",
  "created_at": "2026-09-10T12:00:00Z",
  "risk_assessment": {
    "rule_score": 0.0,
    "ml_score": 12.5,
    "final_score": 5.0,
    "risk_level": "LOW",
    "reasons": [],
    "model_version": "v1.0.0"
  }
}
```

### Submit a Suspicious / High-Risk Transaction
```bash
curl -X POST "http://localhost:8000/api/v1/transactions" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 95000.00,
    "merchant": "Rolex Boutique Dubai",
    "category": "Luxury & Jewelry",
    "location": "Dubai, AE",
    "device_id": "device-emulator-x86"
  }'
```

**Response (201 Created):**
```json
{
  "id": "e4a1b2c3-d4e5-4f6a-8b9c-0d1e2f3a4b5c",
  "user_id": 2,
  "amount": 95000.0,
  "merchant": "Rolex Boutique Dubai",
  "category": "Luxury & Jewelry",
  "location": "Dubai, AE",
  "device_id": "device-emulator-x86",
  "timestamp": "2026-09-10T12:00:00Z",
  "status": "SUSPICIOUS",
  "created_at": "2026-09-10T12:00:00Z",
  "risk_assessment": {
    "rule_score": 60.0,
    "ml_score": 88.0,
    "final_score": 71.2,
    "risk_level": "HIGH",
    "reasons": [
      {
        "code": "HIGH_AMOUNT",
        "triggered": true,
        "score": 25.0,
        "reason": "Transaction amount (₹95,000.00) exceeds threshold ₹50,000.00"
      },
      {
        "code": "LOCATION_ANOMALY",
        "triggered": true,
        "score": 20.0,
        "reason": "Transaction location 'Dubai, AE' is unusual based on user history"
      },
      {
        "code": "NEW_DEVICE",
        "triggered": true,
        "score": 15.0,
        "reason": "Transaction initiated from unrecognized device 'device-emulator-x86'"
      }
    ],
    "model_version": "v1.0.0"
  }
}
```

### List Transactions with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/transactions?risk_level=HIGH&limit=10" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 3. Alerts Management (Admin Only)

### List Active Open Alerts
```bash
curl -X GET "http://localhost:8000/api/v1/alerts?status=OPEN" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Resolve an Alert
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/1/resolve" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_note": "Customer contacted via registered phone; verified genuine high-value luxury gift purchase."
  }'
```

---

## 4. Admin Analytics & Model Controls

### Get System KPI Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/admin/statistics" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Trigger ML Model Retraining
```bash
curl -X POST "http://localhost:8000/api/v1/admin/model/retrain" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```
