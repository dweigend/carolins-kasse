"""Abstract base class for all scenes."""

from abc import ABC, abstractmethod

import pygame


class Scene(ABC):
    """Base class that all scenes must inherit from."""

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle a pygame event.

        Args:
            event: The pygame event to handle.

        Returns:
            Name of scene to switch to, or None to stay on current scene.
        """
        pass

    @abstractmethod
    def update(self) -> None:
        """Update scene state. Called once per frame."""
        pass

    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """Render the scene to the screen.

        Args:
            screen: The pygame surface to render to.
        """
        pass
