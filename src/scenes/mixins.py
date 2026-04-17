"""Reusable mixins for scene classes."""

import pygame


class MessageMixin:
    """Mixin for temporary feedback messages in scenes.

    Provides message display functionality that was previously duplicated
    across scan.py, recipe.py, math_game.py, and cashier.py.

    Usage:
        class MyScene(MessageMixin, Scene):
            def __init__(self):
                # MessageMixin attributes are initialized on first use
                ...

            def update(self):
                self._update_message_timer()

            def render(self, screen):
                self._render_message(screen, font, x, y)
    """

    # These will be initialized on first access via _show_message
    _message: str
    _message_timer: int
    _message_color: tuple[int, int, int]

    # Default message color
    _DEFAULT_MESSAGE_COLOR: tuple[int, int, int] = (80, 80, 80)

    def _show_message(
        self,
        text: str,
        duration_frames: int = 90,
        *,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        """Show a temporary feedback message.

        Args:
            text: The message to display
            duration_frames: How many frames to show the message (default 90 = 3 sec at 30fps)
            color: Optional RGB color tuple (default: gray)
        """
        self._message = text
        self._message_timer = duration_frames
        self._message_color = color or self._DEFAULT_MESSAGE_COLOR

    def _update_message_timer(self) -> None:
        """Decrease message timer. Call this in update()."""
        # Initialize if not set (lazy initialization)
        if not hasattr(self, "_message_timer"):
            self._message_timer = 0
            self._message = ""
            self._message_color = self._DEFAULT_MESSAGE_COLOR
            return

        if self._message_timer > 0:
            self._message_timer -= 1
            if self._message_timer == 0:
                self._message = ""

    def _render_message(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        y: int,
        color: tuple[int, int, int] | None = None,
        *,
        center_x: bool = False,
    ) -> None:
        """Render the current message if active.

        Args:
            screen: Pygame surface to draw on
            font: Font to use for rendering
            x: X position (or center reference if center_x=True)
            y: Y position
            color: RGB color override (default: uses color set in _show_message)
            center_x: If True, center the text around x position
        """
        if not hasattr(self, "_message") or not self._message:
            return

        final_color = color or getattr(
            self, "_message_color", self._DEFAULT_MESSAGE_COLOR
        )
        msg_text = font.render(self._message, True, final_color)
        if center_x:
            x = x - msg_text.get_width() // 2
        screen.blit(msg_text, (x, y))

    def _has_message(self) -> bool:
        """Check if there's an active message."""
        return hasattr(self, "_message") and bool(self._message)
