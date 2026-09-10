"""Unit Tests for Feature Extraction and Parity."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from app.ml.features import (
    FEATURE_COLUMNS,
    context_to_feature_vector,
    dataframe_to_feature_matrix,
    extract_features_from_context,
)
from app.risk_engine.rules import TransactionContext


def test_extract_features_from_context_rich_history():
    dt = datetime(2026, 9, 10, 14, 30, tzinfo=timezone.utc)
    ctx = TransactionContext(
        amount=15000.0,
        merchant="Apple Store",
        category="Electronics",
        location="Delhi, IN",
        device_id="device-new-ipad",
        timestamp=dt,
        user_id=1,
        known_devices={"device-old-phone"},
        known_locations={"Mumbai, IN"},
        recent_transactions_in_window=2,
        recent_failed_attempts=1,
        historical_transaction_count=5,
        historical_mean_amount=5000.0,
    )

    feats = extract_features_from_context(ctx)

    assert feats["amount"] == 15000.0
    assert feats["hour_of_day"] == 14.0
    assert feats["day_of_week"] == float(dt.weekday())
    assert feats["is_new_device"] == 1.0
    assert feats["is_new_location"] == 1.0
    assert feats["amount_deviation"] == 2.0  # (15000 - 5000) / 5000 = 2.0
    assert feats["user_tx_count_24h"] == 2.0
    assert feats["failed_attempts_count"] == 1.0


def test_extract_features_first_transaction_no_history():
    """First transaction for a user with zero history should have 0 deviations and familiar indicators."""
    dt = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)
    ctx = TransactionContext(
        amount=2500.0,
        merchant="Swiggy",
        category="Food & Dining",
        location="Mumbai, IN",
        device_id="device-initial",
        timestamp=dt,
        user_id=99,
        known_devices=set(),
        known_locations=set(),
        recent_transactions_in_window=0,
        recent_failed_attempts=0,
        historical_transaction_count=0,
        historical_mean_amount=0.0,
    )

    feats = extract_features_from_context(ctx)

    assert feats["amount"] == 2500.0
    assert feats["is_new_device"] == 0.0
    assert feats["is_new_location"] == 0.0
    assert feats["amount_deviation"] == 0.0
    assert feats["user_tx_count_24h"] == 0.0
    assert feats["failed_attempts_count"] == 0.0


def test_context_to_feature_vector_structure():
    dt = datetime.now(timezone.utc)
    ctx = TransactionContext(
        amount=500.0,
        merchant="Uber",
        category="Travel",
        location="Mumbai, IN",
        device_id="device-1",
        timestamp=dt,
        user_id=1,
    )

    vec = context_to_feature_vector(ctx)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (1, len(FEATURE_COLUMNS))
    assert list(FEATURE_COLUMNS) == [
        "amount",
        "hour_of_day",
        "day_of_week",
        "user_tx_count_24h",
        "amount_deviation",
        "is_new_device",
        "is_new_location",
        "failed_attempts_count",
    ]


def test_dataframe_to_feature_matrix_chronological_no_leakage():
    """Verify that batch processing computes rolling features strictly chronologically without future leakage."""
    base_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    # 3 sequential transactions for user 10
    df = pd.DataFrame(
        [
            {
                "user_id": 10,
                "amount": 1000.0,
                "timestamp": base_time.isoformat(),
                "merchant": "Store A",
                "location": "Mumbai, IN",
                "device_id": "phone-1",
                "status": "APPROVED",
            },
            {
                "user_id": 10,
                "amount": 2000.0,
                "timestamp": (base_time + timedelta(hours=2)).isoformat(),
                "merchant": "Store B",
                "location": "Mumbai, IN",
                "device_id": "phone-1",
                "status": "APPROVED",
            },
            {
                "user_id": 10,
                "amount": 6000.0,
                "timestamp": (base_time + timedelta(hours=4)).isoformat(),
                "merchant": "Store C",
                "location": "Dubai, AE",
                "device_id": "laptop-new",
                "status": "APPROVED",
            },
        ]
    )

    mat = dataframe_to_feature_matrix(df)
    assert len(mat) == 3

    # Row 0: First transaction -> no prior transactions
    assert mat.loc[0, "amount"] == 1000.0
    assert mat.loc[0, "user_tx_count_24h"] == 0.0
    assert mat.loc[0, "amount_deviation"] == 0.0
    assert mat.loc[0, "is_new_device"] == 0.0
    assert mat.loc[0, "is_new_location"] == 0.0

    # Row 1: Second transaction 2h later -> sees 1 prior transaction (amount 1000)
    assert mat.loc[1, "amount"] == 2000.0
    assert mat.loc[1, "user_tx_count_24h"] == 1.0
    assert mat.loc[1, "amount_deviation"] == (2000.0 - 1000.0) / 1000.0  # 1.0
    assert mat.loc[1, "is_new_device"] == 0.0  # Same phone-1
    assert mat.loc[1, "is_new_location"] == 0.0  # Same Mumbai

    # Row 2: Third transaction 4h later -> sees 2 prior transactions (mean: 1500)
    assert mat.loc[2, "amount"] == 6000.0
    assert mat.loc[2, "user_tx_count_24h"] == 2.0
    assert mat.loc[2, "amount_deviation"] == (6000.0 - 1500.0) / 1500.0  # 3.0
    assert mat.loc[2, "is_new_device"] == 1.0  # New device
    assert mat.loc[2, "is_new_location"] == 1.0  # New location
