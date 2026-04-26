"""Login scene for scanning user badges."""

from pathlib import Path

import pygame

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from src.scenes.base import Scene
from src.scenes.mixins import MessageMixin
from src.utils import state
from src.utils.database import get_user
from src.utils.fonts import body

_LOGIN_IMAGE_PATH = (
    Path(__file__).parent.parent.parent / "assets" / "680er" / "karte_scannen.png"
)


class LoginScene(MessageMixin, Scene):
    """User scans their badge to log in from a fullscreen prompt image."""

    def __init__(self) -> None:
        """Initialize login scene."""
        from src.utils.input import InputManager

        self._input_manager = InputManager()
        self._login_image: pygame.Surface | None = None

    def _init_ui(self) -> None:
        """Load and scale the fullscreen login image."""
        if self._initialized:
            return
        image = pygame.image.load(str(_LOGIN_IMAGE_PATH)).convert()
        self._login_image = pygame.transform.smoothscale(
            image, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self._initialized = True

    def _handle_barcode(self, barcode: str) -> None:
        """Process a scanned barcode."""
        if not barcode.startswith("200"):
            self._show_message("Das ist keine Benutzerkarte!")
            return

        user = get_user(barcode)
        if user:
            state.start_session(user)
            self._show_message(f"Hallo {user.name}!")
            if user.is_admin:
                self._go_to("admin")
            else:
                self._go_to("menu")
        else:
            self._show_message("Karte nicht erkannt!")

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        from src.utils.input import InputType

        self._init_ui()

        input_events = self._input_manager.process_event(event)
        for inp in input_events:
            if inp.type == InputType.BARCODE:
                self._handle_barcode(str(inp.value))

        return self._consume_next_scene()

    def update(self) -> None:
        """Update scene state."""
        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Draw fullscreen login image and optional feedback message."""
        self._init_ui()

        if self._login_image:
            screen.blit(self._login_image, (0, 0))

        self._render_message(
            screen,
            body(),
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 72,
            center_x=True,
        )
