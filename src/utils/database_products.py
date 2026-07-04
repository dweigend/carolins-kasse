"""Product query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import PRODUCT_COLUMNS, Product


def get_product(conn: sqlite3.Connection, barcode: str) -> Product | None:
    """Get an active product by barcode."""
    row = conn.execute(
        f"SELECT {PRODUCT_COLUMNS} FROM products WHERE barcode = ? AND active = 1",
        (barcode,),
    ).fetchone()
    return Product.from_row(row) if row else None


def get_all_products(
    conn: sqlite3.Connection, include_inactive: bool = False
) -> list[Product]:
    """Get all products."""
    where_clause = "" if include_inactive else "WHERE active = 1"
    rows = conn.execute(
        f"""
        SELECT {PRODUCT_COLUMNS}
        FROM products
        {where_clause}
        ORDER BY category, name
        """
    ).fetchall()
    return [Product.from_row(row) for row in rows]


def get_products_by_category(conn: sqlite3.Connection, category: str) -> list[Product]:
    """Get active products by category."""
    rows = conn.execute(
        f"""
        SELECT {PRODUCT_COLUMNS}
        FROM products
        WHERE category = ? AND active = 1
        ORDER BY name
        """,
        (category,),
    ).fetchall()
    return [Product.from_row(row) for row in rows]


def get_picker_products(conn: sqlite3.Connection) -> dict[str, list[Product]]:
    """Get products without barcodes, grouped by category for picker."""
    rows = conn.execute(
        f"""
        SELECT {PRODUCT_COLUMNS}
        FROM products
        WHERE has_barcode = 0 AND active = 1
        ORDER BY category, name_de
        """
    ).fetchall()

    products = [Product.from_row(row) for row in rows]
    grouped: dict[str, list[Product]] = {}
    for product in products:
        if product.category not in grouped:
            grouped[product.category] = []
        grouped[product.category].append(product)
    return grouped


def add_product(conn: sqlite3.Connection, product: Product) -> None:
    """Add a new product."""
    conn.execute(
        """
        INSERT INTO products (
            barcode, name, name_de, price, category, image_path, has_barcode, active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product.barcode,
            product.name,
            product.name_de,
            product.price,
            product.category,
            product.image_path,
            product.has_barcode,
            product.active,
        ),
    )


def update_product(conn: sqlite3.Connection, product: Product) -> None:
    """Update an existing product."""
    conn.execute(
        """
        UPDATE products
        SET name = ?, name_de = ?, price = ?, category = ?, image_path = ?,
            has_barcode = ?, active = ?
        WHERE barcode = ?
        """,
        (
            product.name,
            product.name_de,
            product.price,
            product.category,
            product.image_path,
            product.has_barcode,
            product.active,
            product.barcode,
        ),
    )


def update_product_admin_fields(
    conn: sqlite3.Connection, barcode: str, name_de: str, price: float, active: bool
) -> None:
    """Update parent-facing product fields."""
    conn.execute(
        """
        UPDATE products
        SET name_de = ?, price = ?, active = ?
        WHERE barcode = ?
        """,
        (name_de, price, active, barcode),
    )


def delete_product(conn: sqlite3.Connection, barcode: str) -> None:
    """Delete a product."""
    conn.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
