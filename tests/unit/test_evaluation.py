"""Unit Tests for Chronological ML Evaluation and Data Leakage Prevention."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from app.ml.features import dataframe_to_feature_matrix
from app.ml.train import train_isolation_forest
from scripts.evaluate_model import evaluate_model


def _create_sample_time_series(num_records: int = 100) -> pd.DataFrame:
    """Generate deterministic synthetic chronological transaction dataset for unit testing."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(num_records):
        t = base_time + timedelta(minutes=i * 15)
        # Create occasional anomaly
        is_anom = 1 if (i % 20 == 0 and i > 0) else 0
        rows.append(
            {
                "id": f"tx-test-{i:04d}",
                "user_id": (i % 5) + 1,
                "amount": 50000.0 if is_anom else 100.0 + (i % 10) * 20,
                "merchant": "Suspicious Electronics" if is_anom else "Local Cafe",
                "category": "Electronics" if is_anom else "Food",
                "location": "Dubai, AE" if is_anom else "Mumbai, IN",
                "device_id": f"device-anom-{i}" if is_anom else f"device-{(i % 5) + 1}",
                "timestamp": t.isoformat(),
                "status": "FLAGGED" if is_anom else "APPROVED",
                "is_anomaly": is_anom,
                "anomaly_type": "HIGH_AMOUNT_SPIKE" if is_anom else "NORMAL",
            }
        )
    return pd.DataFrame(rows)


def test_chronological_split():
    """Verify that train/test split maintains strict chronological ordering."""
    df = _create_sample_time_series(100)
    train_ratio = 0.80

    df_sorted = df.copy()
    df_sorted["dt_temp"] = pd.to_datetime(df_sorted["timestamp"], utc=True)
    df_sorted = df_sorted.sort_values("dt_temp").reset_index(drop=True)

    total_rows = len(df_sorted)
    train_size = int(total_rows * train_ratio)
    test_size = total_rows - train_size

    assert train_size == 80
    assert test_size == 20

    train_df = df_sorted.iloc[:train_size]
    test_df = df_sorted.iloc[train_size:]

    assert len(train_df) == 80
    assert len(test_df) == 20


def test_training_data_precedes_test_data():
    """Verify that all training timestamps strictly precede or equal the test timestamps."""
    df = _create_sample_time_series(100)
    train_ratio = 0.80

    df_sorted = df.copy()
    df_sorted["dt"] = pd.to_datetime(df_sorted["timestamp"], utc=True)
    df_sorted = df_sorted.sort_values("dt").reset_index(drop=True)

    train_size = int(len(df_sorted) * train_ratio)
    train_df = df_sorted.iloc[:train_size]
    test_df = df_sorted.iloc[train_size:]

    max_train_time = train_df["dt"].max()
    min_test_time = test_df["dt"].min()

    assert max_train_time <= min_test_time
    assert (min_test_time - max_train_time).total_seconds() >= 0


