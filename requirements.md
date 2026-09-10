# FinTrack: Financial Transaction Monitoring & Fraud Detection System

## 1. Document Control

| Field | Value |
|---|---|
| Project | FinTrack |
| Type | Python backend + data analytics + fraud detection |
| Primary Language | Python 3.12+ |
| Backend | FastAPI |
| Database | PostgreSQL |
| Analytics / ML | Pandas, NumPy, scikit-learn |
| Dashboard | Streamlit + Plotly |
| Authentication | JWT |
| Testing | Pytest |
| Containerization | Docker / Docker Compose |
| Status | Implementation Specification |
| Target Duration | 4 weeks |

> **Academic integrity note:** This document specifies a self-directed project suitable for an internship portfolio/report. It should not be described as a CodSoft-assigned project unless CodSoft actually assigned it.

---

## 2. Purpose

FinTrack is a prototype financial transaction monitoring platform that accepts transaction events, validates and stores them, evaluates transaction risk using deterministic rules and a machine-learning anomaly detector, creates alerts for suspicious activity, and exposes the resulting information through REST APIs and an administrative dashboard.

The system is intended to demonstrate practical Python engineering, API development, database design, data processing, machine learning, testing, security, and software engineering practices.

---

## 3. Problem Statement

Financial systems process large numbers of transactions where unusual behavior may indicate fraud, account compromise, automated abuse, or other risk. A simple transaction record does not provide enough context for an analyst to identify suspicious behavior efficiently.

FinTrack addresses this by:

1. accepting structured transactions;
2. validating transaction data;
3. calculating rule-based risk signals;
4. generating behavioral features;
5. applying an ML anomaly detector;
6. combining signals into a transparent risk score;
7. creating alerts;
8. allowing authorized users to review transactions and alerts;
9. presenting aggregate analytics through a dashboard.

This is a prototype and **not a production banking/fraud-prevention system**.

---

## 4. Goals

### Primary goals

- Build a clean, modular Python backend.
- Provide documented REST APIs.
- Persist transactions and risk assessments in PostgreSQL.
- Implement transparent rule-based risk detection.
- Implement an ML-based anomaly detection pipeline.
- Provide an analyst/admin dashboard.
- Provide automated tests.
- Containerize the application.
- Maintain reproducible setup and documentation.
- Produce meaningful metrics and screenshots for the internship report.

### Secondary goals

- Demonstrate separation of concerns.
- Demonstrate secure configuration management.
- Demonstrate structured logging and error handling.
- Demonstrate API validation and authentication.
- Demonstrate data preprocessing and model evaluation.

---

## 5. Non-Goals / Out of Scope

The following are intentionally excluded from the first version:

- Real bank/payment-gateway integration.
- Real customer financial data.
- Actual automated blocking of bank transactions.
- Real-money transfers.
- Regulatory compliance certification.
- Production-grade distributed deployment.
- Fully autonomous fraud decisions.
- Biometric authentication.
- Live CCTV/device surveillance.
- Mobile applications.
- High-frequency trading functionality.

The project should use synthetic or legally reusable datasets.

---

## 6. Users and Roles

### 6.1 Customer / Standard User

Can:

- register;
- authenticate;
- submit a transaction;
- view their own transactions;
- view the risk status of their own transactions where permitted.

Cannot:

- view other users' data;
- access admin endpoints;
- modify risk assessments.

### 6.2 Analyst / Admin

Can:

- view transactions;
- filter transactions;
- view risk assessments;
- view suspicious transactions;
- view alerts;
- resolve alerts;
- view aggregate dashboard statistics;
- trigger/retrain the ML model if this feature is enabled.

### 6.3 System

The system automatically:

- validates requests;
- stores transactions;
- calculates rule scores;
- generates features;
- obtains ML anomaly scores;
- calculates final risk;
- creates alerts;
- records relevant logs.

---

## 7. Functional Requirements

### FR-01: User Registration

The API shall allow a user to register using:

- name;
- email;
- password.

Requirements:

- email must be valid;
- email must be unique;
- password must not be stored in plaintext;
- password must be hashed using a modern password hashing algorithm.

### FR-02: Authentication

The API shall provide login functionality.

Successful authentication shall return a JWT access token.

Protected endpoints shall require a valid token.

### FR-03: Authorization

The system shall enforce role-based access control.

At minimum:

- `USER`
- `ADMIN`

Admin-only endpoints shall reject standard users.

### FR-04: Transaction Submission

Authenticated users shall be able to submit transactions containing:

- amount;
- merchant;
- location;
- device identifier;
- transaction timestamp;
- optional transaction category.

The server shall generate the transaction ID.

### FR-05: Transaction Validation

The system shall reject invalid transactions, including:

- non-positive amounts;
- malformed timestamps;
- missing mandatory fields;
- invalid field lengths;
- unsupported enum values.

Validation shall happen at the API boundary.

### FR-06: Transaction Persistence

Valid transactions shall be stored in PostgreSQL.

Transactions shall contain creation metadata and timestamps.

### FR-07: Transaction Retrieval

