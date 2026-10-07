"""Module 1: Master Data and Fleet Management (REQ-F-1 to REQ-F-4)."""

import pandas as pd
import streamlit as st
from shared_state import setup_common_page

setup_common_page("Master Data")

st.title("1. Master Data & Fleet Management")
st.caption(
    "Manage product catalog, space consumption rates, delivery routes, and staff profiles."
)

tab1, tab2, tab3 = st.tabs(
    ["Product Catalog", "Routes & Stores", "Fleet & Crew"]
)

with tab1:
    st.subheader("FMCG Product Catalog")
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        prod_name = col1.text_input("Product Name")
        unit_price = col2.number_input(
            "Unit Price (LKR)", min_value=0.0, step=50.0, format="%.2f"
        )
        space_rate = col3.number_input(
            "Train Space Rate (units/box)",
            min_value=0.0,
            step=0.1,
            format="%.2f",
        )

        submit_prod = st.form_submit_button("Add Product")
        if submit_prod:
            if not prod_name:
                st.error("Product name cannot be empty.")
            elif space_rate <= 0:
                st.error(
                    "Space consumption rate must be strictly greater than 0 (REQ-F-4)."
                )
            else:
                new_id = f"PROD-{len(st.session_state.products) + 1:03d}"
                new_row = {
                    "Product ID": new_id,
                    "Name": prod_name,
                    "Unit Price (LKR)": unit_price,
                    "Train Space Rate": space_rate,
                }
                st.session_state.products = pd.concat(
                    [st.session_state.products, pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                st.success(f"Product {new_id} added successfully.")

    st.dataframe(st.session_state.products, use_container_width=True)

with tab2:
    st.subheader("Predefined Delivery Routes")
    routes_data = pd.DataFrame(
        [
            {
                "Route ID": "R-01",
                "Hub Station": "Colombo",
                "Max Time (Hrs)": 4,
                "Coverage Area": "Western Province Hub",
            },
            {
                "Route ID": "R-02",
                "Hub Station": "Galle",
                "Max Time (Hrs)": 5,
                "Coverage Area": "Southern Coastal Belt",
            },
            {
                "Route ID": "R-03",
                "Hub Station": "Jaffna",
                "Max Time (Hrs)": 8,
                "Coverage Area": "Northern Peninsula",
            },
        ]
    )
    st.dataframe(routes_data, use_container_width=True)

with tab3:
    st.subheader("Fleet & Crew Profiles")
    st.info(
        "Staff Rules: Drivers are limited to 40 hrs/week; Assistants are limited to 60 hrs/week."
    )
    fleet_data = pd.DataFrame(
        [
            {
                "ID": "TRK-01",
                "Type": "5T Truck",
                "Status": "Available",
                "Assigned Store": "Colombo",
            },
            {
                "ID": "DRV-101",
                "Name": "Sunil Perera (Driver)",
                "Hours This Week": 32,
                "Status": "Eligible",
            },
            {
                "ID": "AST-201",
                "Name": "Kamal Silva (Assistant)",
                "Hours This Week": 46,
                "Status": "Eligible",
            },
        ]
    )
    st.dataframe(fleet_data, use_container_width=True)