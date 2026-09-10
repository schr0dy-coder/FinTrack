"""Risk Assessment SQLAlchemy Database Model."""

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class RiskAssessment(Base):
    """Risk Assessment calculation entity."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    rule_score: Mapped[float] = mapped_column(Float, nullable=False)
    ml_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False
    )  # LOW, MEDIUM, HIGH, CRITICAL
    reasons_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="risk_assessment"
    )

    @property
    def reasons(self) -> List[Dict[str, Any]]:
        """Deserialize reasons JSON to Python list."""
        try:
            return json.loads(self.reasons_json)
        except Exception:
            return []

    @reasons.setter
    def reasons(self, value: List[Dict[str, Any]]) -> None:
        """Serialize Python list to JSON string."""
        self.reasons_json = json.dumps(value)

    def __repr__(self) -> str:
        return f"<RiskAssessment tx_id='{self.transaction_id}' score={self.final_score} level='{self.risk_level}'>"
