"""Product display component showing the last scanned product."""

import pygame

from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.database import Product
from src.utils.fonts import bold_custom, caption, custom


class ProductDisplay:
    """Shows the current scan state with a strong visual focus."""

    WIDTH = 330
    HEIGHT = 420
    PRODUCT_IMAGE_SIZE = 180
    SAFE_TEXT_WIDTH = WIDTH - 48

    BG_COLOR = (255, 252, 244)
    BORDER_COLOR = (231, 219, 198)
    ACCENT_COLOR = (59, 130, 246)
    NAME_COLOR = (30, 30, 30)
    PRICE_COLOR = (33, 99, 210)
    SUCCESS_COLOR = (34, 197, 94)
    PLACEHOLDER_COLOR = (219, 234, 254)

    def __init__(self, x: int, y: int) -> None:
        """Create product display at position."""
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self._product: Product | None = None

    def set_product(self, product: Product | None) -> None:
        """Set the product to display."""
        self._product = product

    def clear(self) -> None:
        """Clear the displayed product."""
        self._product = None

    @property
    def product(self) -> Product | None:
        """Get currently displayed product."""
        return self._product

    def render(self, surface: pygame.Surface) -> None:
        """Draw the product display."""
        self._render_background(surface)

        if not self._product:
            self._render_empty_state(surface)
            return

        self._render_product(surface)

    def _render_empty_state(self, surface: pygame.Surface) -> None:
        """Render a visual scan cue for children who do not read yet."""
        try:
            scan_hint = get_asset("ui/cashier/scan_hint", "HERO")
            hint_rect = scan_hint.get_rect(
                center=(self.rect.centerx, self.rect.y + 205)
            )
            surface.blit(scan_hint, hint_rect)
        except FileNotFoundError:
            placeholder = pygame.Rect(0, 0, 190, 190)
            placeholder.center = (self.rect.centerx, self.rect.y + 184)
            pygame.draw.rect(
                surface, self.PLACEHOLDER_COLOR, placeholder, border_radius=28
            )

    def _render_background(self, surface: pygame.Surface) -> None:
        """Render the shared cashier panel background asset."""
        try:
            panel = get_raw_asset("ui/cashier/panel_scan_bg")
            surface.blit(panel, self.rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(surface, self.BG_COLOR, self.rect, border_radius=18)
            pygame.draw.rect(surface, self.BORDER_COLOR, self.rect, 2, border_radius=18)

    def _render_product(self, surface: pygame.Surface) -> None:
        """Render the latest scanned product as the main visual focus."""
        if not self._product:
            return

        burst_rect = pygame.Rect(0, 0, 230, 230)
        burst_rect.center = (self.rect.centerx, self.rect.y + 142)
        pygame.draw.ellipse(surface, self.PLACEHOLDER_COLOR, burst_rect)

        try:
            if self._product.image_path:
                image = get_asset(f"products/{self._product.image_path}", "HERO")
                image_rect = image.get_rect(center=burst_rect.center)
                surface.blit(image, image_rect)
        except FileNotFoundError:
            placeholder_rect = pygame.Rect(0, 0, self.PRODUCT_IMAGE_SIZE, 130)
            placeholder_rect.center = burst_rect.center
            pygame.draw.rect(
                surface, (220, 220, 220), placeholder_rect, border_radius=18
            )

        self._render_success_mark(surface)
        self._render_product_name(surface)
        self._render_price(surface)

    def _render_success_mark(self, surface: pygame.Surface) -> None:
        """Render a clear non-text cue that a product was scanned."""
        mark_center = (self.rect.centerx, self.rect.y + 268)
        pygame.draw.circle(surface, self.SUCCESS_COLOR, mark_center, 34)
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (mark_center[0] - 16, mark_center[1] - 1),
            (mark_center[0] - 4, mark_center[1] + 13),
            8,
        )
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (mark_center[0] - 4, mark_center[1] + 13),
            (mark_center[0] + 18, mark_center[1] - 17),
            8,
        )

    def _render_product_name(self, surface: pygame.Surface) -> None:
        """Render a small product name for adults without making it primary."""
        if not self._product:
            return

        name_text = self._fit_text(
            self._product.name_de,
            max_width=self.SAFE_TEXT_WIDTH,
            sizes=(30, 27, 24, 21),
        )
        name_rect = name_text.get_rect(center=(self.rect.centerx, self.rect.y + 326))
        surface.blit(name_text, name_rect)

    def _render_price(self, surface: pygame.Surface) -> None:
        """Render price with a coin icon and a large number."""
        if not self._product:
            return

        price = int(self._product.price)
        coin_size = 44
        coin_gap = 8
        price_font = bold_custom(42)
        price_text = price_font.render(str(price), True, self.PRICE_COLOR)

        try:
            coin = get_asset("products/taler", "M")
            coin = pygame.transform.smoothscale(coin, (coin_size, coin_size))
        except FileNotFoundError:
            coin = pygame.Surface((coin_size, coin_size), pygame.SRCALPHA)
            pygame.draw.circle(
                coin, (245, 158, 11), (coin_size // 2, coin_size // 2), 20
            )

        total_width = coin_size + coin_gap + price_text.get_width()
        start_x = self.rect.centerx - total_width // 2
        y = self.rect.bottom - 62
        surface.blit(coin, (start_x, y))
        surface.blit(price_text, (start_x + coin_size + coin_gap, y - 2))

    def _fit_text(
        self, text: str, *, max_width: int, sizes: tuple[int, ...]
    ) -> pygame.Surface:
        """Render text at the largest size that fits the available width."""
        for size in sizes:
            text_surface = custom(size).render(text, True, self.NAME_COLOR)
            if text_surface.get_width() <= max_width:
                return text_surface

        short_text = text
        while len(short_text) > 4:
            candidate = f"{short_text[:-1]}…"
            text_surface = caption().render(candidate, True, self.NAME_COLOR)
            if text_surface.get_width() <= max_width:
                return text_surface
            short_text = short_text[:-1]

        return caption().render(text[:4], True, self.NAME_COLOR)
