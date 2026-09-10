"""Database Seeding Script.

Seeds initial admin and demo user accounts, along with sample transactions,
risk assessments, and alerts for local exploration and dashboard testing.
Ensures idempotency: skips seeding safely if records already exist.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.risk import RiskAssessment
from app.models.transaction import Transaction
from app.models.user import User


def seed_database():
    """Seed initial users, transactions, risk assessments, and alerts."""
    with SessionLocal() as db:
        # Check if already seeded (Idempotency check)
        existing_admin = db.query(User).filter_by(email="admin@fintrack.com").first()
        if existing_admin:
            print("Database is already seeded with admin account. Skipping seeding.")
            return

        admin_email = os.getenv("DEMO_ADMIN_EMAIL", "admin@fintrack.com")
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "Admin@123")
        user1_email = os.getenv("DEMO_USER1_EMAIL", "john@example.com")
        user1_password = os.getenv("DEMO_USER1_PASSWORD", "Password@123")
        user2_email = os.getenv("DEMO_USER2_EMAIL", "jane@example.com")
        user2_password = os.getenv("DEMO_USER2_PASSWORD", "Password@123")
        user3_email = os.getenv("DEMO_USER3_EMAIL", "robert@example.com")
        user3_password = os.getenv("DEMO_USER3_PASSWORD", "Password@123")

        print("=" * 80)
        print("DEMO ONLY NOTICE:")
        print("These credentials are intended ONLY for local development with synthetic data.")
        print("Never use these credentials in a production environment.")
        print("=" * 80)

        print("Seeding users...")
        admin = User(
            name="FinTrack Administrator",
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            role="ADMIN",
        )
        user1 = User(
            name="John Doe",
            email=user1_email,
            password_hash=get_password_hash(user1_password),
            role="USER",
        )
        user2 = User(
            name="Jane Smith",
            email=user2_email,
            password_hash=get_password_hash(user2_password),
            role="USER",
        )
        user3 = User(
            name="Robert Taylor",
            email=user3_email,
            password_hash=get_password_hash(user3_password),
            role="USER",
        )

        db.add_all([admin, user1, user2, user3])
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        db.refresh(user3)

        print("Seeding sample transactions, risk evaluations, and alerts...")
        now = datetime.now(timezone.utc)

        # Realistic transactions for user1 (John Doe)
        sample_records = [
            # 1. Normal daily spends (LOW risk)
            {
                "user_id": user1.id,
                "amount": 420.00,
                "merchant": "Starbucks Coffee",
                "category": "Food & Dining",
                "location": "Mumbai, IN",
                "device_id": "device-iphone-john",
                "timestamp": now - timedelta(days=5, hours=3),
                "status": "APPROVED",
                "rule_score": 0.0,
                "ml_score": 12.0,
                "final_score": 4.8,
                "risk_level": "LOW",
                "reasons": [
                    {
                        "code": "NORMAL",
                        "triggered": False,
                        "score": 0,
                        "reason": "Normal transaction",
                    }
                ],
            },
            {
                "user_id": user1.id,
                "amount": 1850.00,
                "merchant": "DMart Supermarket",
                "category": "Groceries",
                "location": "Mumbai, IN",
                "device_id": "device-iphone-john",
                "timestamp": now - timedelta(days=4, hours=6),
                "status": "APPROVED",
                "rule_score": 0.0,
                "ml_score": 14.5,
                "final_score": 5.8,
                "risk_level": "LOW",
                "reasons": [
                    {
                        "code": "NORMAL",
                        "triggered": False,
                        "score": 0,
                        "reason": "Normal transaction",
                    }
                ],
            },
            {
                "user_id": user1.id,
                "amount": 3499.00,
                "merchant": "Amazon India",
                "category": "Shopping",
                "location": "Mumbai, IN",
                "device_id": "device-iphone-john",
                "timestamp": now - timedelta(days=3, hours=2),
                "status": "APPROVED",
                "rule_score": 0.0,
                "ml_score": 18.0,
                "final_score": 7.2,
                "risk_level": "LOW",
                "reasons": [
                    {
                        "code": "NORMAL",
                        "triggered": False,
                        "score": 0,
                        "reason": "Normal transaction",
                    }
                ],
            },
            {
                "user_id": user1.id,
                "amount": 299.00,
                "merchant": "Uber India",
                "category": "Travel",
                "location": "Mumbai, IN",
                "device_id": "device-iphone-john",
                "timestamp": now - timedelta(days=2, hours=5),
                "status": "APPROVED",
                "rule_score": 0.0,
                "ml_score": 10.0,
                "final_score": 4.0,
                "risk_level": "LOW",
                "reasons": [
                    {
                        "code": "NORMAL",
                        "triggered": False,
                        "score": 0,
                        "reason": "Normal transaction",
                    }
                ],
            },
            # 2. Medium risk transaction
            {
                "user_id": user1.id,
                "amount": 32000.00,
                "merchant": "Croma Electronics",
                "category": "Electronics",
                "location": "Pune, IN",
                "device_id": "device-laptop-john",
                "timestamp": now - timedelta(days=1, hours=8),
                "status": "APPROVED",
                "rule_score": 35.0,
                "ml_score": 42.0,
                "final_score": 37.8,
                "risk_level": "MEDIUM",
                "reasons": [
                    {
                        "code": "LOCATION_ANOMALY",
                        "triggered": True,
                        "score": 20,
                        "reason": "Transaction location 'Pune, IN' is unusual based on user history",
                    },
                    {
                        "code": "NEW_DEVICE",
                        "triggered": True,
                        "score": 15,
                        "reason": "Transaction initiated from secondary/new device 'device-laptop-john'",
                    },
                ],
            },
            # 3. High risk transaction (Triggers Alert)
            {
                "user_id": user1.id,
                "amount": 88500.00,
                "merchant": "Tanishq Gold & Diamonds",
                "category": "Luxury & Jewelry",
                "location": "Dubai, AE",
                "device_id": "device-unknown-android",
                "timestamp": now - timedelta(hours=14),
                "status": "SUSPICIOUS",
                "rule_score": 60.0,
                "ml_score": 82.0,
                "final_score": 68.8,
                "risk_level": "HIGH",
                "reasons": [
                    {
                        "code": "HIGH_AMOUNT",
                        "triggered": True,
                        "score": 25,
                        "reason": "Transaction amount (₹88,500.00) exceeds threshold ₹50,000.00",
                    },
                    {
                        "code": "LOCATION_ANOMALY",
                        "triggered": True,
                        "score": 20,
                        "reason": "Transaction location 'Dubai, AE' is unusual based on user history",
                    },
                    {
                        "code": "NEW_DEVICE",
                        "triggered": True,
                        "score": 15,
                        "reason": "Unrecognized device 'device-unknown-android'",
                    },
                ],
                "alert": {
                    "severity": "HIGH",
                    "status": "OPEN",
                    "reason": "[HIGH RISK - Score: 68.8/100] High amount ₹88,500.00; Location anomaly (Dubai, AE); Unrecognized device",
                },
            },
            # 4. Critical risk transaction (Triggers Alert)
            {
                "user_id": user2.id,
                "amount": 245000.00,
                "merchant": "Rolex Boutique London",
                "category": "Luxury & Jewelry",
                "location": "London, UK",
                "device_id": "device-botnet-proxy-44",
                "timestamp": now - timedelta(hours=2),
                "status": "FLAGGED",
                "rule_score": 80.0,
                "ml_score": 96.0,
                "final_score": 86.4,
                "risk_level": "CRITICAL",
                "reasons": [
                    {
                        "code": "HIGH_AMOUNT",
                        "triggered": True,
                        "score": 25,
                        "reason": "Transaction amount (₹245,000.00) exceeds high-value threshold",
                    },
                    {
                        "code": "LOCATION_ANOMALY",
                        "triggered": True,
                        "score": 20,
                        "reason": "Location 'London, UK' is unfamiliar for user",
                    },
                    {
                        "code": "NEW_DEVICE",
                        "triggered": True,
                        "score": 15,
                        "reason": "Unrecognized device 'device-botnet-proxy-44'",
                    },
                    {
                        "code": "RAPID_TRANSACTIONS",
                        "triggered": True,
                        "score": 20,
                        "reason": "6 burst transactions in under 2 minutes",
                    },
                ],
                "alert": {
                    "severity": "CRITICAL",
                    "status": "OPEN",
                    "reason": "[CRITICAL RISK - Score: 86.4/100] Severe amount anomaly (₹245,000.00), Rapid burst frequency, Foreign location, Unknown proxy device",
                },
            },
            # 5. Resolved sample alert for demonstration
            {
                "user_id": user2.id,
                "amount": 72000.00,
                "merchant": "Apple Store Regent St",
                "category": "Electronics",
                "location": "London, UK",
                "device_id": "device-macbook-jane",
                "timestamp": now - timedelta(days=2, hours=10),
                "status": "APPROVED",
                "rule_score": 60.0,
                "ml_score": 70.0,
                "final_score": 64.0,
                "risk_level": "HIGH",
                "reasons": [
                    {
                        "code": "HIGH_AMOUNT",
                        "triggered": True,
                        "score": 25,
                        "reason": "Amount exceeds threshold",
                    },
                    {
                        "code": "LOCATION_ANOMALY",
                        "triggered": True,
                        "score": 20,
                        "reason": "Travel location anomaly",
                    },
                    {
                        "code": "NEW_DEVICE",
                        "triggered": True,
                        "score": 15,
                        "reason": "New MacBook registered",
                    },
                ],
                "alert": {
                    "severity": "HIGH",
                    "status": "RESOLVED",
                    "reason": "[HIGH RISK - Score: 64.0/100] High amount purchase at Apple Store during overseas travel.",
                    "resolution_note": "Customer contacted via phone; confirmed legitimate travel purchase of MacBook Pro.",
                    "resolved_at": now - timedelta(days=2, hours=9),
                },
            },
        ]

        for r in sample_records:
            tx = Transaction(
                user_id=r["user_id"],
                amount=r["amount"],
                merchant=r["merchant"],
                category=r["category"],
                location=r["location"],
                device_id=r["device_id"],
                timestamp=r["timestamp"],
                status=r["status"],
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)

            assessment = RiskAssessment(
                transaction_id=tx.id,
                rule_score=r["rule_score"],
                ml_score=r["ml_score"],
                final_score=r["final_score"],
                risk_level=r["risk_level"],
                reasons_json=json.dumps(r["reasons"]),
                model_version="v1.0.0",
                created_at=r["timestamp"],
            )
            db.add(assessment)
            db.commit()

            if "alert" in r:
                al = r["alert"]
                alert = Alert(
                    transaction_id=tx.id,
                    severity=al["severity"],
                    status=al["status"],
                    reason=al["reason"],
                    resolution_note=al.get("resolution_note"),
                    created_at=r["timestamp"],
                    resolved_at=al.get("resolved_at"),
                )
                db.add(alert)
                db.commit()

        print("\nDatabase seeded successfully!")
        print("Default accounts:")
        print("  - Admin:    admin@fintrack.com / Admin@123")
        print("  - Customer: john@example.com   / Password@123")
        print("  - Customer: jane@example.com   / Password@123")


if __name__ == "__main__":
    seed_database()
