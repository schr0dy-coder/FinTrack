import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

try:
    from dashboard.utils import render_sidebar
except ImportError:
    from utils import render_sidebar

st.set_page_config(
    page_title="FinTrack | Fraud Detection & Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Glassmorphic & Modern Dark Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
        color: #f8fafc;
        line-height: 1.1;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 8px;
    }

    /* Risk Badges */
    .badge-low {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-medium {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-high {
        background: rgba(249, 115, 22, 0.15);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-critical {
        background: rgba(239, 68, 68, 0.18);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.75rem;
        display: inline-block;
        animation: pulse-border 2s infinite;
    }

    /* Gradient Hero Banner */
    .hero-banner {
        background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.15) 0%, rgba(15, 23, 42, 0) 70%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None

# Render Common Sidebar Authentication & Diagnostics
render_sidebar()

# Main Portal Landing Page
st.markdown(
    """
    <div class="hero-banner">
        <h1 style="margin: 0; font-size: 2.4rem; background: linear-gradient(90deg, #f8fafc, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            FinTrack Intelligence Portal
        </h1>
        <p style="margin-top: 8px; font-size: 1.1rem; color: #94a3b8; max-width: 800px;">
            Unified transaction monitoring, real-time deterministic fraud rules, and machine learning anomaly detection.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# If not authenticated, prompt sign in
if not st.session_state["token"]:
    st.info(
        "👋 Please sign in using the left sidebar to access the live analytics, transaction monitoring, and alert triage queues."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            ### ⚡ Core Architecture
            - **Deterministic Rules Engine**: High value spikes, rapid burst frequencies, unrecognized devices, location anomalies, failed credential patterns.
            - **Machine Learning**: Isolation Forest anomaly scoring normalized to 0–100 scale.
            - **Hybrid Risk Scoring**: Configurable weighted aggregation (60% Rule + 40% ML) with boundary classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
            """
        )
    with col2:
        st.markdown(
            """
            ### 🚀 Navigation Guide
            - **📊 1. Overview**: Executive KPIs, volume charts, risk distribution donut, severity breakdown.
            - **💳 2. Transactions**: Filterable transaction log, deep rule breakdown inspector, and **Live Transaction Simulator**.
            - **🚨 3. Alerts**: Triage queue for High & Critical transactions with one-click analyst resolution.
            - **🤖 4. ML & System**: Model version inspection, training metadata, and hot retraining.
            """
        )
else:
    st.success(
        f"Session Active: Logged in as **{st.session_state['user']['name']}** ({st.session_state['user']['role']}). Use the sidebar pages to navigate."
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">📊 Executive Dashboard</div>
                <div class="metric-value">Overview</div>
                <div class="metric-subtitle">Volume trends, risk distributions, and merchant analytics.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">💳 Live Inspector & Simulator</div>
                <div class="metric-value">Transactions</div>
                <div class="metric-subtitle">Deep dive into rule signals and test custom scenarios.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">🚨 Incident Management</div>
                <div class="metric-value">Alerts</div>
                <div class="metric-subtitle">Review suspicious events and record investigation notes.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
