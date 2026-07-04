"""Transaction query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import Transaction


def get_user_transactions(
    conn: sqlite3.Connection,
    user_card_id: str,
    limit: int = 10,
) -> list[Transaction]:
    """Get recent transactions for a user."""
    rows = conn.execute(
        """
        SELECT * FROM transactions
        WHERE user_card_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_card_id, limit),
    ).fetchall()
    return [Transaction.from_row(row) for row in rows]
