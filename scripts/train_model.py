"""Train and export Isolation Forest ML model."""

import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from app.ml.train import train_isolation_forest
from scripts.evaluate_model import evaluate_model
from scripts.generate_dataset import generate_synthetic_transactions


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(root_dir, "data", "synthetic", "transactions.csv")
    model_path = os.path.join(root_dir, "models", "artifacts", "isolation_forest.joblib")
    meta_path = os.path.join(root_dir, "models", "artifacts", "model_metadata.json")

    if not os.path.exists(data_path):
        print(
            f"Dataset not found at '{data_path}'. Generating fresh synthetic dataset (5,000 records)..."
        )
        df = generate_synthetic_transactions(
            num_transactions=5000,
            num_users=50,
            anomaly_ratio=0.06,
            random_seed=42,
        )
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df.to_csv(data_path, index=False)
    else:
        print(f"Loading training data from '{data_path}'...")
        df = pd.read_csv(data_path)

    print(f"Training ML Isolation Forest on {len(df)} transactions...")
    metadata = train_isolation_forest(
        df=df,
        contamination=0.05,
        n_estimators=150,
        random_state=42,
        model_version="v1.0.0",
        output_path=model_path,
        metadata_path=meta_path,
    )

    print("\nModel Training Completed Successfully!")
    print(f"Artifact: {model_path}")
    print(f"Metadata: {meta_path}")
    print("\nMetadata Summary:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")

    print("\nRunning Model Evaluation...")
    eval_results = evaluate_model(
        data_path="data/synthetic/transactions.csv",
        model_path="models/artifacts/isolation_forest.joblib",
        output_doc_path="docs/ml_evaluation.md",
    )
    print(f"F1-Score: {eval_results['f1_score']}, ROC-AUC: {eval_results['roc_auc']}")


if __name__ == "__main__":
    main()
