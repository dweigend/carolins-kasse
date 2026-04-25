"""Shared asset-based checkout button renderer."""

import pygame

from src.constants import SUCCESS, WHITE
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset

_REGISTER_CENTER_OFFSET_X = 70
_ARROW_CENTER_OFFSET_FROM_RIGHT = 54


def render_icon_pay_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    background_asset: str,
    fallback_color: tuple[int, int, int] = SUCCESS,
) -> None:
    """Render the shared cash register + arrow checkout button."""
    try:
        button_bg = get_raw_asset(background_asset)
        if button_bg.get_size() != rect.size:
            button_bg = pygame.transform.smoothscale(button_bg, rect.size)
        surface.blit(button_bg, rect.topleft)
    except FileNotFoundError:
        pygame.draw.rect(surface, fallback_color, rect, border_radius=18)

    _render_register(surface, rect)
    _draw_pay_arrow(surface, rect.right - _ARROW_CENTER_OFFSET_FROM_RIGHT, rect.centery)


def _render_register(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Render the cash register icon with a simple fallback."""
    icon_center_x = rect.x + _REGISTER_CENTER_OFFSET_X
    try:
        register = get_asset("recipes/kasse", "M")
        register_rect = register.get_rect(center=(icon_center_x, rect.centery))
        surface.blit(register, register_rect)
    except FileNotFoundError:
        fallback_rect = pygame.Rect(0, 0, 54, 38)
        fallback_rect.center = (icon_center_x, rect.centery)
        pygame.draw.rect(surface, WHITE, fallback_rect, width=4, border_radius=8)


def _draw_pay_arrow(surface: pygame.Surface, center_x: int, center_y: int) -> None:
    """Draw the checkout arrow without relying on font glyph support."""
    pygame.draw.line(
        surface,
        WHITE,
        (center_x - 24, center_y),
        (center_x + 18, center_y),
        9,
    )
    pygame.draw.polygon(
        surface,
        WHITE,
        [
            (center_x + 26, center_y),
            (center_x + 6, center_y - 18),
            (center_x + 6, center_y + 18),
        ],
    )
