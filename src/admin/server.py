"""FastAPI admin backend for viewing products, users, and recipes with barcodes.

Usage:
    uv run uvicorn src.admin.server:app --reload --port 8080

Then open:
    http://localhost:8080/products

For remote admin on the home network:
    uv run uvicorn src.admin.server:app --host 0.0.0.0 --port 8080
"""

import ipaddress
import os
from pathlib import Path
import re
from secrets import compare_digest, token_urlsafe
import sqlite3
from typing import Annotated
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.admin.catalog import (
    ASSET_KEY_PATTERN,
    CatalogAlias,
    CatalogPayload,
    CatalogProduct,
    CatalogSyncClientError,
    CatalogSyncResult,
    InventorySyncRequest,
    send_catalog,
)
from src.admin.printables import PRINT_DIR, generate_all_printables, printable_files
from src.utils.database import (
    Product,
    ProductBarcodeAlias,
    add_product,
    add_product_barcode_alias,
    delete_product_barcode_alias,
    get_all_products,
    get_product,
    get_product_barcode_aliases,
    get_all_recipes,
    get_all_users,
    get_recent_balance_adjustments,
    get_recipe_ingredients,
    get_user,
    init_database,
    next_product_barcode,
    synchronize_products,
    update_product_admin_fields,
    update_recipe_admin_fields,
    update_user_admin_fields,
    update_user_balance,
)
from src.utils.barcodes import BARCODE_DIR, barcode_path, barcode_url, write_ean13_svg
from src.utils.pi_system import (
    collect_debug_snapshot,
    run_admin_action,
    verify_admin_pin,
)

DEBUG_COOKIE = "carolins_admin_debug"
CSRF_COOKIE = "carolins_admin_csrf"
CSRF_FIELD = "csrf_token"
ADMIN_SESSION_MAX_AGE_SECONDS = 3600
CSRF_TOKEN_BYTES = 32
UNLOCK_REQUIRED_MESSAGE = "Bitte PIN eingeben"
CSRF_FAILED_MESSAGE = "Bitte Seite neu laden"
INVENTORY_MODE_ENV_VAR = "CAROLINS_KASSE_INVENTORY_MODE"
INVENTORY_MODE = os.environ.get(INVENTORY_MODE_ENV_VAR, "").lower() in {
    "1",
    "true",
    "yes",
}

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PRODUCT_ASSET_DIR = BASE_DIR.parent.parent / "assets" / "340er"
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
    return RedirectResponse(url="/inventory" if INVENTORY_MODE else "/products")


@app.get("/inventory")
async def inventory_page(request: Request, message: str | None = None):
    """Show the loopback-only inventory workspace."""
    _require_local_inventory(request)
    products = get_all_products(include_inactive=True)
    aliases = get_product_barcode_aliases()
    aliases_by_product: dict[str, list[ProductBarcodeAlias]] = {}
    for alias in aliases:
        aliases_by_product.setdefault(alias.product_barcode, []).append(alias)

    return _template_response(
        request,
        "inventory.html",
        {
            "active": "inventory",
            "products": products,
            "aliases_by_product": aliases_by_product,
            "missing_assets": {
                product.barcode
                for product in products
                if not _product_asset_exists(product)
            },
            "next_barcode": next_product_barcode(),
            "message": message,
        },
    )


@app.post("/inventory/products")
async def create_inventory_product(request: Request):
    """Create a product only from the explicit local inventory workspace."""
    form = await _require_inventory_form(request)
    name = form.get("name", "").strip()
    name_de = form.get("name_de", "").strip()
    category = form.get("category", "").strip()
    if not name or not name_de or not category:
        return _inventory_redirect("Bitte alle Produktfelder ausfüllen")
    if len(name_de) > 120 or len(category) > 120:
        return _inventory_redirect("Name oder Kategorie ist zu lang")
    if re.fullmatch(ASSET_KEY_PATTERN, name) is None:
        return _inventory_redirect("Bildname darf nur a-z, 0-9 und _ enthalten")

    product = Product(
        barcode=next_product_barcode(),
        name=name,
        name_de=name_de,
        price=max(0.0, _parse_float(form.get("price"), default=0.0)),
        category=category,
        image_path=name,
    )
    try:
        add_product(product)
    except (sqlite3.IntegrityError, ValueError):
        return _inventory_redirect("Produkt konnte nicht angelegt werden")
    return _inventory_redirect(f"{name_de} wurde angelegt")


