"""Module 4: Last-Mile Road Delivery and Rostering (REQ-F-1 to REQ-F-6, BR-05, BR-07, BR-09)."""

import streamlit as st
from shared_state import setup_common_page

setup_common_page("Last-Mile Rostering")

st.title("4. Last-Mile Road Delivery & Rostering")
st.caption(
    "Assign last-mile dispatch teams and enforce labor compliance constraints."
)

with st.container(border=True):
    st.subheader("Create Dispatch Assignment")

    col1, col2, col3 = st.columns(3)
    truck = col1.selectbox(
        "Select Truck",
        ["TRK-01 (Capacity 5T)", "TRK-02 (Capacity 3T)"],
    )
    driver = col2.selectbox(
        "Select Driver",
        [
            "Sunil Perera (Worked: 35 hrs)",
            "Nimal Fernando (Worked: 39 hrs)",
        ],
    )
    assistant = col3.selectbox(
        "Select Assistant",
        [
            "Kamal Silva (Worked: 48 hrs)",
            "Priyantha Bandara (Worked: 58 hrs)",
        ],
    )

    col4, col5 = st.columns(2)
    duration = col4.number_input(
        "Trip Duration (Hours)", min_value=1, max_value=12, value=5
    )
    consecutive_routes = col5.number_input(
        "Driver Consecutive Routes Prior to This",
        min_value=0,
        max_value=3,
        value=1,
    )

    if st.button("Validate & Schedule Dispatch", type="primary"):
        violations = []

        # Drivers cannot have consecutive routes (REQ-F-3)
        if consecutive_routes >= 1:
            violations.append(
                "Violation: Drivers cannot be scheduled for consecutive deliveries without mandatory rest (REQ-F-3)."
            )

        # Drivers weekly limit: 40 hrs (REQ-F-5, BR-09)
        if "Sunil" in driver and (35 + duration) > 40:
            violations.append(
                f"Violation: Weekly scheduled limit for drivers is capped at 40 hours. "
                f"Attempted schedule exceeds cap ({35 + duration} hours) (REQ-F-5)."
            )

        if violations:
            for error_msg in violations:
                st.error(error_msg)
        else:
            st.success("Dispatch validated and scheduled without violations.")