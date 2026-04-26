"""FastAPI admin backend for viewing products, users, and recipes with barcodes.

Usage:
    uv run uvicorn src.admin.server:app --reload --port 8080

Then open:
    http://localhost:8080/products

For remote admin on the home network:
    uv run uvicorn src.admin.server:app --host 0.0.0.0 --port 8080
"""

from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.admin.printables import PRINT_DIR, generate_all_printables, printable_files
from src.utils.database import (
    get_all_products,
    get_all_recipes,
    get_all_users,
    get_recent_balance_adjustments,
    get_recipe_ingredients,
    get_user,
    init_database,
    update_product_admin_fields,
    update_recipe_admin_fields,
    update_user_admin_fields,
    update_user_balance,
)
from src.utils.barcodes import BARCODE_DIR, barcode_path, barcode_url, write_ean13_svg

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
# FastAPI app
app = FastAPI(title="Carolin's Kasse - Admin")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
PRINT_DIR.mkdir(parents=True, exist_ok=True)
init_database()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/barcodes", StaticFiles(directory=BARCODE_DIR), name="barcodes")
app.mount("/print", StaticFiles(directory=PRINT_DIR), name="print")


@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to products page."""
    return RedirectResponse(url="/products")


@app.get("/products")
async def products_page(request: Request):
    """Show all products with barcodes."""
    products = get_all_products(include_inactive=True)

    # Add barcode image path for products with barcodes
    product_data = []
    for p in products:
        barcode_path = None
        if p.has_barcode:
            barcode_path = _ensure_barcode_url("products", p.name_de, p.barcode)

        product_data.append(
            {
                "barcode": p.barcode,
                "name": p.name,
                "name_de": p.name_de,
                "price": p.price,
                "category": p.category,
                "has_barcode": p.has_barcode,
                "active": p.active,
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
    users = get_all_users(include_inactive=True)

    user_data = []
    for u in users:
        user_data.append(
            {
                "card_id": u.card_id,
                "name": u.name,
                "balance": u.balance,
                "color": u.color,
                "color_class": _color_class(u.color),
                "difficulty": u.difficulty,
                "is_admin": u.is_admin,
                "active": u.active,
                "barcode_path": _ensure_barcode_url("users", u.name, u.card_id),
            }
        )

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": user_data,
            "adjustments": get_recent_balance_adjustments(),
            "active": "users",
        },
    )


@app.get("/recipes")
async def recipes_page(request: Request):
    """Show all recipes with barcodes and ingredients."""
    recipes = get_all_recipes(include_inactive=True)

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
                "active": r.active,
                "ingredients": ingredient_list,
                "barcode_path": _ensure_barcode_url("recipes", r.name, r.barcode),
            }
        )

    return templates.TemplateResponse(
        "recipes.html",
        {"request": request, "recipes": recipe_data, "active": "recipes"},
    )


@app.get("/printables")
async def printables_page(request: Request):
    """Show printable PDF links."""
    return templates.TemplateResponse(
        "printables.html",
        {
            "request": request,
            "files": printable_files(),
            "active": "printables",
        },
    )


@app.post("/printables/generate")
async def generate_printables():
    """Generate printable PDFs and return to the print page."""
    generate_all_printables()
    return RedirectResponse(url="/printables", status_code=303)


@app.post("/users/{card_id}/balance/set")
async def set_user_balance(card_id: str, request: Request):
    """Set a user's balance from the admin page."""
    form = await _parse_form(request)
    balance = _parse_float(form.get("balance"), default=0.0)
    note = _clean_note(form.get("note"))
    update_user_balance(card_id, max(0.0, balance), note)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/users/{card_id}/balance/adjust")
async def adjust_user_balance(card_id: str, request: Request):
    """Adjust a user's balance by a fixed delta."""
    form = await _parse_form(request)
    delta = _parse_float(form.get("delta"), default=0.0)
    note = _clean_note(form.get("note"))
    user = get_user(card_id, include_inactive=True)
    if user:
        update_user_balance(card_id, max(0.0, user.balance + delta), note)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/users/{card_id}/settings")
async def update_user_settings(card_id: str, request: Request):
    """Update parent-facing user fields."""
    form = await _parse_form(request)
    name = form.get("name", "").strip()
    difficulty = _parse_int(form.get("difficulty"), default=1)
    active = form.get("active") == "on"
    if name:
        update_user_admin_fields(card_id, name, max(1, min(difficulty, 3)), active)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/products/{barcode}/settings")
async def update_product_settings(barcode: str, request: Request):
    """Update parent-facing product fields."""
    form = await _parse_form(request)
    name_de = form.get("name_de", "").strip()
    price = _parse_float(form.get("price"), default=1.0)
    active = form.get("active") == "on"
    if name_de:
        update_product_admin_fields(barcode, name_de, max(0.0, price), active)
    return RedirectResponse(url="/products", status_code=303)


@app.post("/recipes/{barcode}/settings")
async def update_recipe_settings(barcode: str, request: Request):
    """Update parent-facing recipe fields."""
    form = await _parse_form(request)
    name = form.get("name", "").strip()
    active = form.get("active") == "on"
    if name:
        update_recipe_admin_fields(barcode, name, active)
    return RedirectResponse(url="/recipes", status_code=303)


async def _parse_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode()
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return default


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _clean_note(value: str | None) -> str | None:
    if not value:
        return None
    note = value.strip()
    return note or None


def _color_class(color: str | None) -> str:
    color_map = {
        "#0066CC": "color-blue",
        "#CC3333": "color-red",
        "#888888": "color-gray",
        "#FFD700": "color-gold",
    }
    return color_map.get(color or "", "color-orange")


def _ensure_barcode_url(kind, label: str, code: str) -> str:
    path = barcode_path(kind, label, code)
    if not path.exists():
        write_ean13_svg(code, path)
    return barcode_url(kind, label, code)
