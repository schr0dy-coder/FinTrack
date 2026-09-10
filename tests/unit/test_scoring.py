"""Unit Tests for Risk Scoring and Classification."""

from app.risk_engine.classifiers import RiskLevel, classify_risk
from app.risk_engine.rules import RuleResult
from app.risk_engine.scoring import calculate_rule_score, combine_risk_scores


def test_calculate_rule_score_summation_and_bounding():
    # Only triggered rules count
    results = [
        RuleResult(code="R1", triggered=True, score=25.0, reason=""),
        RuleResult(code="R2", triggered=False, score=20.0, reason=""),
        RuleResult(code="R3", triggered=True, score=15.0, reason=""),
    ]
    assert calculate_rule_score(results) == 40.0

    # Over 100 is capped at 100.0
    huge_results = [
        RuleResult(code=f"R{i}", triggered=True, score=30.0, reason="") for i in range(5)
    ]
    assert calculate_rule_score(huge_results) == 100.0


def test_combine_risk_scores_weighted_formula():
    # 60% rule (50) + 40% ML (80) = 30 + 32 = 62.0
    final = combine_risk_scores(rule_score=50.0, ml_score=80.0, rule_weight=0.6, ml_weight=0.4)
    assert final == 62.0

    # Clean bounds
    assert combine_risk_scores(0.0, 0.0) == 0.0
    assert combine_risk_scores(100.0, 100.0) == 100.0


def test_classify_risk_threshold_boundaries():
    # LOW: 0 - 29.99
    assert classify_risk(0.0) == RiskLevel.LOW.value
    assert classify_risk(15.5) == RiskLevel.LOW.value
    assert classify_risk(29.99) == RiskLevel.LOW.value

    # MEDIUM: 30 - 59.99
    assert classify_risk(30.0) == RiskLevel.MEDIUM.value
    assert classify_risk(45.0) == RiskLevel.MEDIUM.value
    assert classify_risk(59.99) == RiskLevel.MEDIUM.value

    # HIGH: 60 - 79.99
    assert classify_risk(60.0) == RiskLevel.HIGH.value
    assert classify_risk(70.0) == RiskLevel.HIGH.value
    assert classify_risk(79.99) == RiskLevel.HIGH.value

    # CRITICAL: 80 - 100
    assert classify_risk(80.0) == RiskLevel.CRITICAL.value
    assert classify_risk(95.0) == RiskLevel.CRITICAL.value
    assert classify_risk(100.0) == RiskLevel.CRITICAL.value
