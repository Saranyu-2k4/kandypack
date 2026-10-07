"""Module 2: Customer Order Processing (REQ-F-1 to REQ-F-4, BR-01)."""

import json
from datetime import date, timedelta

import streamlit as st

from shared_state import setup_common_page
from db import get_connection


# ============================================================
# PAGE SETUP
# ============================================================

setup_common_page("Order Processing")

st.title("2. Customer Order Processing")

st.caption(
    "Capture customer orders, validate 7-day advance placement, "
    "and map delivery routes."
)


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_customers():
    """Load customers from PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    customer_name,
                    address,
                    contact_phone,
                    default_route_id
                FROM customers
                ORDER BY customer_name;
                """
            )

            return cur.fetchall()


def get_products():
    """Load products from PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    product_name,
                    unit_price
                FROM products
                ORDER BY product_name;
                """
            )

            return cur.fetchall()


def get_routes():
    """Load delivery routes from PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    route_name,
                    service_area,
                    store_id
                FROM routes
                ORDER BY route_name;
                """
            )

            return cur.fetchall()


# ============================================================
# LOAD DATABASE DATA
# ============================================================

try:

    customers = get_customers()
    products = get_products()
    routes = get_routes()

except Exception as e:

    st.error(
        "Unable to load data from PostgreSQL. "
        f"Database error: {e}"
    )

    st.stop()


# ============================================================
# CHECK REQUIRED DATA
# ============================================================

if not customers:

    st.warning(
        "No customers are available in the database. "
        "Please add customers before placing an order."
    )

    st.stop()


if not products:

    st.warning(
        "No products are available in the database. "
        "Please add products before placing an order."
    )

    st.stop()


if not routes:

    st.warning(
        "No delivery routes are available in the database. "
        "Please add routes before placing an order."
    )

    st.stop()


# ============================================================
# NEW ORDER ENTRY
# ============================================================

