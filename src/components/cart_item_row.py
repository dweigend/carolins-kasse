"""Cart item row component for displaying items in the shopping cart."""

from collections.abc import Callable

import pygame

from src.components.button import Button
from src.utils.assets import get as get_asset
from src.utils.cart import CartItem
from src.utils.fonts import custom


class CartItemRow:
    """A row displaying a cart item with quantity controls.

    Layout: [Image] Name    ×Qty  Subtotal  [-][+]
    """

    # Layout constants
    WIDTH = 400
    HEIGHT = 50
    IMAGE_SIZE = 30  # S size
    BUTTON_SIZE = 30
    PADDING = 8

    # Colors
    BG_COLOR = (250, 250, 252)
    BG_COLOR_ALT = (245, 245, 247)
    NAME_COLOR = (30, 30, 30)
    QTY_COLOR = (100, 100, 100)
    PRICE_COLOR = (59, 130, 246)
    BUTTON_COLOR = (220, 220, 225)
    BUTTON_HOVER_COLOR = (200, 200, 205)

    def __init__(
        self,
        x: int,
        y: int,
        item: CartItem,
        *,
        on_increase: Callable[[], None] | None = None,
        on_decrease: Callable[[], None] | None = None,
        alternate: bool = False,
    ) -> None:
        """Create a cart item row.

        Args:
            x: X position
            y: Y position
            item: CartItem to display
            on_increase: Callback for + button
            on_decrease: Callback for - button
            alternate: Use alternate background color
        """
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.item = item
        self._alternate = alternate

        # Create +/- buttons
        btn_y = y + (self.HEIGHT - self.BUTTON_SIZE) // 2
        minus_x = x + self.WIDTH - 2 * self.BUTTON_SIZE - self.PADDING
        plus_x = x + self.WIDTH - self.BUTTON_SIZE

        self._minus_btn = Button(
            minus_x,
            btn_y,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE,
            color=self.BUTTON_COLOR,
            on_click=on_decrease,
        )
        self._plus_btn = Button(
            plus_x,
            btn_y,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE,
            color=self.BUTTON_COLOR,
            on_click=on_increase,
        )

    def update_position(self, y: int) -> None:
        """Update row Y position (for scrolling/reordering).

        Args:
            y: New Y position
        """
        self.rect.y = y
        btn_y = y + (self.HEIGHT - self.BUTTON_SIZE) // 2
        self._minus_btn.rect.y = btn_y
        self._plus_btn.rect.y = btn_y

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for buttons.

        Args:
            event: pygame event

        Returns:
            True if a button was clicked
        """
        minus_clicked = self._minus_btn.handle_event(event)
        plus_clicked = self._plus_btn.handle_event(event)
        return minus_clicked or plus_clicked

    def render(self, surface: pygame.Surface) -> None:
        """Draw the cart item row.

        Args:
            surface: Surface to draw on
        """
        font = custom(24)
        small_font = custom(20)

        # Background
        bg_color = self.BG_COLOR_ALT if self._alternate else self.BG_COLOR
        pygame.draw.rect(surface, bg_color, self.rect)

        # Product image
        image_x = self.rect.x + self.PADDING
        image_y = self.rect.y + (self.HEIGHT - self.IMAGE_SIZE) // 2

        try:
            if self.item.product.image_path:
                image = get_asset(f"products/{self.item.product.image_path}", "S")
                surface.blit(image, (image_x, image_y))
        except FileNotFoundError:
            # Placeholder
            pygame.draw.rect(
                surface,
                (220, 220, 220),
                (image_x, image_y, self.IMAGE_SIZE, self.IMAGE_SIZE),
                border_radius=4,
            )

        # Product name (truncate if too long)
        name = self.item.product.name_de
        if len(name) > 15:
            name = name[:14] + "…"
        name_text = font.render(name, True, self.NAME_COLOR)
        name_x = image_x + self.IMAGE_SIZE + self.PADDING
        name_y = self.rect.y + (self.HEIGHT - name_text.get_height()) // 2
        surface.blit(name_text, (name_x, name_y))

        # Quantity
        qty_text = small_font.render(f"×{self.item.quantity}", True, self.QTY_COLOR)
        qty_x = self.rect.x + 180
        qty_y = self.rect.y + (self.HEIGHT - qty_text.get_height()) // 2
        surface.blit(qty_text, (qty_x, qty_y))

        # Subtotal
        subtotal_str = f"{int(self.item.subtotal)}T"
        subtotal_text = font.render(subtotal_str, True, self.PRICE_COLOR)
        subtotal_x = self.rect.x + 230
        subtotal_y = self.rect.y + (self.HEIGHT - subtotal_text.get_height()) // 2
        surface.blit(subtotal_text, (subtotal_x, subtotal_y))

        # +/- buttons
        self._render_button(surface, self._minus_btn, "−")
        self._render_button(surface, self._plus_btn, "+")

    def _render_button(
        self, surface: pygame.Surface, button: Button, symbol: str
    ) -> None:
        """Render a button with a symbol."""
        # Button background
        pygame.draw.rect(
            surface, button.color or self.BUTTON_COLOR, button.rect, border_radius=6
        )

        # Symbol
        font = custom(24)
        symbol_text = font.render(symbol, True, (60, 60, 60))
        symbol_rect = symbol_text.get_rect(center=button.rect.center)
        surface.blit(symbol_text, symbol_rect)
