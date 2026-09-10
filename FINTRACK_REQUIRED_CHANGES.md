# FinTrack - Required Changes Before Resume Submission

## Purpose

This document is the **final pre-resume engineering checklist** for FinTrack.

The project is already strong enough to become a resume project, but it should **not be presented as final yet**. The goal of this pass is not to add lots of features. The goal is to make the existing system technically consistent, reproducible, secure, measurable, and easy to defend in a technical interview or viva.

> **Important academic-integrity note:** Do not claim that CodSoft assigned FinTrack unless that actually happened. The CodSoft certificate establishes completion of the Python Programming internship. FinTrack should be described as an independent/self-directed project unless the university/company documentation explicitly supports another description.

---

# 1. Priority Overview

| Priority | Change | Why |
|---|---|---|
| P0 | Fix ML training/inference feature mismatch | Core technical correctness |
| P0 | Properly evaluate the ML model | Needed for credible ML claims |
| P0 | Remove `.env` / secrets from repository | Security |
| P0 | Remove generated database/cache artifacts | Repository cleanliness |
| P1 | Use Alembic migrations consistently | Architecture correctness |
| P1 | Fix Docker startup/seed behavior | Reproducibility |
| P1 | Replace "enterprise-grade" claims | Credibility |
| P1 | Add reproducible performance measurements | Resume evidence |
| P2 | Improve README/GitHub presentation | Recruiter usability |
| P2 | Final test/quality/security pass | Release confidence |
| P2 | Prepare resume bullets from measured results | Hiring signal |

---

# 2. P0 - Fix ML Feature Engineering Consistency

## Problem

The current project has a mismatch between some features used during model training and the corresponding concepts used during online inference.

For example, a feature described as a 24-hour transaction count must actually represent:

> Number of relevant transactions in the previous 24 hours

It must **not** become a user's total transaction count across the complete dataset.

There are also training heuristics for device-related behavior that should be aligned with the actual online feature definition.

## Required Design

Use a single feature-engineering implementation wherever possible.

Preferred flow:

```text
Historical Transactions
        |
        v
Sort by timestamp
        |
        v
For each transaction:
    use only information available BEFORE this transaction
        |
        v
Generate behavioral features
        |
        v
Model feature vector
```

### Required features

At minimum, make the definitions precise for:

- transaction amount
- transaction hour
- day of week
- transactions in previous 24 hours
- amount deviation from historical behavior
- new device
- new location
- recent failed transaction count

## Critical rule

Do not use future information to construct a feature for a transaction.

Example:

```text
Transaction at 14:00
```

must not use:

```text
transactions at 15:00
transactions at 16:00
```

to determine its 14:00 feature vector.

This prevents data leakage.

## Acceptance Criteria

- [ ] Training features and inference features have identical definitions.
- [ ] Historical features use only information available before the transaction.
- [ ] Feature column order is explicitly controlled.
- [ ] Feature preprocessing is reusable.
- [ ] Feature tests cover boundary cases.
- [ ] A sample transaction produces the same feature schema during training and inference.
- [ ] Model metadata records the feature version.

---

# 3. P0 - Rebuild the ML Training Pipeline

## Current issue

The repository contains a trained model whose metadata indicates a training sample count different from the current 5,000-record dataset.

This must be made reproducible.

## Required workflow

```text
Raw Dataset
    |
    v
Validate Dataset
    |
    v
Sort / Clean
    |
    v
Feature Engineering
    |
    v
Train Model
    |
    v
Evaluate
    |
    v
Save Artifact
    |
    v
Save Metadata
```

## Model metadata should contain

```json
{
  "model_type": "IsolationForest",
  "model_version": "v1",
  "training_sample_count": 5000,
  "feature_count": 8,
  "feature_names": [],
  "random_state": 42,
  "contamination": 0.01,
  "trained_at": "..."
}
```

The exact values must reflect the actual training run.

## Required acceptance criteria

- [ ] Delete/rebuild the stale model artifact.
- [ ] Train from the current dataset.
- [ ] Record the actual sample count.
- [ ] Record actual feature names.
- [ ] Record actual model parameters.
- [ ] Make training reproducible.
- [ ] Use a fixed random seed where appropriate.
- [ ] Document how to retrain the model.
- [ ] Verify that the API can load the newly generated model.

