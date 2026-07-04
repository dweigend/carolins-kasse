"""Lightweight paper texture generator for the kiosk background.

This stays on the kiosk cold path, so it avoids NumPy and per-pixel noise.
"""

import pygame

from src.constants import CREAM

PAPER_LINE_COLOR = (247, 235, 210, 42)
PAPER_SHADOW_COLOR = (238, 222, 194, 28)
PAPER_DOT_COLOR = (242, 228, 201, 48)
LINE_SPACING = 96
SHADOW_LINE_SPACING = 128
DOT_ROW_SPACING = 64
DOT_COLUMN_SPACING = 84
DOT_RADIUS = 1


def generate_paper_texture(width: int, height: int) -> pygame.Surface:
    """Generate a subtle deterministic paper texture without heavy imports."""
    texture = pygame.Surface((width, height))
    texture.fill(CREAM)

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, LINE_SPACING):
        pygame.draw.line(overlay, PAPER_LINE_COLOR, (0, y), (width, y))

    for x in range(SHADOW_LINE_SPACING // 2, width, SHADOW_LINE_SPACING):
        pygame.draw.line(overlay, PAPER_SHADOW_COLOR, (x, 0), (x, height))

    for row, y in enumerate(range(DOT_ROW_SPACING // 2, height, DOT_ROW_SPACING)):
        offset = (row % 3) * 17
        for x in range(24 + offset, width, DOT_COLUMN_SPACING):
            pygame.draw.circle(overlay, PAPER_DOT_COLOR, (x, y), DOT_RADIUS)

    texture.blit(overlay, (0, 0))
    return texture
