"""Direct regression tests for the scrollable cart component."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.components.scrollable_cart import ScrollableCart
from src.utils.cart import Cart
from src.utils.database import Product


class ScrollableCartComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def test_scroll_methods_keep_offset_inside_bounds(self) -> None:
        component, _ = self._build_component(item_count=6)

        component.scroll_down()
        component.scroll_down()
        component.scroll_down()

        self.assertEqual(component._scroll_offset, 2)

        component.scroll_up()
        component.scroll_up()
        component.scroll_up()

        self.assertEqual(component._scroll_offset, 0)

    def test_mousewheel_scrolls_when_pointer_is_inside_cart(self) -> None:
        component, _ = self._build_component(item_count=6)

        with patch("pygame.mouse.get_pos", return_value=component.rect.center):
            handled = component.handle_event(self._wheel_event(-1))

        self.assertTrue(handled)
        self.assertEqual(component._scroll_offset, 1)

    def test_mousewheel_outside_cart_is_ignored(self) -> None:
        component, _ = self._build_component(item_count=6)
        outside_position = (component.rect.right + 20, component.rect.bottom + 20)

        with patch("pygame.mouse.get_pos", return_value=outside_position):
            handled = component.handle_event(self._wheel_event(-1))

        self.assertFalse(handled)
        self.assertEqual(component._scroll_offset, 0)

    def test_visible_row_event_triggers_quantity_callback(self) -> None:
        component, changes = self._build_component(item_count=5)
        plus_button_center = component._rows[1]._plus_btn.rect.center

        down_handled, up_handled = self._click(component, plus_button_center)

        self.assertFalse(down_handled)
        self.assertTrue(up_handled)
        self.assertEqual(changes, [("1000000000011", 1)])

    def test_non_visible_row_event_does_not_trigger_quantity_callback(self) -> None:
        component, changes = self._build_component(item_count=5)
        plus_button_center = component._rows[4]._plus_btn.rect.center

        down_handled, up_handled = self._click(component, plus_button_center)

        self.assertFalse(down_handled)
        self.assertFalse(up_handled)
        self.assertEqual(changes, [])

    def _build_component(
        self,
        *,
        item_count: int,
    ) -> tuple[ScrollableCart, list[tuple[str, int]]]:
        cart = Cart()
        for index in range(item_count):
            cart.add(self._product(index))

        changes: list[tuple[str, int]] = []
        component = ScrollableCart(
            10,
            20,
            420,
            380,
            cart,
            on_quantity_change=lambda barcode, delta: changes.append((barcode, delta)),
        )
        component.rebuild_rows()
        return component, changes

    def _product(self, index: int) -> Product:
        return Product(
            barcode=f"10000000000{index}1",
            name=f"product-{index}",
            name_de=f"Produkt {index}",
            price=1.0,
            category="test",
        )

    def _wheel_event(self, y: int) -> pygame.event.Event:
        return pygame.event.Event(pygame.MOUSEWHEEL, {"y": y})

    def _click(
        self,
        component: ScrollableCart,
        position: tuple[int, int],
    ) -> tuple[bool, bool]:
        down_handled = component.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": position, "button": 1},
            )
        )
        up_handled = component.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {"pos": position, "button": 1},
            )
        )
        return down_handled, up_handled


if __name__ == "__main__":
    unittest.main()
