"""Scene manager for handling scene transitions."""

import pygame

from src.scenes.base import Scene


class SceneManager:
    """Manages scenes and transitions between them."""

    def __init__(self, scenes: dict[str, Scene], initial: str) -> None:
        """Initialize the scene manager.

        Args:
            scenes: Dictionary mapping scene names to Scene instances.
            initial: Name of the initial scene to display.
        """
        self.scenes = scenes
        self.current_name = initial
        self.current_scene = scenes[initial]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Pass event to current scene and handle transitions.

        Args:
            event: The pygame event to handle.
        """
        next_scene = self.current_scene.handle_event(event)
        if next_scene and next_scene in self.scenes:
            self.current_name = next_scene
            self.current_scene = self.scenes[next_scene]

    def update(self) -> None:
        """Update the current scene."""
        self.current_scene.update()

    def render(self, screen: pygame.Surface) -> None:
        """Render the current scene.

        Args:
            screen: The pygame surface to render to.
        """
        self.current_scene.render(screen)
