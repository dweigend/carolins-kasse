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
    TEXT_MUTED,
    TEXT_PRIMARY,
    WARNING,
    WHITE,
)
from src.utils.fonts import body, caption


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

        # Dialog card
        card_x = (SCREEN_WIDTH - self.WIDTH) // 2
        card_y = (SCREEN_HEIGHT - self.HEIGHT) // 2 - 20

        card_rect = pygame.Rect(card_x, card_y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, BG_CARD, card_rect, border_radius=16)
        pygame.draw.rect(surface, DANGER, card_rect, width=3, border_radius=16)

        if self._font and self._small_font:
            # Title with icon
            title = self._font.render("❌ Nicht genug Taler!", True, DANGER)
            title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=card_y + 30)
            surface.blit(title, title_rect)

            # Balance comparison section
            bar_x = (SCREEN_WIDTH - self.BAR_WIDTH) // 2
            section_y = card_y + 80

            # "Du brauchst" bar (needed - red)
            needed_label = self._small_font.render("Du brauchst:", True, TEXT_PRIMARY)
            surface.blit(needed_label, (bar_x, section_y))

            needed_value = self._font.render(f"{self._needed} Taler", True, DANGER)
            value_x = bar_x + self.BAR_WIDTH - needed_value.get_width()
            surface.blit(needed_value, (value_x, section_y - 5))

            bar_y = section_y + 25
            self._render_bar(surface, bar_x, bar_y, self._needed, BALANCE_COLOR_LOW)

            # "Du hast" bar (available - green/yellow)
            available_y = bar_y + 50
            available_label = self._small_font.render("Du hast:", True, TEXT_PRIMARY)
            surface.blit(available_label, (bar_x, available_y))

            available_value = self._font.render(
                f"{self._available} Taler", True, BALANCE_COLOR_HIGH
            )
            value_x = bar_x + self.BAR_WIDTH - available_value.get_width()
            surface.blit(available_value, (value_x, available_y - 5))

            bar_y = available_y + 25
            self._render_bar(surface, bar_x, bar_y, self._available, BALANCE_COLOR_HIGH)

            # Missing amount
            missing = self._needed - self._available
            missing_y = bar_y + 45
            missing_text = self._small_font.render(
                f"Es fehlen: {missing} Taler", True, TEXT_MUTED
            )
            missing_rect = missing_text.get_rect(centerx=SCREEN_WIDTH // 2, y=missing_y)
            surface.blit(missing_text, missing_rect)

        # Close button
        if self._close_button and self._font:
            pygame.draw.rect(surface, WARNING, self._close_button.rect, border_radius=8)
            btn_text = self._font.render("VERSTANDEN", True, WHITE)
            btn_rect = btn_text.get_rect(center=self._close_button.rect.center)
            surface.blit(btn_text, btn_rect)

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
