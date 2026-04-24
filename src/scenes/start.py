"""Start scene — fullscreen splash image before login."""

from pathlib import Path

import pygame

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes.base import Scene

_SPLASH_PATH = (
    Path(__file__).parent.parent.parent / "assets" / "680er" / "startbildschirm.png"
)
_DISPLAY_DURATION_MS = 5_000


class StartScene(Scene):
    """Fullscreen splash screen shown before the login prompt."""

    def __init__(self) -> None:
        """Initialize start scene."""
        self._splash: pygame.Surface | None = None
        self._started_at_ms: int | None = None

    def _init_ui(self) -> None:
        """Load and scale splash image."""
        if self._initialized:
            return
        img = pygame.image.load(str(_SPLASH_PATH)).convert()
        self._splash = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self._started_at_ms = pygame.time.get_ticks()
        self._initialized = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Ignore input while the splash screen is visible."""
        return None

    def update(self) -> None:
        """Advance to login after the configured display duration."""
        self._init_ui()
        if self._started_at_ms is None:
            return
        if pygame.time.get_ticks() - self._started_at_ms >= _DISPLAY_DURATION_MS:
            self._go_to("login")

    def render(self, screen: pygame.Surface) -> None:
        """Draw fullscreen splash image."""
        self._init_ui()
        if self._splash:
            screen.blit(self._splash, (0, 0))
