"""API v1 Router Aggregator."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.alerts import router as alert_router
from app.api.v1.auth import router as auth_router
from app.api.v1.risk import router as risk_router
from app.api.v1.transactions import router as tx_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(tx_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(alert_router)
api_v1_router.include_router(admin_router)
