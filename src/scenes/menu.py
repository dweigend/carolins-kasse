"""Main menu scene with 3 illustrated game mode tiles."""

from pathlib import Path

import pygame

from src.components.button import Button
from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_PRIMARY
from src.scenes.base import Scene
from src.utils import state
from src.utils.fonts import caption

_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

# 3 tiles in a horizontal row: Rezept | Einkauf | Rechnen
_TILE_DEFS: list[tuple[str, str, str]] = [
    ("680er/kochbuch.png", "recipe", "Rezept"),
    ("680er/einkaufskorb.png", "scan", "Einkaufen"),
    ("680er/taschenrechner.png", "math_game", "Rechnen"),
]

# Layout
TILE_SIZE = 200
TILE_GAP = 60
LABEL_OFFSET_Y = 8


class MenuScene(Scene):
    """Main menu with 3 clickable illustrated tiles in a row."""

    def __init__(self) -> None:
        """Initialize menu scene."""
        self._buttons: list[Button] = []
        self._labels: list[tuple[str, int, int]] = []

    def _init_ui(self) -> None:
        """Load tile images and create buttons."""
        if self._initialized:
            return

        # Center 3 tiles horizontally, vertically in content area
        total_w = len(_TILE_DEFS) * TILE_SIZE + (len(_TILE_DEFS) - 1) * TILE_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        tile_y = (SCREEN_HEIGHT - TILE_SIZE) // 2 - 20

        for i, (asset_file, target_scene, label_text) in enumerate(_TILE_DEFS):
            x = start_x + i * (TILE_SIZE + TILE_GAP)
            image = self._load_tile(asset_file)
            button = Button(
                x,
                tile_y,
                TILE_SIZE,
                TILE_SIZE,
                image=image,
                on_click=lambda s=target_scene: self._go_to(s),
            )
            self._buttons.append(button)
            self._labels.append(
                (label_text, x + TILE_SIZE // 2, tile_y + TILE_SIZE + LABEL_OFFSET_Y)
            )

        self._initialized = True

    def _load_tile(self, asset_file: str) -> pygame.Surface:
        """Load and scale a 680er tile image."""
        path = _ASSETS_DIR / asset_file
        img = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle tile clicks."""
        self._init_ui()

        for button in self._buttons:
            button.handle_event(event)

        return self._consume_next_scene()

    def update(self) -> None:
        """Check global time bonus."""
        state.check_time_bonus()

    def render(self, screen: pygame.Surface) -> None:
        """Draw menu tiles with labels. No background fill (shell handles it)."""
        self._init_ui()

        for button in self._buttons:
            button.render(screen)

        label_font = caption()
        for text, cx, y in self._labels:
            surface = label_font.render(text, True, TEXT_PRIMARY)
            rect = surface.get_rect(centerx=cx, y=y)
            screen.blit(surface, rect)
