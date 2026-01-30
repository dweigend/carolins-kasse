"""Main menu scene with 4 game mode tiles."""

import pygame

from src.components.button import Button
from src.constants import LIGHT_PINK, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from src.scenes.base import Scene
from src.utils import assets

# Layout constants
TILE_SIZE = 180
TILE_GAP = 40
TITLE_HEIGHT = 100

# Calculate grid position (centered)
GRID_WIDTH = 2 * TILE_SIZE + TILE_GAP
GRID_HEIGHT = 2 * TILE_SIZE + TILE_GAP
START_X = (SCREEN_WIDTH - GRID_WIDTH) // 2
START_Y = TITLE_HEIGHT + (SCREEN_HEIGHT - TITLE_HEIGHT - GRID_HEIGHT) // 2


class MenuScene(Scene):
    """Main menu with 4 clickable tiles for game modes."""

    def __init__(self) -> None:
        """Initialize menu scene."""
        self._next_scene: str | None = None
        self._buttons: list[Button] = []
        self._font: pygame.font.Font | None = None
        self._initialized = False

    def _init_ui(self) -> None:
        """Initialize UI elements (called after pygame.init)."""
        if self._initialized:
            return

        # Load tile images
        tiles = [
            ("menue/einkauf", "scan", START_X, START_Y),
            ("menue/rezept", "recipe", START_X + TILE_SIZE + TILE_GAP, START_Y),
            (
                "menue/rechenspiel",
                "math_game",
                START_X,
                START_Y + TILE_SIZE + TILE_GAP,
            ),
            (
                "menue/kasse",
                "cashier",
                START_X + TILE_SIZE + TILE_GAP,
                START_Y + TILE_SIZE + TILE_GAP,
            ),
        ]

        for asset_name, target_scene, x, y in tiles:
            image = assets.get(asset_name)
            button = Button(
                x,
                y,
                TILE_SIZE,
                TILE_SIZE,
                image=image,
                on_click=lambda s=target_scene: self._go_to(s),
            )
            self._buttons.append(button)

        # Load font for title
        self._font = pygame.font.Font(None, 48)
        self._initialized = True

    def _go_to(self, scene: str) -> None:
        """Set next scene to navigate to."""
        self._next_scene = scene

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events.

        Args:
            event: pygame event

        Returns:
            Scene name to switch to, or None
        """
        self._init_ui()

        for button in self._buttons:
            button.handle_event(event)

        # Return and reset next scene
        result = self._next_scene
        self._next_scene = None
        return result

    def update(self) -> None:
        """Update scene state."""
        pass

    def render(self, screen: pygame.Surface) -> None:
        """Draw the menu.

        Args:
            screen: Surface to draw on
        """
        self._init_ui()

        # Background
        screen.fill(LIGHT_PINK)

        # Title
        if self._font:
            title = self._font.render("Was möchtest du spielen?", True, WHITE)
            title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
            screen.blit(title, title_rect)

        # Tiles
        for button in self._buttons:
            button.render(screen)
