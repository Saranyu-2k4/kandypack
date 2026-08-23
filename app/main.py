import os
import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="Postgres DB Explorer", page_icon="🐘", layout="wide")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    st.error("Missing `DATABASE_URL` environment variable. Set it in your environment to continue.")
    st.stop()


def get_connection():
    """Returns a psycopg connection with autocommit enabled."""
    return psycopg.connect(DATABASE_URL, autocommit=True)


@st.cache_data(ttl=60)
def get_tables():
    """Fetch all base tables in the public schema."""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        st.error(f"Failed to fetch tables: {e}")
        return []


def execute_query(sql: str):
    """Executes SQL and returns (dataframe, rowcount, error)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    records = cur.fetchall()
                    df = pd.DataFrame(records, columns=columns)
                    return df, len(df), None
                else:
                    return None, cur.rowcount, None
    except Exception as e:
        return None, 0, str(e)


# --- UI Layout ---
st.title("🐘 Postgres Database Explorer")

tab_viewer, tab_sql = st.tabs(["📊 Table Viewer", "⚡ Run Custom SQL"])

# --- Tab 1: Table Viewer ---
with tab_viewer:
    tables = get_tables()

    if not tables:
        st.info("No user tables found in the `public` schema.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_table = st.selectbox("Select Table", tables)
        with col2:
            limit = st.selectbox("Row Limit", [50, 100, 500, 1000], index=1)

        if selected_table:
            # Identifier quotes prevent issues with reserved names
            preview_query = f'SELECT * FROM "{selected_table}" LIMIT {limit};'
            df, count, err = execute_query(preview_query)

            if err:
                st.error(err)
            elif df is not None:
                st.caption(f"Showing up to {limit} rows from **{selected_table}**")
                st.dataframe(df, use_container_width=True)

# --- Tab 2: SQL Console ---
with tab_sql:
    st.write("Execute any `SELECT`, `INSERT`, `UPDATE`, `DELETE`, or `DDL` statement:")

    default_query = "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public';"
    user_query = st.text_area("SQL Query", value=default_query, height=160)

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        run_clicked = st.button("Run Query", type="primary", use_container_width=True)

    if run_clicked and user_query.strip():
        with st.spinner("Executing query..."):
            df, rowcount, err = execute_query(user_query)

            if err:
                st.error(f"**Execution Error:** {err}")
            elif df is not None:
                st.success(f"Query returned **{len(df)}** row(s).")
                st.dataframe(df, use_container_width=True)
            else:
                st.success(f"Query executed successfully. Affected rows: **{rowcount}**")
                st.cache_data.clear()  # Clear cache to reflect possible schema changes