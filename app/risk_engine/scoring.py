"""Risk Scoring and Signal Aggregation Engine."""

from typing import List, Optional

from app.core.config import settings
from app.risk_engine.rules import RuleResult


def calculate_rule_score(rule_results: List[RuleResult]) -> float:
    """Sum up triggered rule scores and normalize to [0, 100]."""
    total_score = sum(r.score for r in rule_results if r.triggered)
    return float(round(min(100.0, max(0.0, total_score)), 2))


def combine_risk_scores(
    rule_score: float,
    ml_score: float,
    rule_weight: Optional[float] = None,
    ml_weight: Optional[float] = None,
) -> float:
    """
    Calculate the combined final risk score using weighted formula:
    Final Risk = (Rule_Weight * Rule_Score) + (ML_Weight * ML_Score)
    Bounded strictly between [0.0, 100.0].
    """
    r_weight = rule_weight if rule_weight is not None else settings.RULE_WEIGHT
    m_weight = ml_weight if ml_weight is not None else settings.ML_WEIGHT

    # Ensure weights sum correctly
    total_weight = r_weight + m_weight
    if total_weight > 0:
        norm_r_weight = r_weight / total_weight
        norm_m_weight = m_weight / total_weight
    else:
        norm_r_weight, norm_m_weight = 0.5, 0.5

    combined = (norm_r_weight * rule_score) + (norm_m_weight * ml_score)
    return float(round(min(100.0, max(0.0, combined)), 2))
