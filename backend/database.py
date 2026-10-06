import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"


@contextmanager
def get_connection():
    """Open a connection, commit on success (rollback on error), always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                company      TEXT NOT NULL,
                role         TEXT NOT NULL,
                status       TEXT NOT NULL,
                date_applied TEXT NOT NULL
            )
            """
        )
