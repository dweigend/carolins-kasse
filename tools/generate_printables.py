#!/usr/bin/env python3
"""Generate printable A4 PDFs for cards and barcode labels.

Usage:
    uv run python tools/generate_printables.py

Creates:
    data/print/user_cards.pdf
    data/print/recipe_cards.pdf
    data/print/product_labels.pdf
    data/print/all_printables.pdf
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.admin.printables import generate_all_printables


def main() -> None:
    """Generate all printable PDFs."""
    print("🖨️  Generiere Druck-PDFs...\n")
    for path in generate_all_printables():
        print(f"  ✓ {path}")
    print("\n✅ Druckdateien erfolgreich erstellt!")


if __name__ == "__main__":
    main()
