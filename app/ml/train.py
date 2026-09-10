"""Isolation Forest Model Training Pipeline."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.core.config import settings
from app.core.logging import logger
from app.ml.features import FEATURE_COLUMNS, dataframe_to_feature_matrix
from app.ml.preprocessing import MLPreprocessor


def train_isolation_forest(
    df: pd.DataFrame,
    contamination: float = 0.05,
    n_estimators: int = 150,
    random_state: int = 42,
    train_ratio: float = 0.80,
    model_version: str = "v1.0.0",
    output_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Train an Isolation Forest anomaly detector on transaction data and persist the artifact.

    Implements a strict chronological train/test split:
    - Sorts transactions chronologically.
    - Constructs features using only historical events prior to each timestamp.
    - Fits preprocessor and Isolation Forest model ONLY on the training portion (e.g., first 80%).
    - Calibrates score normalization bounds on the training portion.
    """
    model_file = output_path or settings.ML_MODEL_PATH
    meta_file = metadata_path or settings.ML_METADATA_PATH

    os.makedirs(os.path.dirname(model_file), exist_ok=True)
    os.makedirs(os.path.dirname(meta_file), exist_ok=True)

    # 1. Sort chronologically
    df_sorted = df.copy()
    if "timestamp" in df_sorted.columns:
        df_sorted["dt_temp"] = pd.to_datetime(df_sorted["timestamp"], utc=True)
        df_sorted = df_sorted.sort_values("dt_temp").reset_index(drop=True)
        df_sorted = df_sorted.drop(columns=["dt_temp"])
    else:
        df_sorted = df_sorted.reset_index(drop=True)

    total_rows = len(df_sorted)
    train_size = int(total_rows * train_ratio) if 0.0 < train_ratio < 1.0 else total_rows
    test_size = total_rows - train_size

    logger.info(
        f"Extracting features from {total_rows} transactions using chronological sequence "
        f"(Train: {train_size}, Held-Out Test: {test_size})..."
    )
    # Feature extraction constructs historical features sequentially without future leakage
    X_df = dataframe_to_feature_matrix(df_sorted)
    
    # Split into train and held-out test partitions chronologically
    X_train_df = X_df.iloc[:train_size]
    X_train_raw = X_train_df.values

    # Preprocessing & Scaling fit strictly on training partition
    preprocessor = MLPreprocessor()
    X_train_scaled = preprocessor.fit_transform(X_train_raw)

    # Train Isolation Forest ONLY on training partition
    logger.info(
        f"Training IsolationForest on {train_size} transactions: n_estimators={n_estimators}, "
        f"contamination={contamination}, random_state={random_state}..."
    )
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train_scaled)

    # Calibrate decision function bounds on training data for score normalization (0 = normal, 100 = anomaly)
    raw_scores = model.decision_function(X_train_scaled)
    min_score = float(np.min(raw_scores))
    max_score = float(np.max(raw_scores))

    # Anomaly rate on training data
    preds = model.predict(X_train_scaled)
    detected_anomalies = int(np.sum(preds == -1))
    anomaly_pct = float(round((detected_anomalies / train_size) * 100, 2))

    artifact = {
        "model": model,
        "preprocessor": preprocessor,
        "feature_names": FEATURE_COLUMNS,
        "min_score": min_score,
        "max_score": max_score,
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "total_sample_count": total_rows,
        "train_sample_count": train_size,
        "test_sample_count": test_size,
        "split_strategy": f"Chronological {int(round(train_ratio*100))}/{int(round((1-train_ratio)*100))}",
    }

    joblib.dump(artifact, model_file)
    logger.info(f"Model artifact saved to '{model_file}'")

    metadata = {
        "model_type": "IsolationForest",
        "model_version": model_version,
        "feature_version": "v1.0.0",
        "dataset_total_count": total_rows,
        "training_sample_count": train_size,
        "held_out_test_sample_count": test_size,
        "split_strategy": f"Chronological {int(round(train_ratio*100))}/{int(round((1-train_ratio)*100))}",
        "evaluation_scope": "Held-out test set only",
        "feature_count": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "random_state": random_state,
        "contamination": contamination,
        "n_estimators": n_estimators,
        "training_detected_anomalies_count": detected_anomalies,
        "training_anomaly_rate_pct": anomaly_pct,
        "min_decision_score": min_score,
        "max_decision_score": max_score,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Model metadata saved to '{meta_file}'")

    return metadata
