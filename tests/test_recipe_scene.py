"""Recipe scene regression tests with isolated temp databases."""

from collections.abc import Iterator
from contextlib import contextmanager
import importlib
import os
from types import ModuleType
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.constants import EARNING_RECIPE
from tests.db_isolation import initialized_temporary_database


RECIPE_BARCODE = "3000000000014"
PRODUCT_BARCODE = "1000000000016"
INACTIVE_PRODUCT_BARCODE = "1000000000023"
USER_CARD_ID = "2000000000015"


class RecipeSceneTests(unittest.TestCase):
    def test_quantity_two_requires_two_product_scans(self) -> None:
        with initialized_temporary_database() as database:
            add_product(database, barcode=PRODUCT_BARCODE, name_de="Milch")
            add_recipe(database, [(PRODUCT_BARCODE, 2)])

            scene = create_initialized_recipe_scene()
            loaded = scene._load_recipe(RECIPE_BARCODE)

            scene._handle_barcode(PRODUCT_BARCODE)

            self.assertTrue(loaded)
            self.assertEqual(scene._scanned_quantities, {PRODUCT_BARCODE: 1})
            self.assertFalse(scene._complete)
            self.assertFalse(scene._checklist_items[0].checked)
            self.assertEqual(scene._scanned_ingredient_count(), 1)
            self.assertEqual(scene._required_ingredient_count(), 2)
            self.assertEqual(scene._get_checkout_total(), 4)

            scene._handle_barcode(PRODUCT_BARCODE)

            self.assertEqual(scene._scanned_quantities, {PRODUCT_BARCODE: 2})
            self.assertTrue(scene._complete)
            self.assertTrue(scene._checklist_items[0].checked)

    def test_inactive_ingredient_does_not_block_completion(self) -> None:
        with initialized_temporary_database() as database:
            add_product(
                database,
                barcode=PRODUCT_BARCODE,
                name_de="Milch",
                price=2.0,
            )
            add_product(
                database,
                barcode=INACTIVE_PRODUCT_BARCODE,
                name_de="Altes Mehl",
                price=5.0,
                active=False,
            )
            add_recipe(
                database,
                [(PRODUCT_BARCODE, 1), (INACTIVE_PRODUCT_BARCODE, 3)],
            )

            scene = create_initialized_recipe_scene()
            loaded = scene._load_recipe(RECIPE_BARCODE)

            scene._handle_barcode(PRODUCT_BARCODE)

            self.assertTrue(loaded)
            self.assertEqual(
                [product.barcode for product, _ in scene._ingredients],
                [PRODUCT_BARCODE],
            )
            self.assertTrue(scene._complete)
            self.assertEqual(scene._get_checkout_total(), 2)

    def test_recipe_bonus_is_awarded_after_successful_checkout_once(self) -> None:
        with (
            initialized_temporary_database() as database,
            active_recipe_session(database, balance=10.0) as session_id,
        ):
            add_product(database, barcode=PRODUCT_BARCODE, name_de="Milch", price=3)
            add_recipe(database, [(PRODUCT_BARCODE, 1)])

            scene = create_initialized_recipe_scene()
            scene._load_recipe(RECIPE_BARCODE)
            scene._handle_barcode(PRODUCT_BARCODE)

            self.assertTrue(scene._complete)
            self.assertEqual(database.get_session_earnings(session_id), [])

            scene._handle_pay()
            handled = scene._handle_checkout_barcode(USER_CARD_ID)

            earnings = database.get_session_earnings(session_id)
            recipe_earnings = [
                earning for earning in earnings if earning.source == "recipe"
            ]
            transactions = database.get_user_transactions(USER_CARD_ID, limit=5)
            user_after_checkout = database.get_user(USER_CARD_ID)

            scene._on_checkout_complete()
            earnings_after_repeated_callback = database.get_session_earnings(session_id)

        self.assertTrue(handled)
        self.assertEqual(len(recipe_earnings), 1)
        self.assertEqual(recipe_earnings[0].amount, EARNING_RECIPE)
        self.assertEqual(len(earnings_after_repeated_callback), len(earnings))
        self.assertEqual(len(transactions), 1)
        self.assertIsNotNone(user_after_checkout)
        self.assertEqual(user_after_checkout.balance, 15.0)

    def test_recipe_bonus_is_not_awarded_when_checkout_fails(self) -> None:
        with (
            initialized_temporary_database() as database,
            active_recipe_session(database, balance=1.0) as session_id,
        ):
            add_product(database, barcode=PRODUCT_BARCODE, name_de="Milch", price=3)
            add_recipe(database, [(PRODUCT_BARCODE, 1)])

            scene = create_initialized_recipe_scene()
            scene._load_recipe(RECIPE_BARCODE)
            scene._handle_barcode(PRODUCT_BARCODE)
            scene._handle_pay()

            handled = scene._handle_checkout_barcode(USER_CARD_ID)

            earnings = database.get_session_earnings(session_id)
            transactions = database.get_user_transactions(USER_CARD_ID, limit=5)
            user_after_checkout = database.get_user(USER_CARD_ID)

        self.assertTrue(handled)
        self.assertEqual(earnings, [])
        self.assertEqual(transactions, [])
        self.assertIsNotNone(user_after_checkout)
        self.assertEqual(user_after_checkout.balance, 1.0)


def create_recipe_scene():
    """Create a RecipeScene bound to the currently isolated database module."""
    recipe_module = importlib.import_module("src.scenes.recipe")
    return recipe_module.RecipeScene()


def create_initialized_recipe_scene():
    """Create a RecipeScene with checkout state initialized for direct testing."""
    scene = create_recipe_scene()
    scene._init_ui()
    scene._checkout_receipt = None
    scene._insufficient_funds_popup = None
    return scene


def add_product(
    database: ModuleType,
    *,
    barcode: str,
    name_de: str,
    price: float = 2.0,
    active: bool = True,
) -> None:
    """Add a product fixture."""
    database.add_product(
        database.Product(
            barcode=barcode,
            name=name_de.lower().replace(" ", "_"),
            name_de=name_de,
            price=price,
            category="zutaten",
            active=active,
        )
    )


def add_recipe(database: ModuleType, ingredients: list[tuple[str, int]]) -> None:
    """Add a recipe fixture with ingredient quantities."""
    database.add_recipe(database.Recipe(RECIPE_BARCODE, "Waffeln"))
    for product_barcode, quantity in ingredients:
        database.add_recipe_ingredient(
            database.RecipeIngredient(
                recipe_barcode=RECIPE_BARCODE,
                product_barcode=product_barcode,
                quantity=quantity,
            )
        )


def add_user(database: ModuleType, *, balance: float):
    """Add and return a user fixture."""
    user = database.User(
        card_id=USER_CARD_ID,
        name="Carolin",
        balance=balance,
    )
    database.add_user(user)
    return user


@contextmanager
def active_recipe_session(database: ModuleType, *, balance: float) -> Iterator[int]:
    """Start a recipe checkout session and always log it out."""
    user = add_user(database, balance=balance)
    state = importlib.import_module("src.utils.state")
    session_id = state.start_session(user)
    try:
        yield session_id
    finally:
        state.logout()


if __name__ == "__main__":
    unittest.main()
