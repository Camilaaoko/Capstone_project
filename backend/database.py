"""Database connection manager for KEMSA Intelligence Platform backend.

Reuses the existing SQLite dimensional warehouse in analytics/analytics.db
without duplicating or copying files.
"""

import sqlite3
from pathlib import Path
from typing import Generator

# Resolve absolute path to existing analytics/analytics.db in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "analytics" / "analytics.db"


def get_db_path() -> Path:
    """Returns the validated path to analytics.db."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Analytics database not found at {DB_PATH}. "
            "Please run 'python etl_pipeline.py' first to build analytics.db."
        )
    return DB_PATH


def init_db_tables(conn: sqlite3.Connection):
    """Ensures transactional workflow tables like transfer_requests exist in analytics.db."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transfer_requests (
            request_id TEXT PRIMARY KEY,
            source_facility_id TEXT NOT NULL,
            destination_facility_id TEXT NOT NULL,
            commodity_id TEXT NOT NULL,
            requested_quantity REAL NOT NULL,
            recommended_quantity REAL NOT NULL,
            distance_km REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'completed')),
            requested_by TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            reviewed_by TEXT,
            reviewed_at TEXT,
            reason TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tr_status ON transfer_requests(status);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tr_dest ON transfer_requests(destination_facility_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tr_src ON transfer_requests(source_facility_id);")
    conn.commit()


def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db_tables(conn)
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency yielding a managed database connection."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
