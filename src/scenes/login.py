"""Login scene for scanning user badges."""

from pathlib import Path

import pygame

from src.constants import BLUE, GREY_MEDIUM, SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_PRIMARY
from src.scenes.base import Scene
from src.scenes.mixins import MessageMixin
from src.utils import state
from src.utils.database import get_user
from src.utils.fonts import bold, body, caption

_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

# Both avatars displayed side by side on login screen
_AVATAR_PATHS = [
    _ASSETS_DIR / "680er" / "avata_carolin.png",
    _ASSETS_DIR / "680er" / "avata_annelie.png",
]
_AVATAR_DISPLAY_SIZE = 160
_AVATAR_GAP = 40


class LoginScene(MessageMixin, Scene):
    """User scans their badge to log in. No frame overlay (pre-login)."""

    def __init__(self) -> None:
        """Initialize login scene."""
        from src.utils.input import InputManager

        self._input_manager = InputManager()
        self._avatars: list[pygame.Surface] = []

    def _init_ui(self) -> None:
        """Load avatar images and fonts."""
        if self._initialized:
            return
        for path in _AVATAR_PATHS:
            if path.exists():
                img = pygame.image.load(str(path)).convert_alpha()
                scaled = pygame.transform.scale(
                    img, (_AVATAR_DISPLAY_SIZE, _AVATAR_DISPLAY_SIZE)
                )
                self._avatars.append(scaled)
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
        """Draw login screen on paper background (rendered by shell)."""
        self._init_ui()

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Avatars side by side (centered)
        if self._avatars:
            total_w = (
                len(self._avatars) * _AVATAR_DISPLAY_SIZE
                + (len(self._avatars) - 1) * _AVATAR_GAP
            )
            start_x = cx - total_w // 2
            avatar_y = cy - _AVATAR_DISPLAY_SIZE - 20
            for i, avatar in enumerate(self._avatars):
                x = start_x + i * (_AVATAR_DISPLAY_SIZE + _AVATAR_GAP)
                screen.blit(avatar, (x, avatar_y))

        # Title
        title_font = bold()
        title_surface = title_font.render("Willkommen!", True, BLUE)
        title_rect = title_surface.get_rect(centerx=cx, y=cy + 10)
        screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle_font = body()
        subtitle_surface = subtitle_font.render(
            "Bitte scanne deine Karte!", True, TEXT_PRIMARY
        )
        subtitle_rect = subtitle_surface.get_rect(centerx=cx, y=cy + 65)
        screen.blit(subtitle_surface, subtitle_rect)

        # Hint
        hint_font = caption()
        hint_surface = hint_font.render(
            "Halte deine Karte vor den Scanner", True, GREY_MEDIUM
        )
        hint_rect = hint_surface.get_rect(centerx=cx, y=cy + 110)
        screen.blit(hint_surface, hint_rect)

        # Feedback message
        msg_font = body()
        self._render_message(screen, msg_font, cx, cy + 160, center_x=True)
