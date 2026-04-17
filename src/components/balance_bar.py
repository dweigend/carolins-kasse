"""Balance bar component for consistent money visualization.

Montessori principle: Same visual representation everywhere makes
abstract numbers concrete and understandable for children.
"""

import pygame

from src.constants import (
    BALANCE_BAR_MAX,
    BALANCE_COLOR_BG,
    BALANCE_COLOR_HIGH,
    BALANCE_COLOR_LOW,
    BALANCE_COLOR_MED,
    BALANCE_THRESHOLD_LOW,
    BALANCE_THRESHOLD_MED,
    SUCCESS,
    TEXT_PRIMARY,
    WARNING,
)
from src.utils.fonts import body, caption


class BalanceBar:
    """A horizontal bar showing balance relative to maximum.

    Visual design:
    ┌──────────────────────────────────────────┐
    │  █████████████████░░░░░░░  32 Taler      │
    └──────────────────────────────────────────┘

    Color coding:
    - Green (> 25 Taler): More than 5 shopping trips
    - Yellow (10-25 Taler): 2-5 shopping trips
    - Red (< 10 Taler): "Getting low!"
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 300,
        height: int = 30,
        *,
        show_text: bool = True,
        show_max: bool = False,
        max_value: int | None = None,
    ) -> None:
        """Create a balance bar.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            width: Bar width in pixels
            height: Bar height in pixels
            show_text: Show "X Taler" text next to bar
            show_max: Show "/50" after the value
            max_value: Custom maximum for fill calculation (default: BALANCE_BAR_MAX)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.show_text = show_text
        self.show_max = show_max
        self._balance = 0
        self._max_value = max_value or BALANCE_BAR_MAX
        self._milestone: int | None = None
        self._font: pygame.font.Font | None = None

    def set_balance(self, balance: int | float) -> None:
        """Update the displayed balance."""
        self._balance = int(balance)

    def set_milestone(self, value: int) -> None:
        """Set milestone marker position (shows ★ at this value)."""
        self._milestone = value

    def _get_color(self) -> tuple[int, int, int]:
        """Get bar color based on balance."""
        if self._balance < BALANCE_THRESHOLD_LOW:
            return BALANCE_COLOR_LOW
        if self._balance < BALANCE_THRESHOLD_MED:
            return BALANCE_COLOR_MED
        return BALANCE_COLOR_HIGH

    def _get_fill_width(self) -> int:
        """Calculate filled portion width."""
        ratio = min(self._balance / self._max_value, 1.0)
        # Leave room for text if shown
        bar_width = self.rect.width
        if self.show_text:
            bar_width = int(self.rect.width * 0.65)
        return int(bar_width * ratio)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the balance bar.

        Args:
            surface: Surface to draw on
        """
        bar_width = self.rect.width
        if self.show_text:
            bar_width = int(self.rect.width * 0.65)

        # Background (empty portion)
        bg_rect = pygame.Rect(self.rect.x, self.rect.y, bar_width, self.rect.height)
        pygame.draw.rect(surface, BALANCE_COLOR_BG, bg_rect, border_radius=6)

        # Filled portion
        fill_width = self._get_fill_width()
        if fill_width > 0:
            fill_rect = pygame.Rect(
                self.rect.x, self.rect.y, fill_width, self.rect.height
            )
            pygame.draw.rect(surface, self._get_color(), fill_rect, border_radius=6)

        # Milestone marker (★)
        if self._milestone and self._max_value:
            if not self._font:
                self._font = body()
            ratio = self._milestone / self._max_value
            milestone_x = self.rect.x + int(bar_width * ratio)
            # Gold if not reached, green if reached
            star_color = SUCCESS if self._balance >= self._milestone else WARNING
            star_text = self._font.render("★", True, star_color)
            surface.blit(star_text, (milestone_x - 8, self.rect.y - 22))

        # Text
        if self.show_text:
            if not self._font:
                self._font = body()
            if self.show_max:
                text = f"{self._balance}/{self._max_value} Taler"
            else:
                text = f"{self._balance} Taler"

            text_surface = self._font.render(text, True, TEXT_PRIMARY)
            text_x = self.rect.x + bar_width + 10
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))


class CompactBalanceBar(BalanceBar):
    """Smaller balance bar for inline use (e.g., in headers)."""

    def __init__(self, x: int, y: int, width: int = 150, height: int = 20) -> None:
        """Create a compact balance bar."""
        super().__init__(x, y, width, height, show_text=True, show_max=False)
        self._font = caption()
