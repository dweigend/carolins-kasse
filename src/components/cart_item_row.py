"""Cart item row component for displaying items in the shopping cart."""

from collections.abc import Callable

import pygame

from src.components.button import Button
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.cart import CartItem
from src.utils.fonts import bold_custom, custom


class CartItemRow:
    """A visual cart row with large touch controls."""

    HEIGHT = 54
    IMAGE_SIZE = 44
    BUTTON_SIZE = 46
    PADDING = 8

    BG_COLOR = (255, 252, 244)
    BG_COLOR_ALT = (250, 244, 235)
    BORDER_COLOR = (232, 220, 200)
    NAME_COLOR = (65, 52, 42)
    QTY_BG_COLORS = (
        (219, 234, 254),
        (252, 231, 243),
        (254, 243, 199),
        (204, 251, 241),
    )
    QTY_COLOR = (65, 52, 42)

    def __init__(
        self,
        x: int,
        y: int,
        item: CartItem,
        *,
        width: int,
        on_increase: Callable[[], None] | None = None,
        on_decrease: Callable[[], None] | None = None,
        alternate: bool = False,
    ) -> None:
        """Create a cart item row."""
        self.rect = pygame.Rect(x, y, width, self.HEIGHT)
        self.item = item
        self._alternate = alternate

        self._minus_btn = Button(
            0,
            0,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE,
            image=self._load_control_asset("quantity_minus_button"),
            on_click=on_decrease,
        )
        self._plus_btn = Button(
            0,
            0,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE,
            image=self._load_control_asset("quantity_plus_button"),
            on_click=on_increase,
        )
        self._position_buttons()

    def _load_control_asset(self, asset_name: str) -> pygame.Surface | None:
        """Load a cashier control asset and scale it to the row button size."""
        try:
            image = get_asset(f"ui/cashier/{asset_name}", "BUTTON")
            return pygame.transform.smoothscale(
                image, (self.BUTTON_SIZE, self.BUTTON_SIZE)
            )
        except FileNotFoundError:
            return None

    def _position_buttons(self) -> None:
        """Keep buttons aligned after scrolling or resizing."""
        btn_y = self.rect.y + (self.HEIGHT - self.BUTTON_SIZE) // 2
        self._plus_btn.rect.topleft = (
            self.rect.right - self.PADDING - self.BUTTON_SIZE,
            btn_y,
        )
        self._minus_btn.rect.topleft = (
            self._plus_btn.rect.x - self.PADDING - self.BUTTON_SIZE,
            btn_y,
        )

    def update_position(self, y: int) -> None:
        """Update row Y position for scrolling."""
        self.rect.y = y
        self._position_buttons()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for the quantity controls."""
        minus_clicked = self._minus_btn.handle_event(event)
        plus_clicked = self._plus_btn.handle_event(event)
        return minus_clicked or plus_clicked

    def render(self, surface: pygame.Surface) -> None:
        """Draw the cart item row."""
        self._render_background(surface)

        self._render_product_image(surface)
        self._render_product_name(surface)
        self._render_quantity_badge(surface)
        self._render_button(surface, self._minus_btn, is_minus=True)
        self._render_button(surface, self._plus_btn, is_minus=False)

    def _render_background(self, surface: pygame.Surface) -> None:
        """Render row background from the cashier asset set."""
        asset_name = (
            "ui/cashier/cart_row_alt_bg"
            if self._alternate
            else "ui/cashier/cart_row_bg"
        )
        try:
            row_bg = get_raw_asset(asset_name)
            surface.blit(row_bg, self.rect.topleft)
        except FileNotFoundError:
            bg_color = self.BG_COLOR_ALT if self._alternate else self.BG_COLOR
            pygame.draw.rect(surface, bg_color, self.rect, border_radius=14)
            pygame.draw.rect(surface, self.BORDER_COLOR, self.rect, 1, border_radius=14)

    def _render_product_image(self, surface: pygame.Surface) -> None:
        """Render the product image as the primary row cue."""
        image_x = self.rect.x + self.PADDING + 4
        image_y = self.rect.y + (self.HEIGHT - self.IMAGE_SIZE) // 2
        image_rect = pygame.Rect(image_x, image_y, self.IMAGE_SIZE, self.IMAGE_SIZE)

        try:
            if self.item.product.image_path:
                image = get_asset(f"products/{self.item.product.image_path}", "CART")
                surface.blit(image, image_rect.topleft)
                return
        except FileNotFoundError:
            pass

        pygame.draw.rect(surface, (220, 220, 220), image_rect, border_radius=10)

    def _render_product_name(self, surface: pygame.Surface) -> None:
        """Render a small adult-readable label without dominating the row."""
        name_x = self.rect.x + self.PADDING + self.IMAGE_SIZE + 18
        badge_left = self._minus_btn.rect.x - 48 - 22
        max_width = max(0, badge_left - name_x - 8)
        if max_width <= 0:
            return

        name_text = self._fit_name_text(self.item.product.name_de, max_width)
        name_y = self.rect.y + (self.HEIGHT - name_text.get_height()) // 2
        surface.blit(name_text, (name_x, name_y))

    def _fit_name_text(self, name: str, max_width: int) -> pygame.Surface:
        """Render a product name that always stays inside the row."""
        for size in (22, 20, 18, 16):
            text = custom(size).render(name, True, self.NAME_COLOR)
            if text.get_width() <= max_width:
                return text

        clipped_name = name
        font = custom(16)
        while len(clipped_name) > 4:
            candidate = f"{clipped_name[:-1]}…"
            text = font.render(candidate, True, self.NAME_COLOR)
            if text.get_width() <= max_width:
                return text
            clipped_name = clipped_name[:-1]

        return font.render(clipped_name[:4], True, self.NAME_COLOR)

    def _render_quantity_badge(self, surface: pygame.Surface) -> None:
        """Render quantity as a large colored number badge."""
        badge_center = (self._minus_btn.rect.x - 48, self.rect.centery)
        badge_color = self.QTY_BG_COLORS[
            (self.item.quantity - 1) % len(self.QTY_BG_COLORS)
        ]
        pygame.draw.circle(surface, badge_color, badge_center, 22)

        qty_font = bold_custom(29)
        qty_text = qty_font.render(str(self.item.quantity), True, self.QTY_COLOR)
        qty_rect = qty_text.get_rect(center=(badge_center[0], badge_center[1] - 2))
        surface.blit(qty_text, qty_rect)

    def _render_button(
        self, surface: pygame.Surface, button: Button, *, is_minus: bool
    ) -> None:
        """Render an image-backed button with a drawn fallback."""
        if button.image:
            surface.blit(button.image, button.rect.topleft)
            return

        fallback_color = (239, 68, 68) if is_minus else (34, 197, 94)
        pygame.draw.circle(
            surface, fallback_color, button.rect.center, self.BUTTON_SIZE // 2
        )
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (button.rect.centerx - 12, button.rect.centery),
            (button.rect.centerx + 12, button.rect.centery),
            6,
        )
        if not is_minus:
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (button.rect.centerx, button.rect.centery - 12),
                (button.rect.centerx, button.rect.centery + 12),
                6,
            )
