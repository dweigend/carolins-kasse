"""Scan/shopping scene for scanning products and managing the cart."""

import pygame

from src.components.button import Button
from src.components.product_display import ProductDisplay
from src.components.scrollable_cart import ScrollableCart
from src.constants import (
    SCREEN_HEIGHT,
    SUCCESS,
    WHITE,
)
from src.scenes.base import Scene
from src.scenes.checkout_mixin import CheckoutMixin
from src.scenes.mixins import MessageMixin
from src.utils import state
from src.utils.cart import Cart
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.database import get_product
from src.utils.fonts import body
from src.utils.input import InputManager, InputType
from src.utils.state import get_and_clear_selected_product

# Layout constants (inside shell content area)
CONTENT_TOP = 82
CONTENT_BOTTOM = 520
LEFT_PANEL_WIDTH = 360
RIGHT_PANEL_X = LEFT_PANEL_WIDTH + 18
CONTENT_RIGHT = 994
PAY_BUTTON_WIDTH = 210
PAY_BUTTON_HEIGHT = 68
PAY_BUTTON_RIGHT_PADDING = 26
PAY_BUTTON_BOTTOM_PADDING = 16


class ScanScene(CheckoutMixin, MessageMixin, Scene):
    """Shopping scene where products are scanned and added to cart."""

    def __init__(self) -> None:
        """Initialize scan scene."""
        self._input_manager = InputManager()
        self._cart = Cart()
        self._pay_button: Button | None = None
        self._product_display: ProductDisplay | None = None
        self._scrollable_cart: ScrollableCart | None = None

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        self._init_checkout_ui()

        # Pay button
        self._pay_button = Button(
            CONTENT_RIGHT - PAY_BUTTON_WIDTH - PAY_BUTTON_RIGHT_PADDING,
            CONTENT_BOTTOM - PAY_BUTTON_HEIGHT - PAY_BUTTON_BOTTOM_PADDING,
            PAY_BUTTON_WIDTH,
            PAY_BUTTON_HEIGHT,
            color=SUCCESS,
            on_click=self._handle_pay,
        )

        # Product display (left side)
        self._product_display = ProductDisplay(
            (LEFT_PANEL_WIDTH - ProductDisplay.WIDTH) // 2,
            CONTENT_TOP,
        )

        # Scrollable cart (right side)
        cart_width = CONTENT_RIGHT - RIGHT_PANEL_X
        cart_height = CONTENT_BOTTOM - CONTENT_TOP
        self._scrollable_cart = ScrollableCart(
            RIGHT_PANEL_X,
            CONTENT_TOP,
            cart_width,
            cart_height,
            self._cart,
            self._change_qty,
        )

        self._initialized = True

    # --- CheckoutMixin implementation ---

    def _get_checkout_total(self) -> int:
        """Return cart total."""
        return int(self._cart.total)

    def _get_checkout_items(self) -> list[dict]:
        """Return cart items for transaction record."""
        return [
            {
                "barcode": item.product.barcode,
                "name": item.product.name_de,
                "qty": item.quantity,
                "price": int(item.product.price),
            }
            for item in self._cart.items
        ]

    def _on_checkout_complete(self) -> None:
        """Clear cart after successful checkout."""
        self._cart.clear()
        if self._product_display:
            self._product_display.clear()
        if self._scrollable_cart:
            self._scrollable_cart.rebuild_rows()

    # --- Event handling ---

    def _handle_barcode(self, barcode: str) -> None:
        """Process a scanned barcode."""
        if self._checkout_mode:
            self._handle_checkout_barcode(barcode)
            return

        product = get_product(barcode)

        if product:
            self._cart.add(product)
            if self._product_display:
                self._product_display.set_product(product)
            if self._scrollable_cart:
                self._scrollable_cart.rebuild_rows()
        else:
            if barcode.startswith("200"):
                self._show_message("Das ist eine Benutzerkarte!")
            elif barcode.startswith("300"):
                self._show_message("Das ist ein Rezept!")
            else:
                self._show_message(f"Unbekannter Barcode: {barcode[:8]}...")

    def _handle_pay(self) -> None:
        """Handle pay button click."""
        if self._cart.is_empty:
            self._show_message("Warenkorb ist leer!")
            return
        self._enter_checkout_mode()

    def _change_qty(self, barcode: str, delta: int) -> None:
        """Change quantity of a cart item."""
        self._cart.update_quantity(barcode, delta)
        if self._scrollable_cart:
            self._scrollable_cart.rebuild_rows()

        if self._product_display and self._product_display.product:
            if self._product_display.product.barcode == barcode and delta < 0:
                remaining = [
                    i for i in self._cart.items if i.product.barcode == barcode
                ]
                if not remaining:
                    self._product_display.clear()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()

        if self._handle_checkout_event(event):
            return self._consume_next_scene()

        input_events = self._input_manager.process_event(event)
        for inp in input_events:
            if inp.type == InputType.BARCODE:
                self._handle_barcode(str(inp.value))

        if self._checkout_mode:
            return self._consume_next_scene()

        if self._pay_button and not self._cart.is_empty:
            self._pay_button.handle_event(event)

        if self._scrollable_cart:
            self._scrollable_cart.handle_event(event)

        return self._consume_next_scene()

    def update(self) -> None:
        """Update scene state."""
        state.check_time_bonus()
        self._update_checkout_ui()

        selected = get_and_clear_selected_product()
        if selected:
            self._cart.add(selected)
            if self._product_display:
                self._product_display.set_product(selected)
            if self._scrollable_cart:
                self._scrollable_cart.rebuild_rows()

        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the scan screen (no background fill — shell handles it)."""
        self._init_ui()

        # Left panel: Product display
        if self._product_display:
            self._product_display.render(screen)

        # Right panel: Scrollable cart
        if self._scrollable_cart:
            self._scrollable_cart.render(screen)

        # Pay button
        self._render_pay_button(screen)

        # Checkout overlays
        self._render_checkout_overlays(screen)

        # Feedback message
        msg_font = body()
        self._render_message(
            screen, msg_font, LEFT_PANEL_WIDTH // 2, SCREEN_HEIGHT - 60, center_x=True
        )

    def _render_pay_button(self, screen: pygame.Surface) -> None:
        """Render the pay button."""
        if not self._pay_button:
            return
        if self._cart.is_empty:
            return

        try:
            button_bg = get_raw_asset("ui/cashier/pay_button_enabled_bg")
            screen.blit(button_bg, self._pay_button.rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(screen, SUCCESS, self._pay_button.rect, border_radius=18)

        icon_center_x = self._pay_button.rect.x + 70
        try:
            register = get_asset("recipes/kasse", "M")
            register_rect = register.get_rect(
                center=(icon_center_x, self._pay_button.rect.centery)
            )
            screen.blit(register, register_rect)
        except FileNotFoundError:
            fallback_rect = pygame.Rect(0, 0, 54, 38)
            fallback_rect.center = (icon_center_x, self._pay_button.rect.centery)
            pygame.draw.rect(screen, WHITE, fallback_rect, width=4, border_radius=8)

        self._draw_pay_arrow(
            screen,
            self._pay_button.rect.right - 54,
            self._pay_button.rect.centery,
        )

    def _draw_pay_arrow(
        self, screen: pygame.Surface, center_x: int, center_y: int
    ) -> None:
        """Draw the checkout arrow without relying on font glyph support."""
        pygame.draw.line(
            screen,
            WHITE,
            (center_x - 24, center_y),
            (center_x + 18, center_y),
            9,
        )
        pygame.draw.polygon(
            screen,
            WHITE,
            [
                (center_x + 26, center_y),
                (center_x + 6, center_y - 18),
                (center_x + 6, center_y + 18),
            ],
        )
