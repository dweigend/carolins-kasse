"""FastAPI admin backend for viewing products, users, and recipes with barcodes.

Usage:
    uv run uvicorn src.admin.server:app --reload --port 8080

Then open: http://localhost:8080/products
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.utils.database import (
    get_all_products,
    get_all_recipes,
    get_all_users,
    get_recipe_ingredients,
)
from src.utils.barcodes import BARCODE_DIR, barcode_url

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
# FastAPI app
app = FastAPI(title="Carolin's Kasse - Admin")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files for barcodes
app.mount("/barcodes", StaticFiles(directory=BARCODE_DIR), name="barcodes")


@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to products page."""
    return RedirectResponse(url="/products")


@app.get("/products")
async def products_page(request: Request):
    """Show all products with barcodes."""
    products = get_all_products()

    # Add barcode image path for products with barcodes
    product_data = []
    for p in products:
        barcode_path = None
        if p.has_barcode:
            barcode_path = barcode_url("products", p.name_de, p.barcode)

        product_data.append(
            {
                "barcode": p.barcode,
                "name": p.name,
                "name_de": p.name_de,
                "price": p.price,
                "category": p.category,
                "has_barcode": p.has_barcode,
                "barcode_path": barcode_path,
            }
        )

    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": product_data, "active": "products"},
    )


@app.get("/users")
async def users_page(request: Request):
    """Show all users with card barcodes."""
    users = get_all_users()

    user_data = []
    for u in users:
        user_data.append(
            {
                "card_id": u.card_id,
                "name": u.name,
                "balance": u.balance,
                "color": u.color,
                "difficulty": u.difficulty,
                "is_admin": u.is_admin,
                "barcode_path": barcode_url("users", u.name, u.card_id),
            }
        )

    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": user_data, "active": "users"},
    )


@app.get("/recipes")
async def recipes_page(request: Request):
    """Show all recipes with barcodes and ingredients."""
    recipes = get_all_recipes()

    recipe_data = []
    for r in recipes:
        # Get ingredients
        ingredients = get_recipe_ingredients(r.barcode)
        ingredient_list = [
            {"name": prod.name_de, "quantity": qty} for prod, qty in ingredients
        ]

        recipe_data.append(
            {
                "barcode": r.barcode,
                "name": r.name,
                "ingredients": ingredient_list,
                "barcode_path": barcode_url("recipes", r.name, r.barcode),
            }
        )

    return templates.TemplateResponse(
        "recipes.html",
        {"request": request, "recipes": recipe_data, "active": "recipes"},
    )
