"""Transaction Processing Service."""

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.risk import RiskAssessment
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.risks import RiskAssessmentRepository
from app.repositories.transactions import TransactionRepository
from app.risk_engine.rules import TransactionContext
from app.schemas.transaction import TransactionCreate
from app.services.alert_service import AlertService
from app.services.risk_service import RiskService


class TransactionService:
    """Coordinates transaction ingestion, risk evaluation, persistence, and alert dispatch."""

    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = TransactionRepository(db)
        self.risk_repo = RiskAssessmentRepository(db)
        self.risk_service = RiskService()
        self.alert_service = AlertService(db)

    def process_transaction(self, tx_in: TransactionCreate, current_user: User) -> Transaction:
        """
        Ingest a transaction:
        1. Query user's historical transaction behavior
        2. Construct TransactionContext
        3. Evaluate deterministic rules + ML anomaly score
        4. Persist Transaction and RiskAssessment
        5. Trigger Alert if risk score exceeds threshold
        """
        tx_time = tx_in.timestamp or datetime.now(timezone.utc)
        logger.info(
            f"Transaction received: user_id={current_user.id}, amount={tx_in.amount}, "
            f"merchant={tx_in.merchant}, location={tx_in.location}"
        )

        # 1. Fetch user historical metrics
        history_summary = self.tx_repo.get_user_history_summary(
            user_id=current_user.id,
            current_time=tx_time,
        )

        # 2. Build TransactionContext
        ctx = TransactionContext(
            amount=tx_in.amount,
            merchant=tx_in.merchant,
            category=tx_in.category,
            location=tx_in.location,
            device_id=tx_in.device_id,
            timestamp=tx_time,
            user_id=current_user.id,
            known_devices=history_summary["known_devices"],
            known_locations=history_summary["known_locations"],
            recent_transactions_in_window=history_summary["recent_transactions_in_window"],
            recent_failed_attempts=history_summary["recent_failed_attempts"],
            historical_transaction_count=history_summary["historical_transaction_count"],
            historical_mean_amount=history_summary["historical_mean_amount"],
        )

        # 3. Evaluate Risk
        risk_result = self.risk_service.evaluate_transaction_risk(ctx)
        risk_level = risk_result["risk_level"]

        # Determine transaction operational status
        tx_status = "APPROVED"
        if risk_level == "CRITICAL":
            tx_status = "FLAGGED"
        elif risk_level == "HIGH":
            tx_status = "SUSPICIOUS"

        # 4. Persist Transaction
        tx = Transaction(
            user_id=current_user.id,
            amount=tx_in.amount,
            merchant=tx_in.merchant,
            category=tx_in.category or "General",
            location=tx_in.location,
            device_id=tx_in.device_id,
            timestamp=tx_time,
            status=tx_status,
        )
        saved_tx = self.tx_repo.create(tx)

        # 5. Persist Risk Assessment
        assessment = RiskAssessment(
            transaction_id=saved_tx.id,
            rule_score=risk_result["rule_score"],
            ml_score=risk_result["ml_score"],
            final_score=risk_result["final_score"],
            risk_level=risk_level,
            reasons_json=json.dumps(risk_result["reasons"]),
            model_version=risk_result["model_version"],
        )
        self.risk_repo.create(assessment)

        logger.info(
            f"Risk assessment completed for transaction_id={saved_tx.id}: "
            f"rule_score={risk_result['rule_score']}, ml_score={risk_result['ml_score']}, "
            f"final_score={risk_result['final_score']} ({risk_level})"
        )

        # 6. Trigger alert if needed
        self.alert_service.process_risk_and_maybe_alert(
            transaction_id=saved_tx.id,
            risk_result=risk_result,
        )

        # Reload with relations
        return self.tx_repo.get_by_id(saved_tx.id)

    def get_transaction_by_id(self, tx_id: str, current_user: User) -> Transaction:
        """Fetch transaction by ID with role-based authorization check."""
        tx = self.tx_repo.get_by_id(tx_id)
        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID '{tx_id}' was not found.",
            )

        # Standard users can only view their own transactions
        if current_user.role != "ADMIN" and tx.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this transaction.",
            )

        return tx

    def list_transactions(
        self,
        current_user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        risk_level: Optional[str] = None,
        tx_status: Optional[str] = None,
        merchant: Optional[str] = None,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Transaction], int]:
        """List transactions with filtering and role-based scoping."""
        # Non-admin users are restricted to their own user_id
        user_id_scope = None if current_user.role == "ADMIN" else current_user.id

        return self.tx_repo.list_filtered(
            user_id=user_id_scope,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            risk_level=risk_level,
            status=tx_status,
            merchant=merchant,
            location=location,
            page=page,
            limit=limit,
        )
