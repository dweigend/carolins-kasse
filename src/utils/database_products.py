"""Product query helpers for the SQLite database."""

import sqlite3

from src.utils.database_models import (
    PRODUCT_COLUMNS,
    Product,
    ProductBarcodeAlias,
    ProductBarcodeConflictError,
)


def get_product(conn: sqlite3.Connection, barcode: str) -> Product | None:
    """Get an active product by canonical or packaging barcode."""
    row = conn.execute(
        f"SELECT {PRODUCT_COLUMNS} FROM products WHERE barcode = ? AND active = 1",
        (barcode,),
    ).fetchone()
    if row:
        return Product.from_row(row)

    row = conn.execute(
        """
        SELECT p.barcode, p.name, p.name_de, p.price, p.category,
               p.image_path, p.has_barcode, p.active
        FROM product_barcode_aliases AS aliases
        JOIN products AS p ON p.barcode = aliases.product_barcode
        WHERE aliases.alias_barcode = ? AND p.active = 1
        """,
        (barcode,),
    ).fetchone()
    return Product.from_row(row) if row else None


def get_product_barcode_aliases(
    conn: sqlite3.Connection, product_barcode: str | None = None
) -> list[ProductBarcodeAlias]:
    """Get packaging barcode aliases, optionally for one canonical product."""
    if product_barcode is None:
        rows = conn.execute(
            """
            SELECT alias_barcode, product_barcode
            FROM product_barcode_aliases
            ORDER BY product_barcode, alias_barcode
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT alias_barcode, product_barcode
            FROM product_barcode_aliases
            WHERE product_barcode = ?
            ORDER BY alias_barcode
            """,
            (product_barcode,),
        ).fetchall()
    return [ProductBarcodeAlias.from_row(row) for row in rows]


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
    alias_row = conn.execute(
        "SELECT product_barcode FROM product_barcode_aliases WHERE alias_barcode = ?",
        (product.barcode,),
    ).fetchone()
    if alias_row:
        raise ProductBarcodeConflictError(
            f"Barcode {product.barcode} is already assigned as a product alias"
        )

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


def add_product_barcode_alias(
    conn: sqlite3.Connection, alias: ProductBarcodeAlias
) -> None:
    """Add a packaging barcode alias without changing canonical product identity."""
    if not alias.alias_barcode:
        raise ValueError("Alias barcode must not be empty")

    canonical_row = conn.execute(
        "SELECT 1 FROM products WHERE barcode = ?", (alias.alias_barcode,)
    ).fetchone()
    if canonical_row:
        raise ProductBarcodeConflictError(
            f"Barcode {alias.alias_barcode} is already a canonical product barcode"
        )

    product_row = conn.execute(
        "SELECT 1 FROM products WHERE barcode = ?", (alias.product_barcode,)
    ).fetchone()
    if not product_row:
        raise ProductBarcodeConflictError(
            f"Canonical product {alias.product_barcode} does not exist"
        )

    existing_row = conn.execute(
        """
        SELECT product_barcode
        FROM product_barcode_aliases
        WHERE alias_barcode = ?
        """,
        (alias.alias_barcode,),
    ).fetchone()
    if existing_row:
        if existing_row[0] == alias.product_barcode:
            return
        raise ProductBarcodeConflictError(
            f"Barcode {alias.alias_barcode} is already assigned to {existing_row[0]}"
        )

    conn.execute(
        """
        INSERT INTO product_barcode_aliases (alias_barcode, product_barcode)
        VALUES (?, ?)
        """,
        (alias.alias_barcode, alias.product_barcode),
    )


def delete_product_barcode_alias(conn: sqlite3.Connection, alias_barcode: str) -> None:
    """Delete a packaging barcode alias."""
    conn.execute(
        "DELETE FROM product_barcode_aliases WHERE alias_barcode = ?",
        (alias_barcode,),
    )


def next_product_barcode(conn: sqlite3.Connection) -> str:
    """Return the first free internal EAN-13 product barcode."""
    from src.utils.barcodes import generate_product_barcode

    occupied_barcodes = {
        row[0]
        for row in conn.execute(
            """
            SELECT barcode FROM products
            UNION
            SELECT alias_barcode FROM product_barcode_aliases
            """
        ).fetchall()
    }
    number = 1
    while True:
        candidate = generate_product_barcode(number)
        if candidate not in occupied_barcodes:
            return candidate
        number += 1


def synchronize_products(
    conn: sqlite3.Connection,
    products: list[Product],
    aliases: list[ProductBarcodeAlias],
) -> None:
    """Upsert selected products and replace their aliases in one transaction."""
    unique_products = _validate_synchronized_products(products)
    unique_aliases = _validate_synchronized_aliases(aliases)

    duplicate_codes = unique_products.keys() & unique_aliases.keys()
    if duplicate_codes:
        duplicate_code = sorted(duplicate_codes)[0]
        raise ProductBarcodeConflictError(
            f"Barcode {duplicate_code} cannot be both a product and an alias"
        )

    for alias in unique_aliases.values():
        if alias.product_barcode in unique_products:
            continue
        if _get_canonical_product(conn, alias.product_barcode) is None:
            raise ProductBarcodeConflictError(
                f"Canonical product {alias.product_barcode} does not exist"
            )

    for product_barcode in unique_products:
        conn.execute(
            "DELETE FROM product_barcode_aliases WHERE product_barcode = ?",
            (product_barcode,),
        )

    for product in unique_products.values():
        existing = _get_canonical_product(conn, product.barcode)
        if existing is None:
            add_product(conn, product)
            continue
        update_product(conn, product)

    for alias in unique_aliases.values():
        add_product_barcode_alias(conn, alias)


def _get_canonical_product(conn: sqlite3.Connection, barcode: str) -> Product | None:
    row = conn.execute(
        f"SELECT {PRODUCT_COLUMNS} FROM products WHERE barcode = ?", (barcode,)
    ).fetchone()
    return Product.from_row(row) if row else None


def _validate_synchronized_products(products: list[Product]) -> dict[str, Product]:
    unique_products: dict[str, Product] = {}
    for product in products:
        existing = unique_products.get(product.barcode)
        if existing is not None and existing != product:
            raise ProductBarcodeConflictError(
                f"Product {product.barcode} occurs with conflicting values"
            )
        unique_products[product.barcode] = product
    return unique_products


def _validate_synchronized_aliases(
    aliases: list[ProductBarcodeAlias],
) -> dict[str, ProductBarcodeAlias]:
    unique_aliases: dict[str, ProductBarcodeAlias] = {}
    for alias in aliases:
        existing = unique_aliases.get(alias.alias_barcode)
        if existing is not None and existing != alias:
            raise ProductBarcodeConflictError(
                f"Alias {alias.alias_barcode} occurs with conflicting products"
            )
        unique_aliases[alias.alias_barcode] = alias
    return unique_aliases


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
