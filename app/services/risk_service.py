"""Risk Evaluation Service."""

from typing import Any, Dict, List

from app.core.logging import logger
from app.ml.predict import predict_anomaly_score
from app.risk_engine.classifiers import classify_risk
from app.risk_engine.rules import (
    RuleResult,
    TransactionContext,
    evaluate_all_rules,
)
from app.risk_engine.scoring import calculate_rule_score, combine_risk_scores


class RiskService:
    """Coordinates deterministic rules and ML anomaly evaluation."""

    def evaluate_transaction_risk(self, ctx: TransactionContext) -> Dict[str, Any]:
        """
        Evaluate full risk profile for a transaction context:
        1. Evaluate 5 deterministic rules -> rule_score & reasons
        2. Execute ML anomaly detector -> ml_score & model_version
        3. Combine scores with configured weights -> final_score
        4. Classify risk level -> LOW, MEDIUM, HIGH, CRITICAL
        """
        # Step 1: Deterministic rules
        rule_results: List[RuleResult] = evaluate_all_rules(ctx)
        rule_score = calculate_rule_score(rule_results)

        # Build list of triggered reason summaries
        reasons_list = [
            {
                "code": r.code,
                "triggered": r.triggered,
                "score": r.score,
                "reason": r.reason,
                "details": r.details,
            }
            for r in rule_results
        ]

        # Step 2: ML anomaly score
        ml_score, model_version = predict_anomaly_score(ctx)

        # Step 3: Combined score
        final_score = combine_risk_scores(rule_score=rule_score, ml_score=ml_score)

        # Step 4: Classification
        risk_level = classify_risk(final_score)

        logger.info(
            f"Risk evaluated: tx user_id={ctx.user_id}, amount={ctx.amount} | "
            f"Rule={rule_score}, ML={ml_score} -> Final={final_score} ({risk_level})"
        )

        return {
            "rule_score": rule_score,
            "ml_score": ml_score,
            "final_score": final_score,
            "risk_level": risk_level,
            "reasons": reasons_list,
            "model_version": model_version,
        }
