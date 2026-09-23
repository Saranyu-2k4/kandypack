# create datatabase tables

import os
import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    pass
    # TODO: Error


def get_connection():
    """Returns a psycopg connection with autocommit enabled."""
    return psycopg.connect(DATABASE_URL, autocommit=True)

def execute_query(sql: str):
    """Executes SQL."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    except Exception as e:
        return None, 0, str(e)
