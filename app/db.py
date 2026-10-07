"""Database connection and query helpers for the KandyPack Logistics app."""

import os
import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    pass

def get_connection():
    return psycopg.connect(DATABASE_URL, autocommit=True)


def execute_query(sql: str, params=None):

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if cur.description:
                    rows = cur.fetchall()
                    cols = [d.name for d in cur.description]
                else:
                    rows, cols = [], []
                return rows, cols, None
    except Exception as exc:
        return [], [], str(exc)


def call_procedure(proc_name: str, params: tuple):
    try:
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            with conn.cursor() as cur:
                placeholders = ", ".join(["%s"] * len(params))
                cur.execute(f"CALL {proc_name}({placeholders})", params)
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)

