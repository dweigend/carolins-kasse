"""Carolin's Kasse - Main entry point."""

import pygame

from src.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes.base import Scene
from src.scenes.manager import SceneDefinition, SceneManager
from src.scenes.start import StartScene
from src.ui.shell import NO_FRAME_SCENES, FrameShell
from src.utils import state
from src.utils.database import init_database


def normalize_touch_event(event: pygame.event.Event) -> pygame.event.Event:
    """Map SDL finger events to the mouse events used by the scene UI."""
    if event.type == pygame.FINGERDOWN:
        return pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": finger_position(event), "button": 1},
        )
    if event.type == pygame.FINGERUP:
        return pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            {"pos": finger_position(event), "button": 1},
        )
    if event.type == pygame.FINGERMOTION:
        return pygame.event.Event(
            pygame.MOUSEMOTION,
            {
                "pos": finger_position(event),
                "rel": (
                    round(event.dx * SCREEN_WIDTH),
                    round(event.dy * SCREEN_HEIGHT),
                ),
                "buttons": (1, 0, 0),
            },
        )
    return event


def finger_position(event: pygame.event.Event) -> tuple[int, int]:
    """Return a pixel position for a normalized SDL finger event."""
    x = max(0, min(SCREEN_WIDTH - 1, round(event.x * SCREEN_WIDTH)))
    y = max(0, min(SCREEN_HEIGHT - 1, round(event.y * SCREEN_HEIGHT)))
    return x, y


def create_scene_registry() -> dict[str, SceneDefinition]:
    """Create the scene registry while keeping non-start scenes lazy."""
    return {
        "start": StartScene(),
        "login": _create_login_scene,
        "admin": _create_admin_scene,
        "menu": _create_menu_scene,
        "scan": _create_scan_scene,
        "recipe": _create_recipe_scene,
        "math_game": _create_math_game_scene,
        "picker": _create_picker_scene,
    }


def _create_login_scene() -> Scene:
    """Create the login scene on first use."""
    from src.scenes.login import LoginScene

    return LoginScene()


def _create_admin_scene() -> Scene:
    """Create the admin scene on first use."""
    from src.scenes.admin import AdminScene

    return AdminScene()


def _create_menu_scene() -> Scene:
    """Create the menu scene on first use."""
    from src.scenes.menu import MenuScene

    return MenuScene()


def _create_scan_scene() -> Scene:
    """Create the scan scene on first use."""
    from src.scenes.scan import ScanScene

    return ScanScene()


def _create_recipe_scene() -> Scene:
    """Create the recipe scene on first use."""
    from src.scenes.recipe import RecipeScene

    return RecipeScene()


def _create_math_game_scene() -> Scene:
    """Create the math game scene on first use."""
    from src.scenes.math_game import MathGameScene

    return MathGameScene()


def _create_picker_scene() -> Scene:
    """Create the picker scene on first use."""
    from src.scenes.picker import PickerScene

    return PickerScene()


def main() -> None:
    """Initialize pygame and run the main game loop."""
    init_database()
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Carolin's Kasse 🛒")
    clock = pygame.time.Clock()

    # Shell: shared UI frame around all scenes
    shell = FrameShell()

    manager = SceneManager(create_scene_registry(), initial="start")

    # Main loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            event = normalize_touch_event(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                # Shell close button (X):
                #   Menu → logout → login
                #   Sub-scene → back to menu
                if (
                    manager.current_name not in NO_FRAME_SCENES
                    and state.get_current_user()
                    and shell.handle_close_click(event)
                ):
                    if manager.current_name in {"menu", "admin"}:
                        state.logout()
                        manager.switch_to("login", reset_user_state=True)
                    else:
                        manager.switch_to("menu")
                    continue
                manager.handle_event(event)

        # Update
        manager.update()

        # Render: Shell background → Scene content → Shell overlay
        shell.render_background(screen)
        manager.render(screen)
        current_user = state.get_current_user()
        shell.render_overlay(screen, current_user, manager.current_name)

        pygame.display.flip()

        # Cap framerate
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
