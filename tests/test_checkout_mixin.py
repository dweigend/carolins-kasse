"""Checkout scene behavior tests with isolated temp state."""

import importlib
from pathlib import Path
import tempfile
from types import ModuleType
import unittest

from tests.db_isolation import isolated_database_module


USER_CARD_ID = "2000000000015"


class FakeReceipt:
    """Minimal receipt double for checkout mixin tests."""

    def __init__(self) -> None:
        self.customer_name: str | None = None
        self.total: int | None = None
        self.new_balance: int | None = None
        self.cashier_name: str | None = None
        self.cashier_salary: int | None = None

    def show(
        self,
        customer_name: str,
        total: int,
        new_balance: int,
        cashier_name: str | None = None,
        cashier_salary: int = 0,
    ) -> None:
        self.customer_name = customer_name
        self.total = total
        self.new_balance = new_balance
        self.cashier_name = cashier_name
        self.cashier_salary = cashier_salary


def create_fake_checkout_scene(
    checkout_mixin: ModuleType,
    *,
    total: int,
    items: list[dict],
):
    """Create a minimal CheckoutMixin scene without pygame rendering."""

    class FakeCheckoutScene(checkout_mixin.CheckoutMixin):
        def __init__(self) -> None:
            self._checkout_mode = True
            self._checkout_receipt = FakeReceipt()
            self._insufficient_funds_popup = None
            self._total = total
            self._items = items
            self.completed = False
            self.messages: list[str] = []

        def _get_checkout_total(self) -> int:
            return self._total

        def _get_checkout_items(self) -> list[dict]:
            return self._items

        def _on_checkout_complete(self) -> None:
            self.completed = True

        def _show_message(
            self, text: str, _frames: int = 60, color: tuple = ()
        ) -> None:
            self.messages.append(text)

    return FakeCheckoutScene()


class CheckoutMixinTests(unittest.TestCase):
    def test_self_checkout_refreshes_current_runtime_user_balance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                database.add_user(
                    database.User(
                        card_id=USER_CARD_ID,
                        name="Carolin",
                        balance=9.0,
                    )
                )
                state = importlib.import_module("src.utils.state")
                checkout_mixin = importlib.import_module("src.scenes.checkout_mixin")
                user = database.get_user(USER_CARD_ID)
                if user is None:
                    raise AssertionError(f"Missing test user {USER_CARD_ID}")
                state.set_current_user(user)

                scene = create_fake_checkout_scene(
                    checkout_mixin,
                    total=4,
                    items=[
                        {
                            "barcode": "1000000000016",
                            "name": "Milch",
                            "price": 4,
                            "qty": 1,
                        }
                    ],
                )

                handled = scene._handle_checkout_barcode(USER_CARD_ID)

                current_user = state.get_current_user()
                persisted_user = database.get_user(USER_CARD_ID)
                transactions = database.get_user_transactions(USER_CARD_ID, limit=5)

            self.assertTrue(handled)
            self.assertTrue(scene.completed)
            if current_user is None:
                raise AssertionError("Expected current runtime user")
            if persisted_user is None:
                raise AssertionError(f"Missing persisted test user {USER_CARD_ID}")
            self.assertEqual(current_user.balance, 5.0)
            self.assertEqual(persisted_user.balance, 5.0)
            self.assertEqual(scene._checkout_receipt.new_balance, 5)
            self.assertEqual(scene._checkout_receipt.cashier_salary, 0)
            self.assertEqual(len(transactions), 1)


if __name__ == "__main__":
    unittest.main()
