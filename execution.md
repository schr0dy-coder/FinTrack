# FinTrack Execution Plan

## 1. Execution Strategy

The project should be developed as a four-week engineering project.

The objective is not to maximize feature count. The objective is to produce a **complete, clean, testable, documented Python application** that can be demonstrated and defended.

Development order:

```text
Requirements
   ↓
Architecture
   ↓
Project Scaffold
   ↓
Database + Models
   ↓
Authentication
   ↓
Transaction APIs
   ↓
Risk Engine
   ↓
ML Pipeline
   ↓
Alerts
   ↓
Dashboard
   ↓
Testing
   ↓
Docker
   ↓
Documentation
   ↓
Demo + Report
```

---

## 2. Before Coding

Create:

- `requirements.md`
- `architecture.md`
- `execution.md`
- `README.md`
- Git repository
- issue/task list

Define:

- scope;
- users;
- database entities;
- API endpoints;
- risk rules;
- ML approach;
- acceptance criteria.

Do not begin by generating random files and wiring them together later.

---

## 3. Recommended Development Environment

### Software

- Python 3.12+
- Git
- Docker Desktop
- PostgreSQL 16+ if running locally outside Docker
- VS Code/PyCharm or equivalent
- Postman/Insomnia optional

### Python packages

Core:

```text
fastapi
uvicorn
pydantic
pydantic-settings
sqlalchemy
psycopg
alembic
python-jose
passlib / pwdlib
```

Data/ML:

```text
pandas
numpy
scikit-learn
joblib
```

Dashboard:

```text
streamlit
plotly
```

Testing/quality:

```text
pytest
pytest-asyncio
httpx
ruff
mypy
```

Exact versions should be pinned after the environment is tested.

---

## 4. Repository Initialization

Create the repository:

```bash
mkdir fintrack
cd fintrack
git init
```

Create the Python environment:

```bash
python -m venv .venv
```

Activate it according to your operating system.

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip
```

Install dependencies from the project's dependency file.

Create the initial commit only after the scaffold is coherent.

Example:

```bash
git add .
git commit -m "chore: initialize project structure"
```

---

## 5. Environment Configuration

Create:

```text
.env
.env.example
```

Example:

```text
DATABASE_URL=postgresql+psycopg://fintrack:password@localhost:5432/fintrack
JWT_SECRET_KEY=replace-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development
LOG_LEVEL=INFO
HIGH_AMOUNT_THRESHOLD=50000
RAPID_TRANSACTION_WINDOW_SECONDS=120
RAPID_TRANSACTION_COUNT=5
RISK_HIGH_THRESHOLD=60
RISK_CRITICAL_THRESHOLD=80
ML_MODEL_PATH=models/artifacts/isolation_forest.joblib
```

`.env` must not be committed.

`.env.example` may be committed with fake/example values.

---

# WEEK 1: Foundation and Backend

## Day 1: Requirements and Architecture

Tasks:

- finalize requirements;
- finalize architecture;
- create repository;
- create folder structure;
- create README;
- create `.gitignore`;
- configure Python tooling.

Deliverable:

A runnable empty FastAPI application with `/health`.

---

## Day 2: Database

Implement:

- PostgreSQL connection;
- SQLAlchemy setup;
- Alembic;
- User model;
- Transaction model;
- RiskAssessment model;
- Alert model.

Define:

- primary keys;
- foreign keys;
- constraints;
- timestamps;
- indexes where justified.

Run the first migration.

Test database connectivity.

---

## Day 3: Authentication

Implement:

- registration;
- password hashing;
- login;
- JWT generation;
- JWT validation;
- current-user dependency.

Tests:

- successful registration;
- duplicate email;
- invalid credentials;
- valid token;
- expired/invalid token.

---

## Day 4: Authorization

Implement:

- user role;
- admin role;
- role-checking dependency.

Test:

```text
USER -> own data       PASS
USER -> admin endpoint FAIL
ADMIN -> admin endpoint PASS
```

---

## Day 5: Transaction API

Implement:

```text
POST /api/v1/transactions
GET  /api/v1/transactions
GET  /api/v1/transactions/{id}
```

Implement:

- Pydantic schemas;
- validation;
- pagination;
- filters;
- repository methods;
- service layer.

---

## Day 6: Error Handling + Logging

Implement:

- application exceptions;
- safe API error responses;
- request logging;
- database error logging;
- validation handling.

Remove all unnecessary `print()` debugging.

---

## Day 7: Week 1 Review

Run:

```bash
pytest
ruff check .
ruff format --check .
```

Verify:

- authentication works;
- database works;
- transaction API works;
- unauthorized requests fail correctly;
- documentation opens.

Commit:

```bash
git commit -m "feat: implement authentication and transaction APIs"
```

---

# WEEK 2: Risk Engine and Alerts

## Day 8: Risk Rule Interface

Design a consistent rule result:

```text
triggered
score
code
reason
```

Implement:

- high amount rule;
- rapid transaction rule;
- new device rule.

Write unit tests before adding more rules where practical.

---

## Day 9: Behavioral Rules

Implement:

- location anomaly;
- failed-attempt pattern.

Avoid pretending to have sophisticated geospatial intelligence.

A prototype can use simple historical behavior:

```text
known user locations
vs.
new transaction location
```

Document the limitation.

---

## Day 10: Scoring

Implement:

```text
Rule Results
     ↓
