"""Manual balance adjustment query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import BalanceAdjustment


def update_user_balance(
    conn: sqlite3.Connection,
    card_id: str,
    new_balance: float,
    note: str | None = None,
) -> None:
    """Update a user's balance and record the manual adjustment."""
    row = conn.execute(
        "SELECT balance FROM users WHERE card_id = ?", (card_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Unknown user card ID: {card_id}")

    old_balance = float(row[0])
    delta = new_balance - old_balance
    update_cursor = conn.execute(
        "UPDATE users SET balance = ? WHERE card_id = ?",
        (new_balance, card_id),
    )
    if update_cursor.rowcount != 1:
        raise RuntimeError(f"Failed to update balance for user {card_id}")

    adjustment_cursor = conn.execute(
        """
        INSERT INTO balance_adjustments (
            user_card_id, old_balance, new_balance, delta, note
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (card_id, old_balance, new_balance, delta, note),
    )
    if adjustment_cursor.rowcount != 1:
        raise RuntimeError(f"Failed to record balance adjustment for user {card_id}")


def get_recent_balance_adjustments(
    conn: sqlite3.Connection,
    limit: int = 20,
) -> list[BalanceAdjustment]:
    """Get recent manual admin balance changes."""
    rows = conn.execute(
        """
        SELECT
            ba.id,
            ba.user_card_id,
            u.name,
            ba.old_balance,
            ba.new_balance,
            ba.delta,
            ba.note,
            ba.created_at
        FROM balance_adjustments ba
        JOIN users u ON ba.user_card_id = u.card_id
        ORDER BY ba.created_at DESC, ba.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [BalanceAdjustment.from_row(row) for row in rows]
