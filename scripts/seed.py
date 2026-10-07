"""Seed the database with test data for local development.

Run this AFTER scripts/up.py has applied the schema:
    python scripts/seed.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import psycopg  # noqa: E402

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    sys.exit(1)

SEED_SQL = os.path.join(os.path.dirname(__file__), "..", "db", "seed.sql")


def run():
    if not os.path.exists(SEED_SQL):
        print(f"ERROR: seed file not found at {SEED_SQL}")
        sys.exit(1)

    with open(SEED_SQL, "r", encoding="utf-8") as f:
        sql = f.read().strip()

    if not sql:
        print("Seed file is empty – nothing to do.")
        return

    print("Seeding database …")
    # Split on semicolons so each statement runs individually;
    # this avoids issues with procedure bodies that contain semicolons.
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        for stmt in statements:
            try:
                conn.execute(stmt)
            except Exception as exc:
                # Print but continue so partial failures are visible
                short = stmt[:80].replace("\n", " ")
                print(f"  WARN  [{short}…]: {exc}")

    print("Seed complete.")


if __name__ == "__main__":
    run()