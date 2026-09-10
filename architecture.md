# FinTrack Architecture

## 1. Architectural Overview

FinTrack follows a layered architecture with clear separation between:

```text
Client / Dashboard
       |
       v
API Layer
       |
       v
Application / Service Layer
       |
       +------------------+
       |                  |
       v                  v
Risk Engine          Repository Layer
       |                  |
       +--------+---------+
                |
                v
            PostgreSQL

ML Pipeline
    |
    +--> Training
    |
    +--> Model Artifact
    |
    +--> Inference
```

The central design principle is:

> **Routes handle HTTP concerns. Services handle business logic. Repositories handle persistence. ML modules handle model lifecycle.**

---

## 2. High-Level Components

### 2.1 API Layer

Responsible for:

- HTTP routing;
- authentication dependencies;
- request validation;
- response serialization;
- HTTP status codes;
- API-level exception translation.

Should not contain complex fraud/risk logic.

### 2.2 Authentication / Authorization

Responsible for:

- password hashing;
- credential verification;
- JWT creation;
- JWT validation;
- role checking.

### 2.3 Transaction Service

Responsible for:

- transaction creation;
- transaction retrieval;
- transaction-level business rules;
- coordinating persistence and risk assessment.

### 2.4 Risk Engine

Responsible for:

- deterministic risk rules;
- rule explanations;
- score calculation;
- risk classification.

The rule engine should be deterministic and independently testable.

### 2.5 Feature Engineering

Responsible for transforming raw transaction/history data into model features.

Example:

```text
Raw Transactions
       |
       v
Cleaning
       |
       v
Feature Extraction
       |
       v
Model Features
```

### 2.6 ML Service

Responsible for:

- loading model artifacts;
- validating model availability;
- generating predictions;
- exposing model metadata/version.

Training should not happen during every API request.

### 2.7 Alert Service

Responsible for:

- deciding whether an alert is required;
- creating alerts;
- assigning severity;
- recording reasons;
- resolving alerts.

### 2.8 Repository Layer

Responsible for database access.

Examples:

- `UserRepository`
- `TransactionRepository`
- `RiskAssessmentRepository`
- `AlertRepository`

Repositories should not contain HTTP-specific behavior.

### 2.9 Dashboard

Streamlit dashboard consumes the backend API or a controlled data-access layer.

Dashboard responsibilities:

- visualization;
- filters;
- summaries;
- analyst-facing views.

It should not duplicate fraud algorithms.

---

## 3. Recommended Repository Structure

```text
fintrack/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── transactions.py
│   │       ├── risk.py
│   │       ├── alerts.py
│   │       └── admin.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── risk.py
│   │   └── alert.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── transaction.py
│   │   ├── risk.py
│   │   └── alert.py
│   │
│   ├── repositories/
│   │   ├── users.py
│   │   ├── transactions.py
│   │   ├── risks.py
│   │   └── alerts.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── transaction_service.py
│   │   ├── risk_service.py
│   │   └── alert_service.py
│   │
│   ├── risk_engine/
│   │   ├── rules.py
│   │   ├── scoring.py
│   │   └── classifiers.py
│   │
│   ├── ml/
│   │   ├── preprocessing.py
│   │   ├── features.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── model_registry.py
│   │
│   └── utils/
│       ├── datetime.py
│       └── pagination.py
│
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── overview.py
│   │   ├── transactions.py
│   │   └── alerts.py
│   └── components/
│
├── tests/
│   ├── unit/
│   │   ├── test_risk_rules.py
│   │   ├── test_scoring.py
│   │   └── test_features.py
│   ├── integration/
│   │   ├── test_transactions.py
│   │   └── test_alerts.py
│   └── api/
│       ├── test_auth.py
│       └── test_transactions.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
│
├── models/
│   └── artifacts/
│
├── scripts/
│   ├── seed_database.py
│   └── generate_dataset.py
│
├── docs/
│   ├── architecture.md
│   └── api-examples.md
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## 4. Dependency Direction

Preferred dependency flow:

```text
API
 ↓
Services
 ↓
Repositories
 ↓
Database

Services
 ↓
Risk Engine

Services
 ↓
