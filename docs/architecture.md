# FinTrack Architecture Reference

## Component Interaction Overview

```text
[Streamlit Analyst Dashboard]
              │
         HTTP │ (REST API / JWT)
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
          │  [Risk Engine & ML]
          │   ├── Rules (HighAmount, Rapid, NewDevice, Location, FailedAttempt)
          │   ├── Feature Pipeline (8 behavioral features)
          │   ├── Isolation Forest Anomaly Inference
          │   └── Hybrid Weighted Combiner (60% Rules + 40% ML)
          │
          ▼
   [Repositories Layer]
     ├── UserRepository
     ├── TransactionRepository
     ├── RiskAssessmentRepository
     └── AlertRepository
          │
          ▼
   [SQLAlchemy ORM]
          │
          ▼
[PostgreSQL / SQLite Database]
```

## Security & Authorization Model

1. **Authentication**:
   - Industry-standard bcrypt password hashing (cost factor 12).
   - Stateless signed JWT access tokens with subject (`sub`) and role (`role`) claims.
2. **Role-Based Access Control**:
   - `USER`: Submit transactions, inspect personal transactions and permitted risk scores.
   - `ADMIN`: Platform-wide transaction filters, full alert triage & resolution, system statistics, and ML model retraining.
3. **Layered Exception Handling**:
   - Database and low-level exceptions are caught and sanitized to prevent leaking internal stack traces.
