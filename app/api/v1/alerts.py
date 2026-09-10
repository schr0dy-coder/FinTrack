"""Alert Management API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.alert import AlertResolveRequest, AlertResponse, PaginatedAlerts
from app.services.alert_service import AlertService
from app.utils.pagination import calculate_pages

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=PaginatedAlerts,
    summary="List fraud alerts (Admin only)",
)
def list_alerts(
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (OPEN, RESOLVED)"
    ),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, CRITICAL)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve filtered alerts queue with pagination. Requires ADMIN role."""
    alert_service = AlertService(db)
    items, total = alert_service.list_alerts(
        status_filter=status_filter,
        severity_filter=severity,
        page=page,
        limit=limit,
    )
    total_pages = calculate_pages(total, limit)

    return PaginatedAlerts(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert details by ID (Admin only)",
)
def get_alert_by_id(
    alert_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve full alert details including triggered reasons and transaction."""
    alert_service = AlertService(db)
    return alert_service.get_alert_by_id(alert_id=alert_id)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Mark an alert as resolved (Admin only)",
)
def resolve_alert(
    alert_id: int,
    resolve_in: AlertResolveRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Mark an open alert as resolved with analyst investigation notes."""
    alert_service = AlertService(db)
    return alert_service.resolve_alert(alert_id=alert_id, note=resolve_in.resolution_note)
