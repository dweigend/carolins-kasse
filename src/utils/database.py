"""Database module for Carolin's Kasse.

SQLite database with tables for products, users, recipes, recipe ingredients,
sessions, earnings, and transactions.
Uses EAN-13 barcodes with prefixes:
- 100: Products
- 200: Users
- 300: Recipes
"""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from src.utils import (
    database_balance_adjustments,
    database_checkout,
    database_earnings,
    database_products,
    database_recipes,
    database_schema,
    database_sessions,
    database_transactions,
    database_users,
)
from src.utils.database_models import (
    PRODUCT_COLUMNS as PRODUCT_COLUMNS,
    RECIPE_COLUMNS as RECIPE_COLUMNS,
    USER_COLUMNS as USER_COLUMNS,
    BalanceAdjustment,
    CheckoutError as CheckoutError,
    CheckoutResult,
    CheckoutUserNotFoundError as CheckoutUserNotFoundError,
    Earning,
    InsufficientFundsError as InsufficientFundsError,
    Product,
    Recipe,
    RecipeIngredient,
    Session,
    Transaction,
    User,
)


# Database path. The Pi installer sets this to /var/lib/carolins-kasse/kasse.db
# so runtime balances are kept outside the Git checkout.
DB_PATH = Path(
    os.environ.get(
        "CAROLINS_KASSE_DB_PATH",
        Path(__file__).parent.parent.parent / "data" / "kasse.db",
    )
).expanduser()


SQLITE_BUSY_TIMEOUT_MS = 5000


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    return conn


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
        database_schema.init_schema(conn)
        conn.commit()


# --- Product CRUD ---


def get_product(barcode: str) -> Product | None:
    """Get an active product by barcode."""
    with get_db() as conn:
        return database_products.get_product(conn, barcode)


def get_all_products(include_inactive: bool = False) -> list[Product]:
    """Get all products."""
    with get_db() as conn:
        return database_products.get_all_products(conn, include_inactive)


def get_products_by_category(category: str) -> list[Product]:
    """Get active products by category."""
    with get_db() as conn:
        return database_products.get_products_by_category(conn, category)


def get_picker_products() -> dict[str, list[Product]]:
    """Get products without barcodes, grouped by category for picker."""
    with get_db() as conn:
        return database_products.get_picker_products(conn)


def add_product(product: Product) -> None:
    """Add a new product."""
    with get_db() as conn:
        database_products.add_product(conn, product)
        conn.commit()


def update_product(product: Product) -> None:
    """Update an existing product."""
    with get_db() as conn:
        database_products.update_product(conn, product)
        conn.commit()


def update_product_admin_fields(
    barcode: str, name_de: str, price: float, active: bool
) -> None:
    """Update parent-facing product fields."""
    with get_db() as conn:
        database_products.update_product_admin_fields(
            conn, barcode, name_de, price, active
        )
        conn.commit()


def delete_product(barcode: str) -> None:
    """Delete a product."""
    with get_db() as conn:
        database_products.delete_product(conn, barcode)
        conn.commit()


# --- User CRUD ---


def get_user(card_id: str, include_inactive: bool = False) -> User | None:
    """Get a user by card ID."""
    with get_db() as conn:
        return database_users.get_user(conn, card_id, include_inactive)


def get_all_users(include_inactive: bool = False) -> list[User]:
    """Get all users."""
    with get_db() as conn:
        return database_users.get_all_users(conn, include_inactive)


def add_user(user: User) -> None:
    """Add a new user."""
    with get_db() as conn:
        database_users.add_user(conn, user)
        conn.commit()


