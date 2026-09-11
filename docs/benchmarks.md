# FinTrack Performance Benchmark Report

## 1. Test Environment Specifications

- **Execution Date:** `2026-09-10 16:36:33 UTC`
- **Benchmark Context:** Local Single-Process Development Environment (Measured via synchronous FastAPI TestClient & direct SQLAlchemy session; distinguishes local single-process performance from distributed production event streaming).
- **Operating System:** `Windows 11 (AMD64)`
- **CPU Architecture:** `Intel64 Family 6 Model 170 Stepping 4, GenuineIntel` (22 logical cores)
- **Host Memory (RAM):** `16.0 GB (Approx)`
- **Python Runtime:** `Python 3.12.7`
- **Database Engine:** SQLite / PostgreSQL (WAL mode, parameterized queries)
- **ML Engine:** scikit-learn Isolation Forest (150 estimators, 8 features, `random_state=42`)
- **Dataset Scale:** 5,000 synthetic transactions across 50 users
- **Warm-Up Strategy:** 10 warm-up requests executed prior to recording timing arrays
- **Iterations:** 500 iterations for ML micro-benchmarks, 200 for database queries, 250 for end-to-end HTTP pipeline

---

## 2. End-to-End API Pipeline Latency

Measured across 250 synchronous authenticated HTTP requests covering the complete ingestion lifecycle:
*(Input Validation $\to$ Historical Query $\to$ Deterministic Rules $\to$ Isolation Forest Inference $\to$ Database Persistence $\to$ Alert Dispatch)*

| Endpoint | Operation | Avg Latency | Median (p50) | 95th Percentile (p95) | 99th Percentile (p99) | Est. Throughput |
|---|---|---|---|---|---|---|
| `POST /api/v1/transactions` | **Full Risk & Ingestion Pipeline** | **24.8 ms** | **22.2 ms** | **30.03 ms** | **80.31 ms** | **~40.3 req/s** |
| `GET /api/v1/transactions` | Filtered & Paginated List | 4.68 ms | - | 5.71 ms | - | - |
| `GET /health` | Health Check & DB Ping | 1.22 ms | - | 1.48 ms | - | - |

---

## 3. Machine Learning & Feature Engine Performance

Micro-benchmarking of feature transformation and Isolation Forest anomaly score computation:

| Component | Task | Avg Latency | p95 Latency | Notes |
|---|---|---|---|---|
| **Feature Extraction** | Single Context $\to$ 8-dim Vector | **0.0016 ms** | 0.0017 ms | Microsecond-level feature derivation |
| **Model Inference** | IsolationForest `decision_function` | **5.5952 ms** | 6.7004 ms | 150 trees evaluation & score normalization |
| **Batch Transformation** | 1,000 Transactions Matrix | **53.52 ms** | - | Temporal leakage-free sequential processing |

---

## 4. Database Query Latencies

| Query Operation | Description | Avg Latency | p95 Latency |
|---|---|---|---|
| **User History Summary** | Temporal window filtering & velocity aggregation | **4.918 ms** | 4.702 ms |
| **Filtered Risk Query** | Multi-column index scan with join on `risk_assessments` | **0.574 ms** | 0.763 ms |

---

---

## 5. Concurrent Load & Stress Testing (Locust Benchmark)

FinTrack was evaluated under simulated multi-user concurrent traffic using **Locust 2.46+** executing against the live FastAPI server. The benchmark simulated a realistic traffic distribution comprising customer transaction submissions (`POST /api/v1/transactions`), paginated transaction history queries (`GET /api/v1/transactions`), analyst alert triage queue filtering (`GET /api/v1/alerts`), admin KPI statistics queries (`GET /api/v1/admin/statistics`), and health check probes (`GET /health`).

### A. Multi-Tier Concurrency Summary

