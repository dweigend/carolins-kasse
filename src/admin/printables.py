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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
PRODUCT_FONT_NAME = "FredokaPrint"
PRODUCT_FONT_PATH = (
    ASSETS_DIR / "fonts" / "Fredoka" / "Fredoka-VariableFont_wdth,wght.ttf"
)
pdfmetrics.registerFont(TTFont(PRODUCT_FONT_NAME, str(PRODUCT_FONT_PATH)))

CREDIT_CARD_SIZE = (85.6 * mm, 53.98 * mm)
USER_CARD_SIZE = CREDIT_CARD_SIZE
RECIPE_CARD_SIZE = (70 * mm, 45 * mm)
PRODUCT_LABEL_SIZE = (70 * mm, 36 * mm)
PRODUCT_LABEL_COLUMNS = 3
PRODUCT_LABEL_ROWS = 8
PRODUCT_LABELS_PER_PAGE = PRODUCT_LABEL_COLUMNS * PRODUCT_LABEL_ROWS
PRODUCT_LABEL_TOP_MARGIN = 4.5 * mm
PRODUCT_BARCODE_ONLY_INSET_X = 8 * mm
PRODUCT_BARCODE_ONLY_INSET_Y = 8 * mm
PRODUCT_BARCODE_CAPTION_FONT_NAME = "Courier"
PRODUCT_BARCODE_CAPTION_FONT_SIZE = 8
PRODUCT_BARCODE_CAPTION_BASELINE = 30.5 * mm
PAGE_MARGIN = 12 * mm
CARD_GAP = 5 * mm

BACKGROUND = colors.HexColor("#FDF6EC")
TEXT = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")
ORANGE = colors.HexColor("#F59E0B")
RED = colors.HexColor("#EF4444")
LIGHT_BORDER = colors.HexColor("#E5E7EB")
PRODUCT_BACKGROUND = colors.HexColor("#FFF9F0")
PRODUCT_PRICE_BACKGROUND = colors.HexColor("#FEE2E2")
USER_ROLE_BACKGROUND = colors.HexColor("#F1F5F9")


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
        generate_product_label_calibration_pdf(),
        generate_combined_printables_pdf(),
    ]
    return generated_paths


