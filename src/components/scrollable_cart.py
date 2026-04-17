"""Scrollable cart component for displaying shopping cart items."""

from collections.abc import Callable

import pygame

from src.components.button import Button
from src.components.cart_item_row import CartItemRow
from src.constants import BG_CARD, TEXT_MUTED, TEXT_PRIMARY
from src.utils.cart import Cart
from src.utils.fonts import body, caption


class ScrollableCart:
    """Scrollable shopping cart with navigation arrows.

    Displays cart items with scroll functionality when items exceed
    the visible area. Shows up/down arrows for navigation.
    """

    VISIBLE_ITEMS = 5
    HEADER_HEIGHT = 40
    FOOTER_HEIGHT = 80  # Space for total and pay button
    ARROW_SIZE = 30
    ARROW_MARGIN = 5

    # Colors
    ARROW_COLOR = (180, 180, 185)
    ARROW_DISABLED_COLOR = (220, 220, 225)
    ARROW_TEXT_COLOR = (80, 80, 80)

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        cart: Cart,
        on_quantity_change: Callable[[str, int], None],
    ) -> None:
        """Create a scrollable cart.

        Args:
            x: X position
            y: Y position
            width: Panel width
            height: Panel height
            cart: Cart instance to display
            on_quantity_change: Callback(barcode, delta) when quantity changes
        """
        self.rect = pygame.Rect(x, y, width, height)
        self._cart = cart
        self._on_quantity_change = on_quantity_change
        self._scroll_offset = 0
        self._rows: list[CartItemRow] = []

        # Fonts
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None

        # Arrow buttons
        arrow_x = x + width - self.ARROW_SIZE - self.ARROW_MARGIN
        self._up_arrow = Button(
            arrow_x,
            y + self.HEADER_HEIGHT,
            self.ARROW_SIZE,
            self.ARROW_SIZE,
            color=self.ARROW_COLOR,
            on_click=self.scroll_up,
        )
        self._down_arrow = Button(
            arrow_x,
            y + height - self.FOOTER_HEIGHT - self.ARROW_SIZE,
            self.ARROW_SIZE,
            self.ARROW_SIZE,
            color=self.ARROW_COLOR,
            on_click=self.scroll_down,
        )

    def _init_fonts(self) -> None:
        """Initialize fonts lazily."""
        if self._font is None:
            self._font = body()
            self._small_font = caption()

    def rebuild_rows(self) -> None:
        """Rebuild row components from current cart state."""
        self._rows.clear()

        items = self._cart.items
        row_y = self.rect.y + self.HEADER_HEIGHT

        for i, item in enumerate(items):
            barcode = item.product.barcode
            row = CartItemRow(
                self.rect.x,
                row_y + i * CartItemRow.HEIGHT,
                item,
                on_increase=lambda b=barcode: self._on_quantity_change(b, 1),
                on_decrease=lambda b=barcode: self._on_quantity_change(b, -1),
                alternate=(i % 2 == 1),
            )
            self._rows.append(row)

        # Clamp scroll offset
        self._clamp_scroll()

    def _clamp_scroll(self) -> None:
        """Clamp scroll offset to valid range."""
        max_offset = max(0, len(self._rows) - self.VISIBLE_ITEMS)
        self._scroll_offset = max(0, min(self._scroll_offset, max_offset))

    def scroll_up(self) -> None:
        """Scroll up one item."""
        self._scroll_offset = max(0, self._scroll_offset - 1)

    def scroll_down(self) -> None:
        """Scroll down one item."""
        max_offset = max(0, len(self._rows) - self.VISIBLE_ITEMS)
        self._scroll_offset = min(max_offset, self._scroll_offset + 1)

    def can_scroll_up(self) -> bool:
        """Check if can scroll up."""
        return self._scroll_offset > 0

    def can_scroll_down(self) -> bool:
        """Check if can scroll down."""
        return self._scroll_offset < len(self._rows) - self.VISIBLE_ITEMS

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events.

        Args:
            event: pygame event

        Returns:
            True if event was consumed
        """
        # Handle arrow buttons
        if self.can_scroll_up():
            if self._up_arrow.handle_event(event):
                return True
        if self.can_scroll_down():
            if self._down_arrow.handle_event(event):
                return True

        # Handle visible row buttons
        for i, row in enumerate(self._rows):
            if self._scroll_offset <= i < self._scroll_offset + self.VISIBLE_ITEMS:
                if row.handle_event(event):
                    return True

        # Handle scroll wheel
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                if event.y > 0:
                    self.scroll_up()
                elif event.y < 0:
                    self.scroll_down()
                return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        """Render the scrollable cart."""
        self._init_fonts()

        # Panel background
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=12)

        # Header
        if self._font:
            title = self._font.render("WARENKORB", True, TEXT_PRIMARY)
            title_x = self.rect.x + 15
            title_y = self.rect.y + 10
            surface.blit(title, (title_x, title_y))

        # Render visible rows
        visible_area_y = self.rect.y + self.HEADER_HEIGHT
        visible_area_height = self.VISIBLE_ITEMS * CartItemRow.HEIGHT

        # Set clipping rect
        clip_rect = pygame.Rect(
            self.rect.x, visible_area_y, self.rect.width, visible_area_height
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        for i, row in enumerate(self._rows):
            if self._scroll_offset <= i < self._scroll_offset + self.VISIBLE_ITEMS:
                # Update row Y position based on scroll
                visible_index = i - self._scroll_offset
                row_y = visible_area_y + visible_index * CartItemRow.HEIGHT
                row.update_position(row_y)
                row.render(surface)

        # Restore clip
        surface.set_clip(old_clip)

        # Empty cart message
        if not self._rows and self._small_font:
            empty_text = self._small_font.render(
                "Noch keine Produkte", True, TEXT_MUTED
            )
            empty_x = self.rect.centerx - empty_text.get_width() // 2
            empty_y = visible_area_y + 50
            surface.blit(empty_text, (empty_x, empty_y))

        # Scroll arrows
        if self.can_scroll_up():
            self._render_arrow(surface, self._up_arrow, "▲")
        if self.can_scroll_down():
            self._render_arrow(surface, self._down_arrow, "▼")

        # Total
        if self._font:
            total_y = self.rect.bottom - self.FOOTER_HEIGHT + 10
            total_str = f"GESAMT: {int(self._cart.total)} Taler"
            total_text = self._font.render(total_str, True, TEXT_PRIMARY)
            total_x = self.rect.centerx - total_text.get_width() // 2
            surface.blit(total_text, (total_x, total_y))

    def _render_arrow(
        self, surface: pygame.Surface, button: Button, symbol: str
    ) -> None:
        """Render an arrow button."""
        pygame.draw.rect(surface, self.ARROW_COLOR, button.rect, border_radius=6)

        font = caption()
        text = font.render(symbol, True, self.ARROW_TEXT_COLOR)
        text_rect = text.get_rect(center=button.rect.center)
        surface.blit(text, text_rect)

    @property
    def cart(self) -> Cart:
        """Get the cart instance."""
        return self._cart

    @property
    def total(self) -> float:
        """Get cart total."""
        return self._cart.total

    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return self._cart.is_empty
