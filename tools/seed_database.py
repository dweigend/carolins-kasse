#!/usr/bin/env python3
"""Seed the database with initial data.

Usage:
    uv run python tools/seed_database.py

Creates data/products.db with:
- 26 products (from concept.md)
- 4 users (Carolin, Annelie, Gast, Admin)
- 5 recipes with ingredients
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.database import (
    DB_PATH,
    Product,
    Recipe,
    RecipeIngredient,
    User,
    add_product,
    add_recipe,
    add_recipe_ingredient,
    add_user,
    generate_product_barcode,
    generate_recipe_barcode,
    generate_user_barcode,
    init_database,
)


def seed_products() -> dict[str, str]:
    """Seed products and return name -> barcode mapping."""
    products_data = [
        # Kühlregal (has_barcode=True)
        ("milk", "Milch", 1.0, "kuehlregal", True),
        ("eggs", "Eier (6er)", 2.0, "kuehlregal", True),
        ("butter", "Butter", 1.0, "kuehlregal", True),
        ("cheese", "Käse", 2.0, "kuehlregal", True),
        ("sausage", "Wurst", 2.0, "kuehlregal", True),
        # Backzutaten (has_barcode=True)
        ("flour", "Mehl", 1.0, "backzutaten", True),
        ("sugar", "Zucker", 1.0, "backzutaten", True),
        # Frühstück/Vorrat (has_barcode=True)
        ("oatmeal", "Haferflocken", 1.0, "vorrat", True),
        ("pasta", "Nudeln", 1.0, "vorrat", True),
        ("tomatoes_canned", "Tomaten (Dose)", 1.0, "vorrat", True),
        # Getränke (has_barcode=True)
        ("lemonade", "Limonade", 2.0, "getraenke", True),
        ("juice", "Saft", 2.0, "getraenke", True),
        # Backwaren (has_barcode=False - Touch-Auswahl)
        ("bread", "Brot", 1.0, "backwaren", True),
        ("roll", "Brötchen", 0.5, "backwaren", False),
        ("croissant", "Croissant", 1.0, "backwaren", False),
        ("pretzel", "Brezel", 0.5, "backwaren", False),
        # Obst (has_barcode=False - Touch-Auswahl)
        ("banana", "Banane", 0.5, "obst", False),
        ("apple", "Apfel", 0.5, "obst", False),
        ("orange", "Orange", 0.5, "obst", False),
        ("cherries", "Kirschen", 1.0, "obst", False),
        ("grapes", "Trauben", 1.0, "obst", False),
        ("pear", "Birne", 0.5, "obst", False),
        # Gemüse (has_barcode=False - Touch-Auswahl)
        ("tomato", "Tomate", 0.5, "gemuese", False),
        ("cucumber", "Gurke", 0.5, "gemuese", False),
        ("carrot", "Karotte", 0.5, "gemuese", False),
        ("pepper", "Paprika", 1.0, "gemuese", False),
        ("lettuce", "Salat", 1.0, "gemuese", False),
        ("onion", "Zwiebel", 0.5, "gemuese", False),
    ]

    barcode_map = {}
    for i, (name, name_de, price, category, has_barcode) in enumerate(
        products_data, start=1
    ):
        barcode = generate_product_barcode(i)
        barcode_map[name] = barcode

        product = Product(
            barcode=barcode,
            name=name,
            name_de=name_de,
            price=price,
            category=category,
            image_path=f"assets/products/{name}.png",
            has_barcode=has_barcode,
        )
        add_product(product)
        print(f"  ✓ {name_de} ({barcode})")

    return barcode_map


def seed_users() -> None:
    """Seed users."""
    users_data = [
        ("Carolin", 10.0, "#0066CC", 1, False),  # Blau
        ("Annelie", 10.0, "#CC3333", 3, False),  # Rot
        ("Gast", 10.0, "#888888", 1, False),  # Grau
        ("Admin", 100.0, "#FFD700", 3, True),  # Gold
    ]

    for i, (name, balance, color, difficulty, is_admin) in enumerate(
        users_data, start=1
    ):
        card_id = generate_user_barcode(i)
        user = User(
            card_id=card_id,
            name=name,
            balance=balance,
            color=color,
            difficulty=difficulty,
            is_admin=is_admin,
        )
        add_user(user)
        print(f"  ✓ {name} ({card_id})")


def seed_recipes(product_barcodes: dict[str, str]) -> None:
    """Seed recipes with ingredients."""
    recipes_data = [
        (
            "Pfannkuchen",
            [("milk", 1), ("eggs", 1), ("flour", 1), ("sugar", 1)],
        ),
        (
            "Nudeln mit Tomatensauce",
            [("pasta", 1), ("tomatoes_canned", 1), ("cheese", 1)],
        ),
        (
            "Nudeln mit Käsesauce",
            [("pasta", 1), ("cheese", 1), ("milk", 1), ("butter", 1)],
        ),
        (
            "Haferflocken mit Kirschen",
            [("oatmeal", 1), ("cherries", 1), ("milk", 1)],
        ),
        (
            "Kuchen",
            [("flour", 1), ("eggs", 1), ("sugar", 1), ("butter", 1), ("milk", 1)],
        ),
    ]

    for i, (name, ingredients) in enumerate(recipes_data, start=1):
        barcode = generate_recipe_barcode(i)
        # Convert German name to safe filename
        safe_name = (
            name.lower()
            .replace(" ", "_")
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
        )

        recipe = Recipe(
            barcode=barcode,
            name=name,
            image_path=f"assets/recipes/{safe_name}.png",
        )
        add_recipe(recipe)
        print(f"  ✓ {name} ({barcode})")

        # Add ingredients
        for product_name, quantity in ingredients:
            ingredient = RecipeIngredient(
                recipe_barcode=barcode,
                product_barcode=product_barcodes[product_name],
                quantity=quantity,
            )
            add_recipe_ingredient(ingredient)


def main() -> None:
    """Main entry point."""
    print("🗄️  Initialisiere Datenbank...")

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"  ✓ Alte Datenbank gelöscht: {DB_PATH}")

    # Initialize schema
    init_database()
    print(f"  ✓ Schema erstellt: {DB_PATH}")

    print("\n📦 Füge Produkte hinzu...")
    product_barcodes = seed_products()

    print("\n👤 Füge Benutzer hinzu...")
    seed_users()

    print("\n🍳 Füge Rezepte hinzu...")
    seed_recipes(product_barcodes)

    print("\n✅ Datenbank erfolgreich befüllt!")
    print(f"   Pfad: {DB_PATH}")


if __name__ == "__main__":
    main()
