# FinTrack: Financial Transaction Monitoring & Fraud Detection System

FinTrack is a Python-based transaction monitoring platform and fraud detection prototype. It combines explainable deterministic risk rules with an unsupervised **Isolation Forest** machine learning anomaly detector to assign risk scores to financial events, generate analyst alerts during request processing, and provide an analyst dashboard and REST API.

> **Note on Data & Scope:** This system is a self-directed engineering prototype developed for transaction risk profiling and fraud detection workflows. All datasets, user profiles, and financial transactions are synthetically generated and do not contain real customer or banking information.

---

## 1. Overview

FinTrack evaluates transactions as they are submitted through a synchronous ingestion and risk assessment pipeline. It addresses real-world fraud detection challenges—such as velocity abuse, geographic hopping, credential stuffing, and unusual high-value spending—using a hybrid architecture:

- **Deterministic Rules Engine:** 5 behavioral rules producing human-readable risk reasons.
- **Unsupervised Anomaly Detection:** An 8-feature Isolation Forest model identifying multidimensional anomalies without data leakage.
- **Hybrid Risk Scoring:** Weighted aggregation ($0.60 \times \text{Rule} + 0.40 \times \text{ML}$) mapped to 4 standard risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Analyst Triage Queue:** High and critical risk transactions automatically trigger alerts with resolution workflows.

---

## 2. Features

- **Layered Architecture:** Strict separation between API routes, business services, data repositories, and database models.
- **Explainable Behavioral Rules:** Independently testable rules with stable codes (`HIGH_AMOUNT`, `RAPID_TRANSACTIONS`, `NEW_DEVICE`, `LOCATION_ANOMALY`, `FAILED_ATTEMPT_PATTERN`).
- **Temporal Leakage-Free ML Pipeline:** Batch training and online inference share identical feature definitions calculated strictly from historical events prior to each transaction timestamp.
- **Role-Based Access Control (RBAC):** JWT authentication with `USER` and `ADMIN` scopes; non-admin users cannot access other users' data or administrative triage endpoints.
- **Database Migrations:** Schema lifecycle managed via **Alembic** migrations.
- **Streamlit Analyst Portal:** Interactive visualization of platform volume, risk distributions, live transaction investigation, and alert resolution.
- **Comprehensive Test Suite:** 37 automated unit, integration, and API tests.

---

## 3. Architecture

```text
[Streamlit Analyst Dashboard]
              │
         HTTP │ (REST API / JWT Auth)
              ▼
     [FastAPI API Layer]
              │
              ▼
    [Application Services]
      ├── AuthService
      ├── TransactionService
      ├── RiskService
      ├── AlertService
      └── AdminService
           │        │
           │        ▼
           │  [Hybrid Risk Engine]
           │   ├── 5 Deterministic Rules (+10 to +25 score)
           │   ├── Feature Extraction (8 behavioral dimensions)
           │   ├── Isolation Forest Anomaly Detection (0–100 score)
           │   └── Weighted Formula: (0.60 * Rule) + (0.40 * ML)
           │
           ▼
    [Repositories Layer]
      ├── UserRepository
      ├── TransactionRepository
      ├── RiskAssessmentRepository
      └── AlertRepository
           │
           ▼
    [SQLAlchemy ORM + Alembic]
           │
           ▼
 [PostgreSQL / SQLite Database]
```

### Risk Scoring Formula & Classification

$$\text{Normalized Rule Score} = \min\left(100.0, \sum \text{Triggered Rule Scores}\right)$$

$$\text{Final Risk Score} = (0.60 \times \text{Rule Score}) + (0.40 \times \text{ML Score})$$

| Risk Score Range | Tier Level | Action Triggered |
|---|---|---|
| **0.0 – 29.99** | `LOW` | Auto-approved |
| **30.0 – 59.99** | `MEDIUM` | Approved with monitoring |
| **60.0 – 79.99** | `HIGH` | Marked `SUSPICIOUS`, opens Analyst Alert |
| **80.0 – 100.0** | `CRITICAL` | Marked `FLAGGED`, opens Critical Alert |

---

## 4. Tech Stack

- **Backend Framework:** FastAPI 0.110+, Uvicorn
- **Database & Migrations:** PostgreSQL 16 / SQLite, SQLAlchemy 2.0+, Alembic 1.13+
- **Machine Learning & Data:** scikit-learn 1.4+, Pandas 2.2+, NumPy 1.26+, Joblib
- **Authentication & Security:** PyJWT, bcrypt (cost factor 12)
- **Analyst Dashboard:** Streamlit 1.32+, Plotly 5.20+
- **Testing & Quality:** Pytest 8.1+, Pytest-Asyncio
- **Deployment:** Docker, Docker Compose

---

## 5. Project Structure

