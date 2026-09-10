"""Alert Management Service."""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.alert import Alert
from app.repositories.alerts import AlertRepository


class AlertService:
    """Handles alert creation, querying, and resolution."""

    def __init__(self, db: Session):
        self.db = db
        self.alert_repo = AlertRepository(db)

    def process_risk_and_maybe_alert(
        self,
        transaction_id: str,
        risk_result: Dict[str, Any],
    ) -> Optional[Alert]:
        """
        Check if transaction risk warrants an alert (HIGH or CRITICAL).
        If so, creates and persists an Alert entity.
        """
        final_score = risk_result["final_score"]
        if final_score < settings.RISK_HIGH_THRESHOLD:
            return None

        severity = "CRITICAL" if final_score >= settings.RISK_CRITICAL_THRESHOLD else "HIGH"

        # Build concise alert reason summary from triggered rules and ML score
        triggered_reasons = [
            r["reason"] for r in risk_result.get("reasons", []) if r.get("triggered")
        ]

        reasons_text = (
            "; ".join(triggered_reasons)
            if triggered_reasons
            else "Elevated ML anomaly score detected"
        )
        full_reason = f"[{severity} RISK - Score: {final_score}/100] {reasons_text}"

        alert = Alert(
            transaction_id=transaction_id,
            severity=severity,
            status="OPEN",
            reason=full_reason,
        )
        created_alert = self.alert_repo.create(alert)
        logger.warning(
            f"Alert #{created_alert.id} generated for transaction {transaction_id} (Severity: {severity})"
        )
        return created_alert

    def get_alert_by_id(self, alert_id: int) -> Alert:
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert #{alert_id} not found",
            )
        return alert

    def resolve_alert(self, alert_id: int, note: str) -> Alert:
        alert = self.get_alert_by_id(alert_id)
        if alert.status == "RESOLVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Alert #{alert_id} has already been resolved.",
            )

        resolved = self.alert_repo.resolve(alert_id, note)
        logger.info(f"Alert #{alert_id} marked as RESOLVED by analyst.")
        return resolved

    def list_alerts(
        self,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Alert], int]:
        return self.alert_repo.list_filtered(
            status=status_filter, severity=severity_filter, page=page, limit=limit
        )
