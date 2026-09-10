"""Risk Level Classification Module."""

from enum import Enum

from app.core.config import settings


class RiskLevel(str, Enum):
    """Categorical risk tiers."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def classify_risk(final_score: float) -> str:
    """
    Map numerical score to standard risk level:
    - 0 to 29.99: LOW
    - 30 to 59.99: MEDIUM
    - 60 to 79.99: HIGH
    - 80 to 100: CRITICAL
    """
    if final_score >= settings.RISK_CRITICAL_THRESHOLD:
        return RiskLevel.CRITICAL.value
    elif final_score >= settings.RISK_HIGH_THRESHOLD:
        return RiskLevel.HIGH.value
    elif final_score >= 30.0:
        return RiskLevel.MEDIUM.value
    else:
        return RiskLevel.LOW.value