ML Service
```

Avoid:

```text
Database → API
Repository → FastAPI
Risk Engine → HTTP request objects
ML module → Streamlit UI
```

The lower-level business modules should not know about the web framework.

---

## 5. Transaction Processing Flow

```text
POST /api/v1/transactions
            |
            v
      Pydantic validation
            |
            v
      Authentication check
            |
            v
     Transaction Service
            |
            +---------------------+
            |                     |
            v                     v
     Transaction Repo       Feature Service
            |                     |
            |                     v
            |               ML Prediction
            |                     |
            +----------+----------+
                       |
                       v
                 Risk Engine
                       |
                       v
                 Final Score
                       |
              +--------+--------+
              |                 |
          Normal            Suspicious
              |                 |
              v                 v
          Persist         Create Alert
              |
              v
            Response
```

---

## 6. Risk Scoring Architecture

Risk scoring should remain explainable.

### Rule score

Each rule returns a structured result:

```python
RuleResult(
    triggered=True,
    score=25,
    code="HIGH_AMOUNT",
    reason="Transaction exceeds configured high-value threshold",
)
```

The scoring service aggregates these results.

### ML score

The ML service returns:

```text
model_version
anomaly_score
normalized_ml_risk
```

### Final score

A configurable weighted formula can be used:

```text
final_score =
    rule_weight * normalized_rule_score
    +
    ml_weight * normalized_ml_score
```

Example initial weights:

```text
rule_weight = 0.60
ml_weight   = 0.40
```

The weights are configuration, not constants hidden throughout the code.

---

## 7. Risk Rule Design

Rules should be independently testable.

Recommended interface:

```text
Transaction Context
        |
        v
+-------------------+
| HighAmountRule    |
+-------------------+
| RapidFrequencyRule|
+-------------------+
| NewDeviceRule     |
+-------------------+
| LocationRule      |
+-------------------+
| FailedAttemptRule |
+-------------------+
        |
        v
 List[RuleResult]
        |
        v
 Scoring Service
```

Adding a new rule should not require rewriting the entire risk engine.

---

## 8. ML Architecture

### Training

```text
Dataset
   |
   v
Data Validation
   |
   v
Preprocessing
   |
   v
Feature Engineering
   |
   v
Train Isolation Forest
   |
   v
Evaluate / Inspect
   |
   v
Persist Model Artifact
   |
   v
Record Model Version
```

### Inference

```text
Transaction + History
        |
        v
Feature Engineering
        |
        v
Loaded Model
        |
        v
Anomaly Score
        |
        v
Normalized ML Risk
```

### Important design rule

**Do not train the model inside a transaction API request.**

Training is an offline operation.

Inference is an online operation.

---

## 9. Database Architecture

Use PostgreSQL with foreign-key relationships.

```text
users
  |
  | 1:N
  v
transactions
  |
  | 1:1 / 1:N depending on implementation
  +--------> risk_assessments
  |
  +--------> alerts
```

Indexes should be considered for:

- `users.email`
- `transactions.user_id`
- `transactions.timestamp`
- `transactions.risk_level` if stored/queried
- `alerts.status`
- `alerts.created_at`

Do not add indexes without a query/use-case justification.

---

## 10. API Architecture

Version APIs:

```text
/api/v1/...
```

This makes future API changes easier to manage.

Suggested response patterns:

### Success

```json
{
  "data": {}
}
```

### Error

```json
{
  "detail": "Resource not found"
}
```

The exact response convention should remain consistent across endpoints.

---

## 11. Authentication Architecture

```text
User
 |
 | email + password
 v
Auth API
 |
 v
Password Hash Verification
 |
 v
JWT Access Token
 |
 v
Protected API
 |
 v
JWT Validation
 |
 v
Role Authorization
```

JWT should contain only necessary claims, such as:

- subject/user ID;
- role;
- expiry.

Do not put sensitive financial data into the token.

---

## 12. Dashboard Architecture

```text
              FastAPI
                 |
       +---------+---------+
       |                   |
       v                   v
Transactions API       Statistics API
       |                   |
       +---------+---------+
                 |
                 v
          Streamlit Dashboard
                 |
       +---------+---------+
       |         |         |
       v         v         v
   Overview  Transactions Alerts
       |
       v
     Plotly
