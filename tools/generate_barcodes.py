#!/usr/bin/env python3
"""Generate EAN-13 barcodes for all products, users, and recipes.

Usage:
    uv run python tools/generate_barcodes.py

Creates:
    data/barcodes/products/{name}_{barcode}.svg
    data/barcodes/users/{name}_{barcode}.svg
    data/barcodes/recipes/{name}_{barcode}.svg
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.barcodes import BARCODE_DIR, barcode_path, write_ean13_svg
from src.utils.database import get_all_products, get_all_recipes, get_all_users


def remove_stale_barcodes(directory: Path, expected_paths: set[Path]) -> int:
    """Remove generated SVG files that are no longer expected."""
    stale_count = 0
    for svg_path in directory.glob("*.svg"):
        if svg_path in expected_paths:
            continue
        svg_path.unlink()
        print(f"  - Entfernt: {svg_path.name}")
        stale_count += 1
    return stale_count


def generate_product_barcodes() -> int:
    """Generate barcodes for all products with has_barcode=True."""
    count = 0
    expected_paths: set[Path] = set()

    products = get_all_products()
    for product in products:
        if not product.has_barcode:
            continue

        output_path = barcode_path("products", product.name_de, product.barcode)
        expected_paths.add(output_path)
        write_ean13_svg(product.barcode, output_path)
        print(f"  ✓ {product.name_de}: {product.barcode}")
        count += 1

    remove_stale_barcodes(BARCODE_DIR / "products", expected_paths)
    return count


def generate_user_barcodes() -> int:
    """Generate barcodes for all users."""
    count = 0
    expected_paths: set[Path] = set()

    users = get_all_users()
    for user in users:
        output_path = barcode_path("users", user.name, user.card_id)
        expected_paths.add(output_path)
        write_ean13_svg(user.card_id, output_path)
        print(f"  ✓ {user.name}: {user.card_id}")
        count += 1

    remove_stale_barcodes(BARCODE_DIR / "users", expected_paths)
    return count


def generate_recipe_barcodes() -> int:
    """Generate barcodes for all recipes."""
    count = 0
    expected_paths: set[Path] = set()

    recipes = get_all_recipes()
    for recipe in recipes:
        output_path = barcode_path("recipes", recipe.name, recipe.barcode)
        expected_paths.add(output_path)
        write_ean13_svg(recipe.barcode, output_path)
        print(f"  ✓ {recipe.name}: {recipe.barcode}")
        count += 1

    remove_stale_barcodes(BARCODE_DIR / "recipes", expected_paths)
    return count


def main() -> None:
    """Generate all barcodes."""
    print("📊 Generiere Barcodes...\n")

    print("📦 Produkte:")
    product_count = generate_product_barcodes()

    print("\n👤 Benutzer:")
    user_count = generate_user_barcodes()

    print("\n🍳 Rezepte:")
    recipe_count = generate_recipe_barcodes()

    total = product_count + user_count + recipe_count
    print(f"\n✅ {total} Barcodes generiert!")
    print(f"   Pfad: {BARCODE_DIR}")


if __name__ == "__main__":
    main()
