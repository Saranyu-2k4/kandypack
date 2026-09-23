"""Module 6: Reporting and Analytics (REQ-F-6 to REQ-F-11)."""

from datetime import date
import pandas as pd
import streamlit as st
from shared_state import setup_common_page

setup_common_page("Reporting & Analytics")

st.title("6. Reporting & Analytics")
st.caption(
    "Generate business intelligence reports and operational performance metrics."
)

report_type = st.selectbox(
    "Select Report Type:",
    [
        "Quarterly Sales Report (REQ-F-6)",
        "Most Ordered Items (REQ-F-7)",
        "City and Route Breakdown (REQ-F-8)",
        "Driver & Assistant Working Hours (REQ-F-9)",
        "Truck Usage and Utilization (REQ-F-10)",
    ],
)

col_chart, col_filter = st.columns([3, 1])

with col_filter:
    st.date_input("Filter Start Date", value=date(2026, 1, 1))
    st.date_input("Filter End Date", value=date(2026, 3, 31))

    st.download_button(
        label="Export CSV",
        data=st.session_state.orders.to_csv(index=False),
        file_name="quarterly_report.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.button("Export PDF", use_container_width=True)

with col_chart:
    st.subheader("Quarterly Sales Performance (Q1 2026)")
    sales_chart_data = pd.DataFrame(
        {"Month": ["January", "February", "March"], "Sales (M LKR)": [16, 12, 18]}
    ).set_index("Month")
    st.bar_chart(sales_chart_data, color="#1a73e8")