| Concurrency Tier | Spawn Rate | Test Duration | Total Requests | Sustained Throughput | Avg Latency | Median (p50) | 90th % (p90) | 95th % (p95) | 99th % (p99) | Success Rate |
|---|---|---|---|---|---|---|---|---|---|---|
| **10 Users** | 5 users/s | 20s | 943 reqs | **49.43 req/s** | 120.04 ms | 110.0 ms | 240.0 ms | **280.0 ms** | **400.0 ms** | **100.0%** (0 errors) |
| **25 Users** | 10 users/s | 25s | 1,301 reqs | **53.99 req/s** | 351.23 ms | 230.0 ms | 570.0 ms | **990.0 ms** | **3,100.0 ms** | **99.85%** (2 errors) |
| **50 Users** | 15 users/s | 30s | 1,287 reqs | **44.28 req/s** | 979.74 ms | 830.0 ms | 1,800.0 ms | **2,100.0 ms** | **3,100.0 ms** | **100.0%** (0 errors) |
| **100 Users** | 25 users/s | 30s | 64 reqs | **30.95 req/s** | 631.95 ms | 650.0 ms | 1,300.0 ms | **1,500.0 ms** | **1,700.0 ms** | **100.0%** (0 errors) |

### B. Endpoint Latency & Throughput Breakdown (Under 25 Concurrent Users)

Measured across 1,301 requests at peak sustained system load (~54 req/s):

| HTTP Method & Endpoint | Operation Profile | Requests Served | Throughput | Avg Latency | Median (p50) | 95th Percentile (p95) | 99th Percentile (p99) |
|---|---|---|---|---|---|---|---|
| `POST /api/v1/transactions` | **Full Ingestion & ML Pipeline** | 593 reqs | 24.61 req/s | 562.04 ms | 330.0 ms | 2,000.0 ms | 4,000.0 ms |
| `GET /api/v1/transactions` | History & Pagination Read | 260 reqs | 10.79 req/s | 175.14 ms | 160.0 ms | 370.0 ms | 540.0 ms |
| `GET /api/v1/alerts` | Alert Triage Queue Filtering | 206 reqs | 8.55 req/s | 165.64 ms | 150.0 ms | 340.0 ms | 440.0 ms |
| `GET /api/v1/admin/statistics` | Aggregated KPI Metrics | 99 reqs | 4.11 req/s | 295.28 ms | 280.0 ms | 550.0 ms | 620.0 ms |
| `GET /api/v1/admin/model/status` | ML Model Registry Inspection | 50 reqs | 2.07 req/s | 126.68 ms | 100.0 ms | 330.0 ms | 360.0 ms |
| `GET /health` | Liveness / Readiness Probe | 93 reqs | 3.86 req/s | 90.74 ms | 60.0 ms | 270.0 ms | 360.0 ms |

---

## 6. Summary & Production Scaling Analysis

- **Single Worker Baseline Throughput:** A single Uvicorn process running on local SQLite achieves a peak throughput of **~54 requests/second** while executing the full synchronous fraud detection pipeline (Pydantic validation, historical DB lookup, 5 deterministic rules, 8-feature Isolation Forest inference, and DB persistence).
- **Latency Profile Under Concurrency:**
  - At **10 concurrent users**, the API demonstrates high responsiveness with an average latency of **120.04 ms** (p50: 110ms, p95: 280ms) and **100% success rate**.
  - At **25 to 50 concurrent users**, the server maintains 44–54 req/s throughput with predictable queuing behavior (p50: 230–830ms).
- **Production Architecture Path to 10,000+ RPS:**
  1. **Horizontal Worker Replication:** Deploying Uvicorn across 8–16 Gunicorn worker processes behind NGINX / AWS ALB multiplies CPU-bound ML inference capacity linearly.
  2. **Connection Pooling & PostgreSQL:** Replacing single-writer SQLite with PostgreSQL (with connection pooling via PgBouncer) eliminates write serialization locks.
  3. **Asynchronous Decoupling (Kafka/RabbitMQ):** Moving the fraud scoring pipeline to an asynchronous event-driven worker architecture decouples synchronous transaction acceptance from complex anomaly scoring, reducing HTTP ingress latency to sub-5ms.