Normalize
     ↓
Aggregate
     ↓
Final Rule Score
     ↓
Risk Level
```

Ensure score is bounded between 0 and 100.

Test boundary values:

```text
29 -> LOW
30 -> MEDIUM
59 -> MEDIUM
60 -> HIGH
79 -> HIGH
80 -> CRITICAL
100 -> CRITICAL
```

---

## Day 11: Alert Service

Implement:

```text
High/Critical transaction
        ↓
AlertService
        ↓
Alert record
```

Admin endpoints:

```text
GET  /api/v1/alerts
GET  /api/v1/alerts/{id}
POST /api/v1/alerts/{id}/resolve
```

---

## Day 12: Integration Testing

Test complete flows:

```text
Register
  ↓
Login
  ↓
Submit transaction
  ↓
Risk assessment
  ↓
Alert creation
  ↓
Admin review
  ↓
Alert resolution
```

---

## Day 13: Synthetic Dataset

Create a reproducible dataset generator.

Generate:

- normal users;
- normal transactions;
- anomalous transactions;
- varying amounts;
- locations;
- device IDs;
- transaction frequency.

Use a fixed random seed for reproducibility where appropriate.

Do not manually fabricate performance numbers.

---

## Day 14: Week 2 Review

Collect:

- API screenshots;
- Swagger/OpenAPI screenshots;
- database schema screenshot;
- sample risk results;
- alert screenshots.

Commit:

```bash
git commit -m "feat: add risk scoring and alert pipeline"
```

---

# WEEK 3: Machine Learning

## Day 15: Data Exploration

Use Pandas to inspect:

- missing values;
- distributions;
- transaction amounts;
- transaction frequency;
- class/anomaly distribution if labels exist.

Create exploratory charts where useful.

Record actual observations.

---

## Day 16: Feature Engineering

Create features such as:

```text
amount
hour
day_of_week
recent_transaction_count
amount_deviation
new_device
new_location
failed_attempt_count
```

Ensure feature generation is deterministic.

---

## Day 17: Model Training

Implement an Isolation Forest pipeline.

Suggested process:

```text
Load data
   ↓
Validate
   ↓
Preprocess
   ↓
Generate features
   ↓
Train model
   ↓
Evaluate/inspect
   ↓
Persist artifact
```

Save:

```text
model
feature configuration
model version
training metadata
```

Do not commit huge raw datasets or secrets.

---

## Day 18: ML Inference

Implement a reusable ML service.

Input:

```text
transaction context
```

Output:

```text
model_version
anomaly_score
normalized_ml_risk
```

Test:

- model exists;
- model loads;
- features match training;
- prediction succeeds;
- output is within expected range.

---

## Day 19: Combine Rules + ML

Integrate:

```text
Rule Risk
    +
ML Risk
    ↓
Final Risk
```

Document the weighting.

Do not claim the ML model is "accurate" unless you have measured appropriate metrics.

---

## Day 20: ML Evaluation

Depending on the dataset, report appropriate metrics.

If labeled:

- precision;
- recall;
- F1;
- confusion matrix;
- ROC-AUC where appropriate.

If using unsupervised anomaly detection without reliable labels:

- anomaly inspection;
- score distribution;
- synthetic scenario validation;
- qualitative analysis.

Be honest about the evaluation limitations.

---

## Day 21: Week 3 Review

Collect:

- dataset statistics;
- feature list;
- model training output;
- evaluation charts;
- sample predictions;
- risk comparisons.

Commit:

```bash
git commit -m "feat: add anomaly detection pipeline"
```

---

# WEEK 4: Dashboard, Quality, Deployment and Report

## Day 22: Dashboard Foundation

Create Streamlit application.

Pages:

```text
Overview
Transactions
Alerts
```

---

## Day 23: Analytics

Add:

- transaction volume;
- risk distribution;
- alert counts;
- time-series chart;
- filters.

Use Plotly.

Do not create decorative charts that do not communicate useful information.

---

## Day 24: Transaction Investigation

Create an analyst view showing:

```text
Transaction
     |
     +-- Amount
     +-- User
     +-- Merchant
     +-- Location
     +-- Device
     +-- Rule Reasons
     +-- ML Risk
     +-- Final Risk
     +-- Alert Status
