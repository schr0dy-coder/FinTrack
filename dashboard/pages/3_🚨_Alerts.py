import os
import sys

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

try:
    from dashboard.utils import fetch_alerts, render_sidebar, resolve_alert_api
except ImportError:
    from utils import fetch_alerts, render_sidebar, resolve_alert_api

st.set_page_config(page_title="Alerts | FinTrack", page_icon="🚨", layout="wide")

# Render Sidebar
render_sidebar()

st.title("🚨 Fraud Alert Triage & Incident Management")
st.caption(
    "Investigate suspicious transaction alerts, examine evidence, and record analyst resolutions"
)

# Filters
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    status_filter = st.selectbox("Alert Status", ["ALL", "OPEN", "RESOLVED"], index=0)
with filter_col2:
    severity_filter = st.selectbox("Severity Tier", ["ALL", "HIGH", "CRITICAL"], index=0)

# Fetch Alerts
alert_data = fetch_alerts(
    status_val=status_filter,
    severity=severity_filter,
    page=1,
    limit=50,
)
items = alert_data.get("items", [])
total_alerts = alert_data.get("total", 0)

st.markdown(f"**Found {total_alerts} alerts matching filters:**")

if not items:
    st.success("🎉 No active alerts matching the selected filters!")
else:
    for al in items:
        sev_color = "🔴" if al["severity"] == "CRITICAL" else "🟠"
        stat_color = "🟢 RESOLVED" if al["status"] == "RESOLVED" else "⏳ OPEN"

        with st.container():
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 700; font-size: 1.1rem; color: #f8fafc;">
                            {sev_color} Alert #{al["id"]} — {al["severity"]} SEVERITY
                        </span>
                        <span style="font-weight: 600; font-size: 0.85rem; padding: 4px 10px; border-radius: 6px; background: {"rgba(16,185,129,0.15)" if al["status"] == "RESOLVED" else "rgba(239,68,68,0.15)"}; color: {"#34d399" if al["status"] == "RESOLVED" else "#f87171"};">
                            {stat_color}
                        </span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 6px;">
                        <strong>Transaction ID:</strong> <code>{al["transaction_id"]}</code> &nbsp;|&nbsp; <strong>Created:</strong> {al["created_at"][:19].replace("T", " ")} UTC
                    </div>
                    <div style="color: #e2e8f0; font-size: 0.95rem; background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: 8px; border-left: 3px solid {"#ef4444" if al["severity"] == "CRITICAL" else "#f97316"}; margin: 10px 0;">
                        {al["reason"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Interactive resolution section
            if al["status"] == "OPEN":
                with st.expander(f"✍️ Investigate & Resolve Alert #{al['id']}", expanded=False):
                    note_text = st.text_area(
                        "Analyst Investigation Note",
                        placeholder="e.g. Verified customer KYC via phone; transaction verified legitimate / flagged as confirmed fraud.",
                        key=f"note_{al['id']}",
                    )
                    if st.button(
                        f"Mark Alert #{al['id']} as Resolved", key=f"btn_{al['id']}", type="primary"
                    ):
                        if not note_text.strip():
                            st.error("Please enter a resolution note before resolving.")
                        else:
                            success, msg = resolve_alert_api(al["id"], note_text)
                            if success:
                                st.success(f"Alert #{al['id']} marked as RESOLVED!")
                                st.rerun()
                            else:
                                st.error(msg)
            else:
                st.markdown(
                    f'✅ **Resolution Note:** *"{al.get("resolution_note", "No note recorded.")}"* (Resolved at: `{al.get("resolved_at", "")[:19].replace("T", " ")}`)'
                )

            st.write("")
