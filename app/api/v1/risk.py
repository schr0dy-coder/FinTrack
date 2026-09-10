"""Risk Assessment API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.risks import RiskAssessmentRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.risk import RiskAssessmentResponse

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


@router.get(
    "/{transaction_id}",
    response_model=RiskAssessmentResponse,
    summary="Get risk assessment for a specific transaction",
)
def get_risk_assessment(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed risk assessment metrics for a transaction."""
    tx_repo = TransactionRepository(db)
    tx = tx_repo.get_by_id(transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found.",
        )

    if current_user.role != "ADMIN" and tx.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to view risk assessment for this transaction.",
        )

    risk_repo = RiskAssessmentRepository(db)
    assessment = risk_repo.get_by_transaction_id(transaction_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk assessment not found for transaction '{transaction_id}'.",
        )

    return RiskAssessmentResponse(
        id=assessment.id,
        transaction_id=assessment.transaction_id,
        rule_score=assessment.rule_score,
        ml_score=assessment.ml_score,
        final_score=assessment.final_score,
        risk_level=assessment.risk_level,
        reasons=assessment.reasons,
        model_version=assessment.model_version,
        created_at=assessment.created_at,
    )
