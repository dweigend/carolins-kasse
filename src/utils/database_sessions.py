"""Session query helpers for the SQLite database."""

import sqlite3
from typing import cast

from src.utils.database_models import Session


def start_session(conn: sqlite3.Connection, user_card_id: str) -> int:
    """Start a new work session, return session ID."""
    cursor = conn.execute(
        "INSERT INTO sessions (user_card_id) VALUES (?)",
        (user_card_id,),
    )
    return cast(int, cursor.lastrowid)


def end_session(conn: sqlite3.Connection, session_id: int) -> None:
    """End a work session by setting ended_at."""
    conn.execute(
        "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,),
    )


def get_session(conn: sqlite3.Connection, session_id: int) -> Session | None:
    """Get a session by ID."""
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return Session.from_row(row) if row else None
