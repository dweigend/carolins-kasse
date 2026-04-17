"""Reusable mixins for UI components."""

from collections.abc import Callable
from typing import Any

import pygame


class ClickableMixin:
    """Mixin for standardized click detection in UI components.

    Usage:
        class MyButton(ClickableMixin):
            def __init__(self):
                self._pressed = False  # Required!

            def handle_event(self, event):
                return self._handle_click(event, self.rect, self.on_click)
                # Or with args: self._handle_click(event, self.rect, self.on_click, product_id)
    """

    _pressed: bool

    def _handle_click(
        self,
        event: pygame.event.Event,
        rect: pygame.Rect,
        on_click: Callable[..., None] | None = None,
        *args: Any,
    ) -> bool:
        """Handle mouse click detection. Calls on_click(*args) on success."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rect.collidepoint(event.pos):
                self._pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and rect.collidepoint(event.pos):
                self._pressed = False
                if on_click:
                    on_click(*args)
                return True
            self._pressed = False

        return False