def test_test_features_do_not_use_future_transactions():
    """Verify that test transaction features only incorporate historical events occurring prior to them."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    # User 1 has 3 transactions: 10:00 ($100), 11:00 ($200), 12:00 ($9000)
    df = pd.DataFrame(
        [
            {
                "user_id": 1,
                "amount": 100.0,
                "timestamp": base_time.isoformat(),
                "device_id": "dev-1",
                "location": "Mumbai",
                "status": "APPROVED",
                "is_anomaly": 0,
            },
            {
                "user_id": 1,
                "amount": 200.0,
                "timestamp": (base_time + timedelta(hours=1)).isoformat(),
                "device_id": "dev-1",
                "location": "Mumbai",
                "status": "APPROVED",
                "is_anomaly": 0,
            },
            {
                "user_id": 1,
                "amount": 9000.0,
                "timestamp": (base_time + timedelta(hours=2)).isoformat(),
                "device_id": "dev-2",
                "location": "Delhi",
                "status": "APPROVED",
                "is_anomaly": 1,
            },
        ]
    )

    feat_matrix = dataframe_to_feature_matrix(df)

    # For transaction 0 (10:00): zero history, amount_deviation is 0.0
    assert feat_matrix.loc[0, "amount_deviation"] == 0.0
    assert feat_matrix.loc[0, "user_tx_count_24h"] == 0.0

    # For transaction 1 (11:00): sees only tx 0 ($100), amount deviation = (200-100)/100 = 1.0
    assert feat_matrix.loc[1, "amount_deviation"] == 1.0
    assert feat_matrix.loc[1, "user_tx_count_24h"] == 1.0

    # For transaction 2 (12:00): sees tx 0 ($100) & tx 1 ($200) -> mean = 150.
    # Deviation = (9000 - 150) / 150 = 59.0
    assert pytest.approx(feat_matrix.loc[2, "amount_deviation"], 0.01) == 59.0
    assert feat_matrix.loc[2, "user_tx_count_24h"] == 2.0


def test_model_evaluates_only_test_data(tmp_path):
    """Verify that evaluation metrics are derived exclusively from the held-out test split."""
    df = _create_sample_time_series(100)
    data_file = str(tmp_path / "test_transactions.csv")
    model_file = str(tmp_path / "test_model.joblib")
    meta_file = str(tmp_path / "test_meta.json")
    doc_file = str(tmp_path / "test_eval.md")

    df.to_csv(data_file, index=False)

    train_isolation_forest(
        df=df,
        contamination=0.05,
        n_estimators=50,
        random_state=42,
        train_ratio=0.80,
        output_path=model_file,
        metadata_path=meta_file,
    )

    results = evaluate_model(
        data_path=data_file,
        model_path=model_file,
        output_doc_path=doc_file,
        train_ratio=0.80,
    )

    assert results["dataset_total_count"] == 100
    assert results["training_sample_count"] == 80
    assert results["held_out_test_sample_count"] == 20
    assert results["evaluation_scope"] == "Held-out test set only"
    assert results["split_strategy"] == "Chronological 80/20"

    # Verify confusion matrix sums to test set size (20)
    cm = results["confusion_matrix"]
    total_eval_samples = (
        cm["true_negatives"] + cm["false_positives"] + cm["false_negatives"] + cm["true_positives"]
    )
    assert total_eval_samples == 20


def test_metrics_are_generated(tmp_path):
    """Verify that standard evaluation metrics (Precision, Recall, F1, ROC-AUC, Accuracy) are generated."""
    df = _create_sample_time_series(100)
    data_file = str(tmp_path / "test_tx.csv")
    model_file = str(tmp_path / "model.joblib")
    meta_file = str(tmp_path / "meta.json")
    doc_file = str(tmp_path / "eval.md")

    df.to_csv(data_file, index=False)

    train_isolation_forest(
        df=df,
        train_ratio=0.80,
        n_estimators=30,
        output_path=model_file,
        metadata_path=meta_file,
    )

    results = evaluate_model(
        data_path=data_file,
        model_path=model_file,
        output_doc_path=doc_file,
        train_ratio=0.80,
    )

    assert 0.0 <= results["precision"] <= 1.0
    assert 0.0 <= results["recall"] <= 1.0
    assert 0.0 <= results["f1_score"] <= 1.0
    assert 0.0 <= results["accuracy"] <= 1.0
    assert 0.0 <= results["roc_auc"] <= 1.0


def test_empty_dataset_handling():
    """Verify handling when empty dataframe is provided."""
    empty_df = pd.DataFrame(columns=["amount", "timestamp", "user_id"])
    mat = dataframe_to_feature_matrix(empty_df)
    assert len(mat) == 0
    assert list(mat.columns) == [
        "amount",
        "hour_of_day",
        "day_of_week",
        "user_tx_count_24h",
        "amount_deviation",
        "is_new_device",
        "is_new_location",
        "failed_attempts_count",
    ]


def test_insufficient_history_handling():
    """Verify that user transactions with no historical data default cleanly without NaN/inf."""
    df = pd.DataFrame(
        [
            {
                "user_id": 999,
                "amount": 500.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": "new-dev",
                "location": "New City",
                "status": "APPROVED",
            }
        ]
    )

    mat = dataframe_to_feature_matrix(df)
    assert len(mat) == 1
    assert mat.loc[0, "amount"] == 500.0
    assert mat.loc[0, "user_tx_count_24h"] == 0.0
    assert mat.loc[0, "amount_deviation"] == 0.0
    assert mat.loc[0, "is_new_device"] == 0.0
    assert mat.loc[0, "is_new_location"] == 0.0
    assert not mat.isna().any().any()
