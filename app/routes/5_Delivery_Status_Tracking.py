"""Module 5: Delivery Status & Lifecycle Tracking (REQ-F-4, REQ-F-5)."""

import streamlit as st
from shared_state import setup_common_page

setup_common_page("Delivery Status Tracking")

st.title("5. Delivery Status & Lifecycle Tracking")
st.caption(
    "Track order state transitions through final last-mile confirmation."
)

st.dataframe(st.session_state.orders, use_container_width=True)

with st.container(border=True):
    st.subheader("Update Order Lifecycle State (REQ-F-4, REQ-F-5)")
    u_col1, u_col2 = st.columns(2)

    order_to_update = u_col1.selectbox(
        "Select Order to Update",
        st.session_state.orders["Order ID"].tolist(),
    )
    target_status = u_col2.selectbox(
        "Set Target Status",
        ["Placed", "Scheduled", "In-Transit", "Delivered"],
    )

    if st.button("Update Status"):
        st.session_state.orders.loc[
            st.session_state.orders["Order ID"] == order_to_update,
            "Current Status",
        ] = target_status
        st.success(
            f"Order {order_to_update} successfully transitioned to '{target_status}'."
        )
        st.rerun()