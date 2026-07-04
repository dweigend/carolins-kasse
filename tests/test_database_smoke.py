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

from tests.db_isolation import isolated_database_module


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
                    new_balance=7.0,
                    total=3,
                    items=items,
                )

                user = database.get_user("2000000000015")
                transactions = database.get_user_transactions("2000000000015", limit=5)

            self.assertGreater(transaction_id, 0)
            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 7.0)
            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0].total, 3)
            self.assertEqual(json.loads(transactions[0].items_json), items)


if __name__ == "__main__":
    unittest.main()
