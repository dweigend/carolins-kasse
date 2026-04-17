"""Product display component showing the last scanned product."""

import pygame

from src.utils.assets import get as get_asset
from src.utils.database import Product


class ProductDisplay:
    """Shows a single product with image, name, and price.

    Used in ScanScene to show the last scanned product.
    """

    # Layout constants
    WIDTH = 300
    HEIGHT = 200
    PADDING = 20
    IMAGE_SIZE = 60  # M size

    # Colors
    BG_COLOR = (255, 255, 255)
    BORDER_COLOR = (200, 200, 200)
    NAME_COLOR = (30, 30, 30)
    PRICE_COLOR = (59, 130, 246)  # Blue

    def __init__(self, x: int, y: int) -> None:
        """Create product display at position.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
        """
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self._product: Product | None = None
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._initialized = False

    def _init_fonts(self) -> None:
        """Initialize fonts (must be called after pygame.init)."""
        if self._initialized:
            return
        self._font = pygame.font.Font(None, 36)
        self._small_font = pygame.font.Font(None, 28)
        self._initialized = True

    def set_product(self, product: Product | None) -> None:
        """Set the product to display.

        Args:
            product: Product to show, or None to clear
        """
        self._product = product

    def clear(self) -> None:
        """Clear the displayed product."""
        self._product = None

    @property
    def product(self) -> Product | None:
        """Get currently displayed product."""
        return self._product

    def render(self, surface: pygame.Surface) -> None:
        """Draw the product display.

        Args:
            surface: Surface to draw on
        """
        self._init_fonts()

        # Background
        pygame.draw.rect(surface, self.BG_COLOR, self.rect, border_radius=12)
        pygame.draw.rect(surface, self.BORDER_COLOR, self.rect, 2, border_radius=12)

        if not self._product:
            # Show placeholder
            if self._small_font:
                text = self._small_font.render(
                    "Scanne ein Produkt...", True, (150, 150, 150)
                )
                text_rect = text.get_rect(center=self.rect.center)
                surface.blit(text, text_rect)
            return

        # Product image
        try:
            if self._product.image_path:
                image = get_asset(f"products/{self._product.image_path}", "M")
                image_x = self.rect.x + (self.WIDTH - image.get_width()) // 2
                image_y = self.rect.y + self.PADDING
                surface.blit(image, (image_x, image_y))
        except FileNotFoundError:
            # Draw placeholder square if image not found
            placeholder_rect = pygame.Rect(
                self.rect.x + (self.WIDTH - self.IMAGE_SIZE) // 2,
                self.rect.y + self.PADDING,
                self.IMAGE_SIZE,
                self.IMAGE_SIZE,
            )
            pygame.draw.rect(
                surface, (220, 220, 220), placeholder_rect, border_radius=8
            )

        # Product name
        if self._font:
            name_text = self._font.render(self._product.name_de, True, self.NAME_COLOR)
            name_x = self.rect.x + (self.WIDTH - name_text.get_width()) // 2
            name_y = self.rect.y + self.PADDING + self.IMAGE_SIZE + 20
            surface.blit(name_text, (name_x, name_y))

        # Price
        if self._font:
            price_str = f"{int(self._product.price)} Taler"
            price_text = self._font.render(price_str, True, self.PRICE_COLOR)
            price_x = self.rect.x + (self.WIDTH - price_text.get_width()) // 2
            price_y = name_y + 35
            surface.blit(price_text, (price_x, price_y))
