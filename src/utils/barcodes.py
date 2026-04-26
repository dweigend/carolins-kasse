"""Barcode helpers for internal product, user, and recipe codes."""

from pathlib import Path
from typing import Literal

import barcode
from barcode.writer import SVGWriter

from src.utils.filename import sanitize_filename

BarcodeKind = Literal["products", "users", "recipes"]

PROJECT_ROOT = Path(__file__).parent.parent.parent
BARCODE_DIR = PROJECT_ROOT / "data" / "barcodes"

PRODUCT_PREFIX = "100"
USER_PREFIX = "200"
RECIPE_PREFIX = "300"
BARCODE_BODY_WIDTH = 9


def calculate_ean13_check_digit(code: str) -> str:
    """Return the full EAN-13 code for a 12-digit input body."""
    if len(code) != 12:
        raise ValueError("Code must be exactly 12 digits")
    if not code.isdigit():
        raise ValueError("Code must contain only digits")

    total = 0
    for index, digit in enumerate(code):
        weight = 1 if index % 2 == 0 else 3
        total += int(digit) * weight

    check_digit = (10 - (total % 10)) % 10
    return code + str(check_digit)


def generate_product_barcode(number: int) -> str:
    """Generate an internal EAN-13 product barcode."""
    return _generate_internal_barcode(PRODUCT_PREFIX, number)


def generate_user_barcode(number: int) -> str:
    """Generate an internal EAN-13 user card barcode."""
    return _generate_internal_barcode(USER_PREFIX, number)


def generate_recipe_barcode(number: int) -> str:
    """Generate an internal EAN-13 recipe card barcode."""
    return _generate_internal_barcode(RECIPE_PREFIX, number)


def barcode_filename(label: str, code: str) -> str:
    """Return the stable SVG filename for a barcode label and code."""
    return f"{sanitize_filename(label)}_{code}.svg"


def barcode_path(kind: BarcodeKind, label: str, code: str) -> Path:
    """Return the filesystem path for a generated barcode SVG."""
    return BARCODE_DIR / kind / barcode_filename(label, code)


def barcode_url(kind: BarcodeKind, label: str, code: str) -> str:
    """Return the mounted admin URL for a generated barcode SVG."""
    return f"/barcodes/{kind}/{barcode_filename(label, code)}"


def write_ean13_svg(code: str, output_path: Path) -> None:
    """Write an EAN-13 barcode as SVG to the given path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ean = barcode.get("ean13", code, writer=SVGWriter())
    ean.save(str(output_path.with_suffix("")))


def _generate_internal_barcode(prefix: str, number: int) -> str:
    if number < 1:
        raise ValueError("Barcode number must be positive")
    base = f"{prefix}{number:0{BARCODE_BODY_WIDTH}d}"
    return calculate_ean13_check_digit(base)
