"""Centralized font management.

Initialize pygame fonts and provide semantic font sizes.
"""

from functools import lru_cache
import os

import pygame

# ─── INITIALIZATION ────────────────────────────────────────
pygame.font.init()

# ─── FONT CONFIGURATION ────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "Fredoka", "static", "Fredoka-Regular.ttf")
BOLD_FONT_PATH = os.path.join(FONT_DIR, "Fredoka", "static", "Fredoka-Bold.ttf")

# Semantic font sizes
HEADING_SIZE = 42  # Titles, headers, buttons
BODY_SIZE = 36  # Regular text, main content
CAPTION_SIZE = 28  # Hints, labels, secondary text


# ─── FONT GETTERS ─────────────────────────────────────────
def heading() -> pygame.font.Font:
    """Get heading font (42pt)."""
    return _get_font(FONT_PATH, HEADING_SIZE)


def bold() -> pygame.font.Font:
    """Get bold heading font (42pt, bold weight)."""
    return _get_font(BOLD_FONT_PATH, HEADING_SIZE)


def body() -> pygame.font.Font:
    """Get body font (36pt)."""
    return _get_font(FONT_PATH, BODY_SIZE)


def caption() -> pygame.font.Font:
    """Get caption font (28pt)."""
    return _get_font(FONT_PATH, CAPTION_SIZE)


def custom(size: int) -> pygame.font.Font:
    """Get custom size font.

    Args:
        size: Font size in pixels

    Returns:
        Font instance at specified size
    """
    return _get_font(FONT_PATH, size)


def bold_custom(size: int) -> pygame.font.Font:
    """Get custom size bold font.

    Args:
        size: Font size in pixels

    Returns:
        Bold font instance at specified size
    """
    return _get_font(BOLD_FONT_PATH, size)


def clear_cache() -> None:
    """Clear cached fonts for focused tests or display resets."""
    _get_font.cache_clear()


@lru_cache(maxsize=None)
def _get_font(font_path: str, size: int) -> pygame.font.Font:
    """Load each immutable font size once per process."""
    return pygame.font.Font(font_path, size)
