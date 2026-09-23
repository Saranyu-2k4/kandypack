"""Entrypoint dashboard displaying high-level operational metrics."""

import streamlit as st
from shared_state import setup_common_page

setup_common_page("Overview Dashboard")

st.title("Kandypack Supply Chain Distribution System")
st.subheader("Central Operations Dashboard")
st.write(
    "Welcome to the multi-modal logistics portal for managing rail and road distribution from Kandy."
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Active Orders", value=len(st.session_state.orders))
with col2:
    st.metric(
        label="FMCG Product Catalog Size",
        value=len(st.session_state.products),
    )
with col3:
    st.metric(label="Primary Rail Hubs Covered", value="6 Destinations")

st.divider()

st.markdown(
    """
    #### System Functional Modules
    Use the navigation menu in the left sidebar to access system modules:
    1. **Master Data & Fleet Management:** Manage FMCG products, space rates, routes, and fleet crew profiles.
    2. **Customer Order Processing:** Capture multi-item orders with strict 7-day advance lead-time validation.
    3. **Railway Bulk Transport Scheduling:** Monitor train cargo capacities to regional station stores and automate spillover.
    4. **Last-Mile Road Delivery & Rostering:** Dispatch delivery trucks while enforcing consecutive-trip rules and working hour caps.
    5. **Delivery Status & Lifecycle Tracking:** Update real-time transit state through final delivery completion.
    6. **Reporting & Analytics:** Generate quarterly sales summaries, item popularity analysis, and staff duty reports.
"""
)