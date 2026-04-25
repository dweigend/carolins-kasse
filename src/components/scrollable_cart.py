"""Scrollable cart component for displaying shopping cart items."""

from collections.abc import Callable

import pygame

from src.components.button import Button
from src.components.cart_item_row import CartItemRow
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.cart import Cart
from src.utils.fonts import bold_custom


class ScrollableCart:
    """Scrollable shopping cart with visual rows and large touch controls."""

    VISIBLE_ITEMS = 4
    HEADER_HEIGHT = 58
    FOOTER_HEIGHT = 82
    ARROW_SIZE = 42
    SIDE_PADDING = 18
    ROW_GAP = 6

    BG_COLOR = (255, 252, 244)
    BORDER_COLOR = (231, 219, 198)
    MUTED_COLOR = (166, 148, 120)
    PRICE_COLOR = (33, 99, 210)

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        cart: Cart,
        on_quantity_change: Callable[[str, int], None],
    ) -> None:
        """Create a scrollable cart."""
        self.rect = pygame.Rect(x, y, width, height)
        self._cart = cart
        self._on_quantity_change = on_quantity_change
        self._scroll_offset = 0
        self._rows: list[CartItemRow] = []

        arrow_x = self.rect.right - self.SIDE_PADDING - self.ARROW_SIZE
        self._up_arrow = Button(
            arrow_x,
            self.rect.y + self.HEADER_HEIGHT + 4,
            self.ARROW_SIZE,
            self.ARROW_SIZE,
            on_click=self.scroll_up,
        )
        self._down_arrow = Button(
            arrow_x,
            self.rect.bottom - self.FOOTER_HEIGHT - self.ARROW_SIZE - 4,
            self.ARROW_SIZE,
            self.ARROW_SIZE,
            on_click=self.scroll_down,
        )

    def rebuild_rows(self) -> None:
        """Rebuild row components from current cart state."""
        self._rows.clear()

        row_x = self.rect.x + self.SIDE_PADDING
        row_width = self.rect.width - self.SIDE_PADDING * 2
        row_y = self.rect.y + self.HEADER_HEIGHT

        for index, item in enumerate(self._cart.items):
            barcode = item.product.barcode
            row = CartItemRow(
                row_x,
                row_y + index * (CartItemRow.HEIGHT + self.ROW_GAP),
                item,
                width=row_width,
                on_increase=lambda b=barcode: self._on_quantity_change(b, 1),
                on_decrease=lambda b=barcode: self._on_quantity_change(b, -1),
                alternate=(index % 2 == 1),
            )
            self._rows.append(row)

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
        """Handle cart row and scroll events."""
        if self.can_scroll_up() and self._up_arrow.handle_event(event):
            return True
        if self.can_scroll_down() and self._down_arrow.handle_event(event):
            return True

        for index, row in enumerate(self._rows):
            if self._scroll_offset <= index < self._scroll_offset + self.VISIBLE_ITEMS:
                if row.handle_event(event):
                    return True

        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(
            pygame.mouse.get_pos()
        ):
            if event.y > 0:
                self.scroll_up()
            elif event.y < 0:
                self.scroll_down()
            return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        """Render the scrollable cart."""
        self._render_background(surface)

        self._render_header(surface)
        self._render_rows(surface)
        self._render_empty_state(surface)
        self._render_scroll_arrows(surface)
        self._render_total(surface)

    def _render_header(self, surface: pygame.Surface) -> None:
        """Render a basket icon instead of a text-heavy cart heading."""
        try:
            basket = get_asset("products/warenkorb", "M")
            basket_rect = basket.get_rect(center=(self.rect.centerx, self.rect.y + 31))
            surface.blit(basket, basket_rect)
        except FileNotFoundError:
            pygame.draw.circle(
                surface, self.MUTED_COLOR, (self.rect.centerx, self.rect.y + 31), 22
            )

    def _render_background(self, surface: pygame.Surface) -> None:
        """Render the shared cashier cart panel background asset."""
        try:
            panel = get_raw_asset("ui/cashier/panel_cart_bg")
            surface.blit(panel, self.rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(surface, self.BG_COLOR, self.rect, border_radius=18)
            pygame.draw.rect(surface, self.BORDER_COLOR, self.rect, 2, border_radius=18)

    def _render_rows(self, surface: pygame.Surface) -> None:
        """Render visible cart rows inside the clipped list area."""
        visible_area_y = self.rect.y + self.HEADER_HEIGHT
        visible_height = (
            self.VISIBLE_ITEMS * CartItemRow.HEIGHT
            + (self.VISIBLE_ITEMS - 1) * self.ROW_GAP
        )
        clip_rect = pygame.Rect(
            self.rect.x + self.SIDE_PADDING,
            visible_area_y,
            self.rect.width - self.SIDE_PADDING * 2,
            visible_height,
        )

        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)
        for index, row in enumerate(self._rows):
            if self._scroll_offset <= index < self._scroll_offset + self.VISIBLE_ITEMS:
                visible_index = index - self._scroll_offset
                row_y = visible_area_y + visible_index * (
                    CartItemRow.HEIGHT + self.ROW_GAP
                )
                row.update_position(row_y)
                row.render(surface)
        surface.set_clip(old_clip)

    def _render_empty_state(self, surface: pygame.Surface) -> None:
        """Render an image-led empty cart state."""
        if self._rows:
            return

        try:
            empty_basket = get_asset("recipes/einkaufskorb", "L")
            empty_area_top = self.rect.y + self.HEADER_HEIGHT
            empty_area_bottom = self.rect.bottom - self.FOOTER_HEIGHT
            empty_rect = empty_basket.get_rect(
                center=(
                    self.rect.centerx,
                    empty_area_top + (empty_area_bottom - empty_area_top) // 2,
                )
            )
            surface.blit(empty_basket, empty_rect)
        except FileNotFoundError:
            empty_area_top = self.rect.y + self.HEADER_HEIGHT
            empty_area_bottom = self.rect.bottom - self.FOOTER_HEIGHT
            empty_rect = pygame.Rect(0, 0, 160, 110)
            empty_rect.center = (
                self.rect.centerx,
                empty_area_top + (empty_area_bottom - empty_area_top) // 2,
            )
            pygame.draw.rect(surface, (238, 222, 190), empty_rect, border_radius=18)

    def _render_scroll_arrows(self, surface: pygame.Surface) -> None:
        """Render simple scroll controls only when needed."""
        if self.can_scroll_up():
            self._render_arrow(surface, self._up_arrow, points_up=True)
        if self.can_scroll_down():
            self._render_arrow(surface, self._down_arrow, points_up=False)

    def _render_total(self, surface: pygame.Surface) -> None:
        """Render total as coin icon plus number."""
        total = int(self._cart.total)
        footer_y = self.rect.bottom - self.FOOTER_HEIGHT + 14
        coin_size = 40
        try:
            coin = get_asset("products/taler", "M")
            coin = pygame.transform.smoothscale(coin, (coin_size, coin_size))
            surface.blit(coin, (self.rect.x + self.SIDE_PADDING + 6, footer_y))
        except FileNotFoundError:
            pygame.draw.circle(
                surface,
                (245, 158, 11),
                (self.rect.x + self.SIDE_PADDING + 29, footer_y + 23),
                22,
            )

        font = bold_custom(42)
        total_text = font.render(str(total), True, self.PRICE_COLOR)
        surface.blit(
            total_text,
            (self.rect.x + self.SIDE_PADDING + coin_size + 20, footer_y - 2),
        )

    def _render_arrow(
        self, surface: pygame.Surface, button: Button, *, points_up: bool
    ) -> None:
        """Render an arrow button."""
        pygame.draw.circle(
            surface, (232, 220, 200), button.rect.center, self.ARROW_SIZE // 2
        )
        cx, cy = button.rect.center
        if points_up:
            points = [(cx, cy - 11), (cx - 12, cy + 8), (cx + 12, cy + 8)]
        else:
            points = [(cx, cy + 11), (cx - 12, cy - 8), (cx + 12, cy - 8)]
        pygame.draw.polygon(surface, self.MUTED_COLOR, points)

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
