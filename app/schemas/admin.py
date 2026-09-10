"""Admin and System Analytics Schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SystemStatsResponse(BaseModel):
    """Aggregated platform statistics for admin dashboard."""

    total_transactions: int
    total_volume: float
    suspicious_transactions: int
    anomaly_rate: float
    open_alerts: int
    resolved_alerts: int
    risk_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    top_suspicious_merchants: List[Dict[str, Any]]
    top_suspicious_locations: List[Dict[str, Any]]


class ModelStatusResponse(BaseModel):
    """Machine Learning model health and metadata."""

    model_loaded: bool
    model_version: str
    model_type: str
    features: List[str]
    trained_at: Optional[str] = None
    training_sample_count: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None


class ModelRetrainResponse(BaseModel):
    """Response after triggering model retraining."""

    message: str
    status: str
    model_version: str
    sample_count: int
