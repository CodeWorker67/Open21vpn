"""
Creates payments_youkassa table if missing. Idempotent.

Usage (from project root):
    python migrate_payments_youkassa_table.py
"""
from pathlib import Path

import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "config_bd" / "open21vpn.db"

CREATE_PAYMENTS_YOUKASSA = """
CREATE TABLE IF NOT EXISTS payments_youkassa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    time_created DATETIME,
    is_gift INTEGER NOT NULL DEFAULT 0,
    status TEXT,
    transaction_id TEXT,
    payload TEXT
)
"""


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def main() -> None:
    if not DB_PATH.is_file():
        raise SystemExit(f"Database file not found: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    try:
        if table_exists(conn, "payments_youkassa"):
            print("skip (exists): payments_youkassa")
        else:
            conn.execute(CREATE_PAYMENTS_YOUKASSA)
            conn.commit()
            print("ok: payments_youkassa")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
