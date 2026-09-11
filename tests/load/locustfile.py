"""Locust Load and Stress Testing Suite for FinTrack.

Simulates concurrent user and analyst workloads against the FastAPI backend:
1. Customer User: Rapidly submits financial transactions through the complete risk assessment pipeline
   (Pydantic validation -> User DB History -> Deterministic Rules -> Isolation Forest Anomaly Scoring -> DB Persistence -> Alert Trigger)
   and queries historical transaction pages.
2. Analyst / Admin User: Monitors the alerts triage queue, queries system KPI statistics,
   and inspects transaction records.
3. Health Probes: Baseline service and DB connectivity checks.
"""

import os
import random
import sys
from locust import HttpUser, between, task, tag

# Ensure root directory is in sys.path so we can use create_access_token
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.security import create_access_token


MERCHANTS = [
    "Amazon India",
    "Flipkart",
    "Swiggy",
    "Zomato",
    "Croma Electronics",
    "Reliance Digital",
    "MakeMyTrip",
    "Uber India",
    "Apple Store",
    "Myntra",
    "BookMyShow",
    "Tata Neu",
]

CATEGORIES = [
    "Shopping",
    "Food & Dining",
    "Electronics",
    "Travel",
    "Entertainment",
    "Utilities",
]

LOCATIONS = [
    "Mumbai, IN",
    "Delhi, IN",
    "Bengaluru, IN",
    "Hyderabad, IN",
    "Pune, IN",
    "Chennai, IN",
    "Kolkata, IN",
    "London, UK",
    "New York, US",
]

DEVICES = [
    "device-iphone-12",
    "device-galaxy-s22",
    "device-pixel-7",
    "device-macbook-pro",
    "device-windows-dell",
    "device-unknown-emulator",
]

# Pre-generate tokens for simulated users to prevent bcrypt login storms
# from masking the real transactional risk engine & database latency under load
CUSTOMER_TOKENS = [
    create_access_token(subject=2, role="USER"),
    create_access_token(subject=3, role="USER"),
    create_access_token(subject=4, role="USER"),
]
ADMIN_TOKEN = create_access_token(subject=1, role="ADMIN")


class FinTrackCustomerUser(HttpUser):
    """Simulates real customer banking & payment activity."""

    weight = 4
    wait_time = between(0.02, 0.10)  # High throughput realistic think time

    def on_start(self):
        """Assign pre-authenticated user session token."""
        token = random.choice(CUSTOMER_TOKENS)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @tag("transaction", "pipeline")
    @task(7)
    def submit_transaction(self):
        """Submit financial transaction executing the complete synchronous risk assessment pipeline."""
        is_spike = random.random() < 0.08
        amount = (
            round(random.uniform(50000.0, 150000.0), 2)
            if is_spike
            else round(random.uniform(50.0, 8500.0), 2)
        )

        payload = {
            "amount": amount,
            "merchant": random.choice(MERCHANTS),
            "category": random.choice(CATEGORIES),
            "location": random.choice(LOCATIONS),
            "device_id": random.choice(DEVICES),
        }
        self.client.post(
            "/api/v1/transactions",
            json=payload,
            headers=self.headers,
            name="[API] POST /api/v1/transactions (Full Pipeline)",
        )

    @tag("query", "read")
    @task(3)
    def list_transactions(self):
        """Query paginated transaction history."""
        page = random.randint(1, 3)
        limit = random.choice([10, 20, 50])
        self.client.get(
            f"/api/v1/transactions?page={page}&limit={limit}",
            headers=self.headers,
            name="[API] GET /api/v1/transactions",
        )

    @tag("health")
    @task(1)
    def health_check(self):
        """Probe service health."""
        self.client.get("/health", name="[Probe] GET /health")


class FinTrackAnalystUser(HttpUser):
    """Simulates fraud investigation analyst activities."""

    weight = 1
    wait_time = between(0.05, 0.20)

    def on_start(self):
        """Assign admin / fraud analyst session token."""
        self.headers = {
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "Content-Type": "application/json",
        }

    @tag("alerts", "triage")
    @task(4)
    def list_alerts(self):
        """Query analyst alert triage queue."""
        severity = random.choice([None, "HIGH", "CRITICAL"])
        url = "/api/v1/alerts?limit=20"
        if severity:
            url += f"&severity={severity}"
        self.client.get(
            url,
            headers=self.headers,
            name="[API] GET /api/v1/alerts",
        )

    @tag("admin", "stats")
    @task(2)
    def view_system_statistics(self):
        """Query platform aggregated KPI statistics."""
        self.client.get(
            "/api/v1/admin/statistics",
            headers=self.headers,
            name="[API] GET /api/v1/admin/statistics",
        )

    @tag("admin", "model")
    @task(1)
    def view_model_status(self):
        """Query ML model registry status."""
        self.client.get(
            "/api/v1/admin/model/status",
            headers=self.headers,
            name="[API] GET /api/v1/admin/model/status",
        )