```

The dashboard should consume stable APIs rather than reaching into internal database tables directly unless there is a deliberate architectural reason.

---

## 13. Error Handling Architecture

Use layered error handling:

```text
Database Exception
       |
       v
Repository / Service
       |
       v
Application Exception
       |
       v
FastAPI Exception Handler
       |
       v
Safe HTTP Error Response
```

Internal stack traces belong in logs, not client responses.

---

## 14. Configuration Architecture

```text
Environment Variables
        |
        v
Configuration Object
        |
        +--> Database
        +--> JWT
        +--> Risk Thresholds
        +--> ML Model
        +--> Logging
```

Configuration should be loaded once and injected/used consistently.

---

## 15. Code Quality Architecture

### Separation of concerns

Bad:

```python
@app.post("/transaction")
def create_transaction(...):
    # validate
    # query database
    # calculate fraud
    # train model
    # create alert
    # send email
    # return response
```

Preferred:

```text
Route
  -> TransactionService
      -> TransactionRepository
      -> FeatureService
      -> MLService
      -> RiskService
      -> AlertService
```

### Clean-code rules

- One responsibility per module/class/function.
- Prefer composition over unnecessary inheritance.
- Avoid global mutable state.
- Avoid circular imports.
- Keep framework-specific code at the edges.
- Use explicit interfaces/data contracts.
- Keep configuration centralized.
- Prefer deterministic functions for risk calculations.
- Keep ML preprocessing identical between training and inference.

---

## 16. Testing Architecture

```text
Unit Tests
   |
   +--> Rules
   +--> Scoring
   +--> Features
   +--> Utilities

Integration Tests
   |
   +--> Database
   +--> Services

API Tests
   |
   +--> Auth
   +--> Transactions
   +--> Alerts
```

The highest-value business logic should have the strongest test coverage.

Do not optimize for an arbitrary coverage percentage. Optimize for meaningful coverage.

---

## 17. Docker Architecture

Development environment:

```text
Docker Compose
   |
   +---- FastAPI container
   |
   +---- PostgreSQL container
   |
   +---- Streamlit container
```

The ML model artifact may be mounted or copied into the application image depending on deployment strategy.

---

## 18. Deployment Architecture

For a simple deployment:

```text
Internet
   |
   v
Reverse Proxy / Platform
   |
   v
FastAPI
   |
   v
PostgreSQL

Streamlit
   |
   v
FastAPI
```

Production deployment should use:

- HTTPS;
- environment-managed secrets;
- database backups;
- restricted database access;
- appropriate CORS settings;
- non-debug configuration.

---

## 19. Observability

Minimum:

- application logs;
- request/error logging;
- database error logging;
- model loading errors;
- health endpoint.

Useful future additions:

- Prometheus metrics;
- request latency;
- error rate;
- model prediction distribution;
- alert volume;
- database query monitoring.

---

## 20. Architectural Decisions

### Why FastAPI?

- Python-native;
- type-friendly;
- automatic OpenAPI documentation;
- Pydantic validation;
- suitable for REST APIs;
- clean dependency injection patterns.

### Why PostgreSQL?

- relational integrity;
- transactions;
- indexing;
- mature ecosystem;
- suitable for structured financial records.

### Why Streamlit?

- Python-centric;
- fast dashboard development;
- useful for analytics prototypes;
- avoids unnecessary frontend complexity.

### Why Isolation Forest?

- suitable for anomaly detection;
- does not require every training example to have a fraud label;
- practical for a prototype;
- straightforward to explain.

### Why separate rules and ML?

Rules are transparent and deterministic.

ML can detect patterns that explicit rules may miss.

Combining both creates a more explainable prototype than relying exclusively on an opaque prediction.

---

## 21. Architecture Principles

1. Keep business logic independent from HTTP.
2. Keep persistence independent from business rules.
3. Keep model training independent from inference.
4. Keep configuration outside source code.
5. Keep security concerns centralized.
6. Keep tests close to the behavior they validate.
7. Prefer simple architecture over unnecessary microservices.
8. Measure performance instead of making unsupported claims.
9. Document architectural trade-offs.
10. Build only what can be defended in a technical viva.
