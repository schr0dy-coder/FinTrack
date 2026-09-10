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
    train_ratio: float = 0.80,
) -> dict:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_data_path = os.path.join(root_dir, data_path)
    full_model_path = os.path.join(root_dir, model_path)
    full_doc_path = os.path.join(root_dir, output_doc_path)

    if not os.path.exists(full_data_path):
        raise FileNotFoundError(f"Dataset not found at {full_data_path}")
    if not os.path.exists(full_model_path):
        raise FileNotFoundError(f"Model artifact not found at {full_model_path}")

    print(f"Loading dataset from '{full_data_path}'...")
    df = pd.read_csv(full_data_path)

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

    train_pct = int(round(train_ratio * 100))
    test_pct = int(round((1 - train_ratio) * 100))

    print(f"Dataset size: {total_rows} total transactions")
    print(f"Chronological Split: Training = {train_size} rows (first {train_pct}%), Held-out Test = {test_size} rows (last {test_pct}%)")

    # 2. Extract features chronologically across the timeline (each row sees only strictly prior events)
    print("Extracting features chronologically without temporal leakage...")
    X_df = dataframe_to_feature_matrix(df_sorted)

    # 3. Partition into training baseline and held-out test set
    test_df = df_sorted.iloc[train_size:].reset_index(drop=True)
    X_test_df = X_df.iloc[train_size:].reset_index(drop=True)
    X_test_raw = X_test_df.values

    # 4. Load trained model artifact (trained only on training partition)
    print(f"Loading trained model artifact from '{full_model_path}'...")
    artifact = joblib.load(full_model_path)
    model = artifact["model"]
    preprocessor = artifact["preprocessor"]
    model_version = artifact.get("model_version", "v1.0.0")

    # 5. Transform test features using fitted preprocessor
    X_test_scaled = preprocessor.transform(X_test_raw)

    # Ground truth labels for held-out test set
    y_test_true = test_df["is_anomaly"].values.astype(int)

    # Predictions on held-out test set: IsolationForest returns 1 for normal, -1 for anomaly
    raw_preds = model.predict(X_test_scaled)
    y_test_pred = (raw_preds == -1).astype(int)

    # Decision function (higher negative value = more anomalous)
    decision_scores = model.decision_function(X_test_scaled)
    # Invert so higher score = higher probability of anomaly
    anomaly_scores = -decision_scores

    # Calculate test-set metrics
    precision = float(precision_score(y_test_true, y_test_pred, zero_division=0))
    recall = float(recall_score(y_test_true, y_test_pred, zero_division=0))
    f1 = float(f1_score(y_test_true, y_test_pred, zero_division=0))
    acc = float(accuracy_score(y_test_true, y_test_pred))
    roc_auc = float(roc_auc_score(y_test_true, anomaly_scores))

    cm = confusion_matrix(y_test_true, y_test_pred)
    tn, fp, fn, tp = cm.ravel()

    # Per-anomaly type breakdown on held-out test set
    type_breakdown = {}
    if "anomaly_type" in test_df.columns:
        for atype, grp in test_df.groupby("anomaly_type"):
            indices = grp.index
            subset_pred = y_test_pred[indices]
            detected = int(np.sum(subset_pred == 1))
            total = len(grp)
            type_breakdown[atype] = {
                "total": total,
                "detected": detected,
                "detection_rate_pct": round((detected / total) * 100, 2),
            }

    test_normal_count = int(np.sum(y_test_true == 0))
    test_anomaly_count = int(np.sum(y_test_true == 1))

    results = {
        "model_version": model_version,
        "dataset_total_count": total_rows,
        "training_sample_count": train_size,
        "held_out_test_sample_count": test_size,
        "split_strategy": f"Chronological {train_pct}/{test_pct}",
        "evaluation_scope": "Held-out test set only",
        "test_normal_count": test_normal_count,
        "test_anomaly_count": test_anomaly_count,
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
- **Total Dataset Size:** {total_rows:,} transactions
- **Evaluation Methodology:** Chronological 80/20 Train/Test Split (Held-Out Evaluation)
- **Training Set Size:** {train_size:,} transactions (first {train_pct}% chronologically)
- **Held-Out Test Set Size:** {test_size:,} transactions (last {test_pct}% chronologically)
- **Test Set Breakdown:** {test_normal_count:,} normal, {test_anomaly_count:,} anomalous ({round(test_anomaly_count / test_size * 100, 2)}% anomaly ratio)
- **Feature Count:** {len(artifact["feature_names"])} features
- **Features Used:** `{", ".join(artifact["feature_names"])}`
- **Contamination Parameter:** {model.contamination}
- **Random Seed:** {model.random_state}
- **Data Leakage Safeguard:** Historical-only rolling feature construction with strict temporal ordering; test set evaluated on genuinely held-out transactions.

---

## 2. Quantitative Performance Metrics (Held-Out Test Set)

| Metric | Score | Explanation |
|---|---|---|
| **Precision** | **{results["precision"]:.4f}** ({results["precision"] * 100:.1f}%) | Proportion of predicted anomalies in test set that were actual anomalies |
| **Recall** | **{results["recall"]:.4f}** ({results["recall"] * 100:.1f}%) | Proportion of actual test set anomalies successfully captured |
| **F1-Score** | **{results["f1_score"]:.4f}** | Harmonic mean of precision and recall on held-out test data |
| **ROC-AUC** | **{results["roc_auc"]:.4f}** | Area under the Receiver Operating Characteristic curve on test data |
| **Accuracy** | **{results["accuracy"]:.4f}** | Overall classification accuracy across test set transactions |

---

## 3. Confusion Matrix (Held-Out Test Set: {test_size:,} Transactions)

| | Predicted Normal | Predicted Anomaly |
|---|---|---|
| **Actual Normal** | **{tn:,}** (TN) | **{fp:,}** (FP) |
| **Actual Anomaly** | **{fn:,}** (FN) | **{tp:,}** (TP) |

- **True Negatives (TN):** {tn:,} legitimate transactions correctly classified as normal.
- **False Positives (FP):** {fp:,} normal transactions flagged as suspicious (investigated by analysts).
- **False Negatives (FN):** {fn:,} anomalies missed by unsupervised ML (covered by deterministic rules).
- **True Positives (TP):** {tp:,} anomalous transactions successfully captured.

---

## 4. Anomaly Type Detection Breakdown (Held-Out Test Set)

| Anomaly Type | Test Samples | Detected | Detection Rate (%) |
|---|---|---|---|
"""
    for atype, stats in type_breakdown.items():
        md_content += f"| `{atype}` | {stats['total']} | {stats['detected']} | **{stats['detection_rate_pct']}%** |\n"

    md_content += """
---

## 5. Technical Limitations & Hybrid System Discussion

1. **Unsupervised Anomaly Trade-Offs:** Isolation Forest learns data isolation geometry rather than explicit class boundaries. It detects zero-day and multi-feature distributional anomalies without requiring labeled historical fraud.
2. **Hybrid Architecture Advantage:** Standalone ML recall on complex velocity patterns is supplemented by deterministic business rules (`HighAmountRule`, `RapidTransactionsRule`, `NewDeviceRule`, `LocationAnomalyRule`, `FailedAttemptRule`). Even when subtle behavioral anomalies score moderate on ML, deterministic rules catch clear policy violations.
3. **Operational Thresholding:** In the hybrid scoring formula ($0.60 \\times \\text{Rule} + 0.40 \\times \\text{ML}$), transactions scoring above 60 trigger alerts for human analyst review.
"""

    with open(full_doc_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nML Evaluation complete! Report saved to '{full_doc_path}'")
    return results


def main():
    results = evaluate_model()
    print("\nHeld-Out Test Evaluation Summary:")
    print(f"  Split:     {results['split_strategy']}")
    print(f"  Test Size: {results['held_out_test_sample_count']} transactions")
    print(f"  Precision: {results['precision']}")
    print(f"  Recall:    {results['recall']}")
    print(f"  F1-Score:  {results['f1_score']}")
    print(f"  ROC-AUC:   {results['roc_auc']}")
    print(f"  Accuracy:  {results['accuracy']}")
    print(f"  Confusion Matrix: {results['confusion_matrix']}")


if __name__ == "__main__":
    main()
