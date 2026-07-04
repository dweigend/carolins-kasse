"""Direct tests for cashier feedback render-only components."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.components.balance_bar import BalanceBar, CompactBalanceBar
from src.components.checkout_receipt import CheckoutReceipt
from src.components.insufficient_funds_popup import InsufficientFundsPopup
from src.constants import (
    BALANCE_COLOR_HIGH,
    BALANCE_COLOR_LOW,
    BALANCE_COLOR_MED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class CashierFeedbackComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def setUp(self) -> None:
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def test_balance_bar_uses_threshold_colors(self) -> None:
        bar = BalanceBar(10, 20, max_value=50)

        bar.set_balance(9)
        self.assertEqual(bar._get_color(), BALANCE_COLOR_LOW)

        bar.set_balance(10)
        self.assertEqual(bar._get_color(), BALANCE_COLOR_MED)

        bar.set_balance(25)
        self.assertEqual(bar._get_color(), BALANCE_COLOR_HIGH)

    def test_balance_bar_fill_width_respects_text_space_and_maximum(self) -> None:
        bar = BalanceBar(10, 20, width=200, show_text=True, max_value=50)

        bar.set_balance(25)
        self.assertEqual(bar._get_fill_width(), 65)

        bar.set_balance(75)
        self.assertEqual(bar._get_fill_width(), 130)

    def test_balance_bar_renders_regular_and_compact_variants(self) -> None:
        bar = BalanceBar(10, 20, width=240, show_max=True, max_value=50)
        bar.set_balance(32)
        bar.set_milestone(40)

        compact_bar = CompactBalanceBar(10, 70)
        compact_bar.set_balance(8)

        bar.render(self.surface)
        compact_bar.render(self.surface)

    def test_checkout_receipt_show_update_and_auto_hide(self) -> None:
        receipt = CheckoutReceipt()

        with patch("pygame.time.get_ticks", return_value=1000):
            receipt.show("Carolin", total=7, new_balance=18, cashier_name="Annelie")

        self.assertTrue(receipt.is_visible())
        self.assertEqual(receipt._customer_name, "Carolin")
        self.assertEqual(receipt._total, 7)
        self.assertEqual(receipt._new_balance, 18)
        self.assertEqual(receipt._cashier_name, "Annelie")
        self.assertEqual(receipt._cashier_salary, 0)

        with patch("pygame.time.get_ticks", return_value=3999):
            receipt.update()
        self.assertTrue(receipt.is_visible())

        with patch("pygame.time.get_ticks", return_value=4000):
            receipt.update()
        self.assertFalse(receipt.is_visible())

    def test_checkout_receipt_render_smoke_visible_and_hidden(self) -> None:
        receipt = CheckoutReceipt()

        receipt.render(self.surface)

        with patch("pygame.time.get_ticks", return_value=200):
            receipt.show(
                "Annelie",
                total=4,
                new_balance=16,
                cashier_name="Carolin",
                cashier_salary=1,
            )

        receipt.render(self.surface)

        receipt.hide()
        receipt.render(self.surface)

    def test_insufficient_funds_popup_show_hide_and_key_event(self) -> None:
        popup = InsufficientFundsPopup()

        self.assertFalse(popup.handle_event(self._key_event()))

        popup.show(needed=12, available=5)
        self.assertTrue(popup.is_visible())
        self.assertEqual(popup._needed, 12)
        self.assertEqual(popup._available, 5)

        self.assertTrue(popup.handle_event(self._key_event()))
        self.assertFalse(popup.is_visible())

        popup.show(needed=12, available=5)
        popup.hide()
        self.assertFalse(popup.is_visible())

    def test_insufficient_funds_popup_mouse_event_consumes_and_hides(self) -> None:
        popup = InsufficientFundsPopup()
        popup.show(needed=15, available=2)

        handled = popup.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), "button": 1},
            )
        )

        self.assertTrue(handled)
        self.assertFalse(popup.is_visible())

    def test_insufficient_funds_popup_render_smoke_visible_and_hidden(self) -> None:
        popup = InsufficientFundsPopup()

        popup.render(self.surface)

        popup.show(needed=15, available=2)
        popup.render(self.surface)

        popup.hide()
        popup.render(self.surface)

    def _key_event(self) -> pygame.event.Event:
        return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})


if __name__ == "__main__":
    unittest.main()
