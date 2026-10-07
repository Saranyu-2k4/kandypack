import sys
import os

import pandas as pd
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.join(_HERE, "..")
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from shared_state import setup_common_page
from db import get_connection

setup_common_page("Last-Mile Rostering")

def _fetch(sql: str, params=None):
    """Execute a SELECT and return rows + column names, or ([], []) on error."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                rows = cur.fetchall()
                cols = [d.name for d in cur.description] if cur.description else []
                return rows, cols
    except Exception as exc:
        st.error(f"DB read error: {exc}")
        return [], []


def _run(sql: str, params=None):
    """Execute a non-SELECT statement. Returns (True, None) or (False, error_str)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return True, None
    except Exception as exc:
        return False, str(exc)


def _routes():
    rows, _ = _fetch(
        "SELECT id, route_name, store_id, max_delivery_time_hrs FROM routes ORDER BY route_name"
    )
    return rows  


def _trucks(store_id=None):
    if store_id:
        rows, _ = _fetch(
            "SELECT id, license_plate, capacity FROM trucks "
            "WHERE vehicle_status = 'Active' AND store_id = %s ORDER BY license_plate",
            (store_id,),
        )
    else:
        rows, _ = _fetch(
            "SELECT id, license_plate, capacity FROM trucks "
            "WHERE vehicle_status = 'Active' ORDER BY license_plate"
        )
    return rows  


def _drivers(store_id=None):
    if store_id:
        rows, _ = _fetch(
            "SELECT id, employee_name FROM employees "
            "WHERE employee_role = 'DRIVER' AND employee_status = 'Available' "
            "AND store_id = %s ORDER BY employee_name",
            (store_id,),
        )
    else:
        rows, _ = _fetch(
            "SELECT id, employee_name FROM employees "
            "WHERE employee_role = 'DRIVER' AND employee_status = 'Available' "
            "ORDER BY employee_name"
        )
    return rows  

def _assistants(store_id=None):
    if store_id:
        rows, _ = _fetch(
            "SELECT id, employee_name FROM employees "
            "WHERE employee_role = 'ASSISTANT' AND employee_status = 'Available' "
            "AND store_id = %s ORDER BY employee_name",
            (store_id,),
        )
    else:
        rows, _ = _fetch(
            "SELECT id, employee_name FROM employees "
            "WHERE employee_role = 'ASSISTANT' AND employee_status = 'Available' "
            "ORDER BY employee_name"
        )
    return rows  


def _store_received_items(route_id=None):
    """Order items that are STORE_RECEIVED, belong to *route_id*, and have a
    compatible train allocation but no truck delivery yet."""
    base = """
        SELECT oi.id,
               o.id          AS order_id,
               p.product_name,
               oi.quantity,
               oi.total_price
        FROM   order_items        AS oi
        JOIN   orders             AS o  ON o.id = oi.order_id
        JOIN   products           AS p  ON p.id = oi.product_id
        WHERE  oi.item_lifecycle_status = 'STORE_RECEIVED'
          AND  NOT EXISTS (
                   SELECT 1 FROM truck_item_deliveries AS d
                   WHERE d.order_item_id = oi.id
               )
          AND  EXISTS (
                   SELECT 1
                   FROM   train_allocations AS a
                   JOIN   train_schedules   AS ts ON ts.id = a.train_id
                   WHERE  a.order_item_id = oi.id
               )
    """
    if route_id:
        base += " AND o.route_id = %s"
        rows, cols = _fetch(base + " ORDER BY oi.id", (route_id,))
    else:
        rows, cols = _fetch(base + " ORDER BY oi.id")
    return rows, cols


def _schedules():
    sql = """
        SELECT ts.id,
               r.route_name,
               t.license_plate,
               d.employee_name  AS driver,
               a.employee_name  AS assistant,
               ts.start_timestamp,
               ts.end_timestamp,
               ts.duration_hours,
               ts.created_at
        FROM   truck_schedules AS ts
        JOIN   routes          AS r  ON r.id = ts.route_id
        JOIN   trucks          AS t  ON t.id = ts.truck_id
        JOIN   employees       AS d  ON d.id = ts.driver_id
        LEFT   JOIN employees  AS a  ON a.id = ts.assistant_id
        ORDER  BY ts.start_timestamp DESC
        LIMIT  200
    """
    return _fetch(sql)


