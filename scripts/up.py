"""Apply the database schema and stored procedures to the target database.

Run this once before starting the app for the first time:
    python scripts/up.py
"""

import os
import sys

# Allow importing from app/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import psycopg  # noqa: E402

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    sys.exit(1)

BASE = os.path.join(os.path.dirname(__file__), "..")

SQL_FILES = [
    os.path.join(BASE, "db", "schema.sql"),
    os.path.join(BASE, "db", "place_order.sql"),
    os.path.join(BASE, "db", "allocate_train.sql"),
    os.path.join(BASE, "db", "receive_cargo.sql"),
    os.path.join(BASE, "db", "procedures", "schedule_delivery.sql"),
    os.path.join(BASE, "db", "complete_delivery.sql"),
]


def run():
    print(f"Connecting to database …")
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        for path in SQL_FILES:
            if not os.path.exists(path):
                print(f"  SKIP  {path}  (file not found)")
                continue
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read().strip()
            if not sql:
                print(f"  SKIP  {path}  (empty)")
                continue
            try:
                conn.execute(sql)
                print(f"  OK    {os.path.relpath(path, BASE)}")
            except Exception as exc:
                print(f"  ERROR {os.path.relpath(path, BASE)}: {exc}")
    print("Schema setup complete.")


if __name__ == "__main__":
    run()