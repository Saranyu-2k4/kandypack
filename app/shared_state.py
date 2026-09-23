"""Shared state initialization and UI helpers across pages."""

import pandas as pd
import streamlit as st


def setup_common_page(title: str):
    st.set_page_config(
        page_title=f"{title} - Kandypack Logistics",
        page_icon="🚆",
        layout="wide",
    )

    # Initialize shared in-memory data
    if "products" not in st.session_state:
        st.session_state.products = pd.DataFrame(
            [
                {
                    "Product ID": "PROD-001",
                    "Name": "Packaged Goods A",
                    "Unit Price (LKR)": 1200.0,
                    "Train Space Rate": 0.5,
                },
                {
                    "Product ID": "PROD-002",
                    "Name": "Beverage Crate B",
                    "Unit Price (LKR)": 2400.0,
                    "Train Space Rate": 1.2,
                },
                {
                    "Product ID": "PROD-003",
                    "Name": "Confectionery Box C",
                    "Unit Price (LKR)": 850.0,
                    "Train Space Rate": 0.3,
                },
            ]
        )

    if "orders" not in st.session_state:
        st.session_state.orders = pd.DataFrame(
            [
                {
                    "Order ID": "ORD-9011",
                    "Customer": "Kandy Retailers",
                    "Route": "R-01 (Colombo)",
                    "Current Status": "Placed",
                },
                {
                    "Order ID": "ORD-9012",
                    "Customer": "Galle Supermart",
                    "Route": "R-02 (Galle)",
                    "Current Status": "Scheduled",
                },
                {
                    "Order ID": "ORD-9013",
                    "Customer": "Jaffna Stores",
                    "Route": "R-03 (Jaffna)",
                    "Current Status": "In-Transit",
                },
            ]
        )

    # Shared sidebar header and user profile display
    with st.sidebar:
        st.markdown("### Kandypack Logistics")
        st.caption("Rail & Road Distribution Platform v1.0")
        st.markdown("---")
        st.markdown(
            """
            <div style="background-color: #e8f0fe; color: #1a73e8; padding: 10px;
                        border-radius: 8px; font-weight: 600; text-align: center; border: 1px solid #d2e3fc;">
                Logged in as: <strong>Logistics Manager</strong>
            </div>
            <br>
            """,
            unsafe_allow_html=True,
        )