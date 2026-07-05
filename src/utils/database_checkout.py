"""Checkout helpers for the SQLite database."""

import sqlite3

from src.utils import database_transactions
from src.utils.database_models import (
    USER_COLUMNS,
    CheckoutUserNotFoundError,
    InsufficientFundsError,
    User,
)


def process_checkout(
    conn: sqlite3.Connection,
    card_id: str,
    total: int,
    items: list[dict],
) -> tuple[int, User]:
    """Apply checkout writes on an existing transaction connection."""
    user = get_checkout_user(conn, card_id)
    if user.balance < total:
        raise InsufficientFundsError(available=user.balance, required=total)

    deduct_checkout_balance(conn, card_id, total)
    transaction_id = database_transactions.save_transaction(
        conn,
        card_id,
        total,
        items,
    )

    user.balance -= total
    return transaction_id, user


def get_checkout_user(conn: sqlite3.Connection, card_id: str) -> User:
    """Get the active checkout user or raise a checkout-specific error."""
    row = conn.execute(
        f"""
        SELECT {USER_COLUMNS}
        FROM users
        WHERE card_id = ? AND active = 1
        """,
        (card_id,),
    ).fetchone()
    if row is None:
        raise CheckoutUserNotFoundError(f"Unknown user card ID: {card_id}")
    return User.from_row(row)


def deduct_checkout_balance(
    conn: sqlite3.Connection,
    card_id: str,
    total: int,
) -> None:
    """Deduct checkout total from a user's balance."""
    update_cursor = conn.execute(
        """
        UPDATE users
        SET balance = balance - ?
        WHERE card_id = ? AND active = 1 AND balance >= ?
        """,
        (total, card_id, total),
    )
    if update_cursor.rowcount != 1:
        raise RuntimeError(f"Failed to update checkout balance for {card_id}")