---

# 4. P0 - Properly Evaluate the ML Model

## Why

The synthetic dataset contains anomaly information that can be used for **evaluation**, even if Isolation Forest is trained in an unsupervised manner.

Do not train the model directly on the labels if the goal is to demonstrate unsupervised anomaly detection.

Instead:

```text
Training data
     |
     v
Isolation Forest
     |
     v
Predictions
     |
     v
Compare with synthetic anomaly labels
     |
     v
Evaluation metrics
```

## Recommended metrics

If the labels are suitable:

- Precision
- Recall
- F1-score
- Confusion matrix

Optionally:

- ROC-AUC
- Precision-Recall curve

Do not report accuracy alone for an imbalanced fraud/anomaly problem.

## Required experiment

Document:

```text
Dataset size
Normal records
Anomalous records
Feature count
Model parameters
Random seed
Threshold/contamination
Precision
Recall
F1
```

## Important

Do not manufacture a good result.

If the model performs poorly, document the result and explain why.

A realistic limitation is more credible than a suspiciously perfect model.

## Acceptance criteria

- [ ] Model predictions are generated on a held-out or clearly separated evaluation set where appropriate.
- [ ] Labels are used for evaluation rather than improperly leaking into training.
- [ ] Metrics are generated automatically.
- [ ] Confusion matrix is saved for the report.
- [ ] Results are recorded in documentation.
- [ ] Limitations are documented.

---

# 5. P0 - Remove Secrets from the Repository

## Current problem

The project contains a development JWT secret in Docker configuration and an `.env` file exists in the project directory.

Do not publish either as part of the final Git repository.

## Required configuration

Use:

```yaml
environment:
  JWT_SECRET_KEY: ${JWT_SECRET_KEY}
```

or an equivalent secure configuration.

## Required files

Commit:

```text
.env.example
```

Do not commit:

```text
.env
.env.local
```

## `.env.example`

Use fake/example values:

```text
DATABASE_URL=postgresql+psycopg://fintrack:password@localhost:5432/fintrack
JWT_SECRET_KEY=replace-with-a-random-development-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## If a secret has ever been pushed to Git

Even if it is only a development secret:

1. remove it from the current files;
2. rotate/recreate it;
3. if the repository was public, consider it compromised;
4. remove it from Git history if necessary.

## Acceptance criteria

- [ ] No real secret in source code.
- [ ] No `.env` committed.
- [ ] No secret in Docker Compose.
- [ ] `.gitignore` covers environment files.
- [ ] `.env.example` exists.
- [ ] README explains configuration.

---

# 6. P0 - Clean the Repository

The final GitHub repository should contain source and reproducible project assets, not local development debris.

## Remove

```text
.env
fintrack.db
__pycache__/
.pytest_cache/
*.pyc
generated ZIP files
temporary files
IDE-specific files
local logs
```

Also inspect:

```text
.vscode/
.idea/
```

Only commit IDE configuration if there is a deliberate reason.

## Recommended `.gitignore`

Include at least:

```gitignore
.venv/
venv/
env/

.env
.env.*
!.env.example

__pycache__/
*.py[cod]

.pytest_cache/
.mypy_cache/
.ruff_cache/

*.db
*.sqlite
*.sqlite3

*.log

.idea/
.vscode/

.DS_Store

dist/
build/
*.egg-info/

