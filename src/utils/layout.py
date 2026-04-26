"""Centralized layout calculations for all scenes.

All UI positioning should use this module to ensure consistent
spacing and proper frame overlay handling.
"""

from src.constants import (
    FRAME_MARGIN,
    HEADER_HEIGHT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

# Content area (inside frame overlay)
CONTENT_LEFT = FRAME_MARGIN
CONTENT_RIGHT = SCREEN_WIDTH - FRAME_MARGIN
CONTENT_TOP = FRAME_MARGIN
CONTENT_BOTTOM = SCREEN_HEIGHT - FRAME_MARGIN
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT
CONTENT_HEIGHT = CONTENT_BOTTOM - CONTENT_TOP

# Usable area below header (most common case)
BODY_TOP = HEADER_HEIGHT + 10
BODY_BOTTOM = CONTENT_BOTTOM
BODY_HEIGHT = BODY_BOTTOM - BODY_TOP


def center_x(width: int) -> int:
    """Get x position to center an element horizontally on screen."""
    return (SCREEN_WIDTH - width) // 2


def center_in_content_x(width: int) -> int:
    """Get x position to center an element within content area."""
    return CONTENT_LEFT + (CONTENT_WIDTH - width) // 2


def bottom_position(height: int, margin: int = 10) -> int:
    """Get y position for element at bottom of content area."""
    return CONTENT_BOTTOM - height - margin