def printable_files() -> list[PrintableFile]:
    """Return current printable PDF metadata for the admin UI."""
    files = [
        ("user_cards.pdf", "Kinder- und Admin-Karten"),
        ("recipe_cards.pdf", "Rezeptkarten"),
        ("product_labels.pdf", "Produktlabels"),
        ("product_labels_calibration.pdf", "Zweckform-3490-Kalibrierung"),
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


def generate_user_cards_pdf(
    path: Path | None = None, users: list[User] | None = None
) -> Path:
    """Generate barcode cards for all users or an explicitly selected subset."""
    output_path = path or PRINT_DIR / "user_cards.pdf"
    selected_users = users if users is not None else get_all_users()
    pdf = _new_pdf(output_path, "Carolin's Kasse - Karten")
    _draw_user_cards(pdf, selected_users)
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


def generate_product_labels_pdf(
    path: Path | None = None,
    products: list[Product] | None = None,
    *,
    start_position: int = 1,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
    barcode_only: bool = False,
) -> Path:
    """Generate a Zweckform 3490 sheet for products, including repeated items.

    Positive X offsets move labels right; positive Y offsets move labels down.
    """
    output_path = path or PRINT_DIR / "product_labels.pdf"
    selected_products = (
        products
        if products is not None
        else [product for product in get_all_products() if product.has_barcode]
    )
    pdf = _new_pdf(output_path, "Carolin's Kasse - Produkte")
    _draw_product_labels(
        pdf,
        selected_products,
        start_position=start_position,
        x_offset_mm=x_offset_mm,
        y_offset_mm=y_offset_mm,
        barcode_only=barcode_only,
    )
    pdf.save()
    return output_path


def generate_product_label_calibration_pdf(
    path: Path | None = None,
    *,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
) -> Path:
    """Generate an outlined Zweckform 3490 calibration sheet."""
    output_path = path or PRINT_DIR / "product_labels_calibration.pdf"
    pdf = _new_pdf(output_path, "Carolin's Kasse - Zweckform 3490 Kalibrierung")
    _draw_product_label_calibration(
        pdf,
        x_offset_mm=x_offset_mm,
        y_offset_mm=y_offset_mm,
    )
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


def _draw_product_labels(
    pdf: canvas.Canvas,
    products: list[Product],
    *,
    start_position: int = 1,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
    barcode_only: bool = False,
) -> None:
    _validate_product_label_position(start_position)
    draw_label = _draw_product_barcode_label if barcode_only else _draw_product_label
    for index, product in enumerate(products):
        sheet_index = start_position - 1 + index
        position = sheet_index % PRODUCT_LABELS_PER_PAGE + 1
        if index and position == 1:
            pdf.showPage()
        x, y = _product_label_position(position, x_offset_mm, y_offset_mm)
        draw_label(pdf, x, y, product)


def _draw_product_label_calibration(
    pdf: canvas.Canvas,
    *,
    x_offset_mm: float,
    y_offset_mm: float,
) -> None:
    width, height = PRODUCT_LABEL_SIZE
    pdf.setLineWidth(0.25)
    pdf.setStrokeColor(colors.HexColor("#64748B"))
    pdf.setFillColor(TEXT)
    pdf.setFont(PRODUCT_FONT_NAME, 7)

    for position in range(1, PRODUCT_LABELS_PER_PAGE + 1):
        x, y = _product_label_position(position, x_offset_mm, y_offset_mm)
        pdf.rect(x, y, width, height, stroke=1, fill=0)
        pdf.drawString(x + 2 * mm, y + height - 4 * mm, str(position))
        _draw_calibration_cross(pdf, x + width / 2, y + height / 2)


def _draw_calibration_cross(pdf: canvas.Canvas, x: float, y: float) -> None:
    arm = 2 * mm
    pdf.line(x - arm, y, x + arm, y)
    pdf.line(x, y - arm, x, y + arm)


def _draw_user_card(pdf: canvas.Canvas, x: float, y: float, user: User) -> None:
    width, height = USER_CARD_SIZE
    accent = colors.HexColor(user.color or "#F59E0B")
    _draw_credit_card_background(pdf, x, y, width, height, accent)

    _draw_image(
        pdf,
        _user_asset_path(user),
        x + 5 * mm,
        y + 27 * mm,
        30 * mm,
        23 * mm,
    )
    _draw_title(
        pdf,
        user.name,
        x + 40 * mm,
        y + 41 * mm,
        max_width=40 * mm,
        font_size=17,
        min_font_size=11,
    )

    role = "Admin-Karte" if user.is_admin else "Kinderkarte"
    _draw_user_role(pdf, role, x + 40 * mm, y + 30 * mm)
    _draw_barcode(
        pdf,
        user.card_id,
        x + 10 * mm,
        y + 6 * mm,
        width - 20 * mm,
        15 * mm,
    )


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
    _draw_image(
        pdf,
        _asset_path("340er", product.image_path),
        x + 4 * mm,
        y + 17.5 * mm,
        17 * mm,
        15 * mm,
    )
    _draw_title(
        pdf,
        product.name_de,
        x + 24 * mm,
        y + 28 * mm,
        max_width=42 * mm,
        font_size=12,
        min_font_size=7,
        font_name=PRODUCT_FONT_NAME,
    )

    _draw_product_price(pdf, product.price, x + 24 * mm, y + 18.5 * mm)

    _draw_barcode(
        pdf,
        product.barcode,
        x + 5 * mm,
        y + 2 * mm,
        60 * mm,
        13.5 * mm,
        font_name=PRODUCT_FONT_NAME,
    )


def _draw_product_barcode_label(
    pdf: canvas.Canvas, x: float, y: float, product: Product
) -> None:
    """Draw a compact product caption and barcode with trimming space."""
    label_width, label_height = PRODUCT_LABEL_SIZE
    caption = f"{product.name_de} - {int(product.price)} Taler"
    pdf.setFillColor(TEXT)
    pdf.setFont(
        PRODUCT_BARCODE_CAPTION_FONT_NAME,
        PRODUCT_BARCODE_CAPTION_FONT_SIZE,
    )
    pdf.drawCentredString(
        x + label_width / 2,
        y + PRODUCT_BARCODE_CAPTION_BASELINE,
        caption,
    )
    _draw_barcode(
        pdf,
        product.barcode,
        x + PRODUCT_BARCODE_ONLY_INSET_X,
        y + PRODUCT_BARCODE_ONLY_INSET_Y,
        label_width - 2 * PRODUCT_BARCODE_ONLY_INSET_X,
        label_height - 2 * PRODUCT_BARCODE_ONLY_INSET_Y,
        font_name=PRODUCT_FONT_NAME,
    )


def _draw_credit_card_background(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    border_color,
) -> None:
    """Draw the shared warm credit-card shell."""
    pdf.setFillColor(PRODUCT_BACKGROUND)
    pdf.setStrokeColor(border_color)
    pdf.setLineWidth(1.8)
    pdf.roundRect(x, y, width, height, 4 * mm, stroke=1, fill=1)


def _draw_user_role(pdf: canvas.Canvas, role: str, x: float, y: float) -> None:
    """Draw the user card type as a subtle badge."""
    badge_width = max(
        27 * mm,
        pdf.stringWidth(role, "Helvetica-Bold", 10) + 8 * mm,
    )
    badge_height = 7.5 * mm

    pdf.setFillColor(USER_ROLE_BACKGROUND)
    pdf.roundRect(x, y, badge_width, badge_height, 3.75 * mm, stroke=0, fill=1)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(x + badge_width / 2, y + 2.35 * mm, role)


def _draw_product_price(pdf: canvas.Canvas, price: float, x: float, y: float) -> None:
    """Draw the product price as a compact badge."""
    price_text = f"{int(price)} Taler"
    badge_width = max(
        25 * mm,
        pdf.stringWidth(price_text, PRODUCT_FONT_NAME, 10) + 8 * mm,
    )
    badge_height = 7.5 * mm

    pdf.setFillColor(PRODUCT_PRICE_BACKGROUND)
    pdf.roundRect(x, y, badge_width, badge_height, 3.75 * mm, stroke=0, fill=1)
    pdf.setFillColor(RED)
    pdf.setFont(PRODUCT_FONT_NAME, 10)
    pdf.drawCentredString(
        x + badge_width / 2,
        y + 2.35 * mm,
        price_text,
    )


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
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_size: int = 11,
    min_font_size: int = 7,
    font_name: str = "Helvetica-Bold",
) -> None:
    while (
        font_size > min_font_size
        and pdf.stringWidth(text, font_name, font_size) > max_width
    ):
        font_size -= 1
    pdf.setFillColor(TEXT)
    pdf.setFont(font_name, font_size)
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
    pdf: canvas.Canvas,
    code: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    font_name: str | None = None,
) -> None:
    barcode_options = {
        "value": code,
        "barHeight": height,
        "humanReadable": True,
        "quiet": True,
    }
    if font_name:
        barcode_options["fontName"] = font_name
    drawing = createBarcodeDrawing("EAN13", **barcode_options)
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


def _product_label_position(
    position: int,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
) -> tuple[float, float]:
    """Return the lower-left point for a 1-based Zweckform 3490 position."""
    _validate_product_label_position(position)
    width, height = PRODUCT_LABEL_SIZE
    zero_based_position = position - 1
    column = zero_based_position % PRODUCT_LABEL_COLUMNS
    row = zero_based_position // PRODUCT_LABEL_COLUMNS
    x = column * width + x_offset_mm * mm
    y = A4[1] - PRODUCT_LABEL_TOP_MARGIN - (row + 1) * height - y_offset_mm * mm
    return x, y


def _validate_product_label_position(position: int) -> None:
    if not 1 <= position <= PRODUCT_LABELS_PER_PAGE:
        raise ValueError(
            f"Product label position must be between 1 and {PRODUCT_LABELS_PER_PAGE}."
        )


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