Users shall be able to retrieve their permitted transactions.

Admins shall be able to retrieve and filter all transactions.

Supported filters should include:

- date range;
- risk level;
- transaction status;
- minimum/maximum amount;
- location;
- merchant.

Pagination shall be used for collection endpoints.

### FR-08: Rule-Based Risk Engine

The system shall evaluate deterministic risk rules.

Initial rules:

| Rule | Example Trigger | Score |
|---|---|---:|
| High Amount | Amount > configured threshold | +25 |
| Rapid Transactions | Multiple transactions in a short interval | +20 |
| New Device | Device not previously associated with user | +15 |
| Location Anomaly | Unusual location for user | +20 |
| Failed Attempt Pattern | Multiple recent failed attempts | +10 |

Thresholds must be configurable rather than hard-coded where practical.

### FR-09: Risk Classification

The system shall map the final risk score to a risk level.

Initial classification:

- `LOW`: 0–29
- `MEDIUM`: 30–59
- `HIGH`: 60–79
- `CRITICAL`: 80–100

The thresholds should be configurable.

### FR-10: Feature Engineering

The ML pipeline shall derive features such as:

- transaction amount;
- transaction frequency;
- amount deviation from user's historical behavior;
- time-of-day;
- location novelty;
- device novelty;
- recent transaction count;
- recent failed transaction count.

### FR-11: ML Anomaly Detection

The first ML implementation shall use an anomaly-detection approach such as Isolation Forest.

Requirements:

- preprocessing must be reproducible;
- feature selection must be documented;
- training and inference code must be separated;
- the trained artifact must be versioned;
- the model must not receive raw sensitive information unnecessarily.

### FR-12: Risk Score Combination

The system shall combine deterministic and ML signals.

Example conceptual formula:

`Final Risk = Rule Score Contribution + ML Risk Contribution`

The exact weighting must be documented and configurable.

The final score must be normalized to 0–100.

### FR-13: Alert Generation

The system shall create an alert when a transaction crosses a configured risk threshold.

An alert should contain:

- alert ID;
- transaction ID;
- severity;
- reason(s);
- risk score;
- creation timestamp;
- resolution status.

### FR-14: Alert Review

Admins shall be able to:

- list alerts;
- filter alerts;
- inspect alert details;
- mark an alert as resolved;
- add a resolution note.

### FR-15: Dashboard

The dashboard shall display:

- total transactions;
- suspicious transactions;
- fraud/anomaly rate;
- transaction volume over time;
- risk-level distribution;
- alerts by severity;
- top suspicious locations/merchants where appropriate.

### FR-16: Health Check

The backend shall expose a health endpoint.

Example:

`GET /health`

It should report application availability and, where practical, database connectivity.

### FR-17: API Documentation

FastAPI's generated OpenAPI documentation shall be available in development.

API request/response schemas must be documented.

---

## 8. API Requirements

Suggested API structure:

```text
/api/v1/auth/register
/api/v1/auth/login

/api/v1/transactions
/api/v1/transactions/{transaction_id}

/api/v1/risk/{transaction_id}

/api/v1/alerts
/api/v1/alerts/{alert_id}
/api/v1/alerts/{alert_id}/resolve

/api/v1/admin/statistics
/api/v1/admin/model/status

/health
```

### API standards

- JSON request/response bodies.
- Correct HTTP status codes.
- Consistent error response format.
- Input validation through Pydantic.
- Pagination for collection endpoints.
- Authentication on protected endpoints.
- No sensitive information in error messages.

---

## 9. Data Requirements

### User

Required fields:

- `id`
- `name`
- `email`
- `password_hash`
- `role`
- `created_at`
- `updated_at`

### Transaction

Required fields:

- `id`
- `user_id`
- `amount`
- `merchant`
- `location`
- `device_id`
- `timestamp`
- `status`
- `created_at`

### Risk Assessment

Required fields:

- `id`
- `transaction_id`
- `rule_score`
- `ml_score`
- `final_score`
- `risk_level`
- `reasons`
- `model_version`
- `created_at`

### Alert

Required fields:

- `id`
- `transaction_id`
- `severity`
- `status`
- `reason`
- `resolution_note`
- `created_at`
- `resolved_at`

Database constraints and foreign keys must preserve referential integrity.

---

## 10. Security Requirements

- Passwords must never be stored as plaintext.
- JWT secrets must come from environment configuration.
- Secrets must never be committed to Git.
- `.env` must be included in `.gitignore`.
- API input must be validated.
- Protected endpoints must enforce authentication.
- Admin endpoints must enforce authorization.
- SQL queries must use ORM/query parameters rather than string concatenation.
- Logs must not contain passwords, JWTs, or unnecessary sensitive information.
- CORS must be explicitly configured.
- Production deployment must use HTTPS.
- Development secrets must not be reused in production.

---

## 11. Non-Functional Requirements

### NFR-01: Maintainability

Code shall be modular and organized by responsibility.

### NFR-02: Readability

Use:

