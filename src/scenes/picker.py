"""Product picker scene for touch selection."""

import pygame

from src.components.button import Button
from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from src.scenes.base import Scene

BG_COLOR = (245, 245, 250)
HEADER_COLOR = (100, 100, 120)


class PickerScene(Scene):
    """Product picker for items without barcodes (fruits, etc.)."""

    def __init__(self) -> None:
        """Initialize picker scene."""
        self._next_scene: str | None = None
        self._font: pygame.font.Font | None = None
        self._back_button: Button | None = None
        self._initialized = False

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        self._font = pygame.font.Font(None, 36)
        self._back_button = Button(
            20, 20, 100, 40, color=(200, 200, 200), on_click=lambda: self._go_to("scan")
        )
        self._initialized = True

    def _go_to(self, scene: str) -> None:
        """Set next scene."""
        self._next_scene = scene

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()
        if self._back_button:
            self._back_button.handle_event(event)
        result = self._next_scene
        self._next_scene = None
        return result

    def update(self) -> None:
        """Update scene state."""
        pass

    def render(self, screen: pygame.Surface) -> None:
        """Draw the picker screen."""
        self._init_ui()

        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, 80))

        if self._font:
            title = self._font.render("Produkt auswählen", True, WHITE)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 25))

            info = self._font.render("Wähle Obst oder Gemüse...", True, (100, 100, 100))
            screen.blit(
                info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT // 2)
            )

            back_text = self._font.render("← Zurück", True, WHITE)
            screen.blit(back_text, (30, 25))
