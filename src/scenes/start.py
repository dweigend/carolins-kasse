"""Start scene — fullscreen splash image before login."""

from pathlib import Path

import pygame

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes.base import Scene

_SPLASH_PATH = (
    Path(__file__).parent.parent.parent / "assets" / "680er" / "startbildschirm.png"
)


class StartScene(Scene):
    """Fullscreen splash screen. Any key or touch goes to login."""

    def __init__(self) -> None:
        """Initialize start scene."""
        self._splash: pygame.Surface | None = None

    def _init_ui(self) -> None:
        """Load and scale splash image."""
        if self._initialized:
            return
        img = pygame.image.load(str(_SPLASH_PATH)).convert()
        self._splash = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self._initialized = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Any key press or touch → go to login."""
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            return "login"
        return None

    def update(self) -> None:
        """No state updates needed."""

    def render(self, screen: pygame.Surface) -> None:
        """Draw fullscreen splash image."""
        self._init_ui()
        if self._splash:
            screen.blit(self._splash, (0, 0))
