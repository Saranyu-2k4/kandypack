import os
from contextlib import contextmanager
from typing import Any, NamedTuple, Optional
from urllib.parse import quote
import streamlit as st
from psycopg import Connection
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    try:
        with open("/run/secrets/db_password", encoding="utf-8") as secret_file:
            password = secret_file.read().strip()
        if password:
            return f"postgresql://postgres:{quote(password, safe='')}@db:5432/kandypack"
    except OSError:
        pass

    return "postgresql://postgres:postgres@db:5432/kandypack"


DATABASE_URL = _get_database_url()


@st.cache_resource
def get_connection_pool(
    conn_info: str,
) -> ConnectionPool[Connection[NamedTuple]]:
    return ConnectionPool(
        conninfo=conn_info,
        min_size=1,
        max_size=10,
        open=True,
        kwargs={"row_factory": namedtuple_row},
    )


pool = get_connection_pool(DATABASE_URL)


@contextmanager
def get_connection():
    """Provides a connection from the pool that safely works with 'with get_connection() as conn:'."""
    with pool.connection() as conn:
        yield conn


def execute_query(query: str, params: Optional[Any] = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()


def fetch_one(query: str, params: Optional[Any] = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: Optional[Any] = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def safe_execute_query(query: str, params: Optional[Any] = None):
    try:
        execute_query(query, params)
        return True, None
    except Exception as e:
        print(f"DB Error: {e}")
        return False, e


def safe_fetch_one(query: str, params: Optional[Any] = None):
    try:
        return fetch_one(query, params), None
    except Exception as e:
        print(f"DB Error: {e}")
        return None, e


def safe_fetch_all(query: str, params: Optional[Any] = None):
    try:
        return fetch_all(query, params), None
    except Exception as e:
        print(f"DB Error: {e}")
        return None, e