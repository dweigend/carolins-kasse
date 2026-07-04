"""Temporary database regression smoke tests."""

from collections.abc import Iterator
from contextlib import closing, contextmanager, redirect_stdout
import importlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType
import unittest
from unittest.mock import patch

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


LOCAL_DAY_TEST_TIMEZONE = "UTC-2"
CHECKOUT_USER_CARD_ID = "2000000000015"
CHECKOUT_USER_NAME = "Carolin"
CHECKOUT_STARTING_BALANCE = 10.0
CHECKOUT_TOTAL = 3
CHECKOUT_ITEM_BARCODE = "1000000000016"
CHECKOUT_ITEM_NAME = "Milch"
CHECKOUT_ITEM_PRICE = 1
CHECKOUT_ITEM_QUANTITY = 3


@contextmanager
def temporary_timezone(timezone_name: str) -> Iterator[None]:
    previous_timezone = os.environ.get("TZ")
    os.environ["TZ"] = timezone_name
    time.tzset()
    try:
        yield
    finally:
        if previous_timezone is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous_timezone
        time.tzset()


def create_checkout_items() -> list[dict]:
    return [
        {
            "barcode": CHECKOUT_ITEM_BARCODE,
            "name": CHECKOUT_ITEM_NAME,
            "price": CHECKOUT_ITEM_PRICE,
            "qty": CHECKOUT_ITEM_QUANTITY,
        }
    ]