```text
fintrack/
├── alembic/                         # Alembic database migration scripts
│   ├── env.py                       # Migration environment & metadata loader
│   └── versions/
│       └── 0001_initial_schema.py   # Initial database schema migration
├── app/
│   ├── main.py                      # FastAPI application entrypoint & middleware
│   ├── api/                         # Route controllers & dependency injection
│   │   ├── deps.py                  # JWT auth & RBAC dependencies
│   │   └── v1/                      # Endpoints: auth, transactions, alerts, admin
│   ├── core/                        # Configuration, security, and logging
│   ├── db/                          # Engine, session management, and Base
│   ├── models/                      # SQLAlchemy models (User, Transaction, Risk, Alert)
│   ├── schemas/                     # Pydantic validation models
│   ├── repositories/                # Data access layer
│   ├── services/                    # Business orchestration services
│   ├── risk_engine/                 # 5 deterministic rules, scoring, classifiers
│   └── ml/                          # Feature extraction, Isolation Forest trainer & inference
├── dashboard/                       # Streamlit multi-page analyst application
│   ├── app.py                       # Dashboard entrypoint & theme
│   └── pages/                       # Overview, Transactions, Alerts, ML & System
├── data/
│   └── synthetic/                   # Generated 5,000-transaction CSV dataset
├── models/
│   └── artifacts/                   # Serialized model (.joblib) & metadata JSON
├── scripts/
│   ├── generate_dataset.py          # Synthetic dataset generator CLI
│   ├── train_model.py               # Reproducible ML training pipeline
│   ├── evaluate_model.py            # Quantitative ML evaluation script
│   ├── benchmark.py                 # Performance & latency benchmark suite
│   └── seed_database.py             # Idempotent database seeder
├── docs/
│   ├── api-examples.md              # REST API request/response examples
│   ├── architecture.md              # Component interactions & security model
│   ├── ml_evaluation.md             # Quantitative ML evaluation report
│   └── benchmarks.md                # Measured API & ML latency report
├── tests/                           # 37 automated test cases
├── Dockerfile                       # Multi-stage Docker container build
├── docker-compose.yml               # PostgreSQL + API + Dashboard stack
├── .dockerignore                    # Build exclusion rules for Docker
├── .env.example                     # Sample configuration template
├── .gitignore                       # Git exclusion rules
├── pyproject.toml                   # Project metadata & tool configuration
├── requirements.txt                 # Dependencies
└── README.md
```

---

## 6. Setup & Installation

### Local Virtual Environment

```bash
# 1. Clone repository and navigate to folder
git clone https://github.com/username/fintrack.git
cd fintrack

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

---

## 7. Environment Variables

Configuration is loaded from `.env` via Pydantic Settings:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./fintrack.db` | Database connection string |
| `JWT_SECRET_KEY` | *(Set in `.env`)* | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT cryptographic algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration duration (24h) |
| `HIGH_AMOUNT_THRESHOLD` | `50000.0` | Rule threshold for high amount (₹) |
| `RAPID_TRANSACTION_COUNT` | `5` | Transaction count threshold in window |
| `RAPID_TRANSACTION_WINDOW_SECONDS` | `120` | Velocity window in seconds |
| `RULE_WEIGHT` | `0.60` | Weight for deterministic rule score |
| `ML_WEIGHT` | `0.40` | Weight for Isolation Forest score |
| `ENVIRONMENT` | `development` | Environment mode (`development` / `production`) |

---

## 8. Database Migrations

FinTrack uses Alembic for version-controlled database migrations:

```bash
# Apply migrations to bring database schema to latest version
alembic upgrade head

# Check current migration version
alembic current

# Create a new migration after model changes
alembic revision --autogenerate -m "describe schema change"
```

---

## 9. Dataset Generation

The dataset generator creates synthetic transactions with labeled normal and anomalous patterns:

```bash
python scripts/generate_dataset.py --rows 5000 --users 50 --anomaly-ratio 0.06 --seed 42
```

Supported anomaly categories:
1. `HIGH_AMOUNT_SPIKE`: Severe deviations from normal user spend.
2. `RAPID_BURST`: High-velocity bursts within short intervals.
3. `LOCATION_HOPPING`: Geographic anomalies from unfamiliar locations.
4. `UNRECOGNIZED_DEVICE`: Access through emulators or foreign devices.
5. `FAILED_ATTEMPT_STUFFING`: Repeated failed transactions before submission.

---

## 10. ML Training & Evaluation

Train the Isolation Forest model and generate evaluation metrics:

```bash
# Train Isolation Forest on 5,000 transactions
python scripts/train_model.py

# Run standalone evaluation against ground-truth labels
python scripts/evaluate_model.py
```

---

## 11. Running the API

Start the FastAPI application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Reference:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 12. Running the Dashboard

Seed the database with sample records and launch Streamlit:

