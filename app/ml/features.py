"""Feature Engineering for ML Anomaly Detection.

Ensures strict parity between online transaction context evaluation
and batch dataframe feature extraction, preventing temporal data leakage.
"""

from datetime import timedelta
from typing import Any, Dict, List, Set

import numpy as np
import pandas as pd

from app.risk_engine.rules import TransactionContext

FEATURE_COLUMNS: List[str] = [
    "amount",
    "hour_of_day",
    "day_of_week",
    "user_tx_count_24h",
    "amount_deviation",
    "is_new_device",
    "is_new_location",
    "failed_attempts_count",
]


def extract_features_from_context(ctx: TransactionContext) -> Dict[str, float]:
    """
    Extract a dictionary of numerical features for a single transaction context.
    Ensures exact feature parity between training and online inference.
    """
    amount = float(ctx.amount)
    hour = float(ctx.timestamp.hour)
    day_of_week = float(ctx.timestamp.weekday())

    # Calculate deviation from user's historical mean
    if ctx.historical_transaction_count > 0 and ctx.historical_mean_amount > 0:
        amount_deviation = (amount - ctx.historical_mean_amount) / ctx.historical_mean_amount
    else:
        amount_deviation = 0.0

    is_new_dev = (
        1.0
        if (ctx.historical_transaction_count > 0 and ctx.device_id not in ctx.known_devices)
        else 0.0
    )
    is_new_loc = (
        1.0
        if (ctx.historical_transaction_count > 0 and ctx.location not in ctx.known_locations)
        else 0.0
    )

    return {
        "amount": amount,
        "hour_of_day": hour,
        "day_of_week": day_of_week,
        "user_tx_count_24h": float(ctx.recent_transactions_in_window),
        "amount_deviation": float(amount_deviation),
        "is_new_device": float(is_new_dev),
        "is_new_location": float(is_new_loc),
        "failed_attempts_count": float(ctx.recent_failed_attempts),
    }


def context_to_feature_vector(ctx: TransactionContext) -> np.ndarray:
    """Convert transaction context directly to a 2D numpy feature array for model inference."""
    feat_dict = extract_features_from_context(ctx)
    vector = [feat_dict[col] for col in FEATURE_COLUMNS]
    return np.array([vector], dtype=np.float64)


def dataframe_to_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare feature matrix from a transaction DataFrame.

    Strictly prevents temporal leakage by calculating historical and rolling features
    chronologically using only events occurring prior to each transaction timestamp.
    """
    df_work = df.copy()
    original_index = df_work.index

    # Parse timestamps
    if "timestamp" in df_work.columns:
        df_work["dt"] = pd.to_datetime(df_work["timestamp"], utc=True)
    else:
        df_work["dt"] = pd.Timestamp.now(tz="UTC")

    # If features are already precomputed explicitly, use them directly
    if all(col in df_work.columns for col in FEATURE_COLUMNS):
        return df_work[FEATURE_COLUMNS].astype(float)

    # If user_id is present, compute rolling historical metrics per user chronologically
    if "user_id" in df_work.columns:
        # Sort chronologically to preserve strict temporal sequence
        df_work = df_work.sort_values("dt").reset_index(drop=False)
        # We stored original index in column 'index'
        orig_indices = df_work["index"].values

        feature_rows: List[Dict[str, float]] = []

        # Group by user while maintaining temporal order within each user
        user_histories: Dict[Any, Dict[str, Any]] = {}

        for _, row in df_work.iterrows():
            uid = row.get("user_id", 1)
            t_curr = row["dt"]
            amount = float(row.get("amount", 0.0))
            dev = str(row.get("device_id", ""))
            loc = str(row.get("location", ""))
            status_val = str(row.get("status", "APPROVED")).upper()

            if uid not in user_histories:
                user_histories[uid] = {
                    "known_devices": set(),
                    "known_locations": set(),
                    "tx_records": [],  # (dt, amount, status)
                }

            history = user_histories[uid]
            known_devs: Set[str] = history["known_devices"]
            known_locs: Set[str] = history["known_locations"]
            tx_records = history["tx_records"]

            # Filter historical records strictly BEFORE current transaction
            window_24h_start = t_curr - timedelta(hours=24)
            prior_24h_count = sum(1 for (t, _, _) in tx_records if t >= window_24h_start)
            prior_failed_count = sum(
                1
                for (t, _, s) in tx_records
                if t >= window_24h_start and s in ("FLAGGED", "REJECTED", "SUSPICIOUS")
            )

            hist_count = len(tx_records)
            if hist_count > 0:
                hist_mean = sum(a for (_, a, _) in tx_records) / hist_count
                amount_dev = (amount - hist_mean) / hist_mean if hist_mean > 0 else 0.0
                is_new_dev = 1.0 if (dev and dev not in known_devs) else 0.0
                is_new_loc = 1.0 if (loc and loc not in known_locs) else 0.0
            else:
                amount_dev = 0.0
                is_new_dev = 0.0
                is_new_loc = 0.0

            feature_rows.append(
                {
                    "amount": amount,
                    "hour_of_day": float(t_curr.hour),
                    "day_of_week": float(t_curr.weekday()),
                    "user_tx_count_24h": float(prior_24h_count),
                    "amount_deviation": float(amount_dev),
                    "is_new_device": float(is_new_dev),
                    "is_new_location": float(is_new_loc),
                    "failed_attempts_count": float(prior_failed_count),
                }
            )

            # Update history AFTER computing features for current transaction (no leakage)
            if dev:
                known_devs.add(dev)
            if loc:
                known_locs.add(loc)
            history["tx_records"].append((t_curr, amount, status_val))

        result_df = pd.DataFrame(feature_rows, index=orig_indices)
        # Re-index to match original dataframe ordering
        result_df = result_df.reindex(original_index)
        return result_df[FEATURE_COLUMNS]

    # Fallback for single-row or unassociated dataframe
    feature_rows = []
    for _, row in df_work.iterrows():
        t_curr = row["dt"]
        feature_rows.append(
            {
                "amount": float(row.get("amount", 0.0)),
                "hour_of_day": float(t_curr.hour),
                "day_of_week": float(t_curr.weekday()),
                "user_tx_count_24h": float(row.get("user_tx_count_24h", 0.0)),
                "amount_deviation": float(row.get("amount_deviation", 0.0)),
                "is_new_device": float(row.get("is_new_device", 0.0)),
                "is_new_location": float(row.get("is_new_location", 0.0)),
                "failed_attempts_count": float(row.get("failed_attempts_count", 0.0)),
            }
        )

    result_df = pd.DataFrame(feature_rows, index=original_index)
    return result_df[FEATURE_COLUMNS]
