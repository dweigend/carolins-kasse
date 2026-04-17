"""Touch-friendly numpad component for number input."""

from typing import Callable

import pygame

from src.constants import BG_CARD, DANGER, GREY_LIGHT, PRIMARY, SUCCESS, WHITE
from src.utils.fonts import bold_custom


class Numpad:
    """A touch-friendly numpad with 0-9, Clear, and Enter buttons.

    Attributes:
        rect: pygame.Rect for the numpad area
        value: Current entered value as string
    """

    GRID_COLS = 3
    GRID_ROWS = 4
    BUTTON_SIZE = 88
    BUTTON_GAP = 12
    PANEL_PADDING = 18
    PANEL_RADIUS = 26
    BUTTON_RADIUS = 18
    SHADOW_OFFSET = 4

    def __init__(
        self,
        x: int,
        y: int,
        *,
        on_enter: Callable[[str], None] | None = None,
        on_change: Callable[[str], None] | None = None,
        max_digits: int = 4,
    ) -> None:
        """Create a numpad.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            on_enter: Callback when Enter is pressed, receives current value
            on_change: Callback when value changes
            max_digits: Maximum number of digits allowed
        """
        self.value = ""
        self.on_enter = on_enter
        self.on_change = on_change
        self.max_digits = max_digits

        width = self.width()
        height = self.height()

        self.rect = pygame.Rect(x, y, width, height)
        self._pressed_button: str | None = None

        # Build button layout: 7-8-9, 4-5-6, 1-2-3, C-0-✓
        self._buttons: list[tuple[pygame.Rect, str, tuple[int, int, int]]] = []
        layout = [
            ["7", "8", "9"],
            ["4", "5", "6"],
            ["1", "2", "3"],
            ["C", "0", "✓"],
        ]

        grid_x = x + self.PANEL_PADDING
        grid_y = y + self.PANEL_PADDING

        for row_idx, row in enumerate(layout):
            for col_idx, label in enumerate(row):
                btn_x = grid_x + col_idx * (self.BUTTON_SIZE + self.BUTTON_GAP)
                btn_y = grid_y + row_idx * (self.BUTTON_SIZE + self.BUTTON_GAP)
                btn_rect = pygame.Rect(btn_x, btn_y, self.BUTTON_SIZE, self.BUTTON_SIZE)

                # Button colors
                if label == "C":
                    color = DANGER
                elif label == "✓":
                    color = SUCCESS
                else:
                    color = PRIMARY

                self._buttons.append((btn_rect, label, color))

    @classmethod
    def width(cls) -> int:
        """Get total component width including outer panel padding."""
        grid_width = (
            cls.GRID_COLS * cls.BUTTON_SIZE + (cls.GRID_COLS - 1) * cls.BUTTON_GAP
        )
        return grid_width + 2 * cls.PANEL_PADDING

    @classmethod
    def height(cls) -> int:
        """Get total component height including outer panel padding."""
        grid_height = (
            cls.GRID_ROWS * cls.BUTTON_SIZE + (cls.GRID_ROWS - 1) * cls.BUTTON_GAP
        )
        return grid_height + 2 * cls.PANEL_PADDING

    def clear(self) -> None:
        """Clear the current value."""
        self.value = ""
        if self.on_change:
            self.on_change(self.value)

    def set_max_digits(self, max_digits: int) -> None:
        """Update the allowed number of digits for the current context."""
        self.max_digits = max_digits
        if len(self.value) <= self.max_digits:
            return

        self.value = self.value[: self.max_digits]
        if self.on_change:
            self.on_change(self.value)

    def _handle_button(self, label: str) -> None:
        """Handle a button press."""
        if label == "C":
            self.clear()
        elif label == "✓":
            if self.on_enter:
                self.on_enter(self.value)
        else:
            # Digit
            if len(self.value) < self.max_digits:
                self.value += label
                if self.on_change:
                    self.on_change(self.value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events.

        Args:
            event: pygame event

        Returns:
            True if a button was clicked, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, label, _ in self._buttons:
                if rect.collidepoint(event.pos):
                    self._pressed_button = label
                    return False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed_button:
                for rect, label, _ in self._buttons:
                    if rect.collidepoint(event.pos) and label == self._pressed_button:
                        self._handle_button(label)
                        self._pressed_button = None
                        return True
                self._pressed_button = None

        # Handle keyboard input as well
        if event.type == pygame.KEYDOWN:
            if event.unicode.isdigit():
                if len(self.value) < self.max_digits:
                    self.value += event.unicode
                    if self.on_change:
                        self.on_change(self.value)
                    return True
            elif event.key == pygame.K_BACKSPACE:
                if self.value:
                    self.value = self.value[:-1]
                    if self.on_change:
                        self.on_change(self.value)
                    return True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.on_enter:
                    self.on_enter(self.value)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.clear()
                return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        """Draw the numpad.

        Args:
            surface: Surface to draw on
        """
        self._draw_panel(surface)

        for rect, label, color in self._buttons:
            button_rect = rect.copy()
            shadow_rect = button_rect.move(0, self.SHADOW_OFFSET)

            pygame.draw.rect(
                surface,
                (0, 0, 0, 28),
                shadow_rect,
                border_radius=self.BUTTON_RADIUS,
            )

            if self._pressed_button == label:
                r, g, b = color
                color = (max(0, r - 40), max(0, g - 40), max(0, b - 40))
                button_rect.y += 2

            pygame.draw.rect(
                surface,
                color,
                button_rect,
                border_radius=self.BUTTON_RADIUS,
            )

            if label == "✓":
                self._draw_checkmark(surface, button_rect)
                continue

            font = bold_custom(34 if label == "C" else 38)
            text = font.render(label, True, WHITE)
            text_rect = text.get_rect(center=button_rect.center)
            surface.blit(text, text_rect)

    def _draw_panel(self, surface: pygame.Surface) -> None:
        """Draw the outer card behind the numpad buttons."""
        shadow_rect = self.rect.move(0, self.SHADOW_OFFSET)
        pygame.draw.rect(
            surface,
            (0, 0, 0, 22),
            shadow_rect,
            border_radius=self.PANEL_RADIUS,
        )
        pygame.draw.rect(
            surface,
            BG_CARD,
            self.rect,
            border_radius=self.PANEL_RADIUS,
        )
        pygame.draw.rect(
            surface,
            GREY_LIGHT,
            self.rect,
            width=2,
            border_radius=self.PANEL_RADIUS,
        )

    def _draw_checkmark(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Draw a robust checkmark without depending on font glyph support."""
        start = (rect.x + 24, rect.y + 46)
        mid = (rect.x + 39, rect.y + 60)
        end = (rect.x + 65, rect.y + 28)
        pygame.draw.lines(surface, WHITE, False, [start, mid, end], width=8)
