"""Module 2: Customer Order Processing (REQ-F-1 to REQ-F-4, BR-01)."""

from datetime import date, timedelta
import pandas as pd
import streamlit as st
from shared_state import setup_common_page

setup_common_page("Order Processing")

st.title("2. Customer Order Processing")
st.caption(
    "Capture customer orders, validate 7-day advance placement, and map delivery routes."
)

with st.container(border=True):
    st.subheader("New Order Entry")

    col1, col2 = st.columns(2)
    cust_name = col1.text_input("Customer / Business Name")
    delivery_address = col2.text_input(
        "Delivery Address (e.g., Main Street, Galle)"
    )

    today = date(2026, 7, 28)
    col3, col4 = st.columns(2)
    order_date = col3.date_input("Order Placement Date", value=today)
    req_date = col4.date_input(
        "Requested Delivery Date", value=today + timedelta(days=8)
    )

    st.subheader("Line Items")
    item_col1, item_col2 = st.columns(2)
    prod_options = st.session_state.products["Name"].tolist()
    selected_prod = item_col1.selectbox("Select Product", prod_options)
    qty = item_col2.number_input("Quantity", min_value=1, value=50, step=10)

    if st.button("Submit Order", type="primary"):
        lead_time = (req_date - order_date).days

        if not cust_name or not delivery_address:
            st.error("Please fill in customer and address information.")
        elif lead_time < 7:
            st.error(
                f"Validation Error: Orders must be placed at least 7 days prior to target delivery (REQ-F-2 / BR-01). "
                f"Selected lead time: {lead_time} days."
            )
        else:
            matched_route = (
                "R-02 (Galle)"
                if "galle" in delivery_address.lower()
                else "R-01 (Colombo)"
            )
            new_order_id = f"ORD-{9010 + len(st.session_state.orders) + 1}"
            new_entry = {
                "Order ID": new_order_id,
                "Customer": cust_name,
                "Route": matched_route,
                "Current Status": "Placed",
            }
            st.session_state.orders = pd.concat(
                [st.session_state.orders, pd.DataFrame([new_entry])],
                ignore_index=True,
            )
            st.success(
                f"Order {new_order_id} recorded in 'Placed' status and mapped to {matched_route}."
            )