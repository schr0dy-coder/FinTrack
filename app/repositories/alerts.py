"""Alert Repository."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.alert import Alert
from app.models.transaction import Transaction


class AlertRepository:
    """Handles persistence operations for alerts."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, alert_id: int) -> Optional[Alert]:
        stmt = (
            select(Alert)
            .options(joinedload(Alert.transaction).joinedload(Transaction.risk_assessment))
            .where(Alert.id == alert_id)
        )
        return self.db.scalars(stmt).first()

    def create(self, alert: Alert) -> Alert:
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve(self, alert_id: int, note: str) -> Optional[Alert]:
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        alert.status = "RESOLVED"
        alert.resolution_note = note.strip()
        alert.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_filtered(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Alert], int]:
        """Query alerts with filtering and pagination."""
        query = select(Alert).options(
            joinedload(Alert.transaction).joinedload(Transaction.risk_assessment)
        )
        count_query = select(func.count(Alert.id))

        if status is not None and status.strip():
            query = query.where(Alert.status == status.upper().strip())
            count_query = count_query.where(Alert.status == status.upper().strip())

        if severity is not None and severity.strip():
            query = query.where(Alert.severity == severity.upper().strip())
            count_query = count_query.where(Alert.severity == severity.upper().strip())

        total = self.db.scalar(count_query) or 0
        offset = (page - 1) * limit
        query = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit)

        items = list(self.db.scalars(query).unique().all())
        return items, total

    def count_by_status(self) -> dict:
        stmt = select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        results = self.db.execute(stmt).all()
        return {status: count for status, count in results}

    def count_by_severity(self) -> dict:
        stmt = select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
        results = self.db.execute(stmt).all()
        return {sev: count for sev, count in results}
