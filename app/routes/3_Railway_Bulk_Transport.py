"""Module 3: Railway Bulk Transport Scheduling (REQ-F-1 to REQ-F-4, BR-02, BR-03)."""

import streamlit as st
from shared_state import setup_common_page

setup_common_page("Railway Bulk Transport")

st.title("3. Railway Bulk Transport Scheduling")
st.caption(
    "Manage Sri Lanka Railways bulk cargo capacity allocations and automatic spillovers."
)

dest_hub = st.selectbox(
    "Select Destination Railway Hub:",
    [
        "Colombo",
        "Negombo",
        "Galle",
        "Matara",
        "Jaffna",
        "Trincomalee",
    ],
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Train Trip #101 (Primary)")
        st.write("**Total Cargo Capacity:** 500 Units")
        st.write("**Allocated Space:** 420 Units")
        st.progress(420 / 500)
        st.write("84% Capacity Utilized")

with col2:
    with st.container(border=True):
        st.subheader("Train Trip #102 (Next Available - Spillover)")
        st.write("**Total Cargo Capacity:** 500 Units")
        st.write("**Allocated Space:** 0 Units")
        st.progress(0 / 500)
        st.write("0% Capacity Utilized")

st.divider()
st.subheader("Test Space Allocation & Spillover Simulation")
test_qty = st.number_input(
    "Cargo Space Needed for Pending Orders (Units)",
    min_value=10,
    max_value=600,
    value=150,
    step=10,
)

if st.button("Calculate Allocation"):
    primary_rem = 500 - 420
    if test_qty <= primary_rem:
        st.success(
            f"Full cargo of {test_qty} units allocated to Train Trip #101. No spillover needed."
        )
    else:
        spillover = test_qty - primary_rem
        st.warning(
            f"Trip #101 capacity exceeded. Allocated {primary_rem} units to Trip #101. "
            f"Remaining {spillover} units automatically spilled over onto Trip #102 (REQ-F-3 / BR-03)."
        )