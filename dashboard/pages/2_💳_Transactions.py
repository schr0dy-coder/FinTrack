import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.utils import fetch_transactions, render_sidebar, submit_transaction_api
except ImportError:
    from utils import fetch_transactions, render_sidebar, submit_transaction_api

st.set_page_config(page_title="Transactions | FinTrack", page_icon="💳", layout="wide")

# Render Sidebar
render_sidebar()

st.title("💳 Transaction Intelligence & Live Simulator")
st.caption("Inspect live transaction streams, analyze risk signals, and simulate fraud scenarios")

tab_explorer, tab_simulator = st.tabs(
    ["🔍 Transaction Explorer & Inspector", "⚡ Live Transaction Simulator"]
)

with tab_explorer:
    # Filter Bar
    with st.expander("Filter Transactions", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            risk_filter = st.selectbox("Risk Level", ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
        with f_col2:
            status_filter = st.selectbox("Status", ["ALL", "APPROVED", "SUSPICIOUS", "FLAGGED"])
        with f_col3:
            merchant_filter = st.text_input("Merchant Contains", placeholder="e.g. Amazon, Rolex")
        with f_col4:
            min_amt = st.number_input("Min Amount (₹)", min_value=0.0, value=0.0, step=500.0)

    # Fetch Transactions
    res = fetch_transactions(
        page=1,
        limit=50,
        risk_level=risk_filter,
        status_val=status_filter,
        merchant=merchant_filter,
        min_amount=min_amt if min_amt > 0 else None,
    )
    items = res.get("items", [])
    total_tx = res.get("total", 0)

    st.markdown(f"**Found {total_tx} matching transactions:**")

    if items:
        # Build table DataFrame
        table_rows = []
        for it in items:
            risk_info = it.get("risk_assessment") or {}
            table_rows.append(
                {
                    "ID": it["id"][:8] + "...",
                    "Full_ID": it["id"],
                    "Timestamp": it["timestamp"][:19].replace("T", " "),
                    "Merchant": it["merchant"],
                    "Category": it.get("category", "General"),
                    "Amount": f"₹{it['amount']:,.2f}",
                    "Raw_Amount": it["amount"],
                    "Location": it["location"],
                    "Device": it["device_id"],
                    "Risk Level": risk_info.get("risk_level", "LOW"),
                    "Risk Score": risk_info.get("final_score", 0.0),
                    "Status": it["status"],
                }
            )

        df_display = pd.DataFrame(table_rows)

        # Show Table
        st.dataframe(
            df_display[
                [
                    "ID",
                    "Timestamp",
                    "Merchant",
                    "Category",
                    "Amount",
                    "Location",
                    "Risk Level",
                    "Risk Score",
                    "Status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # Deep Transaction Inspector
        st.subheader("🔬 Deep Risk Breakdown Inspector")
        selected_tx_id = st.selectbox(
            "Select a transaction to inspect rule & ML signals:",
            options=[r["Full_ID"] for r in table_rows],
            format_func=lambda x: next(
                (
                    f"{r['ID']} | {r['Merchant']} | {r['Amount']} | Risk: {r['Risk Level']} ({r['Risk Score']}/100)"
                    for r in table_rows
                    if r["Full_ID"] == x
                ),
                x,
            ),
        )

        selected_tx = next((it for it in items if it["id"] == selected_tx_id), None)

        if selected_tx:
            risk = selected_tx.get("risk_assessment") or {}
            col_meta, col_gauge, col_reasons = st.columns([1.2, 1.2, 1.6])

            with col_meta:
                st.markdown("#### 📋 Metadata")
                st.markdown(f"**Transaction ID:** `{selected_tx['id']}`")
                st.markdown(f"**Amount:** `₹{selected_tx['amount']:,.2f}`")
                st.markdown(
                    f"**Merchant:** `{selected_tx['merchant']}` ({selected_tx.get('category', 'General')})"
                )
                st.markdown(f"**Location:** `{selected_tx['location']}`")
                st.markdown(f"**Device ID:** `{selected_tx['device_id']}`")
                st.markdown(f"**Timestamp:** `{selected_tx['timestamp']}`")
                st.markdown(f"**Operational Status:** `{selected_tx['status']}`")

            with col_gauge:
                st.markdown("#### 🎯 Risk Score")
                score = risk.get("final_score", 0.0)
                level = risk.get("risk_level", "LOW")

                fig_gauge = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": f"Level: {level}", "font": {"size": 18}},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1},
                            "bar": {
                                "color": "#ef4444"
                                if score >= 80
                                else "#f97316"
                                if score >= 60
                                else "#f59e0b"
                                if score >= 30
                                else "#10b981"
                            },
                            "steps": [
                                {"range": [0, 30], "color": "rgba(16, 185, 129, 0.2)"},
                                {"range": [30, 60], "color": "rgba(245, 158, 11, 0.2)"},
                                {"range": [60, 80], "color": "rgba(249, 115, 22, 0.2)"},
                                {"range": [80, 100], "color": "rgba(239, 68, 68, 0.2)"},
                            ],
                            "threshold": {
                                "line": {"color": "white", "width": 3},
                                "thickness": 0.75,
                                "value": score,
                            },
                        },
                    )
                )
                fig_gauge.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=200,
                )
                st.plotly_chart(fig_gauge, use_container_width=True)
                st.caption(
                    f"Weights: Rule 60% (`{risk.get('rule_score', 0)}`) + ML 40% (`{risk.get('ml_score', 0)}`)"
                )

            with col_reasons:
                st.markdown("#### 🛡️ Signal & Rules Breakdown")
                reasons = risk.get("reasons", [])
                triggered_any = False

                for r in reasons:
                    if r.get("triggered"):
                        triggered_any = True
                        st.error(
                            f"❌ **{r.get('code')}** (+{r.get('score')} pts)\n{r.get('reason')}"
                        )

                if not triggered_any:
                    st.success(
                        "✅ **No deterministic risk rules triggered.** Transaction within normal parameters."
                    )

                st.info(
                    f"🤖 **ML Model ({risk.get('model_version', 'v1.0.0')}):** Anomaly score evaluated at **{risk.get('ml_score', 0.0)}/100**."
                )
    else:
        st.info("No transactions found matching the filter criteria.")

with tab_simulator:
    st.subheader("⚡ Live Transaction Simulator")
    st.markdown(
        "Submit a transaction payload to test the real-time scoring engine against any scenario."
    )

    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        sim_amount = st.number_input(
            "Transaction Amount (₹)", min_value=1.0, value=85000.0, step=1000.0
        )
        sim_merchant = st.text_input("Merchant Name", value="Tanishq Gold & Diamonds")
        sim_category = st.selectbox(
            "Category",
            [
                "Shopping",
                "Luxury & Jewelry",
                "Electronics",
                "Food & Dining",
                "Travel",
                "Utilities",
                "General",
            ],
        )
        sim_location = st.text_input("Location", value="Dubai, AE")
        sim_device = st.text_input("Device ID", value="device-unknown-emulator-99")

        preset = st.selectbox(
            "Quick Scenario Presets",
            [
                "Custom",
                "Scenario A: Normal Grocery (₹750, Known Device & Home City)",
                "Scenario B: High Value Spike (₹85,000, Home City)",
                "Scenario C: International Location Anomaly (₹45,000 in Dubai)",
                "Scenario D: Critical Fraud Attempt (₹280,000 in London with Emulator)",
            ],
        )

        if preset == "Scenario A: Normal Grocery (₹750, Known Device & Home City)":
            sim_amount = 750.0
            sim_merchant = "DMart Supermarket"
            sim_category = "Groceries"
            sim_location = "Mumbai, IN"
            sim_device = "device-iphone-john"
        elif preset == "Scenario B: High Value Spike (₹85,000, Home City)":
            sim_amount = 85000.0
            sim_merchant = "Croma Electronics"
            sim_category = "Electronics"
            sim_location = "Mumbai, IN"
            sim_device = "device-iphone-john"
        elif preset == "Scenario C: International Location Anomaly (₹45,000 in Dubai)":
            sim_amount = 45000.0
            sim_merchant = "Apple Store Mall of Emirates"
            sim_category = "Electronics"
            sim_location = "Dubai, AE"
            sim_device = "device-iphone-john"
        elif preset == "Scenario D: Critical Fraud Attempt (₹280,000 in London with Emulator)":
            sim_amount = 280000.0
            sim_merchant = "Rolex Boutique London"
            sim_category = "Luxury & Jewelry"
            sim_location = "London, UK"
            sim_device = "device-emulator-botnet-404"

        submit_btn = st.button(
            "🚀 Evaluate & Submit Transaction", type="primary", use_container_width=True
        )

    with sim_col2:
        st.markdown("#### Real-time Risk Assessment Result")
        if submit_btn:
            payload = {
                "amount": float(sim_amount),
                "merchant": sim_merchant,
                "category": sim_category,
                "location": sim_location,
                "device_id": sim_device,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            with st.spinner("Executing rule engine & ML anomaly detection pipeline..."):
                ok, res_tx = submit_transaction_api(payload)

            if ok and res_tx:
                r_eval = res_tx.get("risk_assessment") or {}
                f_score = r_eval.get("final_score", 0.0)
                r_level = r_eval.get("risk_level", "LOW")

                st.success(f"✅ Transaction processed! Assigned ID: `{res_tx['id']}`")

                # Big Result Card
                if r_level in ("HIGH", "CRITICAL"):
                    st.error(
                        f"🚨 **Threat Detected: {r_level} RISK** (Score: {f_score}/100) — Status: `{res_tx['status']}`"
                    )
                elif r_level == "MEDIUM":
                    st.warning(
                        f"⚠️ **Caution: {r_level} RISK** (Score: {f_score}/100) — Status: `{res_tx['status']}`"
                    )
                else:
                    st.success(
                        f"🟢 **Safe: {r_level} RISK** (Score: {f_score}/100) — Status: `{res_tx['status']}`"
                    )

                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.metric("Deterministic Rule Score", f"{r_eval.get('rule_score', 0)} / 100")
                with res_col2:
                    st.metric("ML Anomaly Score", f"{r_eval.get('ml_score', 0)} / 100")

                st.markdown("##### Triggered Rules:")
                reasons = r_eval.get("reasons", [])
                any_trig = False
                for r in reasons:
                    if r.get("triggered"):
                        any_trig = True
                        st.markdown(
                            f"• ❌ **{r.get('code')}** (+{r.get('score')} pts): {r.get('reason')}"
                        )
                if not any_trig:
                    st.markdown("• ✅ *No rules triggered.*")

                if f_score >= 60:
                    st.warning(
                        "🔔 An alert has been automatically dispatched to the Analyst Triage Queue."
                    )
            else:
                st.error(f"Submission failed: {res_tx}")
        else:
            st.info(
                "Configure parameters and click 'Evaluate & Submit Transaction' to run real-time inference."
            )
