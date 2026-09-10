# 🛡️ FinTrack: Complete User & Operational Guide

Welcome to the **FinTrack Financial Transaction Monitoring & Fraud Detection Platform**. This guide explains how to access, navigate, test, and operate the platform.

---

## 📌 Quick Access Links & Portals

| Portal | URL | Purpose |
|---|---|---|
| **Streamlit Analyst Portal** | [http://localhost:8501](http://localhost:8501) | Main interactive web UI for monitoring, simulation, and alert triage |
| **FastAPI Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive REST API explorer and testing sandbox |
| **FastAPI ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Formal OpenAPI technical specification |
| **Backend Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Real-time database latency and ML model status |

---

## 🔑 Demo Accounts & Credentials

The database comes pre-seeded with accounts for immediate demonstration:

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Administrator / Analyst** | `admin@fintrack.com` | `Admin@123` | Full access to platform KPIs, alert triage queue, resolution workflows, and model retraining. |
| **Customer User** | `john@example.com` | `Password@123` | Submit transactions, view personal transaction logs and risk scores. |
| **Customer User** | `jane@example.com` | `Password@123` | Submit transactions, view personal transaction logs and risk scores. |

> **💡 Pro Tip:** The Streamlit dashboard includes a **1-Click "Quick Admin"** button in the left sidebar to sign in instantly.

---

## 🚀 How to Start the Services

### 1. Terminal 1: Start the Backend Server (Port 8000)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Terminal 2: Start the Dashboard (Port 8501)
```bash
streamlit run dashboard/app.py --server.port 8501
```

---

## 🧭 Step-by-Step Dashboard Workflows

```text
                  FinTrack Web Portal (http://localhost:8501)
                                       │
        ┌───────────────────┬──────────┴─────────┬───────────────────┐
        ▼                   ▼                    ▼                   ▼
   1. Overview       2. Transactions         3. Alerts        4. ML & System
(Executive KPIs)   (Inspector & Simulator) (Triage Queue)  (Model Diagnostics)
```

---

### Workflow 1: Executive Overview (`1_📊_Overview.py`)

1. Navigate to **Overview** from the left navigation menu.
2. **Review Top Metric Cards**:
   - **Total Volume**: Cumulative value of all processed transactions in INR.
   - **Total Transactions**: Total transaction count across all users.
   - **Suspicious Txns**: Number of transactions categorized as `HIGH` or `CRITICAL` risk with calculated anomaly rate %.
   - **Open Alerts**: Active alerts awaiting analyst review.
3. **Interactive Charts**:
   - **Transaction Volume Over Time**: Zoomable time series colored by status (`APPROVED`, `SUSPICIOUS`, `FLAGGED`).
   - **Risk Level Distribution**: Donut chart showing the proportion of `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL` transactions.
   - **Alert Volume by Severity**: Comparison of High vs Critical incidents.
   - **Hotspot Rankings**: Top suspicious merchants and geographical locations.

---

### Workflow 2: Transaction Inspector (`2_💳_Transactions.py`)

1. Navigate to **Transactions** $\rightarrow$ select the **🔍 Transaction Explorer & Inspector** tab.
2. **Filter & Search**:
   - Filter by **Risk Level** (`ALL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
   - Filter by **Status** (`APPROVED`, `SUSPICIOUS`, `FLAGGED`).
   - Search by **Merchant** name or set a **Minimum Amount**.
3. **Deep Signal Inspection**:
   - Select any transaction from the dropdown to open the **Deep Risk Breakdown**.
   - **Metadata Column**: Shows ID, Timestamp, User, Amount, Location, and Device ID.
   - **Risk Score Gauge**: Visual dial displaying the final combined score ($0–100$) and the 60/40 Rule vs ML weights.
   - **Signal Breakdown**: Shows exactly which deterministic rules triggered (e.g. `HIGH_AMOUNT`, `NEW_DEVICE`, `LOCATION_ANOMALY`) and the ML Anomaly detector score.

---

### Workflow 3: Live Fraud Simulator (`2_💳_Transactions.py`)

Test the real-time scoring engine by simulating live transaction scenarios:

1. In **Transactions**, switch to the **⚡ Live Transaction Simulator** tab.
2. Select a **Quick Scenario Preset** or enter custom details:
   - **Scenario A (Normal Grocery Spend)**:
     - Amount: ₹750.00 | Merchant: DMart | Location: Mumbai, IN | Device: `device-iphone-john`
     - **Expected Result**: 🟢 `LOW RISK` (Score ~ 4–10/100, Status: `APPROVED`).
   - **Scenario B (High Value Spike)**:
     - Amount: ₹85,000.00 | Merchant: Croma | Location: Mumbai, IN | Device: `device-iphone-john`
     - **Expected Result**: 🟠 `HIGH RISK` (Score ~ 60–75/100, Status: `SUSPICIOUS`).
   - **Scenario C (International Location Anomaly)**:
     - Amount: ₹45,000.00 | Merchant: Apple Store | Location: Dubai, AE | Device: `device-iphone-john`
     - **Expected Result**: 🟠 `HIGH RISK` (Score ~ 65–75/100, Status: `SUSPICIOUS`).
   - **Scenario D (Critical Coordinated Fraud Attempt)**:
     - Amount: ₹280,000.00 | Merchant: Rolex Boutique | Location: London, UK | Device: `device-emulator-botnet-404`
     - **Expected Result**: 🔴 `CRITICAL RISK` (Score ~ 85–95/100, Status: `FLAGGED`).
3. Click **🚀 Evaluate & Submit Transaction**.
4. Observe the immediate response: Rule score + ML Anomaly score calculation, assigned risk level, and automatic alert dispatch notification!

---

### Workflow 4: Alert Triage & Incident Resolution (`3_🚨_Alerts.py`)

1. Navigate to **Alerts** from the sidebar.
2. Filter by **Alert Status** (`OPEN` or `RESOLVED`) and **Severity** (`HIGH` or `CRITICAL`).
3. **Investigate Alert**:
   - Examine the severity badge, transaction ID, creation timestamp, and triggered reasons.
4. **Resolve Alert**:
   - Click **✍️ Investigate & Resolve Alert**.
   - Enter an **Analyst Investigation Note** (e.g., *"Customer contacted via registered phone; confirmed legitimate travel purchase."*).
   - Click **Mark Alert as Resolved**.
   - The alert updates in real-time to `RESOLVED` with a timestamp and resolution note.

---

### Workflow 5: Machine Learning Diagnostics & Retraining (`4_🤖_ML_and_System.py`)

1. Navigate to **ML & System** from the sidebar.
2. **Model Registry Tab**:
   - Inspect active model version (`v1.0.0`), algorithm (`Isolation Forest`), and sample count ($5,000+$).
   - Review the **8 Engineered Behavioral Features**: `amount`, `hour_of_day`, `day_of_week`, `user_tx_count_24h`, `amount_deviation`, `is_new_device`, `is_new_location`, `failed_attempts_count`.
   - **Hot Retraining**: Click **🚀 Retrain Isolation Forest Model** to execute the background pipeline and reload the model artifact into memory without stopping the server.
3. **System & Database Diagnostics Tab**:
   - View real-time database connection status and query latency in milliseconds.

---

## 💻 Programmatic API Usage (Curl Examples)

### 1. User Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@fintrack.com",
    "password": "Admin@123"
  }'
```

### 2. Submit a Transaction
```bash
curl -X POST "http://localhost:8000/api/v1/transactions" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 88500.00,
    "merchant": "Tanishq Diamonds",
    "category": "Luxury & Jewelry",
    "location": "Dubai, AE",
    "device_id": "device-unknown-android"
  }'
```

### 3. List Filtered Transactions
```bash
curl -X GET "http://localhost:8000/api/v1/transactions?risk_level=HIGH&limit=10" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### 4. Resolve an Alert
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/1/resolve" \
  -H "Authorization: Bearer <YOUR_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_note": "Verified customer identity via 2FA; customer authorized transaction."
  }'
```

---

## 🛠️ CLI & Maintenance Commands Cheat Sheet

| Task | Command |
|---|---|
| **Run Pytest Suite** | `pytest -v` |
| **Generate Synthetic Dataset** | `python scripts/generate_dataset.py` |
| **Train ML Model Artifact** | `python scripts/train_model.py` |
| **Reset / Seed Database** | `python scripts/seed_database.py` |
| **Run Complete Stack via Docker** | `docker compose up --build` |

---

## ❓ Frequently Asked Questions (FAQ)

### Q: Why did I see "Admin privileges required"?
**A:** Endpoints for alerts, platform statistics, and model retraining require an account with the `ADMIN` role. Click the **"Quick Admin"** or **"Switch to Admin"** button in the sidebar to switch to `admin@fintrack.com`.

### Q: How does FinTrack calculate the final risk score?
**A:** FinTrack uses a hybrid formula combining deterministic rule checks and machine learning:
$$\text{Final Score} = (0.60 \times \text{Rule Score}) + (0.40 \times \text{ML Anomaly Score})$$
- Scores from $0–29.9$ are classified as **LOW**.
- Scores from $30–59.9$ are classified as **MEDIUM**.
- Scores from $60–79.9$ are classified as **HIGH** (Triggers Alert).
- Scores from $80–100$ are classified as **CRITICAL** (Triggers Alert & Flags Transaction).
