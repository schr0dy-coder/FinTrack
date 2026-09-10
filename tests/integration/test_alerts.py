"""Integration Tests for Alert Triage and Resolution."""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.transaction import Transaction
from app.models.user import User
from app.services.alert_service import AlertService


def test_alert_lifecycle_and_resolution(db_session: Session, regular_user: User):
    service = AlertService(db_session)

    # 1. Create transaction & open alert
    tx = Transaction(
        user_id=regular_user.id,
        amount=88000.0,
        merchant="Rolex London",
        location="London, UK",
        device_id="device-unknown-proxy",
        timestamp=datetime.now(timezone.utc),
        status="FLAGGED",
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    alert = Alert(
        transaction_id=tx.id,
        severity="CRITICAL",
        status="OPEN",
        reason="Severe amount anomaly and proxy device detected",
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    # 2. Query alert
    fetched = service.get_alert_by_id(alert.id)
    assert fetched.id == alert.id
    assert fetched.status == "OPEN"

    # 3. Resolve alert
    note = "Customer identity confirmed via phone call and 2FA."
    resolved = service.resolve_alert(alert.id, note=note)

    assert resolved.status == "RESOLVED"
    assert resolved.resolution_note == note
    assert resolved.resolved_at is not None

    # 4. Resolving an already resolved alert should raise 400 Bad Request
    with pytest.raises(HTTPException) as exc_info:
        service.resolve_alert(alert.id, note="Second resolve attempt")
    assert exc_info.value.status_code == 400
