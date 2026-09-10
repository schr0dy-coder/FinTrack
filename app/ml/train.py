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
    model_version: str = "v1.0.0",
    output_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Train an Isolation Forest anomaly detector on transaction data and persist the artifact.

    Ensures reproducible feature extraction, parameter tracking, and calibration bounds.
    """
    model_file = output_path or settings.ML_MODEL_PATH
    meta_file = metadata_path or settings.ML_METADATA_PATH

    os.makedirs(os.path.dirname(model_file), exist_ok=True)
    os.makedirs(os.path.dirname(meta_file), exist_ok=True)

    logger.info(f"Extracting features from {len(df)} transactions (temporal leakage-free)...")
    X_df = dataframe_to_feature_matrix(df)
    X_raw = X_df.values

    # Preprocessing & Scaling
    preprocessor = MLPreprocessor()
    X_scaled = preprocessor.fit_transform(X_raw)

    # Train Isolation Forest
    logger.info(
        f"Training IsolationForest: n_estimators={n_estimators}, "
        f"contamination={contamination}, random_state={random_state}..."
    )
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Calibrate decision function bounds for score normalization (0 = normal, 100 = anomaly)
    # IsolationForest decision_function: lower values indicate greater anomaly
    raw_scores = model.decision_function(X_scaled)
    min_score = float(np.min(raw_scores))
    max_score = float(np.max(raw_scores))

    # Anomaly rate on training data
    preds = model.predict(X_scaled)
    detected_anomalies = int(np.sum(preds == -1))
    anomaly_pct = float(round((detected_anomalies / len(df)) * 100, 2))

    artifact = {
        "model": model,
        "preprocessor": preprocessor,
        "feature_names": FEATURE_COLUMNS,
        "min_score": min_score,
        "max_score": max_score,
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(df),
    }

    joblib.dump(artifact, model_file)
    logger.info(f"Model artifact saved to '{model_file}'")

    metadata = {
        "model_type": "IsolationForest",
        "model_version": model_version,
        "feature_version": "v1.0.0",
        "training_sample_count": len(df),
        "feature_count": len(FEATURE_COLUMNS),
        "feature_names": FEATURE_COLUMNS,
        "random_state": random_state,
        "contamination": contamination,
        "n_estimators": n_estimators,
        "detected_anomalies_count": detected_anomalies,
        "training_anomaly_rate_pct": anomaly_pct,
        "min_decision_score": min_score,
        "max_decision_score": max_score,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Model metadata saved to '{meta_file}'")

    return metadata