with st.container(border=True):

    st.subheader("New Order Entry")

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    customer_options = {
        customer[1]: customer
        for customer in customers
    }

    selected_customer_name = st.selectbox(
        "Customer / Business Name",
        list(customer_options.keys())
    )

    selected_customer = customer_options[
        selected_customer_name
    ]

    customer_id = selected_customer[0]

    customer_address = selected_customer[2]
    customer_phone = selected_customer[3]
    customer_default_route_id = selected_customer[4]


    # --------------------------------------------------------
    # Contact phone
    # --------------------------------------------------------

    phone = st.text_input(
        "Contact Phone",
        value=customer_phone or ""
    )


    # --------------------------------------------------------
    # Delivery address
    # --------------------------------------------------------

    delivery_address = st.text_input(
        "Delivery Address",
        value=customer_address or "",
        placeholder="e.g. Main Street, Galle"
    )


    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    # Use the actual current date for the UI.
    order_date = col1.date_input(
        "Order Placement Date",
        value=date.today()
    )

    req_date = col2.date_input(
        "Requested Delivery Date",
        value=date.today() + timedelta(days=8)
    )


    # --------------------------------------------------------
    # Preferred delivery slot
    # --------------------------------------------------------

    preferred_slot = st.selectbox(
        "Preferred Delivery Slot",
        [
            "Morning",
            "Afternoon",
            "Evening"
        ]
    )


    # ========================================================
    # ROUTE
    # ========================================================

    st.subheader("Delivery Route")

    # If the customer already has a default route,
    # select it automatically.

    default_route_index = 0

    if customer_default_route_id is not None:

        for i, route in enumerate(routes):

            if route[0] == customer_default_route_id:
                default_route_index = i
                break


    selected_route = st.selectbox(
        "Delivery Route",
        routes,
        index=default_route_index,
        format_func=lambda route: (
            f"{route[1]} - {route[2]}"
        )
    )

    route_id = selected_route[0]
    route_name = selected_route[1]
    service_area = selected_route[2]


    # Show route information

    st.info(
        f"Selected Route: **{route_name}**  \n"
        f"Service Area: **{service_area}**"
    )


    # ========================================================
    # LINE ITEMS
    # ========================================================

    st.subheader("Line Items")

    item_col1, item_col2 = st.columns(2)


    # --------------------------------------------------------
    # Product
    # --------------------------------------------------------

    selected_product = item_col1.selectbox(
        "Select Product",
        products,
        format_func=lambda product: (
            f"{product[1]} - Rs. {product[2]:,.2f}"
        )
    )

    product_id = selected_product[0]
    product_name = selected_product[1]
    product_price = selected_product[2]


    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    qty = item_col2.number_input(
        "Quantity",
        min_value=1,
        value=50,
        step=10
    )


    # --------------------------------------------------------
    # Show line total
    # --------------------------------------------------------

    line_total = float(product_price) * int(qty)

    st.write(
        f"**Line Total:** Rs. {line_total:,.2f}"
    )


    # ========================================================
    # ORDER SUMMARY
    # ========================================================

    st.subheader("Order Summary")

    summary_col1, summary_col2 = st.columns(2)

    summary_col1.write(
        f"**Customer:** {selected_customer_name}"
    )

    summary_col1.write(
        f"**Product:** {product_name}"
    )

    summary_col1.write(
        f"**Quantity:** {qty}"
    )

    summary_col2.write(
        f"**Route:** {route_name}"
    )

    summary_col2.write(
        f"**Delivery Date:** {req_date}"
    )

    summary_col2.write(
        f"**Order Value:** Rs. {line_total:,.2f}"
    )


    # ========================================================
    # SUBMIT ORDER
    # ========================================================

    if st.button(
        "Submit Order",
        type="primary",
        use_container_width=True
    ):

        # ----------------------------------------------------
        # Python-side validation
        # ----------------------------------------------------

        if not selected_customer_name:

            st.error(
                "Please select a customer."
            )

            st.stop()


        if not delivery_address.strip():

            st.error(
                "Please enter a delivery address."
            )

            st.stop()


        if not phone.strip():

            st.error(
                "Please enter a contact phone number."
            )

            st.stop()


        # ----------------------------------------------------
        # Check phone format approximately before DB call
        # ----------------------------------------------------

        allowed_phone_characters = (
            "0123456789+- ()."
        )

        if any(
            character not in allowed_phone_characters
            for character in phone
        ):

            st.error(
                "Invalid phone number format."
            )

            st.stop()


        # ----------------------------------------------------
        # 7-day advance validation
        #
        # This is also enforced by the PostgreSQL procedure.
        # We validate here first so the user gets immediate
        # feedback in the Streamlit UI.
        # ----------------------------------------------------

        lead_time = (
            req_date - order_date
        ).days


        if lead_time < 7:

            st.error(
                "Validation Error: Orders must be placed "
                "at least 7 days prior to target delivery "
                "(REQ-F-2 / BR-01). "
                f"Selected lead time: {lead_time} days."
            )

            st.stop()


        # ----------------------------------------------------
        # Convert selected item to JSON for PostgreSQL
        # ----------------------------------------------------

        items = [
            {
                "product_id": int(product_id),
                "quantity": int(qty)
            }
        ]


        # ----------------------------------------------------
        # Convert delivery date to timestamp
        #
        # The procedure accepts TIMESTAMPTZ.
        # Use midnight for the requested delivery date.
        # ----------------------------------------------------

        delivery_datetime = (
            req_date.isoformat()
            + " 00:00:00+05:30"
        )


        # ====================================================
        # CALL POSTGRESQL PROCEDURE
        # ====================================================

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CALL place_order(
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s::jsonb,
                            %s,
                            NULL
                        );
                        """,
                        (
                            customer_id,
                            route_id,
                            delivery_address,
                            phone,
                            preferred_slot,
                            delivery_datetime,
                            json.dumps(items),
                            None
                        )
                    )

                conn.commit()

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id
                        FROM orders
                        WHERE customer_id = %s
                        ORDER BY id DESC
                        LIMIT 1;
                        """,
                        (customer_id,)
                    )
                    result = cur.fetchone()

            if result:
                new_order_id = result[0]
                st.success(
                    f"Order #{new_order_id} successfully "
                    f"placed in 'PLACED' status."
                )
                st.info(
                    f"""
                    **Order ID:** {new_order_id}

                    **Customer:** {selected_customer_name}

                    **Route:** {route_name}

                    **Delivery Date:** {req_date}

                    **Product:** {product_name}

                    **Quantity:** {qty}

                    **Order Value:** Rs. {line_total:,.2f}
                    """
                )
            else:
                st.success("Order placed successfully.")
        except Exception as e:
            st.error(
                f"Unable to place order: {e}"
            )
