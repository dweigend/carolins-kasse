"""Database module for Carolin's Kasse.

SQLite database with tables for products, users, recipes, recipe ingredients,
sessions, earnings, and transactions.
Uses EAN-13 barcodes with prefixes:
- 100: Products
- 200: Users
- 300: Recipes
"""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self


# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "kasse.db"


@dataclass
class Product:
    """A product in the shop."""

    barcode: str
    name: str
    name_de: str
    price: float
    category: str
    image_path: str | None = None
    has_barcode: bool = True

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Product from database row."""
        return cls(
            barcode=row[0],
            name=row[1],
            name_de=row[2],
            price=row[3],
            category=row[4],
            image_path=row[5],
            has_barcode=bool(row[6]),
        )


@dataclass
class User:
    """A user/customer."""

    card_id: str
    name: str
    balance: float = 10.0
    color: str | None = None
    difficulty: int = 1
    is_admin: bool = False

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create User from database row."""
        return cls(
            card_id=row[0],
            name=row[1],
            balance=row[2],
            color=row[3],
            difficulty=row[4],
            is_admin=bool(row[5]),
        )


@dataclass
class Recipe:
    """A recipe card."""

    barcode: str
    name: str
    image_path: str | None = None

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Recipe from database row."""
        return cls(
            barcode=row[0],
            name=row[1],
            image_path=row[2],
        )


@dataclass
class RecipeIngredient:
    """An ingredient in a recipe."""

    recipe_barcode: str
    product_barcode: str
    quantity: int = 1


@dataclass
class Session:
    """A work session (login to logout)."""

    id: int
    user_card_id: str
    started_at: datetime
    ended_at: datetime | None = None

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Session from database row."""
        return cls(
            id=row[0],
            user_card_id=row[1],
            started_at=datetime.fromisoformat(row[2]),
            ended_at=datetime.fromisoformat(row[3]) if row[3] else None,
        )


@dataclass
class Earning:
    """An earning entry from an activity."""

    id: int
    session_id: int
    user_card_id: str
    source: str  # 'math', 'cashier', 'time'
    amount: int
    description: str | None
    earned_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Earning from database row."""
        return cls(
            id=row[0],
            session_id=row[1],
            user_card_id=row[2],
            source=row[3],
            amount=row[4],
            description=row[5],
            earned_at=datetime.fromisoformat(row[6]),
        )


@dataclass
class Transaction:
    """A purchase transaction."""

    id: int
    user_card_id: str
    total: int
    items_json: str
    timestamp: datetime

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create Transaction from database row."""
        return cls(
            id=row[0],
            user_card_id=row[1],
            total=row[2],
            items_json=row[3],
            timestamp=datetime.fromisoformat(row[4]),
        )


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


@contextmanager
def get_db() -> Generator[sqlite3.Connection]:
    """Context manager for safe database connections.

    Ensures the connection is always closed, even on exceptions.

    Usage:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM products").fetchone()
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """Initialize the database schema."""
    with get_db() as conn:
        # Products table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                barcode TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                name_de TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                image_path TEXT,
                has_barcode BOOLEAN DEFAULT 1
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
                is_admin BOOLEAN DEFAULT 0
            )
        """)

        # Recipes table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                barcode TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                image_path TEXT
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

        conn.commit()


# --- Product CRUD ---


def get_product(barcode: str) -> Product | None:
    """Get a product by barcode."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE barcode = ?", (barcode,)
        ).fetchone()
        return Product.from_row(row) if row else None


def get_all_products() -> list[Product]:
    """Get all products."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
        return [Product.from_row(row) for row in rows]


def get_products_by_category(category: str) -> list[Product]:
    """Get products by category."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
        ).fetchall()
        return [Product.from_row(row) for row in rows]


def get_picker_products() -> dict[str, list[Product]]:
    """Get products without barcodes, grouped by category for picker."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE has_barcode = 0 ORDER BY category, name_de"
        ).fetchall()

    products = [Product.from_row(row) for row in rows]
    grouped: dict[str, list[Product]] = {}
    for product in products:
        if product.category not in grouped:
            grouped[product.category] = []
        grouped[product.category].append(product)
    return grouped


def add_product(product: Product) -> None:
    """Add a new product."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO products (barcode, name, name_de, price, category, image_path, has_barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.barcode,
                product.name,
                product.name_de,
                product.price,
                product.category,
                product.image_path,
                product.has_barcode,
            ),
        )
        conn.commit()


def update_product(product: Product) -> None:
    """Update an existing product."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, name_de = ?, price = ?, category = ?, image_path = ?, has_barcode = ?
            WHERE barcode = ?
            """,
            (
                product.name,
                product.name_de,
                product.price,
                product.category,
                product.image_path,
                product.has_barcode,
                product.barcode,
            ),
        )
        conn.commit()


def delete_product(barcode: str) -> None:
    """Delete a product."""
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
        conn.commit()


# --- User CRUD ---


def get_user(card_id: str) -> User | None:
    """Get a user by card ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE card_id = ?", (card_id,)
        ).fetchone()
        return User.from_row(row) if row else None


def get_all_users() -> list[User]:
    """Get all users."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [User.from_row(row) for row in rows]


def add_user(user: User) -> None:
    """Add a new user."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (card_id, name, balance, color, difficulty, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.card_id,
                user.name,
                user.balance,
                user.color,
                user.difficulty,
                user.is_admin,
            ),
        )
        conn.commit()


def update_user_balance(card_id: str, new_balance: float) -> None:
    """Update a user's balance."""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET balance = ? WHERE card_id = ?", (new_balance, card_id)
        )
        conn.commit()


def delete_user(card_id: str) -> None:
    """Delete a user."""
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE card_id = ?", (card_id,))
        conn.commit()


