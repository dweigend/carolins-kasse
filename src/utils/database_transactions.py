"""Transaction helpers for the SQLite database."""

import json
import sqlite3

from src.utils.database_models import Transaction


def save_transaction(
    conn: sqlite3.Connection,
    user_card_id: str,
    total: int,
    items: list[dict],
) -> int:
    """Save a purchase transaction and return its ID."""
    items_json = json.dumps(items, ensure_ascii=False)
    cursor = conn.execute(
        """
        INSERT INTO transactions (user_card_id, total, items_json)
        VALUES (?, ?, ?)
        """,
        (user_card_id, total, items_json),
    )
    if cursor.rowcount != 1 or cursor.lastrowid is None:
        raise RuntimeError(f"Failed to save transaction for user {user_card_id}")
    return cursor.lastrowid


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
