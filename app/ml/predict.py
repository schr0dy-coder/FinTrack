"""ML Inference and Anomaly Score Normalization."""

from typing import Tuple

from app.core.logging import logger
from app.ml.features import context_to_feature_vector
from app.ml.model_registry import get_model_registry
from app.risk_engine.rules import TransactionContext


def predict_anomaly_score(ctx: TransactionContext) -> Tuple[float, str]:
    """
    Perform ML anomaly detection on the transaction context.

    Returns:
        Tuple of (normalized_ml_risk_score, model_version)
        Where normalized_ml_risk_score is bounded in [0.0, 100.0].
    """
    registry = get_model_registry()

    if not registry.is_loaded():
        # Heuristic fallback if model not yet trained
        score = _heuristic_fallback_score(ctx)
        return score, registry.get_model_version()

    try:
        artifact = registry.get_artifact()
        model = artifact["model"]
        preprocessor = artifact["preprocessor"]
        min_score = artifact.get("min_score", -0.5)
        max_score = artifact.get("max_score", 0.5)
        version = artifact.get("model_version", "v1.0.0")

        # Extract features and scale
        X_vec = context_to_feature_vector(ctx)
        X_scaled = preprocessor.transform(X_vec)

        # Isolation forest decision_function: lower score = more anomalous
        # Typical range: [-0.5 (very anomalous), +0.5 (very normal)]
        raw_score = float(model.decision_function(X_scaled)[0])

        # Normalize so that:
        # Most normal (max_score) -> 0.0 risk
        # Most anomalous (min_score) -> 100.0 risk
        score_range = max_score - min_score
        if score_range > 0:
            normalized_anomaly = (max_score - raw_score) / score_range
        else:
            normalized_anomaly = 0.5 if raw_score < 0 else 0.1

        # Scale to 0-100 and clip
        ml_risk_score = float(round(min(100.0, max(0.0, normalized_anomaly * 100.0)), 2))
        return ml_risk_score, version

    except Exception as e:
        logger.error(f"Error during ML inference: {e}. Falling back to heuristic scoring.")
        return _heuristic_fallback_score(ctx), "v0.0.0-fallback"


def _heuristic_fallback_score(ctx: TransactionContext) -> float:
    """Heuristic scoring when ML model artifact is not available."""
    score = 10.0
    if ctx.amount > 50000:
        score += 35.0
    if ctx.historical_transaction_count > 0 and ctx.device_id not in ctx.known_devices:
        score += 20.0
    if ctx.historical_transaction_count > 0 and ctx.location not in ctx.known_locations:
        score += 20.0
    if ctx.recent_transactions_in_window >= 5:
        score += 25.0
    return float(round(min(100.0, max(0.0, score)), 2))
