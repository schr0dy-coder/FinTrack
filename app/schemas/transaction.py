"""Transaction Pydantic Schemas."""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.risk import RiskAssessmentResponse


class TransactionCreate(BaseModel):
    """Payload for submitting a new financial transaction."""

    amount: float = Field(
        ...,
        gt=0,
        json_schema_extra={"example": 1250.50},
        description="Transaction amount in local currency (must be > 0)",
    )
    merchant: str = Field(
        ..., min_length=1, max_length=150, json_schema_extra={"example": "Amazon India"}
    )
    category: Optional[str] = Field(
        default="General", max_length=50, json_schema_extra={"example": "Electronics"}
    )
    location: str = Field(
        ..., min_length=1, max_length=100, json_schema_extra={"example": "Mumbai, IN"}
    )
    device_id: str = Field(
        ..., min_length=1, max_length=100, json_schema_extra={"example": "device-android-9912a"}
    )
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        json_schema_extra={"example": "2026-09-10T12:00:00Z"},
    )
    status: Optional[str] = Field(default="APPROVED", json_schema_extra={"example": "APPROVED"})

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be strictly positive")
        return round(v, 2)


class TransactionResponse(BaseModel):
    """Transaction response representation."""

    id: str
    user_id: int
    amount: float
    merchant: str
    category: Optional[str] = None
    location: str
    device_id: str
    timestamp: datetime
    status: str
    created_at: datetime
    risk_assessment: Optional[RiskAssessmentResponse] = None

    model_config = {"from_attributes": True}


class PaginatedTransactions(BaseModel):
    """Paginated collection of transactions."""

    items: List[TransactionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
