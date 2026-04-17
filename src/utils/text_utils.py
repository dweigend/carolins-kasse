"""Text utilities for word wrapping and multiline rendering.

Provides consistent text handling across all scenes.
"""

import pygame


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Break text into lines that fit within max_width.

    Uses word boundaries to wrap - never breaks mid-word.

    Args:
        text: The text to wrap
        font: Font to use for width calculation
        max_width: Maximum width in pixels for each line

    Returns:
        List of lines that fit within max_width
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def truncate_text(
    text: str, font: pygame.font.Font, max_width: int, suffix: str = "..."
) -> str:
    """Truncate text to fit within max_width, adding suffix if truncated.

    Args:
        text: The text to truncate
        font: Font to use for width calculation
        max_width: Maximum width in pixels
        suffix: String to append when truncated (default "...")

    Returns:
        Text truncated to fit within max_width
    """
    if font.size(text)[0] <= max_width:
        return text

    # Binary search for the right length
    suffix_width = font.size(suffix)[0]
    target_width = max_width - suffix_width

    # Start from end and work back
    for i in range(len(text), 0, -1):
        if font.size(text[:i])[0] <= target_width:
            return text[:i].rstrip() + suffix

    return suffix


def render_multiline(
    surface: pygame.Surface,
    lines: list[str],
    font: pygame.font.Font,
    x: int,
    y: int,
    color: tuple[int, int, int],
    line_spacing: float = 1.2,
    *,
    center_x: bool = False,
    max_width: int | None = None,
) -> int:
    """Render multiple lines of text.

    Args:
        surface: Surface to render on
        lines: List of text lines
        font: Font to use
        x: X position (left edge, or center if center_x=True)
        y: Y position of first line
        color: Text color (RGB tuple)
        line_spacing: Multiplier for line height
        center_x: If True, center each line horizontally around x
        max_width: If provided and center_x=True, center within this width

    Returns:
        Total height of rendered text
    """
    if not lines:
        return 0

    line_height = int(font.get_height() * line_spacing)
    current_y = y

    for line in lines:
        text_surface = font.render(line, True, color)

        if center_x:
            if max_width:
                text_x = x + (max_width - text_surface.get_width()) // 2
            else:
                text_x = x - text_surface.get_width() // 2
        else:
            text_x = x

        surface.blit(text_surface, (text_x, current_y))
        current_y += line_height

    return current_y - y