```bash
# Seed initial admin and demo customer accounts (Idempotent)
python scripts/seed_database.py

# Launch Streamlit Analyst Portal
streamlit run dashboard/app.py --server.port 8501
```

- **Analyst Portal URL:** [http://localhost:8501](http://localhost:8501)

### Default Accounts

| Role | Email | Password |
|---|---|---|
| **Analyst / Admin** | `admin@fintrack.com` | `Admin@123` |
| **Customer User** | `john@example.com` | `Password@123` |
| **Customer User** | `jane@example.com` | `Password@123` |

---

## 13. Docker Deployment

Deploy containerized backend, PostgreSQL, and dashboard:

```bash
# Build and run containers
docker compose up --build

# Run database migrations inside container
docker compose exec api alembic upgrade head

# Explicitly seed database records
docker compose exec api python scripts/seed_database.py
```

---

## 14. Testing

Execute the automated test suite covering rules, math, ML inference, API routes, and RBAC:

```bash
pytest -v
```

```text
============================= test session starts =============================
tests/api/test_auth.py .........                                         [ 24%]
tests/api/test_transactions_api.py ........                              [ 45%]
tests/integration/test_alerts.py .                                       [ 48%]
tests/integration/test_transactions.py ..                                [ 54%]
tests/unit/test_features.py ....                                         [ 64%]
tests/unit/test_ml.py ...                                                [ 72%]
tests/unit/test_risk_rules.py .......                                    [ 91%]
tests/unit/test_scoring.py ...                                           [100%]
============================= 37 passed in 4.57s ==============================
```

---

## 15. Measured Results & Benchmarks

### Machine Learning Model Evaluation

Evaluated on 5,000 synthetic transactions (4,700 normal, 300 anomalous across 5 categories):

| Metric | Score | Note |
|---|---|---|
| **Precision** | **88.40%** | Low false alarm rate on normal transactions |
| **Recall** | **73.67%** | Standalone ML capture rate (supplemented by rules) |
| **F1-Score** | **0.8036** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.9758** | High separability across continuous anomaly scores |
| **Accuracy** | **97.84%** | Overall classification accuracy |

### Performance Benchmarks (Measured on Intel Core Ultra 7, 22 Cores)

| Component / Endpoint | Measured Average Latency | 95th Percentile (p95) |
|---|---|---|
| `POST /api/v1/transactions` (Full Pipeline) | **22.39 ms** | **24.94 ms** |
| `GET /api/v1/transactions` (Filtered List) | **4.72 ms** | **5.29 ms** |
| ML Feature Extraction (Single Vector) | **0.0018 ms** | **0.0023 ms** |
| ML Model Inference (Isolation Forest) | **6.65 ms** | **8.08 ms** |
| Historical Profiling Query (DB) | **2.39 ms** | **2.78 ms** |

---

## 16. Technical Limitations & Discussion

1. **Unsupervised Anomaly Assumptions:** Isolation Forest isolates points in feature space without class balance priors. Sub-burst velocity transactions with normal amounts can produce lower ML anomaly scores; these are caught by the deterministic `RapidTransactionsRule`.
2. **Synchronous Ingestion:** Risk scoring executes synchronously within the HTTP request cycle (~22ms). For higher enterprise throughput (10,000+ req/s), an asynchronous event pipeline (Kafka/Celery) would decouple ingestion from scoring.
3. **Synthetic Baseline:** Feature thresholds are calibrated on synthetic data distributions; production deployment requires retraining on actual historical payment traffic.

---

## 17. Future Scope

- **Asynchronous Event-Driven Pipeline:** Integrate Apache Kafka or Redis Streams for event-driven message queuing.
- **Graph Neural Network (GNN) Ring Detection:** Add network analysis for multi-hop money muling rings and shared device clusters.
- **Model Drift Monitoring:** Implement automated Kolmogorov-Smirnov statistical tests to detect feature drift over rolling windows.

---

## 18. Recommended Resume Entry

```text
FinTrack | Financial Transaction Monitoring & Fraud Detection Platform
Python, FastAPI, PostgreSQL, Alembic, Pandas, scikit-learn, Streamlit, Docker

• Built a layered financial transaction monitoring platform with FastAPI, PostgreSQL,
  Alembic migrations, JWT authentication, role-based access control, and repository architecture.

• Developed a hybrid risk engine combining 5 deterministic behavioral rules with an
  Isolation Forest anomaly detector across 8 temporal leakage-free transaction features.

• Implemented automated transaction profiling, risk scoring, alert generation, and
  analyst triage workflows via REST APIs and an interactive Streamlit dashboard.

• Evaluated on 5,000 synthetic transactions, achieving an F1-Score of 0.8036 and ROC-AUC of 0.9758,
  with end-to-end transaction processing latency averaging 22.39 ms (24.94 ms p95) across 37 automated tests.
```
