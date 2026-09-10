"""Machine Learning Model Evaluation Script.

Evaluates unsupervised Isolation Forest predictions against ground-truth synthetic anomaly labels.
Computes Precision, Recall, F1-Score, Confusion Matrix, ROC-AUC, and breakdown by anomaly type.
Generates documentation report in docs/ml_evaluation.md.
"""

import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.ml.features import dataframe_to_feature_matrix


def evaluate_model(
    data_path: str = "data/synthetic/transactions.csv",
    model_path: str = "models/artifacts/isolation_forest.joblib",
    output_doc_path: str = "docs/ml_evaluation.md",
) -> dict:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_data_path = os.path.join(root_dir, data_path)
    full_model_path = os.path.join(root_dir, model_path)
    full_doc_path = os.path.join(root_dir, output_doc_path)

    if not os.path.exists(full_data_path):
        raise FileNotFoundError(f"Dataset not found at {full_data_path}")
    if not os.path.exists(full_model_path):
        raise FileNotFoundError(f"Model artifact not found at {full_model_path}")

    print(f"Loading evaluation dataset from '{full_data_path}'...")
    df = pd.read_csv(full_data_path)

    print(f"Loading trained model artifact from '{full_model_path}'...")
    artifact = joblib.load(full_model_path)
    model = artifact["model"]
    preprocessor = artifact["preprocessor"]
    model_version = artifact.get("model_version", "v1.0.0")

    print(f"Extracting features for {len(df)} transactions...")
    X_df = dataframe_to_feature_matrix(df)
    X_scaled = preprocessor.transform(X_df.values)

    # Ground truth
    y_true = df["is_anomaly"].values.astype(int)

    # Predictions: IsolationForest returns 1 for normal, -1 for anomaly
    raw_preds = model.predict(X_scaled)
    y_pred = (raw_preds == -1).astype(int)

    # Decision function (higher negative value = more anomalous)
    decision_scores = model.decision_function(X_scaled)
    # Invert so higher score = higher probability of anomaly
    anomaly_scores = -decision_scores

    # Calculate metrics
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    roc_auc = float(roc_auc_score(y_true, anomaly_scores))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # Per-anomaly type breakdown
    type_breakdown = {}
    if "anomaly_type" in df.columns:
        for atype, grp in df.groupby("anomaly_type"):
            indices = grp.index
            subset_pred = y_pred[indices]
            detected = int(np.sum(subset_pred == 1))
            total = len(grp)
            type_breakdown[atype] = {
                "total": total,
                "detected": detected,
                "detection_rate_pct": round((detected / total) * 100, 2),
            }

    results = {
        "model_version": model_version,
        "sample_count": len(df),
        "normal_count": int(np.sum(y_true == 0)),
        "anomaly_count": int(np.sum(y_true == 1)),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(acc, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "anomaly_type_breakdown": type_breakdown,
    }

    # Generate Markdown documentation
    os.makedirs(os.path.dirname(full_doc_path), exist_ok=True)
    md_content = f"""# Machine Learning Model Evaluation Report

## 1. Overview & Setup

- **Model Type:** Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Model Version:** `{model_version}`
- **Dataset Size:** {len(df):,} transactions ({results["normal_count"]:,} normal, {results["anomaly_count"]:,} anomalous)
- **Anomaly Ratio:** {round(results["anomaly_count"] / len(df) * 100, 2)}%
- **Feature Count:** {len(artifact["feature_names"])} features
- **Features Used:** `{", ".join(artifact["feature_names"])}`
- **Contamination Parameter:** {model.contamination}
- **Random Seed:** {model.random_state}

---

## 2. Quantitative Performance Metrics

| Metric | Score | Explanation |
|---|---|---|
| **Precision** | **{results["precision"]:.4f}** ({results["precision"] * 100:.1f}%) | Proportion of predicted anomalies that were actual anomalies |
| **Recall** | **{results["recall"]:.4f}** ({results["recall"] * 100:.1f}%) | Proportion of actual anomalies successfully identified |
| **F1-Score** | **{results["f1_score"]:.4f}** | Harmonic mean of precision and recall |
| **ROC-AUC** | **{results["roc_auc"]:.4f}** | Area under the Receiver Operating Characteristic curve |
| **Accuracy** | **{results["accuracy"]:.4f}** | Overall classification accuracy across imbalanced classes |

---

## 3. Confusion Matrix

| | Predicted Normal | Predicted Anomaly |
|---|---|---|
| **Actual Normal** | **{tn:,}** (TN) | **{fp:,}** (FP) |
| **Actual Anomaly** | **{fn:,}** (FN) | **{tp:,}** (TP) |

- **True Negatives (TN):** {tn:,} legitimate transactions correctly classified as normal.
- **False Positives (FP):** {fp:,} normal transactions flagged as suspicious (investigated by analysts).
- **False Negatives (FN):** {fn:,} anomalies missed by unsupervised ML (covered by deterministic rules).
- **True Positives (TP):** {tp:,} anomalous transactions successfully captured.

---

## 4. Anomaly Type Detection Breakdown

| Anomaly Type | Total Samples | Detected | Detection Rate (%) |
|---|---|---|---|
"""
    for atype, stats in type_breakdown.items():
        md_content += f"| `{atype}` | {stats['total']} | {stats['detected']} | **{stats['detection_rate_pct']}%** |\n"

    md_content += """
---

## 5. Technical Limitations & Discussion

1. **Unsupervised Anomaly Trade-Offs:** Isolation Forest learns data isolation geometry rather than explicit class boundaries. It detects zero-day and multi-feature distributional anomalies without requiring labeled historical fraud.
2. **Hybrid Architecture Advantage:** The standalone ML recall is supplemented by deterministic business rules (`HighAmountRule`, `RapidTransactionsRule`, `NewDeviceRule`, `LocationAnomalyRule`, `FailedAttemptRule`). Even when subtle behavioral anomalies score low on ML, deterministic rules catch clear violations.
3. **Operational Thresholding:** In the hybrid scoring formula ($0.60 \\times \\text{Rule} + 0.40 \\times \\text{ML}$), transactions scoring above 60 trigger alerts for human analyst review.
"""

    with open(full_doc_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nML Evaluation complete! Report saved to '{full_doc_path}'")
    return results


def main():
    results = evaluate_model()
    print("\nEvaluation Summary:")
    print(f"  Precision: {results['precision']}")
    print(f"  Recall:    {results['recall']}")
    print(f"  F1-Score:  {results['f1_score']}")
    print(f"  ROC-AUC:   {results['roc_auc']}")
    print(f"  Confusion Matrix: {results['confusion_matrix']}")


if __name__ == "__main__":
    main()
