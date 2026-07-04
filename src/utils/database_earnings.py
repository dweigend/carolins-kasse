"""Earning query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import Earning


def get_today_earnings(conn: sqlite3.Connection, user_card_id: str) -> list[Earning]:
    """Get all earnings for a user from today."""
    rows = conn.execute(
        """
        SELECT * FROM earnings
        WHERE user_card_id = ?
        AND date(earned_at) = date('now', 'localtime')
        ORDER BY earned_at DESC
        """,
        (user_card_id,),
    ).fetchall()
    return [Earning.from_row(row) for row in rows]


def get_session_earnings(conn: sqlite3.Connection, session_id: int) -> list[Earning]:
    """Get all earnings for a specific session."""
    rows = conn.execute(
        "SELECT * FROM earnings WHERE session_id = ? ORDER BY earned_at DESC",
        (session_id,),
    ).fetchall()
    return [Earning.from_row(row) for row in rows]


def get_today_earnings_summary(
    conn: sqlite3.Connection, user_card_id: str
) -> dict[str, int]:
    """Get earnings summary grouped by source for today."""
    rows = conn.execute(
        """
        SELECT source, SUM(amount) as total
        FROM earnings
        WHERE user_card_id = ?
        AND date(earned_at) = date('now', 'localtime')
        GROUP BY source
        """,
        (user_card_id,),
    ).fetchall()
    return {row[0]: row[1] for row in rows}
