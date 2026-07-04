"""Manual balance adjustment query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import BalanceAdjustment


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
