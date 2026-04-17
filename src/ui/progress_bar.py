"""Progress bar rendering utility.

Draws rounded progress bars with system colors.
"""

import pygame

from src.constants import ORANGE, DANGER


def draw_progress_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    progress: float,
    bg_color: tuple[int, int, int] = ORANGE,
    bar_color: tuple[int, int, int] = DANGER,
) -> None:
    """Draw a progress bar with rounded corners.

    Args:
        surface: Pygame surface to draw on
        x, y: Top-left position
        width: Bar width in pixels
        height: Bar height in pixels
        progress: Progress value (0.0 to 1.0)
        bg_color: Background track color (default: ORANGE)
        bar_color: Progress bar color (default: DANGER/RED)
    """
    # Clamp progress to valid range
    progress = max(0.0, min(1.0, progress))

    # Radius: half height for pill-shaped ends
    border_radius = height // 2

    # 1. Draw background track
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, bg_color, bg_rect, border_radius=border_radius)

    # 2. Draw progress bar (minimum width = height to avoid visual glitches)
    if progress > 0.0:
        bar_width = max(int(width * progress), height)
        bar_rect = pygame.Rect(x, y, bar_width, height)
        pygame.draw.rect(surface, bar_color, bar_rect, border_radius=border_radius)
