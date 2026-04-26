"""Printable A4 PDF generation for cards and barcode labels."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from src.utils.database import (
    Product,
    Recipe,
    User,
    get_all_products,
    get_all_recipes,
    get_all_users,
    get_recipe_ingredients,
    init_database,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
PRINT_DIR = PROJECT_ROOT / "data" / "print"

USER_CARD_SIZE = (70 * mm, 45 * mm)
RECIPE_CARD_SIZE = (70 * mm, 45 * mm)
PRODUCT_LABEL_SIZE = (55 * mm, 30 * mm)
PAGE_MARGIN = 12 * mm
CARD_GAP = 5 * mm
LABEL_GAP = 4 * mm

BACKGROUND = colors.HexColor("#FDF6EC")
TEXT = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
ORANGE = colors.HexColor("#F59E0B")
RED = colors.HexColor("#EF4444")
BLUE = colors.HexColor("#3B82F6")
LIGHT_BORDER = colors.HexColor("#E5E7EB")


@dataclass(frozen=True)
class PrintableFile:
    """Metadata for a generated printable file."""

    filename: str
    title: str
    url: str
    exists: bool
    size_kb: int
    modified_at: str | None


def generate_all_printables() -> list[Path]:
    """Generate all printable A4 PDFs and return their paths."""
    init_database()
    PRINT_DIR.mkdir(parents=True, exist_ok=True)

    generated_paths = [
        generate_user_cards_pdf(),
        generate_recipe_cards_pdf(),
        generate_product_labels_pdf(),
        generate_combined_printables_pdf(),
    ]
    return generated_paths


def printable_files() -> list[PrintableFile]:
    """Return current printable PDF metadata for the admin UI."""
    files = [
        ("user_cards.pdf", "Kinder- und Admin-Karten"),
        ("recipe_cards.pdf", "Rezeptkarten"),
        ("product_labels.pdf", "Produktlabels"),
        ("all_printables.pdf", "Alles zusammen"),
    ]

    result = []
    for filename, title in files:
        path = PRINT_DIR / filename
        stat = path.stat() if path.exists() else None
        result.append(
            PrintableFile(
                filename=filename,
                title=title,
                url=f"/print/{filename}",
                exists=path.exists(),
                size_kb=round(stat.st_size / 1024) if stat else 0,
                modified_at=(
                    datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
                    if stat
                    else None
                ),
            )
        )
    return result


def generate_user_cards_pdf(path: Path | None = None) -> Path:
    """Generate user/admin barcode cards."""
    output_path = path or PRINT_DIR / "user_cards.pdf"
    users = get_all_users()
    pdf = _new_pdf(output_path, "Carolin's Kasse - Karten")
    _draw_user_cards(pdf, users)
    pdf.save()
    return output_path


def generate_recipe_cards_pdf(path: Path | None = None) -> Path:
    """Generate recipe barcode cards."""
    output_path = path or PRINT_DIR / "recipe_cards.pdf"
    recipes = get_all_recipes()
    pdf = _new_pdf(output_path, "Carolin's Kasse - Rezepte")
    _draw_recipe_cards(pdf, recipes)
    pdf.save()
    return output_path


def generate_product_labels_pdf(path: Path | None = None) -> Path:
    """Generate product barcode labels."""
    output_path = path or PRINT_DIR / "product_labels.pdf"
    products = [p for p in get_all_products() if p.has_barcode]
    pdf = _new_pdf(output_path, "Carolin's Kasse - Produkte")
    _draw_product_labels(pdf, products)
    pdf.save()
    return output_path


def generate_combined_printables_pdf(path: Path | None = None) -> Path:
    """Generate one combined printable PDF."""
    output_path = path or PRINT_DIR / "all_printables.pdf"
    pdf = _new_pdf(output_path, "Carolin's Kasse - Druckboegen")
    _draw_user_cards(pdf, get_all_users())
    pdf.showPage()
    _draw_recipe_cards(pdf, get_all_recipes())
    pdf.showPage()
    _draw_product_labels(pdf, [p for p in get_all_products() if p.has_barcode])
    pdf.save()
    return output_path


def _new_pdf(path: Path, title: str) -> canvas.Canvas:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setTitle(title)
    return pdf


def _draw_user_cards(pdf: canvas.Canvas, users: list[User]) -> None:
    for index, user in enumerate(users):
        x, y = _grid_position(index, USER_CARD_SIZE, CARD_GAP)
        if index and _starts_new_page(index, USER_CARD_SIZE, CARD_GAP):
            pdf.showPage()
            x, y = _grid_position(0, USER_CARD_SIZE, CARD_GAP)
        _draw_user_card(pdf, x, y, user)


def _draw_recipe_cards(pdf: canvas.Canvas, recipes: list[Recipe]) -> None:
    for index, recipe in enumerate(recipes):
        x, y = _grid_position(index, RECIPE_CARD_SIZE, CARD_GAP)
        if index and _starts_new_page(index, RECIPE_CARD_SIZE, CARD_GAP):
            pdf.showPage()
            x, y = _grid_position(0, RECIPE_CARD_SIZE, CARD_GAP)
        _draw_recipe_card(pdf, x, y, recipe)


def _draw_product_labels(pdf: canvas.Canvas, products: list[Product]) -> None:
    for index, product in enumerate(products):
        x, y = _grid_position(index, PRODUCT_LABEL_SIZE, LABEL_GAP)
        if index and _starts_new_page(index, PRODUCT_LABEL_SIZE, LABEL_GAP):
            pdf.showPage()
            x, y = _grid_position(0, PRODUCT_LABEL_SIZE, LABEL_GAP)
        _draw_product_label(pdf, x, y, product)


def _draw_user_card(pdf: canvas.Canvas, x: float, y: float, user: User) -> None:
    width, height = USER_CARD_SIZE
    accent = colors.HexColor(user.color or "#F59E0B")
    _draw_card_background(pdf, x, y, width, height, accent)

    _draw_image(pdf, _user_asset_path(user), x + 5 * mm, y + 17 * mm, 18 * mm, 18 * mm)
    _draw_title(pdf, user.name, x + 26 * mm, y + 31 * mm, max_width=38 * mm)

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7)
    role = "Admin-Karte" if user.is_admin else "Kinderkarte"
    pdf.drawString(x + 26 * mm, y + 26 * mm, role)

    _draw_barcode(pdf, user.card_id, x + 8 * mm, y + 4 * mm, 54 * mm, 14 * mm)


def _draw_recipe_card(pdf: canvas.Canvas, x: float, y: float, recipe: Recipe) -> None:
    width, height = RECIPE_CARD_SIZE
    _draw_card_background(pdf, x, y, width, height, ORANGE)

    _draw_image(
        pdf,
        _asset_path("680er", recipe.image_path),
        x + 5 * mm,
        y + 18 * mm,
        20 * mm,
        20 * mm,
    )
    _draw_title(pdf, recipe.name, x + 28 * mm, y + 32 * mm, max_width=36 * mm)

    ingredients = get_recipe_ingredients(recipe.barcode)
    ingredient_text = ", ".join(product.name_de for product, _ in ingredients[:4])
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6)
    pdf.drawString(x + 28 * mm, y + 25 * mm, _truncate(ingredient_text, 34))

    _draw_barcode(pdf, recipe.barcode, x + 8 * mm, y + 4 * mm, 54 * mm, 14 * mm)


def _draw_product_label(
    pdf: canvas.Canvas, x: float, y: float, product: Product
) -> None:
    width, height = PRODUCT_LABEL_SIZE
    _draw_card_background(pdf, x, y, width, height, BLUE)

    _draw_image(
        pdf,
        _asset_path("340er", product.image_path),
        x + 4 * mm,
        y + 10 * mm,
        12 * mm,
        12 * mm,
    )
    _draw_title(pdf, product.name_de, x + 18 * mm, y + 21 * mm, max_width=31 * mm)

    pdf.setFillColor(RED)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x + 18 * mm, y + 16 * mm, f"{int(product.price)} Taler")

    _draw_barcode(pdf, product.barcode, x + 5 * mm, y + 3 * mm, 45 * mm, 10 * mm)


def _draw_card_background(
    pdf: canvas.Canvas, x: float, y: float, width: float, height: float, accent
) -> None:
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(LIGHT_BORDER)
    pdf.roundRect(x, y, width, height, 4 * mm, stroke=1, fill=1)
    pdf.setFillColor(BACKGROUND)
    pdf.roundRect(
        x + 1.5 * mm,
        y + 1.5 * mm,
        width - 3 * mm,
        height - 3 * mm,
        3 * mm,
        stroke=0,
        fill=1,
    )
    pdf.setFillColor(accent)
    pdf.roundRect(
        x + 1.5 * mm,
        y + height - 6 * mm,
        width - 3 * mm,
        4.5 * mm,
        2 * mm,
        stroke=0,
        fill=1,
    )


def _draw_title(
    pdf: canvas.Canvas, text: str, x: float, y: float, max_width: float
) -> None:
    font_size = 11
    while (
        font_size > 7 and pdf.stringWidth(text, "Helvetica-Bold", font_size) > max_width
    ):
        font_size -= 1
    pdf.setFillColor(TEXT)
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawString(x, y, text)


def _draw_image(
    pdf: canvas.Canvas,
    path: Path | None,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    if not path or not path.exists():
        return
    image = ImageReader(str(path))
    pdf.drawImage(
        image,
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )


def _draw_barcode(
    pdf: canvas.Canvas, code: str, x: float, y: float, width: float, height: float
) -> None:
    drawing = createBarcodeDrawing(
        "EAN13",
        value=code,
        barHeight=height,
        humanReadable=True,
    )
    scale = min(width / drawing.width, height / drawing.height)
    pdf.saveState()
    pdf.translate(x + (width - drawing.width * scale) / 2, y)
    pdf.scale(scale, scale)
    renderPDF.draw(drawing, pdf, 0, 0)
    pdf.restoreState()


def _grid_position(
    index: int, item_size: tuple[float, float], gap: float
) -> tuple[float, float]:
    page_width, page_height = A4
    item_width, item_height = item_size
    columns = max(1, int((page_width - PAGE_MARGIN * 2 + gap) // (item_width + gap)))
    rows = max(1, int((page_height - PAGE_MARGIN * 2 + gap) // (item_height + gap)))
    page_index = index % (columns * rows)
    col = page_index % columns
    row = page_index // columns
    x = PAGE_MARGIN + col * (item_width + gap)
    y = page_height - PAGE_MARGIN - item_height - row * (item_height + gap)
    return x, y


def _starts_new_page(index: int, item_size: tuple[float, float], gap: float) -> bool:
    page_width, page_height = A4
    item_width, item_height = item_size
    columns = max(1, int((page_width - PAGE_MARGIN * 2 + gap) // (item_width + gap)))
    rows = max(1, int((page_height - PAGE_MARGIN * 2 + gap) // (item_height + gap)))
    return index % (columns * rows) == 0


def _user_asset_path(user: User) -> Path | None:
    asset_by_name = {
        "Carolin": ASSETS_DIR / "680er" / "avata_carolin.png",
        "Annelie": ASSETS_DIR / "680er" / "avata_annelie.png",
        "Gast": ASSETS_DIR / "680er" / "avata_kind_junge_blau.png",
        "Admin": ASSETS_DIR / "680er" / "kasse.png",
    }
    return asset_by_name.get(user.name)


def _asset_path(folder: str, asset_key: str | None) -> Path | None:
    if not asset_key:
        return None
    return ASSETS_DIR / folder / f"{asset_key}.png"


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "..."
