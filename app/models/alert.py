"""Alert SQLAlchemy Database Model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Alert(Base):
    """Fraud / High Risk Alert entity."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(20), index=True, default="OPEN", nullable=False
    )  # OPEN, RESOLVED
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} tx='{self.transaction_id}' severity='{self.severity}' status='{self.status}'>"
