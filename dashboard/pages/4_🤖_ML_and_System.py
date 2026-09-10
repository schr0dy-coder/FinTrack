import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

try:
    from dashboard.utils import (
        fetch_api_health,
        fetch_model_status_api,
        render_sidebar,
        retrain_model_api,
    )
except ImportError:
    from utils import fetch_api_health, fetch_model_status_api, render_sidebar, retrain_model_api

st.set_page_config(page_title="ML & System | FinTrack", page_icon="🤖", layout="wide")

# Render Sidebar
render_sidebar()

st.title("🤖 Machine Learning & System Architecture")
st.caption(
    "Inspect active Isolation Forest anomaly models, engineered feature vectors, and trigger retraining"
)

tab_ml, tab_health = st.tabs(
    ["🧠 ML Model Registry & Retraining", "🖥️ System & Database Diagnostics"]
)

with tab_ml:
    model_status = fetch_model_status_api()

    if not model_status:
        st.error("Could not fetch ML model status from API.")
    else:
        # Metrics Row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric(
                "Model Status", "ACTIVE & LOADED" if model_status["model_loaded"] else "OFFLINE"
            )
        with m_col2:
            st.metric("Model Version", model_status["model_version"])
        with m_col3:
            st.metric("Algorithm", model_status["model_type"])
        with m_col4:
            st.metric("Training Records", f"{model_status.get('training_sample_count', 5000):,}")

        st.divider()

        # Features & Training Parameters
        f_col1, f_col2 = st.columns([1.4, 1.6])

        with f_col1:
            st.subheader("🧬 Engineered Feature Vector")
            st.markdown(
                """
                The ML model extracts 8 deterministic, behavioral features for every transaction context:
                - `amount`: Monetary value in INR.
                - `hour_of_day`: Transaction hour (0–23).
                - `day_of_week`: Day of week (0=Mon, 6=Sun).
                - `user_tx_count_24h`: Transaction frequency in the last 24 hours.
                - `amount_deviation`: Ratio deviation relative to user's historical spend mean.
                - `is_new_device`: Binary signal flag for new/unrecognized device.
                - `is_new_location`: Binary signal flag for anomalous/unfamiliar location.
                - `failed_attempts_count`: Number of recent failed or rejected attempts.
                """
            )

        with f_col2:
            st.subheader("⚙️ Model Hyperparameters & Training")
            metrics = model_status.get("metrics") or {}
            st.json(
                {
                    "Algorithm": "Isolation Forest (scikit-learn)",
                    "Contamination": metrics.get("contamination", 0.05),
                    "n_estimators": metrics.get("n_estimators", 150),
                    "Trained At": model_status.get("trained_at", "N/A"),
                    "Training Anomaly Rate": f"{metrics.get('training_anomaly_rate_pct', 5.0)}%",
                    "Weight in Hybrid Engine": "40% ML + 60% Rules",
                }
            )

            st.subheader("🔄 Model Retraining")
            st.caption(
                "Trigger an offline retraining cycle to fit on current database transaction streams."
            )

            if st.button(
                "🚀 Retrain Isolation Forest Model", type="primary", use_container_width=True
            ):
                with st.spinner("Retraining Isolation Forest model on transaction history..."):
                    ok, msg = retrain_model_api()
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"Retraining failed: {msg}")

with tab_health:
    st.subheader("🖥️ Platform Infrastructure Health")
    health = fetch_api_health()

    h_col1, h_col2, h_col3 = st.columns(3)
    with h_col1:
        st.metric("API Server", health.get("status", "offline").upper())
    with h_col2:
        st.metric("Database", health.get("database", {}).get("status", "unknown").upper())
    with h_col3:
        st.metric("DB Latency", f"{health.get('database', {}).get('latency_ms', 0)} ms")

    st.markdown("#### Full System Diagnostic Payload:")
    st.json(health)
