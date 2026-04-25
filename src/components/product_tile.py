"""Clickable product tile for picker grid."""

from collections.abc import Callable

import pygame

from src.components.mixins import ClickableMixin
from src.constants import BG_CARD, PRIMARY, TEXT_PRIMARY
from src.utils.fonts import custom


class ProductTile(ClickableMixin):
    """A clickable tile showing product image and name.

    Attributes:
        rect: pygame.Rect for position and collision detection
        product_id: ID of the product this tile represents
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        product_id: int,
        name: str,
        image: pygame.Surface | None = None,
        on_click: Callable[[int], None] | None = None,
    ) -> None:
        """Create a product tile.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            width: Tile width
            height: Tile height
            product_id: Database ID of the product
            name: Product name to display
            image: Product image surface
            on_click: Callback with product_id when clicked
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.product_id = product_id
        self.name = name
        self.image = image
        self.on_click = on_click
        self._pressed = False
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events.

        Args:
            event: pygame event

        Returns:
            True if tile was clicked, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)

        return self._handle_click(event, self.rect, self.on_click, self.product_id)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the tile.

        Args:
            surface: Surface to draw on
        """
        # Background with hover/press effect
        bg_color = BG_CARD
        border_color = PRIMARY if (self._hovered or self._pressed) else (231, 219, 198)
        border_width = 3 if self._pressed else 2

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=16)
        pygame.draw.rect(
            surface, border_color, self.rect, width=border_width, border_radius=16
        )

        # Product image (centered in upper portion)
        if self.image:
            img_x = self.rect.x + (self.rect.width - self.image.get_width()) // 2
            img_y = self.rect.y + 12
            surface.blit(self.image, (img_x, img_y))

        # Product name (centered at bottom)
        name_font = custom(24)
        name_text = name_font.render(self.name, True, TEXT_PRIMARY)
        # Truncate if too wide
        if name_text.get_width() > self.rect.width - 10:
            truncated = self.name[:12] + "…"
            name_text = name_font.render(truncated, True, TEXT_PRIMARY)

        name_x = self.rect.x + (self.rect.width - name_text.get_width()) // 2
        name_y = self.rect.y + self.rect.height - name_text.get_height() - 10
        surface.blit(name_text, (name_x, name_y))
