"""Alert Pydantic Schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.transaction import TransactionResponse


class AlertResolveRequest(BaseModel):
    """Payload for resolving an alert."""

    resolution_note: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        json_schema_extra={
            "example": "Verified customer via 2FA; customer authorized high-value transaction."
        },
    )


class AlertResponse(BaseModel):
    """Alert entity schema."""

    id: int
    transaction_id: str
    severity: str  # HIGH, CRITICAL
    status: str  # OPEN, RESOLVED
    reason: str
    resolution_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    transaction: Optional[TransactionResponse] = None

    model_config = {"from_attributes": True}


class PaginatedAlerts(BaseModel):
    """Paginated collection of alerts."""

    items: List[AlertResponse]
    total: int
    page: int
    limit: int
    total_pages: int
