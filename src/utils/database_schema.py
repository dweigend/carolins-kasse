"""Schema initialization helpers for the SQLite database."""

import sqlite3


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize database tables on an existing connection."""
    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_de TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_path TEXT,
            has_barcode BOOLEAN DEFAULT 1,
            active BOOLEAN DEFAULT 1
        )
    """)

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            card_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            balance REAL DEFAULT 10.0,
            color TEXT,
            difficulty INTEGER DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            active BOOLEAN DEFAULT 1
        )
    """)

    # Recipes table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image_path TEXT,
            active BOOLEAN DEFAULT 1
        )
    """)

    # Recipe ingredients (junction table)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_barcode TEXT NOT NULL,
            product_barcode TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (recipe_barcode, product_barcode),
            FOREIGN KEY (recipe_barcode) REFERENCES recipes(barcode),
            FOREIGN KEY (product_barcode) REFERENCES products(barcode)
        )
    """)

    # Sessions table (login to logout)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            user_card_id TEXT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            FOREIGN KEY (user_card_id) REFERENCES users(card_id)
        )
    """)

    # Earnings table (per activity)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS earnings (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            user_card_id TEXT NOT NULL,
            source TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT,
            earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (user_card_id) REFERENCES users(card_id)
        )
    """)

    # Transactions table (purchases)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_card_id TEXT NOT NULL,
            total INTEGER NOT NULL,
            items_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_card_id) REFERENCES users(card_id)
        )
    """)

    # Manual admin balance changes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS balance_adjustments (
            id INTEGER PRIMARY KEY,
            user_card_id TEXT NOT NULL,
            old_balance REAL NOT NULL,
            new_balance REAL NOT NULL,
            delta REAL NOT NULL,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_card_id) REFERENCES users(card_id)
        )
    """)

    _ensure_column(conn, "products", "active", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, "users", "active", "BOOLEAN DEFAULT 1")
    _ensure_column(conn, "recipes", "active", "BOOLEAN DEFAULT 1")


def _ensure_column(
    conn: sqlite3.Connection, table_name: str, column_name: str, column_spec: str
) -> None:
    existing_columns = {
        row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in existing_columns:
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}")
