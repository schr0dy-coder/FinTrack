"""Risk Assessment Pydantic Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleResultSchema(BaseModel):
    """Result of a single deterministic risk rule evaluation."""

    code: str = Field(..., json_schema_extra={"example": "HIGH_AMOUNT"})
    triggered: bool = Field(..., json_schema_extra={"example": True})
    score: float = Field(..., json_schema_extra={"example": 25.0})
    reason: str = Field(..., json_schema_extra={"example": "Transaction amount exceeds threshold"})
    details: Optional[Dict[str, Any]] = None


class RiskAssessmentResponse(BaseModel):
    """Full Risk Assessment output schema."""

    id: Optional[int] = None
    transaction_id: str
    rule_score: float = Field(..., ge=0, le=100, json_schema_extra={"example": 45.0})
    ml_score: float = Field(..., ge=0, le=100, json_schema_extra={"example": 68.5})
    final_score: float = Field(..., ge=0, le=100, json_schema_extra={"example": 54.4})
    risk_level: str = Field(
        ..., json_schema_extra={"example": "MEDIUM"}
    )  # LOW, MEDIUM, HIGH, CRITICAL
    reasons: List[Dict[str, Any]] = Field(default_factory=list)
    model_version: str = Field(default="v1.0.0", json_schema_extra={"example": "v1.0.0"})
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
