#!/usr/bin/env python3
"""Seed the database with initial data.

Usage:
    uv run python tools/seed_database.py

Creates data/products.db with:
- 32 products
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
    init_database,
)
from src.utils.barcodes import (
    generate_product_barcode,
    generate_recipe_barcode,
    generate_user_barcode,
)


def seed_products() -> dict[str, str]:
    """Seed products and return name -> barcode mapping.

    All prices are whole numbers (integers) for easier mental math for kids.
    """
    products_data = [
        # Kühlregal (has_barcode=True)
        ("milk", "Milch", 1, "kuehlregal", True),
        ("eggs", "Eier (6er)", 2, "kuehlregal", True),
        ("butter", "Butter", 1, "kuehlregal", True),
        ("cheese", "Käse", 2, "kuehlregal", True),
        ("sausage", "Wurst", 2, "kuehlregal", True),
        # Backzutaten (has_barcode=True)
        ("flour", "Mehl", 1, "backzutaten", True),
        ("sugar", "Zucker", 1, "backzutaten", True),
        # Frühstück/Vorrat (has_barcode=True)
        ("oatmeal", "Haferflocken", 1, "vorrat", True),
        ("pasta", "Nudeln", 1, "vorrat", True),
        ("tomatoes_canned", "Tomaten (Dose)", 1, "vorrat", True),
        # Getränke (has_barcode=True)
        ("lemonade", "Limonade", 2, "getraenke", True),
        ("juice", "Saft", 2, "getraenke", True),
        # Backwaren (has_barcode=False - Touch-Auswahl)
        ("bread", "Brot", 1, "backwaren", True),
        ("roll", "Brötchen", 1, "backwaren", False),
        ("croissant", "Croissant", 1, "backwaren", False),
        ("pretzel", "Brezel", 1, "backwaren", False),
        ("muffin", "Muffin", 1, "backwaren", False),
        ("cinnamon_roll", "Zimtschnecke", 1, "backwaren", False),
        # Obst (has_barcode=False - Touch-Auswahl)
        ("banana", "Banane", 1, "obst", False),
        ("apple", "Apfel", 1, "obst", False),
        ("orange", "Orange", 1, "obst", False),
        ("cherries", "Kirschen", 1, "obst", False),
        ("grapes", "Trauben", 1, "obst", False),
        ("pear", "Birne", 1, "obst", False),
        ("peach", "Pfirsich", 1, "obst", False),
        # Gemüse (has_barcode=False - Touch-Auswahl)
        ("tomato", "Tomate", 1, "gemuese", False),
        ("cucumber", "Gurke", 1, "gemuese", False),
        ("carrot", "Karotte", 1, "gemuese", False),
        ("pepper", "Paprika", 1, "gemuese", False),
        ("lettuce", "Salat", 1, "gemuese", False),
        ("onion", "Zwiebel", 1, "gemuese", False),
        ("leek", "Lauch", 1, "gemuese", False),
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
            image_path=name,
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
    """Seed recipes with ingredients.

    Image files are stored in assets/L/recipes/ with English names.
    """
    # (name, image_file, ingredients)
    recipes_data = [
        (
            "Pfannkuchen",
            "recipe_pancakes",
            [("milk", 1), ("eggs", 1), ("flour", 1), ("sugar", 1)],
        ),
        (
            "Nudeln mit Tomatensauce",
            "recipe_tomato_pasta",
            [("pasta", 1), ("tomatoes_canned", 1), ("cheese", 1)],
        ),
        (
            "Nudeln mit Käsesauce",
            "recipe_cheese_pasta",
            [("pasta", 1), ("cheese", 1), ("milk", 1), ("butter", 1)],
        ),
        (
            "Haferflocken mit Kirschen",
            "recipe_oatmeal_cherries",
            [("oatmeal", 1), ("cherries", 1), ("milk", 1)],
        ),
        (
            "Rührei",
            "recipe_scrambled_eggs",
            [("eggs", 1), ("butter", 1), ("milk", 1)],
        ),
    ]

    for i, (name, image_file, ingredients) in enumerate(recipes_data, start=1):
        barcode = generate_recipe_barcode(i)

        recipe = Recipe(
            barcode=barcode,
            name=name,
            image_path=image_file,  # Just the filename, no path prefix
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
