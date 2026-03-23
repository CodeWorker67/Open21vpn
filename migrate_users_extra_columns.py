"""
Adds columns to `users` to match the Users model (schema extension).
Idempotent: safe to run multiple times.

Usage (from project root):
    python migrate_users_extra_columns.py
"""
from pathlib import Path

import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "config_bd" / "open21vpn.db"
TABLE = "users"

MIGRATIONS = [
    ("subscribtion", "ALTER TABLE users ADD COLUMN subscribtion TEXT"),
    ("white_subscription", "ALTER TABLE users ADD COLUMN white_subscription TEXT"),
    ("email", "ALTER TABLE users ADD COLUMN email TEXT"),
    ("password", "ALTER TABLE users ADD COLUMN password TEXT"),
    ("activation_pass", "ALTER TABLE users ADD COLUMN activation_pass TEXT"),
    ("field_str_1", "ALTER TABLE users ADD COLUMN field_str_1 TEXT"),
    ("field_str_2", "ALTER TABLE users ADD COLUMN field_str_2 TEXT"),
    ("field_str_3", "ALTER TABLE users ADD COLUMN field_str_3 TEXT"),
    ("field_bool_1", "ALTER TABLE users ADD COLUMN field_bool_1 INTEGER NOT NULL DEFAULT 0"),
    ("field_bool_2", "ALTER TABLE users ADD COLUMN field_bool_2 INTEGER NOT NULL DEFAULT 0"),
    ("field_bool_3", "ALTER TABLE users ADD COLUMN field_bool_3 INTEGER NOT NULL DEFAULT 0"),
]


def existing_columns(conn: sqlite3.Connection):
    cur = conn.execute(f'PRAGMA table_info("{TABLE}")')
    return {row[1] for row in cur.fetchall()}


def main() -> None:
    if not DB_PATH.is_file():
        raise SystemExit(f"Database file not found: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    try:
        cols = existing_columns(conn)
        for name, ddl in MIGRATIONS:
            if name in cols:
                print(f"skip (exists): {name}")
                continue
            conn.execute(ddl)
            conn.commit()
            print(f"ok: {name}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
