"""Admin and System Health API Endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import ModelRetrainResponse, ModelStatusResponse, SystemStatsResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin & System"])


@router.get(
    "/statistics",
    response_model=SystemStatsResponse,
    summary="Get aggregated platform KPI metrics (Admin only)",
)
def get_system_statistics(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Fetch aggregated volume, risk distributions, alert statistics, and suspicious merchant rankings."""
    admin_service = AdminService(db)
    return admin_service.get_system_statistics()


@router.get(
    "/model/status",
    response_model=ModelStatusResponse,
    summary="Get machine learning model registry state (Admin only)",
)
def get_model_status(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Inspect active Isolation Forest model status and training metadata."""
    admin_service = AdminService(db)
    return admin_service.get_model_status()


@router.post(
    "/model/retrain",
    response_model=ModelRetrainResponse,
    summary="Trigger model retraining (Admin only)",
)
def retrain_model(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Trigger offline retraining pipeline and hot-reload model artifact into memory."""
    admin_service = AdminService(db)
    return admin_service.retrain_model_from_database()