def initialize_checkout_user(database: ModuleType) -> None:
    database.init_database()
    database.add_user(
        database.User(
            card_id=CHECKOUT_USER_CARD_ID,
            name=CHECKOUT_USER_NAME,
            balance=CHECKOUT_STARTING_BALANCE,
        )
    )


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

    def test_recipe_public_api_keeps_query_and_commit_behavior(self) -> None:
        with initialized_temporary_database() as database:
            recipe = database.Recipe(
                barcode="3000000000014",
                name="Waffeln",
                image_path="assets/recipes/waffeln.png",
            )
            flour = database.Product(
                barcode="1000000000016",
                name="flour",
                name_de="Mehl",
                price=1.0,
                category="zutaten",
                active=False,
            )
            milk = database.Product(
                barcode="1000000000023",
                name="milk",
                name_de="Milch",
                price=1.5,
                category="zutaten",
            )

            database.add_product(milk)
            database.add_product(flour)
            database.add_recipe(recipe)
            database.add_recipe_ingredient(
                database.RecipeIngredient(recipe.barcode, milk.barcode, quantity=2)
            )
            database.add_recipe_ingredient(
                database.RecipeIngredient(recipe.barcode, flour.barcode, quantity=3)
            )

            ingredients = database.get_recipe_ingredients(recipe.barcode)

            database.update_recipe_admin_fields(
                recipe.barcode,
                name="Sonntagswaffeln",
                active=False,
            )
            inactive_lookup = database.get_recipe(recipe.barcode)
            all_recipes = database.get_all_recipes(include_inactive=True)

            database.clear_recipe_ingredients(recipe.barcode)
            cleared_ingredients = database.get_recipe_ingredients(recipe.barcode)

            database.delete_recipe(recipe.barcode)
            deleted_recipes = database.get_all_recipes(include_inactive=True)

        self.assertEqual(
            [(product.barcode, quantity) for product, quantity in ingredients],
            [(flour.barcode, 3), (milk.barcode, 2)],
        )
        self.assertFalse(ingredients[0][0].active)
        self.assertIsNone(inactive_lookup)
        self.assertEqual([recipe.name for recipe in all_recipes], ["Sonntagswaffeln"])
        self.assertEqual(cleared_ingredients, [])
        self.assertEqual(deleted_recipes, [])

    def test_user_public_api_keeps_query_and_commit_behavior(self) -> None:
        with initialized_temporary_database() as database:
            active_user = database.User(
                card_id="2000000000015",
                name="Carolin",
                balance=10.0,
                color="pink",
                difficulty=1,
            )
            inactive_user = database.User(
                card_id="2000000000022",
                name="Annelie",
                balance=8.0,
                color="blue",
                difficulty=2,
                active=False,
            )

            database.add_user(active_user)
            database.add_user(inactive_user)

            visible_users = database.get_all_users()
            all_users = database.get_all_users(include_inactive=True)
            inactive_lookup = database.get_user(inactive_user.card_id)
            inactive_lookup_with_flag = database.get_user(
                inactive_user.card_id,
                include_inactive=True,
            )

            database.update_user_admin_fields(
                active_user.card_id,
                name="Carolin Update",
                difficulty=3,
                active=False,
            )
            hidden_after_update = database.get_user(active_user.card_id)
            updated_with_flag = database.get_user(
                active_user.card_id,
                include_inactive=True,
            )

            database.delete_user(inactive_user.card_id)
            remaining_users = database.get_all_users(include_inactive=True)

        self.assertEqual(
            [user.card_id for user in visible_users], [active_user.card_id]
        )
        self.assertEqual(
            [user.card_id for user in all_users],
            [inactive_user.card_id, active_user.card_id],
        )
        self.assertIsNone(inactive_lookup)
        self.assertEqual(inactive_lookup_with_flag, inactive_user)
        self.assertIsNone(hidden_after_update)
        self.assertIsNotNone(updated_with_flag)
        self.assertEqual(updated_with_flag.name, "Carolin Update")
        self.assertEqual(updated_with_flag.difficulty, 3)
        self.assertFalse(updated_with_flag.active)
        self.assertEqual(
            [user.card_id for user in remaining_users], [active_user.card_id]
        )

    def test_balance_adjustment_public_api_keeps_query_behavior(self) -> None:
        with initialized_temporary_database() as database:
            user = database.User(
                card_id="2000000000015",
                name="Carolin",
                balance=10.0,
            )

            database.add_user(user)
            database.update_user_balance(user.card_id, 12.5, note="Pocket money")
            adjustments = database.get_recent_balance_adjustments()
            updated_user = database.get_user(user.card_id)

        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.balance, 12.5)
        self.assertEqual(len(adjustments), 1)
        self.assertEqual(adjustments[0].user_card_id, user.card_id)
        self.assertEqual(adjustments[0].user_name, user.name)
        self.assertEqual(adjustments[0].old_balance, 10.0)
        self.assertEqual(adjustments[0].new_balance, 12.5)
        self.assertEqual(adjustments[0].delta, 2.5)
        self.assertEqual(adjustments[0].note, "Pocket money")

    def test_session_public_api_keeps_query_and_commit_behavior(self) -> None:
        with initialized_temporary_database() as database:
            user = database.User(
                card_id="2000000000015",
                name="Carolin",
                balance=10.0,
            )

            database.add_user(user)
            session_id = database.start_session(user.card_id)
            started_session = database.get_session(session_id)

            database.end_session(session_id)
            ended_session = database.get_session(session_id)

        self.assertIsNotNone(started_session)
        self.assertEqual(started_session.id, session_id)
        self.assertEqual(started_session.user_card_id, user.card_id)
        self.assertIsNone(started_session.ended_at)
        self.assertIsNotNone(ended_session)
        self.assertEqual(ended_session.id, session_id)
        self.assertEqual(ended_session.user_card_id, user.card_id)
        self.assertIsNotNone(ended_session.ended_at)

    def test_earning_public_api_keeps_query_behavior(self) -> None:
        with initialized_temporary_database() as database:
            user = database.User(
                card_id="2000000000015",
                name="Carolin",
                balance=10.0,
            )

            database.add_user(user)
            session_id = database.start_session(user.card_id)
            database.add_earning(session_id, user.card_id, "math", 3, "Aufgabe")
            database.add_earning(session_id, user.card_id, "recipe", 5, "Rezept")

            session_earnings = database.get_session_earnings(session_id)
            today_earnings = database.get_today_earnings(user.card_id)
            today_summary = database.get_today_earnings_summary(user.card_id)
            user_after_earnings = database.get_user(user.card_id)

        self.assertCountEqual(
            [(earning.source, earning.amount) for earning in session_earnings],
            [("math", 3), ("recipe", 5)],
        )
        self.assertCountEqual(
            [(earning.source, earning.amount) for earning in today_earnings],
            [("math", 3), ("recipe", 5)],
        )
        self.assertEqual(today_summary, {"math": 3, "recipe": 5})
        self.assertIsNotNone(user_after_earnings)
        self.assertEqual(user_after_earnings.balance, 18.0)

    def test_today_earnings_use_local_day_for_utc_timestamps(self) -> None:
        if not hasattr(time, "tzset"):
            self.skipTest("time.tzset is required for localtime regression coverage")

        with temporary_timezone(LOCAL_DAY_TEST_TIMEZONE):
            with initialized_temporary_database() as database:
                user = database.User(
                    card_id="2000000000015",
                    name="Carolin",
                    balance=10.0,
                )

                database.add_user(user)
                session_id = database.start_session(user.card_id)
                database.add_earning(session_id, user.card_id, "math", 3, "Aufgabe")

                with database.get_db() as conn:
                    conn.execute(
                        """
                        UPDATE earnings
                        SET earned_at = datetime(
                            date('now', 'localtime'),
                            '+30 minutes',
                            'utc'
                        )
                        """
                    )
                    date_row = conn.execute(
                        """
                        SELECT
                            date(earned_at),
                            date(earned_at, 'localtime'),
                            date('now', 'localtime')
                        FROM earnings
                        """
                    ).fetchone()
                    if date_row is None:
                        raise AssertionError("Missing test earning")
                    stored_utc_date, local_earning_date, local_today = date_row
                    conn.commit()

                today_earnings = database.get_today_earnings(user.card_id)
                today_summary = database.get_today_earnings_summary(user.card_id)

        self.assertNotEqual(stored_utc_date, local_today)
        self.assertEqual(local_earning_date, local_today)
        self.assertEqual(
            [(earning.source, earning.amount) for earning in today_earnings],
            [("math", 3)],
        )
        self.assertEqual(today_summary, {"math": 3})

    def test_transaction_public_api_keeps_query_behavior(self) -> None:
        with initialized_temporary_database() as database:
            user = database.User(
                card_id="2000000000015",
                name="Carolin",
                balance=10.0,
            )
            items = [{"barcode": "1000000000016", "name": "Milch", "price": 2}]

            database.add_user(user)
            transaction_id = database.save_transaction(user.card_id, 2, items)
            transactions = database.get_user_transactions(user.card_id)

        self.assertGreater(transaction_id, 0)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].id, transaction_id)
        self.assertEqual(transactions[0].user_card_id, user.card_id)
        self.assertEqual(transactions[0].total, 2)
        self.assertEqual(json.loads(transactions[0].items_json), items)

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

    def test_init_database_adds_active_to_legacy_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("""
                    CREATE TABLE products (
                        barcode TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        name_de TEXT NOT NULL,
                        price REAL NOT NULL,
                        category TEXT NOT NULL,
                        image_path TEXT,
                        has_barcode BOOLEAN DEFAULT 1
                    )
                """)
                conn.execute("""
                    CREATE TABLE users (
                        card_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        balance REAL DEFAULT 10.0,
                        color TEXT,
                        difficulty INTEGER DEFAULT 1,
                        is_admin BOOLEAN DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE recipes (
                        barcode TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        image_path TEXT
                    )
                """)
                conn.commit()

            with isolated_database_module(db_path) as database:
                database.init_database()

            with closing(sqlite3.connect(db_path)) as conn:
                legacy_tables = ("products", "users", "recipes")
                columns_by_table = {
                    table_name: {
                        row[1]
                        for row in conn.execute(f"PRAGMA table_info({table_name})")
                    }
                    for table_name in legacy_tables
                }

            for table_name, column_names in columns_by_table.items():
                with self.subTest(table_name=table_name):
                    self.assertIn("active", column_names)

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
                initialize_checkout_user(database)
                items = create_checkout_items()

                transaction_id = database.process_checkout(
                    CHECKOUT_USER_CARD_ID,
                    total=CHECKOUT_TOTAL,
                    items=items,
                )

                user = database.get_user(CHECKOUT_USER_CARD_ID)
                transactions = database.get_user_transactions(
                    CHECKOUT_USER_CARD_ID,
                    limit=5,
                )

            self.assertGreater(transaction_id.transaction_id, 0)
            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 7.0)
            self.assertEqual(transaction_id.user.balance, 7.0)
            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0].total, 3)
            self.assertEqual(json.loads(transactions[0].items_json), items)

    def test_process_checkout_rolls_back_when_transaction_insert_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                initialize_checkout_user(database)
                items = create_checkout_items()
                observed_balance: float | None = None

                def fail_after_balance_update(
                    conn: sqlite3.Connection,
                    user_card_id: str,
                    _total: int,
                    _items: list[dict],
                ) -> int:
                    nonlocal observed_balance
                    row = conn.execute(
                        "SELECT balance FROM users WHERE card_id = ?",
                        (user_card_id,),
                    ).fetchone()
                    if row is None:
                        raise AssertionError(f"Missing test user {user_card_id}")
                    observed_balance = row[0]
                    raise RuntimeError("simulated transaction insert failure")

                with (
                    patch.object(
                        database.database_transactions,
                        "save_transaction",
                        side_effect=fail_after_balance_update,
                    ),
                    self.assertRaisesRegex(RuntimeError, "simulated transaction"),
                ):
                    database.process_checkout(
                        CHECKOUT_USER_CARD_ID,
                        total=CHECKOUT_TOTAL,
                        items=items,
                    )

                user = database.get_user(CHECKOUT_USER_CARD_ID)
                transactions = database.get_user_transactions(
                    CHECKOUT_USER_CARD_ID,
                    limit=5,
                )

            self.assertEqual(observed_balance, 7.0)
            self.assertIsNotNone(user)
            self.assertEqual(user.balance, 10.0)
            self.assertEqual(transactions, [])

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
