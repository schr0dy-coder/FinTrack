"""Unit Tests for Machine Learning Pipeline and Inference Handling."""

from datetime import datetime, timezone

import numpy as np

from app.ml.features import context_to_feature_vector
from app.ml.predict import _heuristic_fallback_score, predict_anomaly_score
from app.risk_engine.rules import TransactionContext


def test_heuristic_fallback_calculation():
    """Verify fallback heuristics when model artifact is unavailable."""
    ctx_normal = TransactionContext(
        amount=500.0,
        merchant="Store",
        category="Shopping",
        location="Mumbai, IN",
        device_id="device-1",
        timestamp=datetime.now(timezone.utc),
        user_id=1,
    )
    score_normal = _heuristic_fallback_score(ctx_normal)
    assert 0.0 <= score_normal <= 100.0
    assert score_normal == 10.0

    ctx_suspicious = TransactionContext(
        amount=90000.0,
        merchant="Store",
        category="Shopping",
        location="Dubai, AE",
        device_id="device-unknown",
        timestamp=datetime.now(timezone.utc),
        user_id=1,
        known_devices={"device-1"},
        known_locations={"Mumbai, IN"},
        recent_transactions_in_window=6,
        historical_transaction_count=5,
    )
    score_suspicious = _heuristic_fallback_score(ctx_suspicious)
    # 10 + 35 + 20 + 20 + 25 = 110 -> clipped to 100.0
    assert score_suspicious == 100.0


def test_ml_predict_anomaly_score_live():
    """Verify inference pipeline with loaded model."""
    ctx = TransactionContext(
        amount=1500.0,
        merchant="Amazon India",
        category="Shopping",
        location="Mumbai, IN",
        device_id="device-phone",
        timestamp=datetime.now(timezone.utc),
        user_id=1,
        known_devices={"device-phone"},
        known_locations={"Mumbai, IN"},
        recent_transactions_in_window=1,
        historical_transaction_count=10,
        historical_mean_amount=1200.0,
    )

    score, version = predict_anomaly_score(ctx)
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0
    assert isinstance(version, str)
    assert len(version) > 0


def test_feature_vector_dimension():
    """Verify that feature extraction produces exact 8-dimensional float arrays."""
    ctx = TransactionContext(
        amount=100.0,
        merchant="Merchant",
        category="General",
        location="City",
        device_id="Device",
        timestamp=datetime.now(timezone.utc),
        user_id=1,
    )
    vec = context_to_feature_vector(ctx)
    assert vec.shape == (1, 8)
    assert not np.isnan(vec).any()
