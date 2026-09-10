import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from dashboard.utils import fetch_system_statistics, fetch_transactions, render_sidebar
except ImportError:
    from utils import fetch_system_statistics, fetch_transactions, render_sidebar

st.set_page_config(page_title="Overview | FinTrack", page_icon="📊", layout="wide")

# Render Sidebar
render_sidebar()

st.title("📊 Executive Risk & Volume Overview")
st.caption("Real-time transaction volume, anomaly rates, and threat distribution analytics")

stats = fetch_system_statistics()

if not stats:
    st.info(
        "👋 To view platform statistics, please ensure you are signed in as Administrator in the sidebar."
    )
    st.stop()
    st.error("Could not load platform statistics. Ensure the FastAPI backend is running.")
    st.stop()

# 1. Top KPI Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(label="Total Volume", value=f"₹{stats['total_volume']:,.2f}")
with kpi2:
    st.metric(label="Total Transactions", value=f"{stats['total_transactions']:,}")
with kpi3:
    st.metric(
        label="Suspicious Txns",
        value=f"{stats['suspicious_transactions']:,}",
        delta=f"{stats['anomaly_rate']}% rate",
        delta_color="inverse",
    )
with kpi4:
    st.metric(
        label="Open Alerts",
        value=f"{stats['open_alerts']:,}",
        delta="Requires Review" if stats["open_alerts"] > 0 else "Clear",
        delta_color="inverse",
    )
with kpi5:
    st.metric(label="Resolved Alerts", value=f"{stats['resolved_alerts']:,}")

st.divider()

# 2. Charts Row 1: Time Series & Risk Donut
col_chart1, col_chart2 = st.columns([3, 2])

# Fetch recent transactions for volume time series
tx_data = fetch_transactions(page=1, limit=100)
items = tx_data.get("items", [])

with col_chart1:
    st.subheader("📈 Transaction Volume & Risk Velocity")
    if items:
        df_tx = pd.DataFrame(items)
        df_tx["timestamp"] = pd.to_datetime(df_tx["timestamp"])
        df_tx = df_tx.sort_values("timestamp")

        # Aggregate by hour/day
        fig_vol = px.line(
            df_tx,
            x="timestamp",
            y="amount",
            color="status",
            markers=True,
            title="Transaction Amount Over Time",
            color_discrete_map={
                "APPROVED": "#10b981",
                "SUSPICIOUS": "#f59e0b",
                "FLAGGED": "#ef4444",
            },
            template="plotly_dark",
        )
        fig_vol.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No transaction time series data available.")

with col_chart2:
    st.subheader("🎯 Risk Level Distribution")
    risk_dist = stats.get("risk_distribution", {})
    labels = list(risk_dist.keys())
    values = list(risk_dist.values())

    if sum(values) > 0:
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(
                        colors=["#10b981", "#f59e0b", "#f97316", "#ef4444"],
                    ),
                )
            ]
        )
        fig_donut.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No risk distribution data available.")

st.divider()

# 3. Charts Row 2: Severity Bar & Top Suspicious Merchants
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("🚨 Alert Volume by Severity")
    sev_dist = stats.get("severity_distribution", {})
    df_sev = pd.DataFrame({"Severity": list(sev_dist.keys()), "Count": list(sev_dist.values())})
    fig_sev = px.bar(
        df_sev,
        x="Severity",
        y="Count",
        color="Severity",
        color_discrete_map={"HIGH": "#f97316", "CRITICAL": "#ef4444"},
        template="plotly_dark",
    )
    fig_sev.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_sev, use_container_width=True)

with col_chart4:
    st.subheader("🏬 High Risk Merchant & Location Hotspots")
    top_merchants = stats.get("top_suspicious_merchants", [])
    if top_merchants:
        df_m = pd.DataFrame(top_merchants)
        fig_m = px.bar(
            df_m,
            x="count",
            y="merchant",
            orientation="h",
            color="count",
            color_continuous_scale="Reds",
            title="Top Suspicious Merchants",
            template="plotly_dark",
        )
        fig_m.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_m, use_container_width=True)
    else:
        st.info("No suspicious merchant aggregations yet.")
