"""Database module for Carolin's Kasse.

SQLite database with tables for products, users, recipes, and recipe ingredients.
Uses EAN-13 barcodes with prefixes:
- 100: Products
- 200: Users
- 300: Recipes
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Self


# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "products.db"


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


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_database() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Products table
    cursor.execute("""
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
    cursor.execute("""
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image_path TEXT
        )
    """)

    # Recipe ingredients (junction table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_barcode TEXT NOT NULL,
            product_barcode TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (recipe_barcode, product_barcode),
            FOREIGN KEY (recipe_barcode) REFERENCES recipes(barcode),
            FOREIGN KEY (product_barcode) REFERENCES products(barcode)
        )
    """)

    conn.commit()
    conn.close()


# --- Product CRUD ---


def get_product(barcode: str) -> Product | None:
    """Get a product by barcode."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
    row = cursor.fetchone()
    conn.close()
    return Product.from_row(row) if row else None


def get_all_products() -> list[Product]:
    """Get all products."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    return [Product.from_row(row) for row in rows]


def get_products_by_category(category: str) -> list[Product]:
    """Get products by category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [Product.from_row(row) for row in rows]


def add_product(product: Product) -> None:
    """Add a new product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
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
    conn.close()


def update_product(product: Product) -> None:
    """Update an existing product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
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
    conn.close()


def delete_product(barcode: str) -> None:
    """Delete a product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
    conn.commit()
    conn.close()


# --- User CRUD ---


def get_user(card_id: str) -> User | None:
    """Get a user by card ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE card_id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()
    return User.from_row(row) if row else None


def get_all_users() -> list[User]:
    """Get all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [User.from_row(row) for row in rows]


def add_user(user: User) -> None:
    """Add a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
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
    conn.close()


def update_user_balance(card_id: str, new_balance: float) -> None:
    """Update a user's balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = ? WHERE card_id = ?", (new_balance, card_id)
    )
    conn.commit()
    conn.close()


def delete_user(card_id: str) -> None:
    """Delete a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE card_id = ?", (card_id,))
    conn.commit()
    conn.close()


# --- Recipe CRUD ---


def get_recipe(barcode: str) -> Recipe | None:
    """Get a recipe by barcode."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE barcode = ?", (barcode,))
    row = cursor.fetchone()
    conn.close()
    return Recipe.from_row(row) if row else None


def get_all_recipes() -> list[Recipe]:
    """Get all recipes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [Recipe.from_row(row) for row in rows]


def add_recipe(recipe: Recipe) -> None:
    """Add a new recipe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO recipes (barcode, name, image_path)
        VALUES (?, ?, ?)
    """,
        (recipe.barcode, recipe.name, recipe.image_path),
    )
    conn.commit()
    conn.close()


def delete_recipe(barcode: str) -> None:
    """Delete a recipe and its ingredients."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (barcode,)
    )
    cursor.execute("DELETE FROM recipes WHERE barcode = ?", (barcode,))
    conn.commit()
    conn.close()


# --- Recipe Ingredients ---


def get_recipe_ingredients(recipe_barcode: str) -> list[tuple[Product, int]]:
    """Get all ingredients for a recipe with quantities."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, ri.quantity
        FROM recipe_ingredients ri
        JOIN products p ON ri.product_barcode = p.barcode
        WHERE ri.recipe_barcode = ?
        ORDER BY p.name
    """,
        (recipe_barcode,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [(Product.from_row(row[:7]), row[7]) for row in rows]


def add_recipe_ingredient(ingredient: RecipeIngredient) -> None:
    """Add an ingredient to a recipe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO recipe_ingredients (recipe_barcode, product_barcode, quantity)
        VALUES (?, ?, ?)
    """,
        (ingredient.recipe_barcode, ingredient.product_barcode, ingredient.quantity),
    )
    conn.commit()
    conn.close()


def clear_recipe_ingredients(recipe_barcode: str) -> None:
    """Remove all ingredients from a recipe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (recipe_barcode,)
    )
    conn.commit()
    conn.close()


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
