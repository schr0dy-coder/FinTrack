"""Transaction Repository."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.risk import RiskAssessment
from app.models.transaction import Transaction


def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has timezone UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TransactionRepository:
    """Handles persistence operations for transactions."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, tx_id: str) -> Optional[Transaction]:
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.risk_assessment), joinedload(Transaction.alerts))
            .where(Transaction.id == tx_id)
        )
        return self.db.scalars(stmt).first()

    def create(self, tx: Transaction) -> Transaction:
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def list_filtered(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        merchant: Optional[str] = None,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Transaction], int]:
        """Query transactions with filtering, pagination, and eager-loaded relations."""
        query = select(Transaction).options(joinedload(Transaction.risk_assessment))
        count_query = select(func.count(Transaction.id))

        if user_id is not None:
            query = query.where(Transaction.user_id == user_id)
            count_query = count_query.where(Transaction.user_id == user_id)

        if start_date is not None:
            query = query.where(Transaction.timestamp >= start_date)
            count_query = count_query.where(Transaction.timestamp >= start_date)

        if end_date is not None:
            query = query.where(Transaction.timestamp <= end_date)
            count_query = count_query.where(Transaction.timestamp <= end_date)

        if min_amount is not None:
            query = query.where(Transaction.amount >= min_amount)
            count_query = count_query.where(Transaction.amount >= min_amount)

        if max_amount is not None:
            query = query.where(Transaction.amount <= max_amount)
            count_query = count_query.where(Transaction.amount <= max_amount)

        if status is not None:
            query = query.where(Transaction.status == status.upper())
            count_query = count_query.where(Transaction.status == status.upper())

        if merchant is not None and merchant.strip():
            query = query.where(Transaction.merchant.ilike(f"%{merchant.strip()}%"))
            count_query = count_query.where(Transaction.merchant.ilike(f"%{merchant.strip()}%"))

        if location is not None and location.strip():
            query = query.where(Transaction.location.ilike(f"%{location.strip()}%"))
            count_query = count_query.where(Transaction.location.ilike(f"%{location.strip()}%"))

        if risk_level is not None and risk_level.strip():
            query = query.join(Transaction.risk_assessment).where(
                RiskAssessment.risk_level == risk_level.upper().strip()
            )
            count_query = count_query.join(Transaction.risk_assessment).where(
                RiskAssessment.risk_level == risk_level.upper().strip()
            )

        # Count total matching
        total = self.db.scalar(count_query) or 0

        # Pagination and ordering
        offset = (page - 1) * limit
        query = query.order_by(desc(Transaction.timestamp)).offset(offset).limit(limit)

        items = list(self.db.scalars(query).unique().all())
        return items, total

    def get_user_history_summary(
        self,
        user_id: int,
        current_time: datetime,
        rapid_window_seconds: int = 120,
        failed_window_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Fetch historical profiling metrics for risk calculation."""
        current_time_norm = _normalize_dt(current_time)
        window_start = current_time_norm - timedelta(seconds=rapid_window_seconds)
        failed_start = current_time_norm - timedelta(seconds=failed_window_seconds)

        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.timestamp))
        )
        all_prior = list(self.db.scalars(stmt).all())

        known_devices: Set[str] = set()
        known_locations: Set[str] = set()
        amounts: List[float] = []

        recent_in_window = 0
        recent_failed = 0
        hist_count = 0

        for tx in all_prior:
            tx_time = _normalize_dt(tx.timestamp)
            if tx_time > current_time_norm:
                continue

            hist_count += 1
            known_devices.add(tx.device_id)
            known_locations.add(tx.location)
            amounts.append(tx.amount)

            if tx_time >= window_start:
                recent_in_window += 1

            if tx_time >= failed_start and tx.status in ("FLAGGED", "REJECTED"):
                recent_failed += 1

        mean_amount = (sum(amounts) / hist_count) if hist_count > 0 else 0.0

        return {
            "known_devices": known_devices,
            "known_locations": known_locations,
            "recent_transactions_in_window": recent_in_window,
            "recent_failed_attempts": recent_failed,
            "historical_transaction_count": hist_count,
            "historical_mean_amount": mean_amount,
        }
