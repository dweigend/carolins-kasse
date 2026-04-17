"""Centralized font management.

Initialize pygame fonts and provide semantic font sizes.
"""

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
    return pygame.font.Font(FONT_PATH, HEADING_SIZE)


def bold() -> pygame.font.Font:
    """Get bold heading font (42pt, bold weight)."""
    return pygame.font.Font(BOLD_FONT_PATH, HEADING_SIZE)


def body() -> pygame.font.Font:
    """Get body font (36pt)."""
    return pygame.font.Font(FONT_PATH, BODY_SIZE)


def caption() -> pygame.font.Font:
    """Get caption font (28pt)."""
    return pygame.font.Font(FONT_PATH, CAPTION_SIZE)


def custom(size: int) -> pygame.font.Font:
    """Get custom size font.

    Args:
        size: Font size in pixels

    Returns:
        Font instance at specified size
    """
    return pygame.font.Font(FONT_PATH, size)


def bold_custom(size: int) -> pygame.font.Font:
    """Get custom size bold font.

    Args:
        size: Font size in pixels

    Returns:
        Bold font instance at specified size
    """
    return pygame.font.Font(BOLD_FONT_PATH, size)