# --- Recipe CRUD ---


def get_recipe(barcode: str) -> Recipe | None:
    """Get a recipe by barcode."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM recipes WHERE barcode = ?", (barcode,)
        ).fetchone()
        return Recipe.from_row(row) if row else None


def get_all_recipes() -> list[Recipe]:
    """Get all recipes."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM recipes ORDER BY name").fetchall()
        return [Recipe.from_row(row) for row in rows]


def add_recipe(recipe: Recipe) -> None:
    """Add a new recipe."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO recipes (barcode, name, image_path)
            VALUES (?, ?, ?)
            """,
            (recipe.barcode, recipe.name, recipe.image_path),
        )
        conn.commit()


def delete_recipe(barcode: str) -> None:
    """Delete a recipe and its ingredients."""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (barcode,)
        )
        conn.execute("DELETE FROM recipes WHERE barcode = ?", (barcode,))
        conn.commit()


# --- Recipe Ingredients ---


def get_recipe_ingredients(recipe_barcode: str) -> list[tuple[Product, int]]:
    """Get all ingredients for a recipe with quantities."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT p.*, ri.quantity
            FROM recipe_ingredients ri
            JOIN products p ON ri.product_barcode = p.barcode
            WHERE ri.recipe_barcode = ?
            ORDER BY p.name
            """,
            (recipe_barcode,),
        ).fetchall()
        return [(Product.from_row(row[:7]), row[7]) for row in rows]


def add_recipe_ingredient(ingredient: RecipeIngredient) -> None:
    """Add an ingredient to a recipe."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO recipe_ingredients (recipe_barcode, product_barcode, quantity)
            VALUES (?, ?, ?)
            """,
            (
                ingredient.recipe_barcode,
                ingredient.product_barcode,
                ingredient.quantity,
            ),
        )
        conn.commit()


def clear_recipe_ingredients(recipe_barcode: str) -> None:
    """Remove all ingredients from a recipe."""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (recipe_barcode,)
        )
        conn.commit()


# --- Barcode Helpers ---


def calculate_ean13_check_digit(code: str) -> str:
    """Calculate EAN-13 check digit for a 12-digit code."""
    if len(code) != 12:
        raise ValueError("Code must be exactly 12 digits")
    if not code.isdigit():
        raise ValueError("Code must contain only digits")

    total = 0
    for i, digit in enumerate(code):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight

    check_digit = (10 - (total % 10)) % 10
    return code + str(check_digit)


def generate_product_barcode(number: int) -> str:
    """Generate EAN-13 barcode for a product (prefix 100)."""
    base = f"100{number:09d}"
    return calculate_ean13_check_digit(base)


def generate_user_barcode(number: int) -> str:
    """Generate EAN-13 barcode for a user (prefix 200)."""
    base = f"200{number:09d}"
    return calculate_ean13_check_digit(base)


def generate_recipe_barcode(number: int) -> str:
    """Generate EAN-13 barcode for a recipe (prefix 300)."""
    base = f"300{number:09d}"
    return calculate_ean13_check_digit(base)


# --- Session Management ---


def start_session(user_card_id: str) -> int:
    """Start a new work session, return session ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (user_card_id) VALUES (?)",
            (user_card_id,),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore


def end_session(session_id: int) -> None:
    """End a work session by setting ended_at."""
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        conn.commit()


def get_session(session_id: int) -> Session | None:
    """Get a session by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return Session.from_row(row) if row else None


# --- Earnings ---


def add_earning(
    session_id: int,
    user_card_id: str,
    source: str,
    amount: int,
    description: str | None = None,
) -> None:
    """Add an earning entry and update user balance."""
    with get_db() as conn:
        # Add earning record
        conn.execute(
            """
            INSERT INTO earnings (session_id, user_card_id, source, amount, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_card_id, source, amount, description),
        )
        # Update user balance
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE card_id = ?",
            (amount, user_card_id),
        )
        conn.commit()


def get_today_earnings(user_card_id: str) -> list[Earning]:
    """Get all earnings for a user from today."""
    with get_db() as conn:
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


def get_session_earnings(session_id: int) -> list[Earning]:
    """Get all earnings for a specific session."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM earnings WHERE session_id = ? ORDER BY earned_at DESC",
            (session_id,),
        ).fetchall()
        return [Earning.from_row(row) for row in rows]


def get_today_earnings_summary(user_card_id: str) -> dict[str, int]:
    """Get earnings summary grouped by source for today."""
    with get_db() as conn:
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


# --- Transactions ---


def save_transaction(
    user_card_id: str,
    total: int,
    items: list[dict],
) -> int:
    """Save a purchase transaction, return transaction ID."""
    items_json = json.dumps(items, ensure_ascii=False)
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (user_card_id, total, items_json)
            VALUES (?, ?, ?)
            """,
            (user_card_id, total, items_json),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore


def process_checkout(
    card_id: str,
    new_balance: float,
    total: int,
    items: list[dict],
) -> int:
    """Atomically process checkout: update balance + save transaction.

    Both operations happen in a single transaction - if either fails,
    neither change is committed.
    """
    items_json = json.dumps(items, ensure_ascii=False)
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET balance = ? WHERE card_id = ?",
            (new_balance, card_id),
        )
        cursor = conn.execute(
            """
            INSERT INTO transactions (user_card_id, total, items_json)
            VALUES (?, ?, ?)
            """,
            (card_id, total, items_json),
        )
        conn.commit()
        return cursor.lastrowid  # type: ignore


def get_user_transactions(user_card_id: str, limit: int = 10) -> list[Transaction]:
    """Get recent transactions for a user."""
    with get_db() as conn:
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
