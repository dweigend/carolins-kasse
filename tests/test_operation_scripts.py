"""Direct temp-state coverage for operation scripts."""

from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
import importlib
import io
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

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

    def test_generate_selected_user_cards_creates_only_requested_cards(self) -> None:
        with operation_script_context() as context:
            generate_printables = importlib.import_module("tools.generate_printables")

            with (
                patch.object(
                    importlib.import_module("src.admin.printables"),
                    "PRINT_DIR",
                    context.print_dir,
                ),
                patch.object(generate_printables, "PRINT_DIR", context.print_dir),
            ):
                output_path = generate_printables.generate_selected_user_cards(
                    ["Carolin"]
                )

            self.assertEqual(context.print_dir / "user_cards_Carolin.pdf", output_path)
            self.assertEqual(b"%PDF", output_path.read_bytes()[:4])

    def test_generate_selected_product_labels_creates_only_requested_labels(
        self,
    ) -> None:
        with operation_script_context() as context:
            generate_printables = importlib.import_module("tools.generate_printables")

            with (
                patch.object(
                    importlib.import_module("src.admin.printables"),
                    "PRINT_DIR",
                    context.print_dir,
                ),
                patch.object(generate_printables, "PRINT_DIR", context.print_dir),
            ):
                output_path = generate_printables.generate_selected_product_labels(
                    ["Milch"]
                )

            self.assertEqual(
                context.print_dir / "product_labels_Milch.pdf", output_path
            )
            self.assertEqual(b"%PDF", output_path.read_bytes()[:4])

    def test_product_labels_use_zweckform_3490_dimensions(self) -> None:
        printables = importlib.import_module("src.admin.printables")

        width, height = printables.PRODUCT_LABEL_SIZE

        self.assertAlmostEqual(70, width / mm)
        self.assertAlmostEqual(36, height / mm)
        self.assertEqual(24, printables.PRODUCT_LABELS_PER_PAGE)

    def test_product_label_grid_fills_a4_without_gaps(self) -> None:
        printables = importlib.import_module("src.admin.printables")

        first_x, first_y = printables._product_label_position(1)
        third_x, third_y = printables._product_label_position(3)
        last_x, last_y = printables._product_label_position(24)

        self.assertAlmostEqual(0, first_x / mm)
        self.assertAlmostEqual(256.5, first_y / mm)
        self.assertAlmostEqual(140, third_x / mm)
        self.assertAlmostEqual(first_y, third_y)
        self.assertAlmostEqual(140, last_x / mm)
        self.assertAlmostEqual(4.5, last_y / mm)
        self.assertAlmostEqual(A4[0], third_x + 70 * mm)

    def test_product_label_offsets_move_right_and_down(self) -> None:
        printables = importlib.import_module("src.admin.printables")

        base_x, base_y = printables._product_label_position(1)
        offset_x, offset_y = printables._product_label_position(1, 1.5, 2.5)

        self.assertAlmostEqual(1.5, (offset_x - base_x) / mm)
        self.assertAlmostEqual(-2.5, (offset_y - base_y) / mm)

    def test_product_labels_continue_on_new_page_after_start_position(self) -> None:
        printables = importlib.import_module("src.admin.printables")
        product = printables.Product(
            barcode=PRODUCT_BARCODE,
            name="milk",
            name_de="Milch",
            price=1,
            category="kuehlregal",
        )
        pdf = MagicMock()

        with patch.object(printables, "_draw_product_label") as draw_product_label:
            printables._draw_product_labels(
                pdf,
                [product, product],
                start_position=24,
            )

        self.assertEqual(1, pdf.showPage.call_count)
        first_call, second_call = draw_product_label.call_args_list
        self.assertIs(pdf, first_call.args[0])
        self.assertAlmostEqual(140, first_call.args[1] / mm)
        self.assertAlmostEqual(4.5, first_call.args[2] / mm)
        self.assertIs(product, first_call.args[3])
        self.assertIs(pdf, second_call.args[0])
        self.assertAlmostEqual(0, second_call.args[1] / mm)
        self.assertAlmostEqual(256.5, second_call.args[2] / mm)
        self.assertIs(product, second_call.args[3])

    def test_product_label_barcode_requests_quiet_zones(self) -> None:
        printables = importlib.import_module("src.admin.printables")
        pdf = MagicMock()
        drawing = SimpleNamespace(width=37.29 * mm, height=13.5 * mm)

        with (
            patch.object(
                printables, "createBarcodeDrawing", return_value=drawing
            ) as create_barcode,
            patch.object(printables.renderPDF, "draw"),
        ):
            printables._draw_barcode(
                pdf,
                PRODUCT_BARCODE,
                0,
                0,
                60 * mm,
                13.5 * mm,
                font_name=printables.PRODUCT_FONT_NAME,
            )

        create_barcode.assert_called_once_with(
            "EAN13",
            value=PRODUCT_BARCODE,
            barHeight=13.5 * mm,
            humanReadable=True,
            quiet=True,
            fontName=printables.PRODUCT_FONT_NAME,
        )

    def test_user_cards_use_credit_card_dimensions(self) -> None:
        printables = importlib.import_module("src.admin.printables")

        width, height = printables.USER_CARD_SIZE

        self.assertAlmostEqual(85.6, width / mm)
        self.assertAlmostEqual(53.98, height / mm)

    def test_generate_all_product_labels_creates_complete_sheet(self) -> None:
        with operation_script_context() as context:
            generate_printables = importlib.import_module("tools.generate_printables")

            with (
                patch.object(
                    importlib.import_module("src.admin.printables"),
                    "PRINT_DIR",
                    context.print_dir,
                ),
                patch.object(generate_printables, "PRINT_DIR", context.print_dir),
            ):
                output_path = generate_printables.generate_all_product_labels()

            self.assertEqual(
                context.print_dir / "product_labels_all_products.pdf",
                output_path,
            )
            self.assertEqual(b"%PDF", output_path.read_bytes()[:4])

    def test_generate_product_copies_expands_selected_product(self) -> None:
        with operation_script_context() as context:
            generate_printables = importlib.import_module("tools.generate_printables")

            with (
                patch.object(
                    importlib.import_module("src.admin.printables"),
                    "PRINT_DIR",
                    context.print_dir,
                ),
                patch.object(generate_printables, "PRINT_DIR", context.print_dir),
            ):
                output_path = generate_printables.generate_selected_product_labels(
                    ["Milch=3"], start_position=23
                )

            self.assertEqual(
                context.print_dir / "product_labels_Milch_3x.pdf",
                output_path,
            )
            self.assertEqual(b"%PDF", output_path.read_bytes()[:4])

    def test_product_copy_syntax_rejects_invalid_count(self) -> None:
        generate_printables = importlib.import_module("tools.generate_printables")

        with self.assertRaisesRegex(ValueError, "NAME=COUNT"):
            generate_printables._parse_product_spec("Milch=0")

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
    "product_labels_calibration.pdf",
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
        patch.object(generate_printables, "PRINT_DIR", print_dir),
        redirect_stdout(output),
    ):
        generate_printables.main([])

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
