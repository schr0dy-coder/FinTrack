"""Transaction SQLAlchemy Database Model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.risk import RiskAssessment
    from app.models.user import User


class Transaction(Base):
    """Financial Transaction entity."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="APPROVED", nullable=False
    )  # APPROVED, SUSPICIOUS, FLAGGED, REJECTED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    risk_assessment: Mapped[Optional["RiskAssessment"]] = relationship(
        "RiskAssessment", back_populates="transaction", uselist=False, cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="transaction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Transaction id='{self.id}' amount={self.amount} status='{self.status}'>"
