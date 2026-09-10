"""Transaction API Endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService
from app.utils.pagination import calculate_pages

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a transaction for fraud evaluation and storage",
)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new transaction.
    Automatically evaluates rule-based and ML anomaly risk, assigns risk tier,
    stores transaction record, and generates high-risk alerts if warranted.
    """
    tx_service = TransactionService(db)
    return tx_service.process_transaction(tx_in=tx_in, current_user=current_user)


@router.get(
    "",
    response_model=PaginatedTransactions,
    summary="List transactions with filters and pagination",
)
def list_transactions(
    start_date: Optional[datetime] = Query(
        None, description="Filter transactions after this timestamp"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter transactions before this timestamp"
    ),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount"),
    risk_level: Optional[str] = Query(
        None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"
    ),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (APPROVED, SUSPICIOUS, FLAGGED)"
    ),
    merchant: Optional[str] = Query(None, description="Search merchant name substring"),
    location: Optional[str] = Query(None, description="Search location name substring"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve transactions with extensive query filters and pagination.
    Admins see platform-wide transactions; standard users only see their own.
    """
    tx_service = TransactionService(db)
    items, total = tx_service.list_transactions(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        risk_level=risk_level,
        tx_status=status_filter,
        merchant=merchant,
        location=location,
        page=page,
        limit=limit,
    )
    total_pages = calculate_pages(total, limit)

    return PaginatedTransactions(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction details by ID",
)
def get_transaction_by_id(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single transaction record by its unique ID."""
    tx_service = TransactionService(db)
    return tx_service.get_transaction_by_id(tx_id=transaction_id, current_user=current_user)
