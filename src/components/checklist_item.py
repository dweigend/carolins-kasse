"""Checklist item component for recipe ingredients."""

import pygame

from src.constants import SUCCESS, TEXT_MUTED, TEXT_PRIMARY
from src.utils.fonts import custom

# Checkbox dimensions
_BOX_SIZE = 26
_BOX_RADIUS = 4
_BOX_BORDER = 2


class ChecklistItem:
    """A checklist item showing ingredient name with check/uncheck state.

    Attributes:
        rect: pygame.Rect for the item area
        checked: Whether the item is checked off
    """

    HEIGHT = 45

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        *,
        name: str,
        quantity: int = 1,
        checked: bool = False,
    ) -> None:
        """Create a checklist item.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            width: Item width
            name: Ingredient name to display
            quantity: How many of this ingredient needed
            checked: Initial checked state
        """
        self.rect = pygame.Rect(x, y, width, self.HEIGHT)
        self.name = name
        self.quantity = quantity
        self.checked = checked

    def set_checked(self, checked: bool) -> None:
        """Set the checked state."""
        self.checked = checked

    def render(self, surface: pygame.Surface) -> None:
        """Draw the checklist item."""
        font = custom(32)

        # Draw checkbox
        box_x = self.rect.x
        box_y = self.rect.y + (self.HEIGHT - _BOX_SIZE) // 2
        box_rect = pygame.Rect(box_x, box_y, _BOX_SIZE, _BOX_SIZE)

        if self.checked:
            pygame.draw.rect(surface, SUCCESS, box_rect, border_radius=_BOX_RADIUS)
            # Checkmark (✓)
            cx, cy = box_rect.centerx, box_rect.centery
            pygame.draw.lines(
                surface,
                (255, 255, 255),
                False,
                [(cx - 6, cy), (cx - 2, cy + 5), (cx + 7, cy - 5)],
                3,
            )
        else:
            pygame.draw.rect(
                surface, TEXT_MUTED, box_rect, _BOX_BORDER, border_radius=_BOX_RADIUS
            )

        # Text
        text_x = box_x + _BOX_SIZE + 12
        text_color = TEXT_MUTED if self.checked else TEXT_PRIMARY

        display_text = (
            f"{self.quantity}× {self.name}" if self.quantity > 1 else self.name
        )
        name_text = font.render(display_text, True, text_color)

        text_y = self.rect.y + (self.HEIGHT - name_text.get_height()) // 2
        surface.blit(name_text, (text_x, text_y))

        # Strikethrough if checked
        if self.checked:
            line_y = text_y + name_text.get_height() // 2
            pygame.draw.line(
                surface,
                TEXT_MUTED,
                (text_x, line_y),
                (text_x + name_text.get_width(), line_y),
                2,
            )
