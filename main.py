"""Carolin's Kasse - Main entry point."""

import pygame

from src.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes import SceneManager
from src.scenes.test_scene import TestScene


def main() -> None:
    """Initialize pygame and run the main game loop."""
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Carolin's Kasse 🛒")
    clock = pygame.time.Clock()

    # Setup scenes
    scenes = {
        "test": TestScene(),
    }
    manager = SceneManager(scenes, initial="test")

    # Main loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                manager.handle_event(event)

        # Update
        manager.update()

        # Render
        manager.render(screen)
        pygame.display.flip()

        # Cap framerate
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
