#!/usr/bin/env python3
"""Generate printable A4 PDFs for cards and barcode labels.

Usage:
    uv run python tools/generate_printables.py
    uv run python tools/generate_printables.py --users Carolin Annelie
    uv run python tools/generate_printables.py --products Brot Mehl Zucker
    uv run python tools/generate_printables.py --products Brot=3 Mehl=2
    uv run python tools/generate_printables.py --all-products
    uv run python tools/generate_printables.py --calibration

Creates:
    data/print/user_cards.pdf
    data/print/recipe_cards.pdf
    data/print/product_labels.pdf
    data/print/product_labels_calibration.pdf
    data/print/all_printables.pdf
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.admin.printables import (
    PRINT_DIR,
    generate_all_printables,
    generate_product_label_calibration_pdf,
    generate_product_labels_pdf,
    generate_user_cards_pdf,
)
from src.utils.database import (
    get_all_products,
    get_all_users,
    init_database,
)


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse printable selection and Zweckform 3490 alignment options."""
    parser = argparse.ArgumentParser(description="Generate printable checkout cards.")
    selection_group = parser.add_mutually_exclusive_group()
    selection_group.add_argument(
        "--users",
        nargs="+",
        metavar="NAME",
        help="Generate only the cards for these users.",
    )
    selection_group.add_argument(
        "--products",
        nargs="+",
        metavar="NAME[=COUNT]",
        help="Generate labels for these products; append =COUNT for copies.",
    )
    selection_group.add_argument(
        "--all-products",
        action="store_true",
        help="Generate labels for every product in the database.",
    )
    selection_group.add_argument(
        "--calibration",
        action="store_true",
        help="Generate an outlined Zweckform 3490 calibration sheet.",
    )
    parser.add_argument(
        "--start-position",
        type=int,
        choices=range(1, 25),
        default=1,
        metavar="1..24",
        help="First free label position on a partly used sheet (default: 1).",
    )
    parser.add_argument(
        "--x-offset-mm",
        type=float,
        default=0,
        help="Horizontal correction in mm; positive values move right.",
    )
    parser.add_argument(
        "--y-offset-mm",
        type=float,
        default=0,
        help="Vertical correction in mm; positive values move down.",
    )
    parsed_args = parser.parse_args(arguments)
    has_product_selection = bool(parsed_args.products or parsed_args.all_products)
    if parsed_args.start_position != 1 and not has_product_selection:
        parser.error("--start-position requires --products or --all-products")
    if (
        (parsed_args.x_offset_mm or parsed_args.y_offset_mm)
        and not has_product_selection
        and not parsed_args.calibration
    ):
        parser.error(
            "--x-offset-mm and --y-offset-mm require a product or calibration PDF"
        )
    return parsed_args


def select_records_by_name[Record](
    records: list[Record],
    requested_names: list[str],
    get_name: Callable[[Record], str],
    record_type: str,
) -> list[Record]:
    """Return records matching the requested display names."""
    records_by_name = {get_name(record).casefold(): record for record in records}
    selected_records = []
    for requested_name in requested_names:
        record = records_by_name.get(requested_name.casefold())
        if record is None:
            available_names = ", ".join(
                get_name(item) for item in records_by_name.values()
            )
            raise ValueError(
                f"Unknown {record_type} '{requested_name}'. Available {record_type}s: "
                f"{available_names}."
            )
        selected_records.append(record)
    return selected_records


def generate_selected_user_cards(user_names: list[str]) -> Path:
    """Generate one card sheet for the requested users."""
    init_database()
    selected_users = select_records_by_name(
        get_all_users(), user_names, lambda user: user.name, "user"
    )

    filename = "user_cards_" + "_".join(user.name for user in selected_users) + ".pdf"
    return generate_user_cards_pdf(PRINT_DIR / filename, selected_users)


def generate_selected_product_labels(
    product_specs: list[str],
    *,
    start_position: int = 1,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
) -> Path:
    """Generate one label sheet for the requested products."""
    init_database()
    product_names_and_copies = [
        _parse_product_spec(product_spec) for product_spec in product_specs
    ]
    selected_once = select_records_by_name(
        get_all_products(include_inactive=True),
        [name for name, _ in product_names_and_copies],
        lambda product: product.name_de,
        "product",
    )
    selected_products = [
        product
        for product, (_, copies) in zip(
            selected_once, product_names_and_copies, strict=True
        )
        for _ in range(copies)
    ]

    filename = (
        "product_labels_"
        + "_".join(
            product.name_de if copies == 1 else f"{product.name_de}_{copies}x"
            for product, (_, copies) in zip(
                selected_once, product_names_and_copies, strict=True
            )
        )
        + ".pdf"
    )
    return generate_product_labels_pdf(
        PRINT_DIR / filename,
        selected_products,
        start_position=start_position,
        x_offset_mm=x_offset_mm,
        y_offset_mm=y_offset_mm,
    )


def generate_all_product_labels(
    *,
    start_position: int = 1,
    x_offset_mm: float = 0,
    y_offset_mm: float = 0,
) -> Path:
    """Generate one label sheet for every product in the database."""
    init_database()
    products = get_all_products(include_inactive=True)
    return generate_product_labels_pdf(
        PRINT_DIR / "product_labels_all_products.pdf",
        products,
        start_position=start_position,
        x_offset_mm=x_offset_mm,
        y_offset_mm=y_offset_mm,
    )


def _parse_product_spec(product_spec: str) -> tuple[str, int]:
    name, separator, copies_text = product_spec.rpartition("=")
    if not separator:
        return product_spec, 1
    if not name or not copies_text.isdigit() or int(copies_text) < 1:
        raise ValueError(
            f"Invalid product copies '{product_spec}'. Use NAME=COUNT with COUNT >= 1."
        )
    return name, int(copies_text)


def main(arguments: list[str] | None = None) -> None:
    """Generate all printable PDFs."""
    args = parse_args(arguments)
    if args.users:
        output_path = generate_selected_user_cards(args.users)
        print(f"✓ Nutzerkarten erstellt: {output_path}")
        return
    if args.products:
        output_path = generate_selected_product_labels(
            args.products,
            start_position=args.start_position,
            x_offset_mm=args.x_offset_mm,
            y_offset_mm=args.y_offset_mm,
        )
        print(f"✓ Produktetiketten erstellt: {output_path}")
        return
    if args.all_products:
        output_path = generate_all_product_labels(
            start_position=args.start_position,
            x_offset_mm=args.x_offset_mm,
            y_offset_mm=args.y_offset_mm,
        )
        print(f"✓ Alle Produktetiketten erstellt: {output_path}")
        return
    if args.calibration:
        output_path = generate_product_label_calibration_pdf(
            PRINT_DIR / "product_labels_calibration.pdf",
            x_offset_mm=args.x_offset_mm,
            y_offset_mm=args.y_offset_mm,
        )
        print(f"✓ Zweckform-3490-Kalibrierung erstellt: {output_path}")
        return

    print("🖨️  Generiere Druck-PDFs...\n")
    for path in generate_all_printables():
        print(f"  ✓ {path}")
    print("\n✅ Druckdateien erfolgreich erstellt!")


if __name__ == "__main__":
    main()
