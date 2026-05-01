"""Carolin's Kasse - Main entry point."""

import pygame

from src.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes import (
    AdminScene,
    LoginScene,
    MathGameScene,
    MenuScene,
    PickerScene,
    RecipeScene,
    ScanScene,
    StartScene,
    SceneManager,
)
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


def main() -> None:
    """Initialize pygame and run the main game loop."""
    init_database()
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Carolin's Kasse 🛒")
    clock = pygame.time.Clock()

    # Shell: shared UI frame around all scenes
    shell = FrameShell()

    # Setup scenes
    scenes = {
        "start": StartScene(),
        "login": LoginScene(),
        "admin": AdminScene(),
        "menu": MenuScene(),
        "scan": ScanScene(),
        "recipe": RecipeScene(),
        "math_game": MathGameScene(),
        "picker": PickerScene(),
    }
    manager = SceneManager(scenes, initial="start")

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
                        manager.switch_to("login")
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
