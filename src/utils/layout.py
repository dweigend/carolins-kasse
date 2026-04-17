"""Centralized layout calculations for all scenes.

All UI positioning should use this module to ensure consistent
spacing and proper frame overlay handling.
"""

import pygame

from src.constants import (
    FRAME_BORDER,
    FRAME_MARGIN,
    FOOTER_HEIGHT,
    HEADER_HEIGHT,
    HEADER_HEIGHT_NEW,
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


# ─── Phase 6.1: New UI System ─────────────────────────────────
# New layout with header + footer + paper frame
CONTENT_X_NEW = FRAME_BORDER  # 24
CONTENT_Y_NEW = HEADER_HEIGHT_NEW  # 72
CONTENT_W_NEW = SCREEN_WIDTH - 2 * FRAME_BORDER  # 976
CONTENT_H_NEW = SCREEN_HEIGHT - HEADER_HEIGHT_NEW - FOOTER_HEIGHT  # 468
FOOTER_Y_NEW = SCREEN_HEIGHT - FOOTER_HEIGHT  # 540


class ContentLayout:
    """Helper for positioning items in content area using different layout modes."""

    @staticmethod
    def place_row(items: int, item_width: int) -> list[tuple[int, int]]:
        """Position items horizontally in a row, centered in content area.

        Args:
            items: Number of items to position
            item_width: Width of each item in pixels

        Returns:
            List of (x, y) tuples for each item's top-left corner

        Trade-off:
            - Equal spacing between items maximizes clarity
            - Could also use fixed left-alignment or space-between
        """
        # TODO: Implement row layout positioning
        # Hints:
        # - Total width needed: items * item_width
        # - Extra space: CONTENT_W_NEW - total_width
        # - Distribute space evenly between/around items
        # - Center vertically in CONTENT_Y_NEW...FOOTER_Y_NEW
        pass

    @staticmethod
    def place_split(
        left_ratio: float = 0.4,
    ) -> tuple[pygame.Rect, pygame.Rect]:
        """Divide content area into left and right sections.

        Args:
            left_ratio: Fraction of width for left section (0.0-1.0)

        Returns:
            (left_rect, right_rect) as pygame.Rect objects

        Trade-off:
            - 40/60 split balances left detail with right action area
            - Could also use 50/50 for balance or 30/70 for emphasis
        """
        # TODO: Implement split layout
        # Hints:
        # - left_rect starts at CONTENT_X_NEW, CONTENT_Y_NEW
        # - width = CONTENT_W_NEW * left_ratio
        # - right_rect starts after left section
        # - Both rects have height = CONTENT_H_NEW
        pass