- meaningful names;
- small functions;
- clear module boundaries;
- type hints where practical;
- docstrings for public interfaces;
- PEP 8 formatting.

### NFR-03: Testability

Business logic must be testable independently from HTTP and database layers.

### NFR-04: Reliability

The API shall handle expected failures without exposing stack traces to clients.

### NFR-05: Performance

The system should support normal development-scale workloads efficiently.

Performance claims must be measured, not invented.

### NFR-06: Reproducibility

A new developer should be able to run the project using the documented setup instructions.

### NFR-07: Observability

Important events and errors should be logged using structured/consistent application logging.

---

## 12. Code Quality Rules

The project shall follow these rules:

1. No business logic inside route handlers when it can live in a service.
2. No database credentials hard-coded in source code.
3. No duplicated validation logic.
4. No giant files containing unrelated responsibilities.
5. No `except Exception: pass`.
6. No unexplained magic numbers.
7. Use configuration objects/environment variables for thresholds.
8. Use type hints for service/repository interfaces where practical.
9. Keep functions focused on one responsibility.
10. Separate API schemas from database models.
11. Separate ML training from ML inference.
12. Write tests for important risk rules.
13. Use linting/formatting before commits.
14. Remove debugging prints before merging.
15. Keep README and API documentation synchronized with implementation.

---

## 13. Testing Requirements

Minimum testing layers:

### Unit tests

Test:

- risk rules;
- risk classification;
- feature engineering;
- utility functions;
- authentication helpers.

### Integration tests

Test:

- API + database;
- transaction creation;
- authentication;
- alert generation;
- protected endpoints.

### API tests

Test:

- valid requests;
- invalid requests;
- unauthorized requests;
- forbidden requests;
- missing resources;
- pagination/filtering.

### ML tests

Test:

- preprocessing output;
- feature consistency;
- model loading;
- prediction output shape/range;
- model artifact availability.

---

## 14. Logging and Error Handling

Use Python's `logging` framework or an equivalent structured logging approach.

Log:

- authentication events at an appropriate level;
- transaction processing events;
- risk assessment failures;
- model loading/training failures;
- unexpected application errors.

Do not log:

- plaintext passwords;
- JWT tokens;
- full secrets;
- unnecessary personal data.

API errors should use a consistent format, for example:

```json
{
  "detail": "Transaction amount must be greater than zero"
}
```

---

## 15. Configuration

Configuration should include:

```text
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
HIGH_AMOUNT_THRESHOLD
RAPID_TRANSACTION_WINDOW_SECONDS
RAPID_TRANSACTION_COUNT
RISK_HIGH_THRESHOLD
RISK_CRITICAL_THRESHOLD
ML_MODEL_PATH
ENVIRONMENT
LOG_LEVEL
```

Use a `.env.example` file for documentation.

Never commit actual secret values.

---

## 16. Dataset Requirements

Use synthetic or appropriately licensed data.

Dataset should contain enough examples for development and demonstration.

Potential fields:

```text
transaction_id
user_id
amount
merchant
category
location
device_id
timestamp
transaction_status
```

For supervised experiments, a `fraud_label` may be included if the dataset supports it.

For anomaly detection, the project may operate without a fraud label.

---

## 17. Acceptance Criteria

The project is considered complete when:

- [ ] Users can register and log in.
- [ ] JWT-protected APIs work.
- [ ] Transactions can be submitted and persisted.
- [ ] Transactions are validated.
- [ ] Rule-based risk scoring works.
- [ ] Risk levels are assigned.
- [ ] ML preprocessing and inference work.
- [ ] Alerts are generated for high-risk transactions.
- [ ] Admins can review alerts.
- [ ] Dashboard displays meaningful analytics.
- [ ] Unit tests pass.
- [ ] Integration/API tests pass.
- [ ] Docker setup works.
- [ ] Environment configuration is documented.
- [ ] README contains setup and usage instructions.
- [ ] No secrets are committed.
- [ ] Code is formatted/linted.
- [ ] Project architecture is documented.
- [ ] Screenshots and measured results are collected for the internship report.

---

## 18. Definition of Done

A feature is not "done" merely because it works locally.

A feature is done when:

1. implementation is complete;
2. relevant tests exist;
3. errors are handled;
4. configuration is externalized;
5. code is formatted;
6. documentation is updated;
7. the feature has been manually verified;
8. no known critical defect remains;
9. changes are committed with a meaningful Git message.

---

## 19. Deliverables

Final project should contain:

- source code;
- database migrations/schema;
- synthetic dataset or dataset-generation script;
- trained model artifact or reproducible training pipeline;
- automated tests;
- Docker configuration;
- `.env.example`;
- README;
- API documentation;
- architecture diagram;
- screenshots;
- sample API requests;
- internship report;
- optional demo deployment.

---

## 20. Future Scope

Potential future extensions:

- streaming transaction ingestion;
- Kafka-based event pipeline;
- model monitoring;
- human feedback loop;
- explainable ML;
- feature store;
- Redis caching;
- distributed processing;
- notification service;
- more sophisticated behavioral profiling.

These should remain future scope unless actually implemented.
