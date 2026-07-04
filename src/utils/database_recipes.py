"""Recipe query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import (
    PRODUCT_COLUMNS,
    RECIPE_COLUMNS,
    Product,
    Recipe,
    RecipeIngredient,
)


def get_recipe(conn: sqlite3.Connection, barcode: str) -> Recipe | None:
    """Get an active recipe by barcode."""
    row = conn.execute(
        f"SELECT {RECIPE_COLUMNS} FROM recipes WHERE barcode = ? AND active = 1",
        (barcode,),
    ).fetchone()
    return Recipe.from_row(row) if row else None


def get_all_recipes(
    conn: sqlite3.Connection, include_inactive: bool = False
) -> list[Recipe]:
    """Get all recipes."""
    where_clause = "" if include_inactive else "WHERE active = 1"
    rows = conn.execute(
        f"""
        SELECT {RECIPE_COLUMNS}
        FROM recipes
        {where_clause}
        ORDER BY name
        """
    ).fetchall()
    return [Recipe.from_row(row) for row in rows]


def add_recipe(conn: sqlite3.Connection, recipe: Recipe) -> None:
    """Add a new recipe."""
    conn.execute(
        """
        INSERT INTO recipes (barcode, name, image_path, active)
        VALUES (?, ?, ?, ?)
        """,
        (recipe.barcode, recipe.name, recipe.image_path, recipe.active),
    )


def update_recipe_admin_fields(
    conn: sqlite3.Connection, barcode: str, name: str, active: bool
) -> None:
    """Update parent-facing recipe fields."""
    conn.execute(
        """
        UPDATE recipes
        SET name = ?, active = ?
        WHERE barcode = ?
        """,
        (name, active, barcode),
    )


def delete_recipe(conn: sqlite3.Connection, barcode: str) -> None:
    """Delete a recipe and its ingredients."""
    conn.execute("DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (barcode,))
    conn.execute("DELETE FROM recipes WHERE barcode = ?", (barcode,))


def get_recipe_ingredients(
    conn: sqlite3.Connection, recipe_barcode: str
) -> list[tuple[Product, int]]:
    """Get all ingredients for a recipe with quantities."""
    rows = conn.execute(
        f"""
        SELECT {PRODUCT_COLUMNS}, ri.quantity
        FROM recipe_ingredients ri
        JOIN products p ON ri.product_barcode = p.barcode
        WHERE ri.recipe_barcode = ?
        ORDER BY p.name
        """,
        (recipe_barcode,),
    ).fetchall()
    return [(Product.from_row(row[:8]), row[8]) for row in rows]


def add_recipe_ingredient(
    conn: sqlite3.Connection, ingredient: RecipeIngredient
) -> None:
    """Add an ingredient to a recipe."""
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


def clear_recipe_ingredients(conn: sqlite3.Connection, recipe_barcode: str) -> None:
    """Remove all ingredients from a recipe."""
    conn.execute(
        "DELETE FROM recipe_ingredients WHERE recipe_barcode = ?", (recipe_barcode,)
    )
