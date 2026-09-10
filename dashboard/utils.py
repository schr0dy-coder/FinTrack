"""Dashboard API Client and Helper Utilities."""

import os
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def login_user(email: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Authenticate user with API backend and return success, error_message, user_data."""
    try:
        url = f"{API_BASE_URL}/api/v1/auth/login"
        resp = requests.post(url, json={"email": email, "password": password}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return True, None, data
        else:
            detail = resp.json().get("detail", "Authentication failed")
            return False, detail, None
    except Exception as e:
        return False, f"Could not connect to API server at {API_BASE_URL}: {e}", None


def auto_login_demo_admin() -> bool:
    """Convenience auto-login for development and demo mode."""
    success, _, data = login_user("admin@fintrack.com", "Admin@123")
    if success and data:
        st.session_state["token"] = data["access_token"]
        st.session_state["user"] = {
            "id": data["user_id"],
            "name": data["name"],
            "email": data["email"],
            "role": data["role"],
        }
        return True
    return False


def get_headers() -> Dict[str, str]:
    """Build Authorization headers from current Streamlit session state."""
    # If not logged in, attempt auto-login as demo admin for seamless demonstration
    if "token" not in st.session_state or not st.session_state.get("token"):
        auto_login_demo_admin()

    token = st.session_state.get("token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def render_sidebar():
    """Render common sidebar authentication, navigation, and live API status."""
    with st.sidebar:
        st.title("🛡️ FinTrack")
        st.caption("Financial Risk Intelligence")
        st.divider()

        # Initialize session state if missing
        if "token" not in st.session_state:
            st.session_state["token"] = None
        if "user" not in st.session_state:
            st.session_state["user"] = None

        if st.session_state.get("token") is None:
            st.subheader("🔑 Sign In")
            email_val = st.text_input("Email", value="admin@fintrack.com", key="sb_email")
            pass_val = st.text_input("Password", value="Admin@123", type="password", key="sb_pass")

            col_in1, col_in2 = st.columns(2)
            with col_in1:
                if st.button(
                    "Sign In", type="primary", use_container_width=True, key="sb_login_btn"
                ):
                    success, err, data = login_user(email_val, pass_val)
                    if success and data:
                        st.session_state["token"] = data["access_token"]
                        st.session_state["user"] = {
                            "id": data["user_id"],
                            "name": data["name"],
                            "email": data["email"],
                            "role": data["role"],
                        }
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(err or "Login failed")
            with col_in2:
                if st.button("Quick Admin", use_container_width=True, key="sb_quick_admin"):
                    if auto_login_demo_admin():
                        st.success("Signed in as Admin!")
                        st.rerun()

            st.caption("Demo Accounts:")
            st.caption("• **Admin**: `admin@fintrack.com` / `Admin@123`")
            st.caption("• **Customer**: `john@example.com` / `Password@123`")
        else:
            u = st.session_state["user"] or {}
            st.markdown(
                f"**Logged in as:**\n👤 **{u.get('name', 'User')}**\n📧 `{u.get('email', '')}`\n🏷️ **Role:** `{u.get('role', 'USER')}`"
            )

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                if st.button("Sign Out", use_container_width=True, key="sb_logout_btn"):
                    st.session_state["token"] = None
                    st.session_state["user"] = None
                    st.rerun()
            with col_u2:
                if u.get("role") != "ADMIN":
                    if st.button(
                        "Switch to Admin", use_container_width=True, key="sb_switch_admin"
                    ):
                        if auto_login_demo_admin():
                            st.rerun()

        st.divider()
        # System Health in Sidebar
        health = fetch_api_health()
        status_color = "🟢" if health.get("status") == "healthy" else "🔴"
        db_status = health.get("database", {}).get("status", "unknown")
        db_latency = health.get("database", {}).get("latency_ms", 0)
        ml_loaded = health.get("ml_model", {}).get("loaded", False)
        ml_version = health.get("ml_model", {}).get("version", "unknown")

        st.markdown(f"**API Status:** {status_color} `{health.get('status', 'offline').upper()}`")
        st.caption(f"Database: `{db_status}` | Latency: `{db_latency}ms`")
        st.caption(f"ML Model: `{'Loaded (' + ml_version + ')' if ml_loaded else 'Fallback'}`")


def fetch_api_health() -> Dict[str, Any]:
    """Query /health endpoint."""
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return resp.json() if resp.status_code == 200 else {"status": "unhealthy"}
    except Exception:
        return {
            "status": "offline",
            "database": {"status": "offline"},
            "ml_model": {"loaded": False},
        }


def fetch_system_statistics() -> Optional[Dict[str, Any]]:
    """Query /api/v1/admin/statistics."""
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/admin/statistics",
            headers=get_headers(),
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            st.error(
                "🔒 Admin privileges required. Please switch to the Administrator account in the sidebar."
            )
            return None
        return None
    except Exception:
        return None


def fetch_transactions(
    page: int = 1,
    limit: int = 50,
    risk_level: Optional[str] = None,
    status_val: Optional[str] = None,
    merchant: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> Dict[str, Any]:
    """Query /api/v1/transactions with filters."""
    params: Dict[str, Any] = {"page": page, "limit": limit}
    if risk_level and risk_level != "ALL":
        params["risk_level"] = risk_level
    if status_val and status_val != "ALL":
        params["status"] = status_val
    if merchant and merchant.strip():
        params["merchant"] = merchant.strip()
    if min_amount is not None and min_amount > 0:
        params["min_amount"] = min_amount
    if max_amount is not None and max_amount > 0:
        params["max_amount"] = max_amount

    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/transactions",
            headers=get_headers(),
            params=params,
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"items": [], "total": 0, "page": 1, "total_pages": 1}
    except Exception:
        return {"items": [], "total": 0, "page": 1, "total_pages": 1}


def fetch_alerts(
    status_val: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict[str, Any]:
    """Query /api/v1/alerts."""
    params: Dict[str, Any] = {"page": page, "limit": limit}
    if status_val and status_val != "ALL":
        params["status"] = status_val
    if severity and severity != "ALL":
        params["severity"] = severity

    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/alerts",
            headers=get_headers(),
            params=params,
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            st.error(
                "🔒 Admin privileges required to view alerts queue. Please log in as Admin in the sidebar."
            )
            return {"items": [], "total": 0, "page": 1, "total_pages": 1}
        return {"items": [], "total": 0, "page": 1, "total_pages": 1}
    except Exception:
        return {"items": [], "total": 0, "page": 1, "total_pages": 1}


def resolve_alert_api(alert_id: int, note: str) -> Tuple[bool, str]:
    """Submit resolution for an alert."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/alerts/{alert_id}/resolve",
            headers=get_headers(),
            json={"resolution_note": note},
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "Alert successfully resolved."
        else:
            return False, resp.json().get("detail", "Failed to resolve alert.")
    except Exception as e:
        return False, f"Network error: {e}"


def submit_transaction_api(payload: Dict[str, Any]) -> Tuple[bool, Any]:
    """Submit transaction for immediate evaluation."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/transactions",
            headers=get_headers(),
            json=payload,
            timeout=5,
        )
        if resp.status_code == 201:
            return True, resp.json()
        else:
            return False, resp.json().get("detail", "Submission rejected.")
    except Exception as e:
        return False, f"Network error: {e}"


def fetch_model_status_api() -> Optional[Dict[str, Any]]:
    """Query /api/v1/admin/model/status."""
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/admin/model/status",
            headers=get_headers(),
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            st.error(
                "🔒 Admin privileges required to inspect model status. Please log in as Admin in the sidebar."
            )
            return None
        return None
    except Exception:
        return None


def retrain_model_api() -> Tuple[bool, str]:
    """Trigger /api/v1/admin/model/retrain."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/admin/model/retrain",
            headers=get_headers(),
            timeout=30,
        )
        if resp.status_code == 200:
            msg = resp.json().get("message", "Model retrained successfully")
            return True, msg
        else:
            return False, resp.json().get("detail", "Retraining failed")
    except Exception as e:
        return False, f"Network error: {e}"
