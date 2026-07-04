"""User query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import USER_COLUMNS, User


def get_user(
    conn: sqlite3.Connection, card_id: str, include_inactive: bool = False
) -> User | None:
    """Get a user by card ID."""
    active_clause = "" if include_inactive else "AND active = 1"
    row = conn.execute(
        f"""
        SELECT {USER_COLUMNS}
        FROM users
        WHERE card_id = ? {active_clause}
        """,
        (card_id,),
    ).fetchone()
    return User.from_row(row) if row else None


def get_all_users(
    conn: sqlite3.Connection, include_inactive: bool = False
) -> list[User]:
    """Get all users."""
    where_clause = "" if include_inactive else "WHERE active = 1"
    rows = conn.execute(
        f"""
        SELECT {USER_COLUMNS}
        FROM users
        {where_clause}
        ORDER BY name
        """
    ).fetchall()
    return [User.from_row(row) for row in rows]


def add_user(conn: sqlite3.Connection, user: User) -> None:
    """Add a new user."""
    conn.execute(
        """
        INSERT INTO users (
            card_id, name, balance, color, difficulty, is_admin, active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.card_id,
            user.name,
            user.balance,
            user.color,
            user.difficulty,
            user.is_admin,
            user.active,
        ),
    )


def update_user_admin_fields(
    conn: sqlite3.Connection, card_id: str, name: str, difficulty: int, active: bool
) -> None:
    """Update parent-facing user fields."""
    conn.execute(
        """
        UPDATE users
        SET name = ?, difficulty = ?, active = ?
        WHERE card_id = ?
        """,
        (name, difficulty, active, card_id),
    )


def delete_user(conn: sqlite3.Connection, card_id: str) -> None:
    """Delete a user."""
    conn.execute("DELETE FROM users WHERE card_id = ?", (card_id,))
