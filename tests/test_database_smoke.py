"""Temporary database regression smoke tests."""

from contextlib import closing, redirect_stdout
import importlib
import io
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest

from tests.db_isolation import initialized_temporary_database, isolated_database_module


EXPECTED_SCHEMA_TABLES = {
    "balance_adjustments",
    "earnings",
    "products",
    "recipe_ingredients",
    "recipes",
    "sessions",
    "transactions",
    "users",
}


class DatabaseSmokeTests(unittest.TestCase):
    def test_database_reexports_models_for_import_compatibility(self) -> None:
        from src.utils import database, database_models

        exported_names = (
            "Product",
            "User",
            "Recipe",
            "RecipeIngredient",
            "Session",
            "Earning",
            "Transaction",
            "BalanceAdjustment",
            "CheckoutError",
            "CheckoutUserNotFoundError",
            "InsufficientFundsError",
            "CheckoutResult",
            "PRODUCT_COLUMNS",
            "USER_COLUMNS",
            "RECIPE_COLUMNS",
        )

        for exported_name in exported_names:
            with self.subTest(exported_name=exported_name):
                self.assertIs(
                    getattr(database, exported_name),
                    getattr(database_models, exported_name),
                )

    def test_product_public_api_keeps_query_and_commit_behavior(self) -> None:
        with initialized_temporary_database() as database:
            scanned_product = database.Product(
                barcode="1000000000016",
                name="milk",
                name_de="Milch",
                price=1.5,
                category="food",
                image_path="assets/milk.png",
                has_barcode=True,
            )
            picker_product = database.Product(
                barcode="1000000000023",
                name="apple",
                name_de="Apfel",
                price=0.5,
                category="food",
                has_barcode=False,
            )

            database.add_product(scanned_product)
            database.add_product(picker_product)

            database.update_product_admin_fields(
                scanned_product.barcode,
                name_de="Frische Milch",
                price=1.75,
                active=True,
            )
            updated_product = database.get_product(scanned_product.barcode)
            picker_products = database.get_picker_products()
            food_products = database.get_products_by_category("food")

            database.delete_product(scanned_product.barcode)
            deleted_product = database.get_product(scanned_product.barcode)

        self.assertIsNotNone(updated_product)
        self.assertEqual(updated_product.name_de, "Frische Milch")
        self.assertEqual(updated_product.price, 1.75)
        self.assertEqual(picker_products, {"food": [picker_product]})
        self.assertEqual(
            [product.barcode for product in food_products],
            [picker_product.barcode, scanned_product.barcode],
        )
        self.assertIsNone(deleted_product)

    def test_init_database_creates_schema_on_empty_temp_db(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()

            self.assertTrue(db_path.exists())
            with closing(sqlite3.connect(db_path)) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

            self.assertTrue(EXPECTED_SCHEMA_TABLES.issubset(table_names))

    def test_seed_database_refuses_existing_temp_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                database.add_user(
                    database.User(
                        card_id="2000000000992",
                        name="Existing",
                        balance=42.0,
                    )
                )

                seed_database = importlib.import_module("tools.seed_database")
                previous_argv = sys.argv
                sys.argv = ["seed_database.py"]
                try:
                    with redirect_stdout(io.StringIO()):
                        exit_code = seed_database.main()
                finally:
                    sys.argv = previous_argv

                self.assertEqual(exit_code, 1)
                user = database.get_user("2000000000992")

            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 42.0)

    def test_process_checkout_updates_balance_and_records_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                database.add_user(
                    database.User(
                        card_id="2000000000015",
                        name="Carolin",
                        balance=10.0,
                    )
                )
                items = [
                    {
                        "barcode": "1000000000016",
                        "name": "Milch",
                        "price": 1,
                        "qty": 3,
                    }
                ]

                transaction_id = database.process_checkout(
                    "2000000000015",
                    total=3,
                    items=items,
                )

                user = database.get_user("2000000000015")
                transactions = database.get_user_transactions("2000000000015", limit=5)

            self.assertGreater(transaction_id.transaction_id, 0)
            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 7.0)
            self.assertEqual(transaction_id.user.balance, 7.0)
            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0].total, 3)
            self.assertEqual(json.loads(transactions[0].items_json), items)

    def test_foreign_key_enforcement_is_enabled_per_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()

                with database.get_db() as conn:
                    enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
                    with self.assertRaises(sqlite3.IntegrityError):
                        conn.execute(
                            """
                            INSERT INTO transactions (user_card_id, total, items_json)
                            VALUES (?, ?, ?)
                            """,
                            ("2000000000992", 1, "[]"),
                        )

            self.assertEqual(enabled, 1)

    def test_process_checkout_rejects_insufficient_balance_without_transaction(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                database.add_user(
                    database.User(
                        card_id="2000000000015",
                        name="Carolin",
                        balance=2.0,
                    )
                )

                with self.assertRaises(database.InsufficientFundsError):
                    database.process_checkout(
                        "2000000000015",
                        total=3,
                        items=[],
                    )

                user = database.get_user("2000000000015")
                transactions = database.get_user_transactions("2000000000015", limit=5)

            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 2.0)
            self.assertEqual(transactions, [])

    def test_process_checkout_rejects_unknown_card_without_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()

                with self.assertRaises(database.CheckoutUserNotFoundError):
                    database.process_checkout(
                        "2000000000992",
                        total=3,
                        items=[],
                    )

                transactions = database.get_user_transactions("2000000000992", limit=5)

            self.assertEqual(transactions, [])


if __name__ == "__main__":
    unittest.main()