```

This should be one of the strongest demo screens.

---

## Day 25: Docker

Create:

- `Dockerfile`;
- `docker-compose.yml`.

Services:

```text
api
database
dashboard
```

Verify that a clean machine can start the project using documented commands.

---

## Day 26: Quality Pass

Run:

```bash
pytest
ruff check .
ruff format .
```

If using mypy:

```bash
mypy app
```

Fix:

- duplicated code;
- naming issues;
- dead code;
- unnecessary dependencies;
- bad exception handling;
- missing tests;
- unclear functions.

---

## Day 27: Security + Documentation

Check:

- no secrets in Git;
- `.env` ignored;
- `.env.example` present;
- admin authorization;
- password hashing;
- safe error responses;
- CORS;
- dependency versions;
- README setup.

Update:

- architecture;
- API examples;
- known limitations;
- future scope.

---

## Day 28: Final Demo + Report Material

Collect:

1. Login screenshot.
2. Dashboard overview.
3. Transaction list.
4. Suspicious transaction.
5. Risk explanation.
6. Alert dashboard.
7. Alert resolution.
8. API documentation.
9. Database schema.
10. Architecture diagram.
11. ML feature/process diagram.
12. Test results.
13. Docker execution.
14. GitHub repository.

Create a final demo flow:

```text
Login
 ↓
Submit normal transaction
 ↓
Show LOW risk
 ↓
Submit suspicious transaction
 ↓
Show triggered rules
 ↓
Show ML risk
 ↓
Show HIGH/CRITICAL result
 ↓
Open admin dashboard
 ↓
Review alert
 ↓
Resolve alert
```

This is far more convincing than clicking around randomly.

---

# 6. Git Workflow

Use meaningful commits.

Examples:

```text
chore: initialize project structure
feat: add database models
feat: implement JWT authentication
feat: add transaction APIs
feat: implement high amount risk rule
feat: implement rapid transaction rule
feat: add alert service
feat: add ML preprocessing pipeline
feat: integrate anomaly detector
feat: add admin dashboard
test: add risk engine test suite
test: add transaction API integration tests
docs: update architecture documentation
chore: add Docker configuration
fix: handle duplicate transaction edge case
```

Avoid:

```text
update
changes
final
final2
final_final
working
plswork
```

The Git history itself should look like an engineering project.

---

# 7. Branching

For a solo academic project, do not over-engineer Git.

Recommended:

```text
main
  |
  +-- feature/auth
  +-- feature/transactions
  +-- feature/risk-engine
  +-- feature/ml
  +-- feature/dashboard
```

Merge stable features into `main`.

For small changes, direct commits to a personal development branch are also acceptable.

---

# 8. Pull Request Checklist

Before merging a feature:

- [ ] Code works.
- [ ] Tests added.
- [ ] Existing tests pass.
- [ ] No secrets.
- [ ] No debug prints.
- [ ] Error cases handled.
- [ ] Naming is clear.
- [ ] Documentation updated.
- [ ] API behavior documented.
- [ ] No unnecessary dependencies.
- [ ] Formatting/linting passes.

---

# 9. Clean Code Checklist

Before final submission, inspect every module.

### Naming

Bad:

```python
x
tmp
data2
do_it()
```

Prefer:

```python
transaction
risk_score
transaction_history
calculate_risk_score()
```

### Functions

Avoid 200-line functions.

Prefer:

```text
validate_transaction()
calculate_rule_score()
generate_features()
predict_anomaly()
create_alert()
```

### Constants

Bad:

```python
if amount > 50000:
```

Prefer configuration:

```python
if amount > settings.high_amount_threshold:
```

### Comments

Don't comment obvious code.

Bad:

```python
# Add two numbers
total = a + b
```

Good comments explain:

- why a non-obvious decision exists;
- a domain limitation;
- an important trade-off.

### Exceptions

Never hide failures:

```python
try:
    ...
except Exception:
    pass
