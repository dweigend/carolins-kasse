#!/usr/bin/env python3
"""Generate printable A4 PDFs for cards and barcode labels.

Usage:
    uv run python tools/generate_printables.py
    uv run python tools/generate_printables.py --users Carolin Annelie
    uv run python tools/generate_printables.py --products Brot Mehl Zucker
    uv run python tools/generate_printables.py --all-products

Creates:
    data/print/user_cards.pdf
    data/print/recipe_cards.pdf
    data/print/product_labels.pdf
    data/print/all_printables.pdf
"""

import argparse
from collections.abc import Callable
import sys
from pathlib import Path
from typing import TypeVar

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.admin.printables import (
    PRINT_DIR,
    generate_all_printables,
    generate_product_labels_pdf,
    generate_user_cards_pdf,
)
from src.utils.database import (
    get_all_products,
    get_all_users,
    init_database,
)

Record = TypeVar("Record")


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse the optional user-card selection."""
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
        metavar="NAME",
        help="Generate only the labels for these products.",
    )
    selection_group.add_argument(
        "--all-products",
        action="store_true",
        help="Generate labels for every product in the database.",
    )
    return parser.parse_args(arguments)


def select_records_by_name(
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


def generate_selected_product_labels(product_names: list[str]) -> Path:
    """Generate one label sheet for the requested products."""
    init_database()
    selected_products = select_records_by_name(
        get_all_products(include_inactive=True),
        product_names,
        lambda product: product.name_de,
        "product",
    )

    filename = (
        "product_labels_"
        + "_".join(product.name_de for product in selected_products)
        + ".pdf"
    )
    return generate_product_labels_pdf(PRINT_DIR / filename, selected_products)


def generate_all_product_labels() -> Path:
    """Generate one label sheet for every product in the database."""
    init_database()
    products = get_all_products(include_inactive=True)
    return generate_product_labels_pdf(
        PRINT_DIR / "product_labels_all_products.pdf",
        products,
    )


def main(arguments: list[str] | None = None) -> None:
    """Generate all printable PDFs."""
    args = parse_args(arguments)
    if args.users:
        output_path = generate_selected_user_cards(args.users)
        print(f"✓ Nutzerkarten erstellt: {output_path}")
        return
    if args.products:
        output_path = generate_selected_product_labels(args.products)
        print(f"✓ Produktetiketten erstellt: {output_path}")
        return
    if args.all_products:
        output_path = generate_all_product_labels()
        print(f"✓ Alle Produktetiketten erstellt: {output_path}")
        return

    print("🖨️  Generiere Druck-PDFs...\n")
    for path in generate_all_printables():
        print(f"  ✓ {path}")
    print("\n✅ Druckdateien erfolgreich erstellt!")


if __name__ == "__main__":
    main()
