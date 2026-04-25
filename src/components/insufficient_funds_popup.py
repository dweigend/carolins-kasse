"""Insufficient funds popup - visual feedback when balance is too low."""

import pygame

from src.components.button import Button
from src.constants import (
    BALANCE_BAR_MAX,
    BALANCE_COLOR_BG,
    BALANCE_COLOR_HIGH,
    BALANCE_COLOR_LOW,
    BG_CARD,
    DANGER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WARNING,
    WHITE,
)
from src.utils.assets import get as get_asset
from src.utils.fonts import bold_custom, body, caption


class InsufficientFundsPopup:
    """Popup showing visual comparison when balance is insufficient.

    Montessori principle: Visual bars are easier to understand than numbers.
    Shows "what you need" vs "what you have" with color-coded bars.
    """

    WIDTH = 500
    HEIGHT = 350
    BAR_WIDTH = 300
    BAR_HEIGHT = 25

    def __init__(self) -> None:
        """Initialize popup."""
        self._visible = False
        self._needed: int = 0
        self._available: int = 0
        self._font: pygame.font.Font | None = None
        self._small_font: pygame.font.Font | None = None
        self._close_button: Button | None = None

    def _init_ui(self) -> None:
        """Initialize UI elements lazily."""
        if self._font is not None:
            return

        self._font = body()
        self._small_font = caption()

        # Close button centered at bottom
        btn_width = 180
        btn_height = 45
        btn_x = (SCREEN_WIDTH - btn_width) // 2
        btn_y = (SCREEN_HEIGHT + self.HEIGHT) // 2 - btn_height - 30

        self._close_button = Button(
            btn_x,
            btn_y,
            btn_width,
            btn_height,
            color=WARNING,
            on_click=self.hide,
        )

    def show(self, needed: int, available: int) -> None:
        """Show the popup with balance comparison.

        Args:
            needed: Total amount required
            available: User's current balance
        """
        self._needed = needed
        self._available = available
        self._visible = True

    def hide(self) -> None:
        """Hide the popup."""
        self._visible = False

    def is_visible(self) -> bool:
        """Check if popup is currently visible."""
        return self._visible

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events, return True if event was consumed."""
        if not self._visible:
            return False

        self._init_ui()

        # Close on any key press or click
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.hide()
            return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        """Render the popup overlay."""
        if not self._visible:
            return

        self._init_ui()

        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        card_x = (SCREEN_WIDTH - self.WIDTH) // 2
        card_y = (SCREEN_HEIGHT - self.HEIGHT) // 2 - 20

        card_rect = pygame.Rect(card_x, card_y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, BG_CARD, card_rect, border_radius=22)
        pygame.draw.rect(surface, DANGER, card_rect, width=4, border_radius=22)

        if self._font and self._small_font:
            try:
                icon = get_asset("ui/cashier/insufficient_funds", "L")
                icon_rect = icon.get_rect(center=(SCREEN_WIDTH // 2, card_y + 76))
                surface.blit(icon, icon_rect)
            except FileNotFoundError:
                pygame.draw.circle(
                    surface, DANGER, (SCREEN_WIDTH // 2, card_y + 76), 42
                )

            bar_x = (SCREEN_WIDTH - self.BAR_WIDTH) // 2
            section_y = card_y + 130

            self._render_coin_value(
                surface, bar_x, section_y - 12, self._needed, DANGER
            )

            bar_y = section_y + 25
            self._render_bar(surface, bar_x, bar_y, self._needed, BALANCE_COLOR_LOW)

            available_y = bar_y + 50
            self._render_coin_value(
                surface, bar_x, available_y - 12, self._available, BALANCE_COLOR_HIGH
            )

            bar_y = available_y + 25
            self._render_bar(surface, bar_x, bar_y, self._available, BALANCE_COLOR_HIGH)

        # Close button
        if self._close_button and self._font:
            pygame.draw.rect(surface, WARNING, self._close_button.rect, border_radius=8)
            self._draw_check(surface, self._close_button.rect.center)

    def _draw_check(self, surface: pygame.Surface, center: tuple[int, int]) -> None:
        """Draw a check mark without depending on font glyph support."""
        pygame.draw.line(
            surface,
            WHITE,
            (center[0] - 18, center[1]),
            (center[0] - 6, center[1] + 13),
            8,
        )
        pygame.draw.line(
            surface,
            WHITE,
            (center[0] - 6, center[1] + 13),
            (center[0] + 22, center[1] - 16),
            8,
        )

    def _render_coin_value(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        value: int,
        color: tuple[int, int, int],
    ) -> None:
        """Render a compact coin plus number value."""
        coin_size = 34
        try:
            coin = get_asset("products/taler", "M")
            coin = pygame.transform.smoothscale(coin, (coin_size, coin_size))
            surface.blit(coin, (x, y))
        except FileNotFoundError:
            pygame.draw.circle(surface, WARNING, (x + 17, y + 17), 16)

        font = bold_custom(32)
        value_text = font.render(str(value), True, color)
        surface.blit(value_text, (x + coin_size + 8, y - 2))

    def _render_bar(
        self, surface: pygame.Surface, x: int, y: int, value: int, color: tuple
    ) -> None:
        """Render a progress bar."""
        # Background
        bg_rect = pygame.Rect(x, y, self.BAR_WIDTH, self.BAR_HEIGHT)
        pygame.draw.rect(surface, BALANCE_COLOR_BG, bg_rect, border_radius=6)

        # Filled portion
        fill_width = min(self.BAR_WIDTH, int(self.BAR_WIDTH * value / BALANCE_BAR_MAX))
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.BAR_HEIGHT)
            pygame.draw.rect(surface, color, fill_rect, border_radius=6)

        # Border
        pygame.draw.rect(surface, (180, 180, 180), bg_rect, width=1, border_radius=6)
