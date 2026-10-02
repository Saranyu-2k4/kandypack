import os
from psycopg import Connection
from psycopg.rows import namedtuple_row, NamedTuple
import streamlit as st
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", st.secrets.get("DATABASE_URL"))
@st.cache_resource
def get_connection_pool(conn_info: str) -> ConnectionPool[Connection[NamedTuple]]:
    return ConnectionPool(conninfo=conn_info, min_size=1, max_size=10, open=True, kwargs={"row_factory": namedtuple_row})

pool = get_connection_pool(DATABASE_URL)

def execute_query(query: str, params: dict = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()

def fetch_one(query: str, params: dict = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

def fetch_all(query: str, params: dict = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

def safe_execute_query(query: str, params: dict = None):
    try:
        execute_query(query, params)
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False, e

def safe_fetch_one(query: str, params: dict = None):
    try:
        return fetch_one(query, params)
    except Exception as e:
        print(f"DB Error: {e}")
        return None, e

def safe_fetch_all(query: str, params: dict = None):
    try:
        return fetch_all(query, params)
    except Exception as e:
        print(f"DB Error: {e}")
        return None, e