models/artifacts/*
!models/artifacts/.gitkeep
```

Whether model artifacts are committed should be a deliberate choice. If the model is small and required for the demo, it may be committed. If it is large, provide a reproducible training command or external artifact storage.

---

# 7. P1 - Use Alembic Properly

The architecture specifies migrations and Alembic is already part of the technology stack, so use it consistently.

## Desired structure

```text
alembic/
├── env.py
├── script.py.mako
└── versions/
    └── xxxx_initial_schema.py
```

## Workflow

Create migration:

```bash
alembic revision --autogenerate -m "create initial schema"
```

Apply:

```bash
alembic upgrade head
```

Check:

```bash
alembic current
```

## Important

Do not depend on:

```python
Base.metadata.create_all(...)
```

as the primary production/deployment schema mechanism.

It is acceptable for quick local experiments, but the final project should demonstrate migration-based database management.

## Acceptance criteria

- [ ] Initial migration exists.
- [ ] Fresh PostgreSQL database can be initialized through migrations.
- [ ] Application startup does not silently create an uncontrolled schema.
- [ ] README documents migration commands.

---

# 8. P1 - Fix Docker Startup

## Current concern

The API container currently combines database seeding and application startup.

That means a restart can cause seeding behavior to happen again.

## Preferred flow

```text
docker compose up
       |
       v
PostgreSQL starts
       |
       v
Migration
       |
       v
Optional explicit seed
       |
       v
FastAPI starts
```

## Better commands

Development:

```bash
docker compose up --build
```

Migration:

```bash
docker compose exec api alembic upgrade head
```

Seed only when wanted:

```bash
docker compose exec api python scripts/seed_database.py
```

## Acceptance criteria

- [ ] Restarting the API does not unexpectedly reseed the database.
- [ ] Migration is explicit/reproducible.
- [ ] Seeding is idempotent or clearly controlled.
- [ ] Docker Compose starts reliably from a clean environment.

---

# 9. P1 - Remove Overclaiming

Avoid:

```text
enterprise-grade
banking-grade
production-ready fraud detection
real-time banking fraud prevention
AI-powered fraud elimination
```

unless you have evidence and architecture that genuinely supports those claims.

## Recommended positioning

```text
Financial Transaction Monitoring & Fraud Detection System
```

or:

```text
Python-based Financial Transaction Monitoring & Fraud Detection Platform
```

README description:

> FinTrack is a production-inspired prototype for financial transaction monitoring that combines explainable rule-based risk scoring with Isolation Forest anomaly detection, REST APIs, PostgreSQL persistence, and an analyst dashboard.

This is technically ambitious without pretending to be a bank.

---

# 10. P1 - Clarify "Real-Time"

The current application can evaluate a transaction as it is submitted and generate an alert immediately within the request flow.

That is valid.

But avoid implying a distributed real-time event platform.

Use:

> Automated risk assessment and alert generation during transaction processing.

If later you add Kafka/background workers/WebSockets, then you can make stronger real-time claims.

---

# 11. P1 - Improve Risk Rule Architecture

Keep the current rule abstraction.

Each rule should return something equivalent to:

```python
RuleResult(
    triggered=True,
    score=25,
    code="HIGH_AMOUNT",
    reason="Transaction exceeds configured threshold",
)
```

## Rules

At minimum:

```text
HighAmountRule
RapidTransactionsRule
NewDeviceRule
LocationAnomalyRule
FailedAttemptRule
```

## Required improvements

- [ ] Each rule independently testable.
- [ ] Rule codes are stable.
- [ ] Rule reasons are human-readable.
- [ ] Thresholds come from configuration.
- [ ] Rules do not contain HTTP logic.
- [ ] Rules do not directly manipulate database sessions unless specifically designed to do so.
- [ ] Adding a new rule does not require rewriting the scoring service.

---

# 12. P1 - Make Risk Scoring Transparent

Document the formula.

For example:

```text
normalized_rule_score = rule_score / maximum_rule_score

final_score =
    0.60 * normalized_rule_score
    +
    0.40 * normalized_ml_score
```

Then:

```text
0–29    LOW
30–59   MEDIUM
60–79   HIGH
80–100  CRITICAL
```

The actual implementation must match the documentation.

## Test boundaries

```text
29  -> LOW
30  -> MEDIUM
59  -> MEDIUM
60  -> HIGH
79  -> HIGH
80  -> CRITICAL
100 -> CRITICAL
```

---

# 13. P1 - Add Stronger Edge-Case Tests

Existing testing is a strength. Expand it around the highest-risk business logic.

## Risk tests

Test:

- amount exactly at threshold;
- amount one unit below threshold;
- amount one unit above threshold;
- zero amount;
- negative amount;
- rapid transaction boundary;
- first transaction for a user;
- known device;
- new device;
- known location;
- new location;
- no transaction history;
- missing optional data.

## API tests

Test:

- duplicate registration;
- invalid password;
- expired JWT;
- malformed JWT;
- user accessing another user's transaction;
- user accessing admin endpoint;
- admin accessing admin endpoint;
- transaction not found;
- invalid pagination;
- invalid filters.

## ML tests

Test:

- missing model;
- corrupted model;
- wrong feature count;
- wrong feature names/order;
- NaN input;
- unexpected category;
- inference output range.

---

# 14. P1 - Add Data Validation

Before training or inference:

```text
Dataset
  ↓
Schema validation
  ↓
Missing-value checks
  ↓
Type checks
  ↓
Range checks
  ↓
Feature generation
```

Check:

- amount > 0;
- valid timestamp;
- required user ID;
- required device ID;
- supported categorical values;
- no unexpected nulls in required model features.

Fail clearly rather than silently repairing bad data.

---

# 15. P1 - Make Synthetic Data Generation Reproducible

The project should be able to regenerate its dataset.

Example:

```bash
python scripts/generate_dataset.py --rows 5000 --seed 42
```

Document:

- number of records;
- random seed;
- normal behavior generation;
- anomaly generation;
- anomaly types;
- anomaly ratio.

## Anomaly types

If already supported, document the actual types, such as:

```text
HIGH_VALUE
VELOCITY_SPIKE
NEW_DEVICE
LOCATION_ANOMALY
FAILED_ATTEMPT
```

Do not claim types that the generator does not actually produce.

---

# 16. P1 - Separate Training and Inference

Use:

```text
app/ml/train.py
app/ml/predict.py
```

Training:

```text
dataset -> features -> model -> artifact
```

Inference:

```text
transaction context -> features -> loaded model -> prediction
```

Never retrain the model inside:

```text
POST /transactions
```

---

# 17. P1 - Version the Model

Use a simple model version.

Example:

```text
isolation_forest_v1
```

Store:

```text
model_type
model_version
training_date
training_rows
feature_version
parameters
```

Risk assessments should record the model version used.

This allows future comparison between model versions.

---

# 18. P1 - Add Performance Benchmarks

Do not invent performance numbers.

Measure them.

## Useful benchmarks

### API

Measure:

```text
average latency
p95 latency
request count
error rate
```

### ML

Measure:

```text
feature generation time
model inference time
```

### Database

Measure important query timings.

## Benchmark documentation

Record:

```text
Environment:
CPU:
RAM:
Python:
Dataset:
Number of requests:
Concurrency:
Average latency:
p95 latency:
```

Only put measured numbers on the resume.

---

# 19. P2 - Improve API Documentation

FastAPI automatically provides OpenAPI documentation.

Ensure:

- endpoint summaries;
- response models;
- request examples;
- authentication requirements;
- useful error responses.

Add an API examples document:

```text
docs/api-examples.md
```

Include:

```text
Register
Login
Create transaction
List transactions
Get risk
List alerts
Resolve alert
Get statistics
```

---

# 20. P2 - Improve README

The README should have this structure:

```text
FinTrack
├── Overview
├── Features
├── Architecture
├── Tech Stack
├── Project Structure
├── Setup
├── Environment Variables
├── Database Migration
├── Dataset Generation
├── ML Training
├── Running the API
├── Running the Dashboard
├── Testing
├── API Documentation
├── Screenshots
├── Results
├── Limitations
└── Future Scope
```

Add a short architecture image near the top.

Add screenshots only after the UI is final.

---

# 21. P2 - Improve Dashboard

The dashboard does not need many more pages.

Prioritize quality.

## Overview

Show:

```text
Total Transactions
Suspicious Transactions
High/Critical Alerts
Anomaly Rate
```

## Transactions

Include:

- filters;
- pagination;
- risk level;
- transaction details.

## Alerts

Include:

- severity;
- risk score;
- reason;
- status;
- resolution action.

## Investigation view

Make the strongest screen show:

```text
Transaction
     ↓
Rule Signals
     ↓
ML Risk
     ↓
Final Score
     ↓
Alert
```

This makes the system easy to demonstrate.

---

# 22. P2 - Security Review

Verify:

- [ ] Password hashing.
- [ ] JWT expiration.
- [ ] Role-based authorization.
- [ ] No plaintext passwords.
- [ ] No secrets in Git.
- [ ] Safe error responses.
- [ ] CORS explicitly configured.
- [ ] SQL injection protected through ORM/parameterization.
- [ ] Sensitive information excluded from logs.
- [ ] Debug mode disabled for production.
- [ ] HTTPS documented for deployment.

Optional future work:

- rate limiting;
- refresh tokens;
- account lockout;
- audit logging;
- secret manager.

Do not implement all of these merely to increase feature count.

---

# 23. P2 - Logging Review

Use consistent application logging.

Log useful events:

```text
application startup
authentication failures
transaction processing
risk assessment failures
alert creation
model load failures
unexpected exceptions
```

Never log:

```text
password
JWT token
JWT secret
database password
unnecessary sensitive user data
```

---

# 24. P2 - Clean Architecture Review

Final dependency direction:

```text
API
 ↓
Services
 ↓
Repositories
 ↓
Database
```

and:

```text
Services
 ↓
Risk Engine
 ↓
ML Service
```

Avoid:

```text
Route → database implementation → risk algorithm → Streamlit
```

Routes should remain thin.

Bad:

```python
@app.post(...)
def create_transaction(...):
    # 150 lines of business logic
```

Preferred:

```python
@app.post(...)
def create_transaction(...):
    return transaction_service.create(...)
```

---

# 25. Code Quality Tooling

Use:

```bash
ruff check .
ruff format .
pytest
```

Optional:

```bash
mypy app
```

Recommended `pyproject.toml` configuration should centralize tool configuration rather than scattering configuration across many files.

## Before final submission

```bash
ruff check .
ruff format --check .
pytest
```

If using mypy:

```bash
mypy app
```

All should pass.

---

# 26. Dependency Hygiene

Review `requirements.txt`.

Remove packages that are not actually used.

Prefer pinned or bounded versions once the environment is stable.

Example principle:

```text
package>=minimum,<next-breaking-major
```

or use a modern dependency lock workflow if desired.

The important part is reproducibility.

---

# 27. Database Review

Verify:

- [ ] Foreign keys.
- [ ] Unique email constraint.
- [ ] Appropriate indexes.
- [ ] Correct numeric type for monetary amounts.
- [ ] UTC timestamps or an explicitly documented timezone strategy.
- [ ] Cascading behavior is intentional.
- [ ] Transactions are committed safely.
- [ ] Database sessions are closed correctly.

For monetary values, prefer an exact decimal/numeric representation rather than binary floating-point storage.

---

# 28. Transaction Processing Integrity

Risk assessment and transaction persistence should have a clearly defined consistency strategy.

At minimum:

```text
Create Transaction
       |
       v
Calculate Risk
       |
       v
Persist Risk Assessment
       |
       v
Create Alert if required
       |
       v
Commit
```

If a critical step fails, avoid leaving an incomplete database state.

Document the transaction boundary.

---

# 29. Data Privacy

Because this project models financial transactions:

- use synthetic data;
- do not use real bank/customer information;
- do not commit personal financial data;
- document that this is a prototype;
- avoid unnecessary personally identifiable information.

README should explicitly state:

> The repository uses synthetic/demo transaction data and is not intended for processing real customer financial information.

---

# 30. Final Repository Structure

Target something close to:

```text
fintrack/
├── app/
├── dashboard/
├── tests/
├── data/
│   ├── synthetic/
│   └── processed/
├── models/
│   └── artifacts/
├── scripts/
├── docs/
│   ├── architecture.md
│   ├── api-examples.md
│   └── report-assets/
├── alembic/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
```

---

# 31. Final Test Matrix

Before calling the project finished:

| Area | Test |
|---|---|
| Auth | Register |
| Auth | Login |
| Auth | Invalid credentials |
| Auth | Expired/invalid JWT |
| Authorization | User blocked from admin |
| Transactions | Create valid |
| Transactions | Reject invalid amount |
| Transactions | Retrieve own transaction |
| Transactions | Prevent unauthorized access |
| Risk | High amount |
| Risk | Rapid transactions |
| Risk | New device |
| Risk | Location anomaly |
| Risk | Failed attempts |
| Risk | Score boundaries |
| Alerts | Alert creation |
| Alerts | Alert filtering |
| Alerts | Alert resolution |
| ML | Model loads |
| ML | Feature schema |
| ML | Prediction |
| ML | Missing model |
| ML | Evaluation |
| Dashboard | Statistics |
| Dashboard | Transaction filters |
| Dashboard | Alert view |
| Database | Fresh migration |
| Docker | Clean startup |
| Docker | Restart |
| Quality | Ruff |
| Quality | Tests |

---

# 32. Final Release Checklist

## Repository

- [ ] No `.env`
- [ ] No secrets
- [ ] No local database
- [ ] No cache directories
- [ ] No temporary files
- [ ] No unnecessary IDE files
- [ ] README polished
- [ ] License added if appropriate

## Backend

- [ ] Authentication works
- [ ] Authorization works
- [ ] API validation works
- [ ] Error handling works
- [ ] Logging works
- [ ] Database migrations work
- [ ] Risk engine works

## ML

- [ ] Feature definitions consistent
- [ ] No temporal leakage
- [ ] Training reproducible
- [ ] Model artifact current
- [ ] Metadata accurate
- [ ] Evaluation complete
- [ ] Limitations documented

## Dashboard

- [ ] Overview works
- [ ] Transaction investigation works
- [ ] Alerts work
- [ ] Charts are meaningful
- [ ] No broken/empty states

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] ML tests pass
- [ ] Edge cases covered

## Deployment

- [ ] Docker build succeeds
- [ ] Docker Compose works
- [ ] PostgreSQL starts correctly
- [ ] Migrations work
- [ ] Seeding is explicit/idempotent
- [ ] Secrets are externalized

## Evidence

- [ ] Architecture diagram
- [ ] ER diagram
- [ ] API screenshot
- [ ] Dashboard screenshot
- [ ] Risk assessment screenshot
- [ ] Alert screenshot
- [ ] ML evaluation results
- [ ] Test results
- [ ] Performance benchmark

---

# 33. Resume Readiness Gate

Do **not** put a metric on the resume until it is measured.

Do **not** call something real-time unless the architecture supports the claim.

Do **not** call something enterprise-grade unless you can defend the claim.

Do **not** claim an ML accuracy/F1/recall number until it has been generated from an actual experiment.

Do **not** claim CodSoft assigned FinTrack unless that is documented.

Once the P0 items and the important P1 items are complete, the project is ready for a final resume review.

---

# 34. Target Resume Signal

After the fixes, the project should communicate these engineering capabilities:

```text
Python
    ↓
FastAPI
    ↓
REST API Design
    ↓
PostgreSQL
    ↓
Authentication / Authorization
    ↓
Risk Engine
    ↓
Data Processing
    ↓
Machine Learning
    ↓
Automated Testing
    ↓
Docker
    ↓
Analytics Dashboard
```

That is a much stronger story than simply saying:

> "Created a fraud detection app in Python."

---

# 35. Recommended Final Resume Entry

Do not copy this blindly. Replace every placeholder with an actual measured value after the final benchmark.

```text
FinTrack | Financial Transaction Monitoring & Fraud Detection
Python, FastAPI, PostgreSQL, Pandas, scikit-learn, Streamlit, Docker

• Built a layered financial transaction monitoring platform with FastAPI, PostgreSQL,
  JWT authentication, role-based authorization, and service/repository architecture.

• Developed a hybrid risk engine combining 5 explainable behavioral rules with
  Isolation Forest anomaly detection across [N] engineered transaction features.

• Implemented automated transaction profiling, risk scoring, alert generation,
  and analyst triage through REST APIs and an interactive Streamlit dashboard.

• Generated and evaluated [N]-record synthetic transaction data, achieving
  [actual metric] on [actual evaluation setup], with automated unit, integration,
  and API tests covering core transaction and risk workflows.
```

The final numbers must come from the finished implementation.

---

# 36. Stop Condition

Once these are complete:

```text
ML consistency
      +
ML evaluation
      +
security cleanup
      +
migration cleanup
      +
Docker cleanup
      +
repository cleanup
      +
real benchmarks
      +
tests
      +
README
      =
RESUME READY
```

**Do not turn this into a never-ending feature factory.**

At that point, freeze the feature set, tag a release such as:

```text
v1.0.0
```

and move to resume optimization.

The next improvement to your career will probably come from **applying to internships**, not from adding the 37th feature to FinTrack.
