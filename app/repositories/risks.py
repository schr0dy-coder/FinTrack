"""Risk Assessment Repository."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.risk import RiskAssessment


class RiskAssessmentRepository:
    """Handles persistence operations for risk assessments."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_transaction_id(self, tx_id: str) -> Optional[RiskAssessment]:
        stmt = select(RiskAssessment).where(RiskAssessment.transaction_id == tx_id)
        return self.db.scalars(stmt).first()

    def create(self, assessment: RiskAssessment) -> RiskAssessment:
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_risk_level_counts(self) -> dict:
        """Aggregate counts of transactions grouped by risk level."""
        stmt = select(RiskAssessment.risk_level, func.count(RiskAssessment.id)).group_by(
            RiskAssessment.risk_level
        )
        results = self.db.execute(stmt).all()
        return {level: count for level, count in results}