```

Handle expected exceptions explicitly and log unexpected failures.

---

# 10. Performance Measurement

Do not write claims such as:

> "The system handles 100,000 transactions per second"

unless you actually benchmarked it.

For a university project, realistic measurements include:

- API response latency under a defined test load;
- database query timing;
- model inference time;
- dataset processing time;
- test suite execution time.

Record:

```text
Test environment
Dataset size
Number of requests
Concurrency
Average latency
p95 latency
Error rate
```

Only publish measurements you can reproduce.

---

# 11. Demo Data Strategy

Use deterministic synthetic scenarios.

### Scenario A: Normal

```text
Amount: ₹750
Known device
Known location
Normal frequency
```

Expected:

```text
LOW
```

### Scenario B: High Amount

```text
Amount: ₹85,000
Known device
Known location
```

Expected:

```text
HIGH
```

### Scenario C: Rapid Activity

```text
6 transactions
within 2 minutes
```

Expected:

```text
HIGH/CRITICAL depending on scoring
```

### Scenario D: Multiple Signals

```text
High amount
+
New device
+
New location
+
Rapid transactions
```

Expected:

```text
CRITICAL
```

The exact result should come from the implemented scoring system, not from hard-coded demo output.

---

# 12. Final Validation

Run the complete project from a clean environment.

Example sequence:

```bash
docker compose up --build
```

Then verify:

```text
API health
Authentication
Database
Transaction creation
Risk assessment
Alert generation
Dashboard
Tests
```

If a fresh setup cannot reproduce the application, the project is not finished.

---

# 13. Report Evidence Collection

Maintain an evidence folder:

```text
docs/
└── report-assets/
    ├── 01-login.png
    ├── 02-api-docs.png
    ├── 03-database.png
    ├── 04-transaction.png
    ├── 05-risk-analysis.png
    ├── 06-alert.png
    ├── 07-dashboard.png
    ├── 08-ml-results.png
    ├── 09-tests.png
    └── 10-docker.png
```

Every screenshot should demonstrate a real feature.

Avoid screenshots of empty pages.

---

# 14. Internship Report Mapping

Map implementation work to report chapters:

| Report Section | Evidence |
|---|---|
| Introduction | Problem + objectives |
| Technologies | Python stack |
| System Analysis | Requirements |
| Architecture | Architecture diagram |
| Database Design | ER/schema diagram |
| Implementation | API + services |
| Risk Engine | Rule logic |
| ML | Feature pipeline + model |
| Dashboard | Screenshots |
| Testing | Test results |
| Results | Measured observations |
| Challenges | Actual implementation problems |
| Learning Outcomes | Python/API/DB/ML/testing |
| Future Scope | Streaming, model monitoring, etc. |

Do not invent challenges or results. Record what actually happened during implementation.

---

# 15. Viva Preparation

Be able to answer:

### Python

- Why Python?
- How did you structure the project?
- Why type hints?
- How does exception handling work?
- Why separate services and repositories?

### FastAPI

- Why FastAPI?
- What is Pydantic validation?
- How does dependency injection work?
- How is JWT authentication implemented?

### PostgreSQL

- Why PostgreSQL?
- What are foreign keys?
- Why indexes?
- How are transactions handled?

### Fraud Detection

- Why rules?
- How does the risk score work?
- Why combine rules and ML?
- How do you avoid arbitrary thresholds?

### Machine Learning

- Why Isolation Forest?
- What is an anomaly?
- How are features generated?
- How was the model evaluated?
- What are the limitations?

### Security

- Why hash passwords?
- Why JWT?
- Where are secrets stored?
- How is authorization enforced?

### Testing

- What is unit testing?
- What is integration testing?
- What did you test?
- What edge cases did you consider?

### Deployment

- Why Docker?
- What does Docker Compose provide?
- How does the API connect to PostgreSQL?

---

# 16. Final Definition of Done

The project is ready for submission only when:

```text
[ ] Requirements complete
[ ] Architecture documented
[ ] Clean repository structure
[ ] Authentication working
[ ] Authorization working
[ ] Transactions working
[ ] PostgreSQL working
[ ] Risk engine working
[ ] Alerts working
[ ] ML pipeline working
[ ] Dashboard working
[ ] Unit tests working
[ ] Integration/API tests working
[ ] Linting/formatting clean
[ ] Docker working
[ ] Environment documented
[ ] No secrets committed
[ ] README complete
[ ] API examples complete
[ ] Screenshots collected
[ ] Actual measurements recorded
[ ] Limitations documented
[ ] Future scope documented
[ ] Viva questions prepared
[ ] Internship report evidence collected
```

---

# 17. The Golden Rule

**Do not build features for screenshots. Build features that you can explain.**

A smaller system with:

- clean architecture;
- real tests;
- reproducible data;
- honest measurements;
- understandable algorithms;
- good documentation;

is substantially stronger academically and technically than a huge application whose internals you cannot defend.

The final project should tell one coherent story:

```text
Python
  ↓
API Engineering
  ↓
Data Processing
  ↓
Risk Analysis
  ↓
Machine Learning
  ↓
Database
  ↓
Dashboard
  ↓
Testing
  ↓
Deployment
```

That is the story the internship report should tell.
