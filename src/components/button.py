"""Clickable button component."""

from collections.abc import Callable

import pygame

from src.components.mixins import ClickableMixin


class Button(ClickableMixin):
    """A clickable button with image or color fill.

    Attributes:
        rect: pygame.Rect for position and collision detection
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        image: pygame.Surface | None = None,
        color: tuple[int, int, int] | None = None,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """Create a button.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            width: Button width
            height: Button height
            image: Optional surface to display
            color: Optional fill color (used if no image)
            on_click: Optional callback when clicked
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.image = image
        self.color = color
        self.on_click = on_click
        self._pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events.

        Args:
            event: pygame event

        Returns:
            True if button was clicked, False otherwise
        """
        return self._handle_click(event, self.rect, self.on_click)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the button.

        Args:
            surface: Surface to draw on
        """
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        elif self.color:
            pygame.draw.rect(surface, self.color, self.rect)
