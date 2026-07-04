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
        self._enter_current_scene()

    def switch_to(self, scene_name: str, *, reset_user_state: bool = False) -> None:
        """Switch to a scene directly (used by main.py for shell actions).

        Args:
            scene_name: Name of the scene to switch to.
            reset_user_state: Whether to clear per-user scene state first.
        """
        if scene_name not in self.scenes:
            return

        if reset_user_state:
            self.reset_user_state()

        self.current_name = scene_name
        self.current_scene = self.scenes[scene_name]
        self._enter_current_scene()

    def reset_user_state(self) -> None:
        """Clear per-user state held by reusable scene instances."""
        for scene in self.scenes.values():
            reset = getattr(scene, "reset_user_state", None)
            if callable(reset):
                reset()

    def _enter_current_scene(self) -> None:
        """Run a scene enter hook when a scene provides one."""
        on_enter = getattr(self.current_scene, "on_enter", None)
        if callable(on_enter):
            on_enter()

    def _activate_next_scene(self, scene_name: str) -> None:
        """Switch to the next scene and reset after a successful login."""
        reset_for_login = self.current_name == "login" and scene_name != "login"
        self.switch_to(scene_name, reset_user_state=reset_for_login)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Pass event to current scene and handle transitions.

        Args:
            event: The pygame event to handle.
        """
        next_scene = self.current_scene.handle_event(event)
        if next_scene and next_scene in self.scenes:
            self._activate_next_scene(next_scene)

    def update(self) -> None:
        """Update the current scene."""
        self.current_scene.update()
        next_scene = self.current_scene._consume_next_scene()
        if next_scene and next_scene in self.scenes:
            self._activate_next_scene(next_scene)

    def render(self, screen: pygame.Surface) -> None:
        """Render the current scene.

        Args:
            screen: The pygame surface to render to.
        """
        self.current_scene.render(screen)
