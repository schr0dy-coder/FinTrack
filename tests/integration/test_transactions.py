"""Integration Tests for Transaction Flow and Risk Scoring."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService


def test_normal_transaction_flow(db_session: Session, regular_user: User):
    service = TransactionService(db_session)
    tx_in = TransactionCreate(
        amount=1250.0,
        merchant="DMart Supermarket",
        category="Groceries",
        location="Mumbai, IN",
        device_id="device-iphone-1",
    )

    tx = service.process_transaction(tx_in, current_user=regular_user)

    assert tx is not None
    assert tx.amount == 1250.0
    assert tx.user_id == regular_user.id
    assert tx.status == "APPROVED"
    assert tx.risk_assessment is not None
    assert tx.risk_assessment.risk_level == "LOW"
    assert tx.risk_assessment.final_score < 30.0

    # Normal transaction does not generate alert
    alerts = db_session.query(Alert).filter_by(transaction_id=tx.id).all()
    assert len(alerts) == 0


def test_high_risk_transaction_triggers_alert(db_session: Session, regular_user: User):
    service = TransactionService(db_session)

    # First, seed normal transaction history so subsequent foreign device triggers
    tx_normal = Transaction(
        user_id=regular_user.id,
        amount=500.0,
        merchant="Uber",
        location="Mumbai, IN",
        device_id="device-iphone-1",
        timestamp=datetime.now(timezone.utc),
        status="APPROVED",
    )
    db_session.add(tx_normal)
    db_session.commit()

    # Now submit a high-amount foreign transaction
    tx_high = TransactionCreate(
        amount=95000.0,
        merchant="Tanishq Luxury",
        category="Luxury & Jewelry",
        location="Dubai, AE",
        device_id="device-unknown-android",
    )

    tx = service.process_transaction(tx_high, current_user=regular_user)

    assert tx.status in ("SUSPICIOUS", "FLAGGED")
    assert tx.risk_assessment is not None
    assert tx.risk_assessment.risk_level in ("HIGH", "CRITICAL")
    assert tx.risk_assessment.final_score >= 60.0

    # High risk transaction generates an active alert
    alerts = db_session.query(Alert).filter_by(transaction_id=tx.id).all()
    assert len(alerts) == 1
    assert alerts[0].status == "OPEN"
    assert alerts[0].severity in ("HIGH", "CRITICAL")
    assert "Score:" in alerts[0].reason
