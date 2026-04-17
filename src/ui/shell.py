"""Shared UI shell — renders paper background, frame overlay, and shell UI.

The FrameShell wraps every scene with a consistent visual frame:
1. Paper texture background (fullscreen)
2. Scene content (rendered by the scene itself)
3. Frame overlay (colored per user)
4. Shell UI: title, footer (balance bar + money icon), close button
"""

from pathlib import Path

import pygame

from src.constants import (
    BALANCE_BAR_MAX,
    BLACK,
    COLOR_TO_FRAME,
    DANGER,
    FRAME_TITLE_COLOR,
    ORANGE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHELL_CLOSE_POS,
    SHELL_COUNT_X,
    SHELL_COUNT_Y,
    SHELL_MONEY_ICON_X,
    SHELL_MONEY_ICON_Y,
    SHELL_PROGRESS_H,
    SHELL_PROGRESS_W,
    SHELL_PROGRESS_X,
    SHELL_PROGRESS_Y,
    SHELL_TITLE_POS,
)
from src.ui.progress_bar import draw_progress_bar
from src.ui.texture import generate_paper_texture
from src.utils.database import User
from src.utils.fonts import bold, caption

_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

# Scenes that show NO frame overlay (pre-login screens)
NO_FRAME_SCENES = {"start", "login"}


class FrameShell:
    """Renders the shared UI shell around scene content."""

    def __init__(self) -> None:
        """Initialize shell — generate paper texture and load assets."""
        self._paper_texture = generate_paper_texture(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._frames: dict[str, pygame.Surface] = {}
        self._money_icon = self._load_icon("40er/geld.png")
        self._close_font = bold()
        self._title_font = bold()
        self._count_font = caption()

    # ─── Public API ────────────────────────────────────────────

    def render_background(self, screen: pygame.Surface) -> None:
        """Render paper texture background (step 1 of rendering)."""
        screen.blit(self._paper_texture, (0, 0))

    def render_overlay(
        self, screen: pygame.Surface, user: User | None, scene_name: str
    ) -> None:
        """Render frame overlay + shell UI (step 3+4 of rendering).

        Args:
            screen: Pygame surface to render to
            user: Currently logged-in user (None if not logged in)
            scene_name: Current scene name (to skip frame on login/start)
        """
        if scene_name in NO_FRAME_SCENES or user is None:
            return

        frame_key = COLOR_TO_FRAME.get(user.color, "hintergrund/linie_blau")

        # Frame overlay
        frame = self._get_frame(frame_key)
        screen.blit(frame, (0, 0))

        # Title in top notch
        title_color = FRAME_TITLE_COLOR.get(frame_key, DANGER)
        title_surface = self._title_font.render(user.name.upper(), True, title_color)
        screen.blit(title_surface, SHELL_TITLE_POS)

        # Close button (X) — top right
        close_surface = self._close_font.render("X", True, DANGER)
        screen.blit(close_surface, SHELL_CLOSE_POS)

        # Footer: money icon + progress bar + count
        self._render_footer(screen, user)

    def get_content_rect(self) -> pygame.Rect:
        """Get the renderable content area inside the frame.

        Returns:
            Rect defining the area scenes should render into.
        """
        # Content area: inside frame borders, below title notch, above footer
        return pygame.Rect(24, 72, SCREEN_WIDTH - 48, SCREEN_HEIGHT - 72 - 60)

    def handle_close_click(self, event: pygame.event.Event) -> bool:
        """Check if the close button (X) was clicked.

        Args:
            event: Pygame event

        Returns:
            True if close button was clicked
        """
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False
        # Hit area around the X button
        close_rect = pygame.Rect(
            SHELL_CLOSE_POS[0] - 10, SHELL_CLOSE_POS[1] - 10, 50, 50
        )
        return close_rect.collidepoint(event.pos)

    # ─── Private Helpers ───────────────────────────────────────

    def _get_frame(self, frame_key: str) -> pygame.Surface:
        """Get cached scaled frame surface."""
        if frame_key not in self._frames:
            path = _ASSETS_DIR / f"{frame_key}.png"
            img = pygame.image.load(str(path)).convert_alpha()
            self._frames[frame_key] = pygame.transform.scale(
                img, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        return self._frames[frame_key]

    def _load_icon(self, filename: str) -> pygame.Surface | None:
        """Load a small icon from assets."""
        path = _ASSETS_DIR / filename
        if not path.exists():
            return None
        return pygame.image.load(str(path)).convert_alpha()

    def _render_footer(self, screen: pygame.Surface, user: User) -> None:
        """Render footer area: money icon + progress bar + balance count."""
        # Money icon
        if self._money_icon:
            screen.blit(self._money_icon, (SHELL_MONEY_ICON_X, SHELL_MONEY_ICON_Y))

        # Progress bar (balance / max)
        progress = min(user.balance / BALANCE_BAR_MAX, 1.0) if user.balance >= 0 else 0
        draw_progress_bar(
            screen,
            SHELL_PROGRESS_X,
            SHELL_PROGRESS_Y,
            SHELL_PROGRESS_W,
            SHELL_PROGRESS_H,
            progress,
            ORANGE,
            DANGER,
        )

        # Balance count text
        count_text = self._count_font.render(str(int(user.balance)), True, BLACK)
        screen.blit(count_text, (SHELL_COUNT_X, SHELL_COUNT_Y))