@app.post("/inventory/aliases")
async def create_inventory_alias(request: Request):
    """Assign a scanned packaging barcode to a canonical product."""
    form = await _require_inventory_form(request)
    alias_barcode = form.get("alias_barcode", "").strip()
    product_barcode = form.get("product_barcode", "").strip()
    if not alias_barcode or not product_barcode:
        return _inventory_redirect("Barcode und Produkt werden benötigt")

    try:
        add_product_barcode_alias(
            ProductBarcodeAlias(
                alias_barcode=alias_barcode,
                product_barcode=product_barcode,
            )
        )
    except (sqlite3.IntegrityError, ValueError):
        return _inventory_redirect("Barcode ist bereits vergeben")
    return _inventory_redirect("Verpackungscode wurde zugeordnet")


@app.post("/inventory/aliases/delete")
async def remove_inventory_alias(request: Request):
    """Remove one packaging alias from the local inventory."""
    form = await _require_inventory_form(request)
    alias_barcode = form.get("alias_barcode", "").strip()
    if not alias_barcode:
        return _inventory_redirect("Verpackungscode fehlt")
    delete_product_barcode_alias(alias_barcode)
    return _inventory_redirect("Verpackungscode wurde entfernt")


@app.post("/inventory/sync", response_model=CatalogSyncResult)
async def synchronize_inventory_selection(
    request: Request,
    sync_request: InventorySyncRequest,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> CatalogSyncResult:
    """Send only selected local products and their aliases to the Pi."""
    _require_local_inventory(request)
    if not _valid_csrf_header(request, csrf_token):
        raise HTTPException(status_code=403, detail=CSRF_FAILED_MESSAGE)

    selected_barcodes = set(sync_request.product_barcodes)
    products = [
        CatalogProduct.from_database(product)
        for product in get_all_products(include_inactive=True)
        if product.barcode in selected_barcodes
    ]
    if len(products) != len(selected_barcodes):
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    missing_assets = [
        product.name_de
        for product in products
        if not _catalog_product_asset_exists(product)
    ]
    if missing_assets:
        missing_names = ", ".join(missing_assets)
        raise HTTPException(
            status_code=409,
            detail=f"Bild fehlt für: {missing_names}",
        )
    aliases = [
        CatalogAlias.from_database(alias)
        for alias in get_product_barcode_aliases()
        if alias.product_barcode in selected_barcodes
    ]
    try:
        return send_catalog(
            sync_request.destination_url,
            sync_request.pin,
            CatalogPayload(products=products, aliases=aliases),
        )
    except CatalogSyncClientError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/catalog", response_model=CatalogPayload)
async def catalog_api() -> CatalogPayload:
    """Return the product catalog and packaging aliases without modifying it."""
    return CatalogPayload(
        products=[
            CatalogProduct.from_database(product)
            for product in get_all_products(include_inactive=True)
        ],
        aliases=[
            CatalogAlias.from_database(alias) for alias in get_product_barcode_aliases()
        ],
    )


@app.get("/api/catalog/resolve/{barcode}", response_model=CatalogProduct)
async def resolve_catalog_barcode(barcode: str) -> CatalogProduct:
    """Resolve a canonical product barcode or packaging alias read-only."""
    product = get_product(barcode)
    if product is None:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    return CatalogProduct.from_database(product)


@app.post("/api/catalog/sync", response_model=CatalogSyncResult)
async def import_catalog_api(
    catalog: CatalogPayload,
    admin_pin: Annotated[str | None, Header(alias="X-Admin-PIN")] = None,
) -> CatalogSyncResult:
    """Atomically import selected catalog records after remote PIN validation."""
    if not verify_admin_pin(admin_pin):
        raise HTTPException(status_code=401, detail="Admin-PIN fehlt oder ist falsch")
    missing_assets = [
        product.name_de
        for product in catalog.products
        if not _catalog_product_asset_exists(product)
    ]
    if missing_assets:
        missing_names = ", ".join(missing_assets)
        raise HTTPException(status_code=409, detail=f"Bild fehlt für: {missing_names}")
    try:
        synchronize_products(
            [product.to_database() for product in catalog.products],
            [alias.to_database() for alias in catalog.aliases],
        )
    except (sqlite3.IntegrityError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return CatalogSyncResult(
        product_count=len(catalog.products),
        alias_count=len(catalog.aliases),
    )


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

    return _template_response(
        request,
        "products.html",
        {"products": product_data, "active": "products"},
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

    return _template_response(
        request,
        "users.html",
        {
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

    return _template_response(
        request,
        "recipes.html",
        {"recipes": recipe_data, "active": "recipes"},
    )


@app.get("/printables")
async def printables_page(request: Request):
    """Show printable PDF links."""
    return _template_response(
        request,
        "printables.html",
        {
            "files": printable_files(),
            "active": "printables",
        },
    )


@app.get("/debug")
async def debug_page(request: Request, message: str | None = None):
    """Show PIN-protected Raspberry Pi diagnostics and maintenance actions."""
    unlocked = verify_admin_pin(request.cookies.get(DEBUG_COOKIE))
    return _template_response(
        request,
        "debug.html",
        {
            "active": "debug",
            "unlocked": unlocked,
            "snapshot": collect_debug_snapshot() if unlocked else None,
            "message": message,
        },
    )


@app.post("/debug/unlock")
async def unlock_debug(request: Request):
    """Unlock the debug page with the locally generated admin PIN."""
    form = await _parse_form(request)
    if not _valid_csrf_form(request, form):
        return _security_redirect(CSRF_FAILED_MESSAGE)

    pin = form.get("pin")
    if not verify_admin_pin(pin):
        return RedirectResponse(
            url="/debug?message=PIN%20ist%20falsch",
            status_code=303,
        )

    response = RedirectResponse(url="/debug", status_code=303)
    response.set_cookie(
        DEBUG_COOKIE,
        pin or "",
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="strict",
    )
    _set_csrf_cookie(response, _new_csrf_token())
    return response


@app.post("/debug/action")
async def run_debug_action(request: Request):
    """Run a PIN-protected system action from the debug page."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    result = run_admin_action(form.get("action", ""))
    status = "gestartet" if result.ok else "fehlgeschlagen"
    message = f"Aktion {status}"
    if result.output:
        message = f"{message}: {result.output[:160]}"
    return RedirectResponse(url=f"/debug?message={quote(message)}", status_code=303)


@app.post("/printables/generate")
async def generate_printables(request: Request):
    """Generate printable PDFs and return to the print page."""
    _, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    generate_all_printables()
    return RedirectResponse(url="/printables", status_code=303)


@app.post("/users/{card_id}/balance/set")
async def set_user_balance(card_id: str, request: Request):
    """Set a user's balance from the admin page."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    balance = _parse_float(form.get("balance"), default=0.0)
    note = _clean_note(form.get("note"))
    update_user_balance(card_id, max(0.0, balance), note)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/users/{card_id}/balance/adjust")
async def adjust_user_balance(card_id: str, request: Request):
    """Adjust a user's balance by a fixed delta."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    delta = _parse_float(form.get("delta"), default=0.0)
    note = _clean_note(form.get("note"))
    user = get_user(card_id, include_inactive=True)
    if user:
        update_user_balance(card_id, max(0.0, user.balance + delta), note)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/users/{card_id}/settings")
async def update_user_settings(card_id: str, request: Request):
    """Update parent-facing user fields."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    name = form.get("name", "").strip()
    difficulty = _parse_int(form.get("difficulty"), default=1)
    active = form.get("active") == "on"
    if name:
        update_user_admin_fields(card_id, name, max(1, min(difficulty, 3)), active)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/products/{barcode}/settings")
async def update_product_settings(barcode: str, request: Request):
    """Update parent-facing product fields."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    name_de = form.get("name_de", "").strip()
    price = _parse_float(form.get("price"), default=1.0)
    active = form.get("active") == "on"
    if name_de:
        update_product_admin_fields(barcode, name_de, max(0.0, price), active)
    return RedirectResponse(url="/products", status_code=303)


@app.post("/recipes/{barcode}/settings")
async def update_recipe_settings(barcode: str, request: Request):
    """Update parent-facing recipe fields."""
    form, redirect = await _require_admin_form(request)
    if redirect:
        return redirect

    name = form.get("name", "").strip()
    active = form.get("active") == "on"
    if name:
        update_recipe_admin_fields(barcode, name, active)
    return RedirectResponse(url="/recipes", status_code=303)


async def _require_admin_form(
    request: Request,
) -> tuple[dict[str, str], RedirectResponse | None]:
    form = await _parse_form(request)
    if not verify_admin_pin(request.cookies.get(DEBUG_COOKIE)):
        return {}, _security_redirect(UNLOCK_REQUIRED_MESSAGE)
    if not _valid_csrf_form(request, form):
        return {}, _security_redirect(CSRF_FAILED_MESSAGE)
    return form, None


async def _require_inventory_form(request: Request) -> dict[str, str]:
    _require_local_inventory(request)
    form = await _parse_form(request)
    if not _valid_csrf_form(request, form):
        raise HTTPException(status_code=403, detail=CSRF_FAILED_MESSAGE)
    return form


def _require_local_inventory(request: Request) -> None:
    client_host = request.client.host if request.client else ""
    try:
        is_loopback = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        is_loopback = False
    if not INVENTORY_MODE or not is_loopback:
        raise HTTPException(status_code=404, detail="Nicht gefunden")


async def _parse_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode()
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def _template_response(request: Request, template_name: str, context: dict):
    csrf_token, refresh_cookie = _csrf_token_for_request(request)
    response = templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "csrf_token": csrf_token,
            "inventory_mode": INVENTORY_MODE,
            **context,
        },
    )
    if refresh_cookie:
        _set_csrf_cookie(response, csrf_token)
    return response


def _csrf_token_for_request(request: Request) -> tuple[str, bool]:
    token = request.cookies.get(CSRF_COOKIE)
    if _valid_csrf_token(token):
        assert token is not None
        return token, False
    return _new_csrf_token(), True


def _valid_csrf_form(request: Request, form: dict[str, str]) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    form_token = form.get(CSRF_FIELD)
    if not _valid_csrf_token(cookie_token) or not _valid_csrf_token(form_token):
        return False
    assert cookie_token is not None
    assert form_token is not None
    return compare_digest(cookie_token, form_token)


def _valid_csrf_header(request: Request, header_token: str | None) -> bool:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if not _valid_csrf_token(cookie_token) or not _valid_csrf_token(header_token):
        return False
    assert cookie_token is not None
    assert header_token is not None
    return compare_digest(cookie_token, header_token)


def _valid_csrf_token(token: str | None) -> bool:
    return bool(token and len(token) <= 128)


def _new_csrf_token() -> str:
    return token_urlsafe(CSRF_TOKEN_BYTES)


def _set_csrf_cookie(response, token: str) -> None:
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="strict",
    )


def _security_redirect(message: str) -> RedirectResponse:
    return RedirectResponse(url=f"/debug?message={quote(message)}", status_code=303)


def _inventory_redirect(message: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"/inventory?message={quote(message)}",
        status_code=303,
    )


def _product_asset_exists(product: Product) -> bool:
    return bool(
        product.image_path
        and (PRODUCT_ASSET_DIR / f"{product.image_path}.png").is_file()
    )


def _catalog_product_asset_exists(product: CatalogProduct) -> bool:
    return bool(
        product.image_path
        and (PRODUCT_ASSET_DIR / f"{product.image_path}.png").is_file()
    )


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
