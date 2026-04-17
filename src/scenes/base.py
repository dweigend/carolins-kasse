"""Abstract base class for all scenes."""

from abc import ABC, abstractmethod

import pygame


class Scene(ABC):
    """Base class that all scenes must inherit from.

    Provides common infrastructure for scene navigation and initialization.

    Attributes:
        _next_scene: Scene name to transition to (or None)
        _initialized: Whether UI has been initialized
    """

    _next_scene: str | None = None
    _initialized: bool = False

    def _go_to(self, scene: str) -> None:
        """Request transition to another scene.

        Args:
            scene: Name of the scene to transition to
        """
        self._next_scene = scene

    def _consume_next_scene(self) -> str | None:
        """Get and clear pending scene transition.

        Returns:
            Scene name if transition pending, None otherwise
        """
        result = self._next_scene
        self._next_scene = None
        return result

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
