"""Direct temp-state coverage for operation scripts."""

from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
import importlib
import io
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from tests.db_isolation import isolated_database_module


PRODUCT_BARCODE = "1000000000016"
NO_LABEL_BARCODE = "1000000000023"
USER_BARCODE = "2000000000015"
RECIPE_BARCODE = "3000000000014"

OPERATION_MODULES = (
    "src.admin.printables",
    "src.utils.barcodes",
    "tools.generate_barcodes",
    "tools.generate_printables",
)


class OperationScriptTests(unittest.TestCase):
    def test_generate_barcodes_main_uses_temp_db_and_output_dir(self) -> None:
        with operation_script_context() as context:
            stale_svg = create_stale_product_svg(context.barcode_dir)

            output = run_generate_barcodes(context.barcode_dir)

            self.assert_expected_barcodes(context.barcode_dir)
            self.assertFalse(stale_svg.exists())
            self.assertFalse(product_barcode_path(context.barcode_dir).exists())
            self.assertIn("3 Barcodes generiert", output.getvalue())

    def test_generate_printables_main_uses_temp_db_and_output_dir(self) -> None:
        with operation_script_context() as context:
            output = run_generate_printables(context.print_dir)

            self.assert_expected_printables(context.print_dir)
            self.assertIn("Druckdateien erfolgreich erstellt", output.getvalue())

    def assert_expected_barcodes(self, barcode_dir: Path) -> None:
        for svg_path in expected_barcode_paths(barcode_dir):
            self.assertTrue(svg_path.exists(), svg_path)
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))

    def assert_expected_printables(self, print_dir: Path) -> None:
        self.assertEqual(
            EXPECTED_PRINTABLE_NAMES,
            {path.name for path in print_dir.glob("*.pdf")},
        )
        for pdf_path in print_dir.glob("*.pdf"):
            self.assertGreater(pdf_path.stat().st_size, 500)
            self.assertEqual(pdf_path.read_bytes()[:4], b"%PDF")


@dataclass(frozen=True)
class OperationScriptContext:
    barcode_dir: Path
    print_dir: Path


EXPECTED_PRINTABLE_NAMES = {
    "user_cards.pdf",
    "recipe_cards.pdf",
    "product_labels.pdf",
    "all_printables.pdf",
}


@contextmanager
def operation_script_context() -> Iterator[OperationScriptContext]:
    """Yield temp database and output paths with a minimal seeded catalog."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with isolated_operation_modules(temp_path / "kasse.db") as database:
            seed_operation_script_data(database)
            yield OperationScriptContext(
                barcode_dir=temp_path / "barcodes",
                print_dir=temp_path / "print",
            )


def run_generate_barcodes(barcode_dir: Path) -> io.StringIO:
    """Run the barcode script with generated files redirected to a temp path."""
    barcode_helpers = importlib.import_module("src.utils.barcodes")
    generate_barcodes = importlib.import_module("tools.generate_barcodes")
    output = io.StringIO()

    with (
        patch.object(barcode_helpers, "BARCODE_DIR", barcode_dir),
        patch.object(generate_barcodes, "BARCODE_DIR", barcode_dir),
        redirect_stdout(output),
    ):
        generate_barcodes.main()

    return output


def run_generate_printables(print_dir: Path) -> io.StringIO:
    """Run the printable script with generated files redirected to a temp path."""
    printables = importlib.import_module("src.admin.printables")
    generate_printables = importlib.import_module("tools.generate_printables")
    output = io.StringIO()

    with (
        patch.object(printables, "PRINT_DIR", print_dir),
        redirect_stdout(output),
    ):
        generate_printables.main()

    return output


def create_stale_product_svg(barcode_dir: Path) -> Path:
    stale_svg = barcode_dir / "products" / "stale.svg"
    stale_svg.parent.mkdir(parents=True)
    stale_svg.write_text("<svg />", encoding="utf-8")
    return stale_svg


def expected_barcode_paths(barcode_dir: Path) -> set[Path]:
    return {
        barcode_dir / "products" / f"Milch_{PRODUCT_BARCODE}.svg",
        barcode_dir / "users" / f"Carolin_{USER_BARCODE}.svg",
        barcode_dir / "recipes" / f"Pfannkuchen_{RECIPE_BARCODE}.svg",
    }


def product_barcode_path(barcode_dir: Path) -> Path:
    return barcode_dir / "products" / f"Broetchen_{NO_LABEL_BARCODE}.svg"


@contextmanager
def isolated_operation_modules(db_path: Path) -> Iterator[ModuleType]:
    """Import operation modules against a temporary database path."""
    previous_modules = {
        module_name: sys.modules[module_name]
        for module_name in OPERATION_MODULES
        if module_name in sys.modules
    }
    for module_name in OPERATION_MODULES:
        sys.modules.pop(module_name, None)

    try:
        with isolated_database_module(db_path) as database:
            yield database
    finally:
        for module_name in OPERATION_MODULES:
            sys.modules.pop(module_name, None)
        sys.modules.update(previous_modules)


def seed_operation_script_data(database: ModuleType) -> None:
    """Create a minimal catalog for barcode and printable generation."""
    database.init_database()
    database.add_product(
        database.Product(
            barcode=PRODUCT_BARCODE,
            name="milk",
            name_de="Milch",
            price=1,
            category="kuehlregal",
            image_path="missing_milk_asset",
            has_barcode=True,
        )
    )
    database.add_product(
        database.Product(
            barcode=NO_LABEL_BARCODE,
            name="roll",
            name_de="Broetchen",
            price=1,
            category="backwaren",
            image_path="missing_roll_asset",
            has_barcode=False,
        )
    )
    database.add_user(
        database.User(
            card_id=USER_BARCODE,
            name="Carolin",
            balance=10.0,
            color="#0066CC",
        )
    )
    database.add_recipe(
        database.Recipe(
            barcode=RECIPE_BARCODE,
            name="Pfannkuchen",
            image_path="missing_recipe_asset",
        )
    )
    database.add_recipe_ingredient(
        database.RecipeIngredient(
            recipe_barcode=RECIPE_BARCODE,
            product_barcode=PRODUCT_BARCODE,
            quantity=1,
        )
    )


if __name__ == "__main__":
    unittest.main()