def _schedule_items(schedule_id: int):
    sql = """
        SELECT tid.order_item_id,
               p.product_name,
               oi.quantity,
               oi.total_price,
               tid.delivered_at
        FROM   truck_item_deliveries AS tid
        JOIN   order_items           AS oi ON oi.id = tid.order_item_id
        JOIN   products              AS p  ON p.id = oi.product_id
        WHERE  tid.truck_schedule_id = %s
        ORDER  BY tid.order_item_id
    """
    return _fetch(sql, (schedule_id,))


st.title("4. Last-Mile Road Delivery & Rostering")
st.caption("Assign last-mile dispatch teams and enforce labor compliance constraints.")

tab_create, tab_read, tab_update, tab_delete = st.tabs(
    ["➕ Schedule Delivery", "📋 View Schedules", "✏️ Update Schedule", "🗑️ Cancel Schedule"]
)

with tab_create:
    st.subheader("Schedule a New Delivery")
    st.info(
        "The **schedule_delivery** stored procedure enforces all business rules "
        "(REQ-F-1 to REQ-F-6, BR-05, BR-07, BR-09) server-side before committing.",
        icon="ℹ️",
    )

    routes = _routes()
    if not routes:
        st.warning("No routes found in the database. Please seed the database first.")
    else:
        route_opts = {f"[{r[0]}] {r[1]}": r for r in routes}
        chosen_route_label = st.selectbox("Select Route", list(route_opts.keys()), key="cr_route")
        chosen_route = route_opts[chosen_route_label]
        route_id, route_name, route_store_id, max_hrs = chosen_route

        col1, col2 = st.columns(2)

        trucks = _trucks(route_store_id)
        truck_opts = {f"[{t[0]}] {t[1]} (cap {t[2]})" : t[0] for t in trucks}
        chosen_truck_label = col1.selectbox("Select Truck (Active, same store)", list(truck_opts.keys()) or ["No active trucks"], key="cr_truck")
        truck_id = truck_opts.get(chosen_truck_label)

        drivers = _drivers(route_store_id)
        driver_opts = {f"[{d[0]}] {d[1]}": d[0] for d in drivers}
        chosen_driver_label = col2.selectbox("Select Driver (Available, same store)", list(driver_opts.keys()) or ["No available drivers"], key="cr_driver")
        driver_id = driver_opts.get(chosen_driver_label)

        assistants = _assistants(route_store_id)
        asst_opts = {f"[{a[0]}] {a[1]}": a[0] for a in assistants}
        chosen_asst_label = col1.selectbox("Select Assistant (Available, same store)", list(asst_opts.keys()) or ["No available assistants"], key="cr_asst")
        asst_id = asst_opts.get(chosen_asst_label)

        import datetime
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        col3, col4 = st.columns(2)
        start_date = col3.date_input("Delivery Start Date", value=tomorrow, min_value=tomorrow, key="cr_sdate")
        start_time = col3.time_input("Delivery Start Time", value=datetime.time(8, 0), key="cr_stime")
        end_date   = col4.date_input("Delivery End Date",   value=tomorrow, min_value=tomorrow, key="cr_edate")
        end_time   = col4.time_input("Delivery End Time",   value=datetime.time(13, 0), key="cr_etime")

        start_ts = datetime.datetime.combine(start_date, start_time)
        end_ts   = datetime.datetime.combine(end_date,   end_time)

        st.markdown("#### Select Order Items to Deliver")
        st.caption(
            f"Only items with status **STORE_RECEIVED** on route **{route_name}** "
            "that are not yet assigned to a truck delivery are listed."
        )
        item_rows, item_cols = _store_received_items(route_id)
        if not item_rows:
            st.warning("No eligible order items found for this route.")
            selected_item_ids = []
        else:
            items_df = pd.DataFrame(item_rows, columns=item_cols)
            items_df.rename(
                columns={
                    "id": "Item ID",
                    "order_id": "Order ID",
                    "product_name": "Product",
                    "quantity": "Qty",
                    "total_price": "Total (LKR)",
                },
                inplace=True,
            )
            items_df.insert(0, "Select", False)
            edited = st.data_editor(
                items_df,
                column_config={"Select": st.column_config.CheckboxColumn("Select")},
                use_container_width=True,
                hide_index=True,
                key="cr_items_editor",
            )
            selected_item_ids = edited.loc[edited["Select"], "Item ID"].tolist()

        if st.button("✅ Validate & Schedule Delivery", type="primary", key="cr_submit"):
            errors = []
            if not truck_id:
                errors.append("No active truck selected.")
            if not driver_id:
                errors.append("No available driver selected.")
            if not asst_id:
                errors.append("No available assistant selected.")
            if driver_id and asst_id and driver_id == asst_id:
                errors.append("Driver and assistant must be different employees.")
            if end_ts <= start_ts:
                errors.append("End timestamp must be after start timestamp.")
            if not selected_item_ids:
                errors.append("At least one order item must be selected.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Format the array literal for psycopg
                item_array = list(selected_item_ids)
                ok, err = _run(
                    "CALL public.schedule_delivery(%s, %s, %s, %s, %s, %s, %s)",
                    (
                        route_id,
                        truck_id,
                        driver_id,
                        asst_id,
                        start_ts,
                        end_ts,
                        item_array,
                    ),
                )
                if ok:
                    st.success(
                        "🎉 Delivery scheduled successfully! All business rules passed."
                    )
                    st.balloons()
                else:
                    st.error(f"❌ Scheduling failed: {err}")

with tab_read:
    st.subheader("All Truck Schedules")
    if st.button("🔄 Refresh", key="rd_refresh"):
        st.rerun()

    rows, cols = _schedules()
    if not rows:
        st.info("No truck schedules found in the database.")
    else:
        df = pd.DataFrame(rows, columns=cols)
        df.rename(
            columns={
                "id": "Schedule ID",
                "route_name": "Route",
                "license_plate": "Truck",
                "driver": "Driver",
                "assistant": "Assistant",
                "start_timestamp": "Start",
                "end_timestamp": "End",
                "duration_hours": "Duration (hrs)",
                "created_at": "Created At",
            },
            inplace=True,
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Delivery Items for a Schedule")
        sched_ids = [r[0] for r in rows]
        sel_id = st.selectbox("Select Schedule ID", sched_ids, key="rd_sched_id")
        if sel_id:
            item_rows, item_cols = _schedule_items(sel_id)
            if not item_rows:
                st.info("No items linked to this schedule.")
            else:
                idf = pd.DataFrame(item_rows, columns=item_cols)
                idf.rename(
                    columns={
                        "order_item_id": "Order Item ID",
                        "product_name": "Product",
                        "quantity": "Qty",
                        "total_price": "Total (LKR)",
                        "delivered_at": "Delivered At",
                    },
                    inplace=True,
                )
                st.dataframe(idf, use_container_width=True, hide_index=True)

with tab_update:
    st.subheader("Update a Delivery Schedule")
    st.warning(
        "Only the **start** and **end** timestamps can be updated here. "
        "The schedule must belong to a delivery that has not yet started.",
        icon="⚠️",
    )

    rows, cols = _schedules()
    if not rows:
        st.info("No schedules available to update.")
    else:
        import datetime as _dt

        sched_opts = {
            f"[{r[0]}] {r[5].strftime('%Y-%m-%d %H:%M') if r[5] else 'N/A'} – {r[2]} ({r[1]})": r
            for r in rows
        }
        chosen_label = st.selectbox("Select Schedule to Update", list(sched_opts.keys()), key="upd_sel")
        chosen = sched_opts[chosen_label]
        upd_sched_id = chosen[0]
        cur_start    = chosen[5]
        cur_end      = chosen[6]

        col1, col2 = st.columns(2)
        new_start_date = col1.date_input(
            "New Start Date",
            value=cur_start.date() if cur_start else _dt.date.today() + _dt.timedelta(days=1),
            key="upd_sdate",
        )
        new_start_time = col1.time_input(
            "New Start Time",
            value=cur_start.time() if cur_start else _dt.time(8, 0),
            key="upd_stime",
        )
        new_end_date = col2.date_input(
            "New End Date",
            value=cur_end.date() if cur_end else _dt.date.today() + _dt.timedelta(days=1),
            key="upd_edate",
        )
        new_end_time = col2.time_input(
            "New End Time",
            value=cur_end.time() if cur_end else _dt.time(13, 0),
            key="upd_etime",
        )

        new_start_ts = _dt.datetime.combine(new_start_date, new_start_time)
        new_end_ts   = _dt.datetime.combine(new_end_date,   new_end_time)

        if st.button("💾 Save Changes", type="primary", key="upd_submit"):
            if new_end_ts <= new_start_ts:
                st.error("End time must be after start time.")
            elif new_start_ts <= _dt.datetime.now():
                st.error("New start time must be in the future.")
            else:
                ok, err = _run(
                    """
                    UPDATE public.truck_schedules
                    SET    start_timestamp = %s,
                           end_timestamp   = %s,
                           updated_at      = CURRENT_TIMESTAMP
                    WHERE  id = %s
                      AND  start_timestamp > CURRENT_TIMESTAMP
                    """,
                    (new_start_ts, new_end_ts, upd_sched_id),
                )
                if ok:
                    st.success(f"✅ Schedule {upd_sched_id} updated successfully.")
                else:
                    st.error(f"❌ Update failed: {err}")

with tab_delete:
    st.subheader("Cancel a Delivery Schedule")
    st.error(
        "Cancelling a schedule is **irreversible**. It will:\n"
        "- Remove the truck schedule and all linked delivery assignments.\n"
        "- Revert all linked order items from **OUT_FOR_DELIVERY** back to **STORE_RECEIVED**.\n\n"
        "Only schedules that have **not yet started** can be cancelled.",
        icon="🚨",
    )

    rows, cols = _schedules()
    if not rows:
        st.info("No schedules available to cancel.")
    else:
        import datetime as _dt

        del_opts = {
            f"[{r[0]}] {r[5].strftime('%Y-%m-%d %H:%M') if r[5] else 'N/A'} – {r[2]} ({r[1]})": r
            for r in rows
        }
        del_label = st.selectbox("Select Schedule to Cancel", list(del_opts.keys()), key="del_sel")
        del_sched = del_opts[del_label]
        del_sched_id  = del_sched[0]
        del_start_ts  = del_sched[5]

        started = del_start_ts and del_start_ts <= _dt.datetime.now(_dt.timezone.utc)
        if started:
            st.warning("This schedule has already started and cannot be cancelled.")
        else:
            confirm = st.checkbox(
                f"I confirm I want to permanently cancel Schedule **{del_sched_id}**.",
                key="del_confirm",
            )
            if st.button("🗑️ Cancel Schedule", type="primary", disabled=not confirm, key="del_submit"):
                # Revert order items first, then delete the schedule (cascades deliveries)
                ok, err = _run(
                    """
                    UPDATE public.order_items
                    SET    item_lifecycle_status = 'STORE_RECEIVED',
                           updated_at            = CURRENT_TIMESTAMP
                    WHERE  id IN (
                        SELECT order_item_id
                        FROM   public.truck_item_deliveries
                        WHERE  truck_schedule_id = %s
                    )
                    """,
                    (del_sched_id,),
                )
                if not ok:
                    st.error(f"❌ Failed to revert order items: {err}")
                else:
                    ok2, err2 = _run(
                        "DELETE FROM public.truck_schedules WHERE id = %s AND start_timestamp > CURRENT_TIMESTAMP",
                        (del_sched_id,),
                    )
                    if ok2:
                        st.success(f"✅ Schedule {del_sched_id} cancelled and order items reverted.")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete schedule: {err2}")
            st.success("Dispatch validated and scheduled without violations.")