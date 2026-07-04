"""Scene manager for handling scene transitions."""

from collections.abc import Callable, Mapping

import pygame

from src.scenes.base import Scene

type SceneFactory = Callable[[], Scene]
type SceneDefinition = Scene | SceneFactory


class SceneManager:
    """Manages scenes and transitions between them."""

    def __init__(self, scenes: Mapping[str, SceneDefinition], initial: str) -> None:
        """Initialize the scene manager.

        Args:
            scenes: Mapping of scene names to Scene instances or factories.
            initial: Name of the initial scene to display.
        """
        self.scenes: dict[str, Scene] = {}
        self._scene_factories: dict[str, SceneFactory] = {}
        self._scene_names = set(scenes)
        for scene_name, scene_definition in scenes.items():
            if isinstance(scene_definition, Scene):
                self.scenes[scene_name] = scene_definition
            else:
                self._scene_factories[scene_name] = scene_definition

        if initial not in self._scene_names:
            raise KeyError(f"Unknown initial scene: {initial}")

        self.current_name = initial
        self.current_scene = self._get_scene(initial)
        self._enter_current_scene()

    def switch_to(self, scene_name: str, *, reset_user_state: bool = False) -> None:
        """Switch to a scene directly (used by main.py for shell actions).

        Args:
            scene_name: Name of the scene to switch to.
            reset_user_state: Whether to clear per-user scene state first.
        """
        if not self._has_scene(scene_name):
            return

        if reset_user_state:
            self.reset_user_state()

        self.current_name = scene_name
        self.current_scene = self._get_scene(scene_name)
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

    def _has_scene(self, scene_name: str) -> bool:
        """Return whether a scene name is registered."""
        return scene_name in self._scene_names

    def _get_scene(self, scene_name: str) -> Scene:
        """Return a cached scene instance, constructing it on first use."""
        if scene_name in self.scenes:
            return self.scenes[scene_name]

        factory = self._scene_factories[scene_name]
        scene = factory()
        if not isinstance(scene, Scene):
            raise TypeError(f"Scene factory for {scene_name!r} did not return a Scene")
        self.scenes[scene_name] = scene
        return scene

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
        if next_scene and self._has_scene(next_scene):
            self._activate_next_scene(next_scene)

    def update(self) -> None:
        """Update the current scene."""
        self.current_scene.update()
        next_scene = self.current_scene._consume_next_scene()
        if next_scene and self._has_scene(next_scene):
            self._activate_next_scene(next_scene)

    def render(self, screen: pygame.Surface) -> None:
        """Render the current scene.

        Args:
            screen: The pygame surface to render to.
        """
        self.current_scene.render(screen)