def update_user_balance(
    card_id: str, new_balance: float, note: str | None = None
) -> None:
    """Update a user's balance and record the manual adjustment."""
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            database_balance_adjustments.update_user_balance(
                conn, card_id, new_balance, note
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def update_user_admin_fields(
    card_id: str, name: str, difficulty: int, active: bool
) -> None:
    """Update parent-facing user fields."""
    with get_db() as conn:
        database_users.update_user_admin_fields(conn, card_id, name, difficulty, active)
        conn.commit()


def get_recent_balance_adjustments(limit: int = 20) -> list[BalanceAdjustment]:
    """Get recent manual admin balance changes."""
    with get_db() as conn:
        return database_balance_adjustments.get_recent_balance_adjustments(conn, limit)


def delete_user(card_id: str) -> None:
    """Delete a user."""
    with get_db() as conn:
        database_users.delete_user(conn, card_id)
        conn.commit()


# --- Recipe CRUD ---


def get_recipe(barcode: str) -> Recipe | None:
    """Get an active recipe by barcode."""
    with get_db() as conn:
        return database_recipes.get_recipe(conn, barcode)


def get_all_recipes(include_inactive: bool = False) -> list[Recipe]:
    """Get all recipes."""
    with get_db() as conn:
        return database_recipes.get_all_recipes(conn, include_inactive)


def add_recipe(recipe: Recipe) -> None:
    """Add a new recipe."""
    with get_db() as conn:
        database_recipes.add_recipe(conn, recipe)
        conn.commit()


def update_recipe_admin_fields(barcode: str, name: str, active: bool) -> None:
    """Update parent-facing recipe fields."""
    with get_db() as conn:
        database_recipes.update_recipe_admin_fields(conn, barcode, name, active)
        conn.commit()


def delete_recipe(barcode: str) -> None:
    """Delete a recipe and its ingredients."""
    with get_db() as conn:
        database_recipes.delete_recipe(conn, barcode)
        conn.commit()


# --- Recipe Ingredients ---


def get_recipe_ingredients(recipe_barcode: str) -> list[tuple[Product, int]]:
    """Get all ingredients for a recipe with quantities."""
    with get_db() as conn:
        return database_recipes.get_recipe_ingredients(conn, recipe_barcode)


def add_recipe_ingredient(ingredient: RecipeIngredient) -> None:
    """Add an ingredient to a recipe."""
    with get_db() as conn:
        database_recipes.add_recipe_ingredient(conn, ingredient)
        conn.commit()


def clear_recipe_ingredients(recipe_barcode: str) -> None:
    """Remove all ingredients from a recipe."""
    with get_db() as conn:
        database_recipes.clear_recipe_ingredients(conn, recipe_barcode)
        conn.commit()


# --- Session Management ---


def start_session(user_card_id: str) -> int:
    """Start a new work session, return session ID."""
    with get_db() as conn:
        session_id = database_sessions.start_session(conn, user_card_id)
        conn.commit()
        return session_id


def end_session(session_id: int) -> None:
    """End a work session by setting ended_at."""
    with get_db() as conn:
        database_sessions.end_session(conn, session_id)
        conn.commit()


def get_session(session_id: int) -> Session | None:
    """Get a session by ID."""
    with get_db() as conn:
        return database_sessions.get_session(conn, session_id)


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
        database_earnings.add_earning(
            conn,
            session_id,
            user_card_id,
            source,
            amount,
            description,
        )
        conn.commit()


def get_today_earnings(user_card_id: str) -> list[Earning]:
    """Get all earnings for a user from today."""
    with get_db() as conn:
        return database_earnings.get_today_earnings(conn, user_card_id)


def get_session_earnings(session_id: int) -> list[Earning]:
    """Get all earnings for a specific session."""
    with get_db() as conn:
        return database_earnings.get_session_earnings(conn, session_id)


def get_today_earnings_summary(user_card_id: str) -> dict[str, int]:
    """Get earnings summary grouped by source for today."""
    with get_db() as conn:
        return database_earnings.get_today_earnings_summary(conn, user_card_id)


# --- Transactions ---


def save_transaction(
    user_card_id: str,
    total: int,
    items: list[dict],
) -> int:
    """Save a purchase transaction, return transaction ID."""
    with get_db() as conn:
        transaction_id = database_transactions.save_transaction(
            conn,
            user_card_id,
            total,
            items,
        )
        conn.commit()
        return transaction_id


def process_checkout(
    card_id: str,
    total: int,
    items: list[dict],
) -> CheckoutResult:
    """Atomically process checkout: update balance + save transaction.

    Both operations happen in a single transaction - if either fails,
    neither change is committed.
    """
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            transaction_id, user = database_checkout.process_checkout(
                conn,
                card_id,
                total,
                items,
            )
            conn.commit()
            return CheckoutResult(
                transaction_id=transaction_id,
                user=user,
            )
        except Exception:
            conn.rollback()
            raise


def get_user_transactions(user_card_id: str, limit: int = 10) -> list[Transaction]:
    """Get recent transactions for a user."""
    with get_db() as conn:
        return database_transactions.get_user_transactions(conn, user_card_id, limit)
