"""Checklist item component for recipe ingredients."""

import pygame

from src.constants import SUCCESS, TEXT_MUTED, TEXT_PRIMARY
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.fonts import bold_custom, custom

_IMAGE_SIZE = 54
_STATUS_SIZE = 46
_PADDING = 10
_TEXT_LEFT_GAP = 16
_STATUS_RIGHT_PADDING = 20


class ChecklistItem:
    """A visual recipe ingredient row with product image and scan status."""

    HEIGHT = 70

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        *,
        name: str,
        quantity: int = 1,
        image_path: str | None = None,
        checked: bool = False,
    ) -> None:
        """Create a checklist item.

        Args:
            x: X position (top-left)
            y: Y position (top-left)
            width: Item width
            name: Ingredient name to display
            quantity: How many of this ingredient needed
            image_path: Product image path from the product database
            checked: Initial checked state
        """
        self.rect = pygame.Rect(x, y, width, self.HEIGHT)
        self.name = name
        self.quantity = quantity
        self.image_path = image_path
        self.checked = checked

    def set_checked(self, checked: bool) -> None:
        """Set the checked state."""
        self.checked = checked

    def render(self, surface: pygame.Surface) -> None:
        """Draw the checklist item."""
        self._render_background(surface)
        self._render_product_image(surface)
        self._render_quantity_badge(surface)
        self._render_name(surface)
        self._render_status(surface)

    def _render_background(self, surface: pygame.Surface) -> None:
        """Render row background from the recipe asset set."""
        asset_name = (
            "ui/recipe/ingredient_row_done_bg"
            if self.checked
            else "ui/recipe/ingredient_row_pending_bg"
        )
        try:
            row_bg = get_raw_asset(asset_name)
            if row_bg.get_size() != self.rect.size:
                row_bg = pygame.transform.smoothscale(row_bg, self.rect.size)
            surface.blit(row_bg, self.rect.topleft)
        except FileNotFoundError:
            bg_color = (244, 255, 247) if self.checked else (255, 252, 244)
            pygame.draw.rect(surface, bg_color, self.rect, border_radius=15)
            pygame.draw.rect(surface, (232, 220, 200), self.rect, 1, border_radius=15)

    def _render_product_image(self, surface: pygame.Surface) -> None:
        """Render the ingredient product image."""
        image_rect = pygame.Rect(0, 0, _IMAGE_SIZE, _IMAGE_SIZE)
        image_rect.centery = self.rect.centery
        image_rect.x = self.rect.x + _PADDING

        try:
            if self.image_path:
                image = get_asset(f"products/{self.image_path}", "CART")
                surface.blit(image, image_rect.topleft)
                return
        except FileNotFoundError:
            pass

        pygame.draw.rect(surface, (220, 220, 220), image_rect, border_radius=10)

    def _render_quantity_badge(self, surface: pygame.Surface) -> None:
        """Render quantity as a small number badge when needed."""
        if self.quantity <= 1:
            return

        badge_center = (self.rect.x + _PADDING + _IMAGE_SIZE - 7, self.rect.y + 19)
        pygame.draw.circle(surface, (219, 234, 254), badge_center, 16)
        quantity_text = bold_custom(22).render(str(self.quantity), True, TEXT_PRIMARY)
        quantity_rect = quantity_text.get_rect(center=badge_center)
        surface.blit(quantity_text, quantity_rect)

    def _render_name(self, surface: pygame.Surface) -> None:
        """Render an adult-readable ingredient label that stays inside the row."""
        text_x = self.rect.x + _PADDING + _IMAGE_SIZE + _TEXT_LEFT_GAP
        status_left = self.rect.right - _STATUS_RIGHT_PADDING - _STATUS_SIZE
        max_width = max(0, status_left - text_x - 14)
        if max_width <= 0:
            return

        text_color = TEXT_MUTED if self.checked else TEXT_PRIMARY
        name_text = self._fit_text(self.name, max_width, text_color)
        name_rect = name_text.get_rect(midleft=(text_x, self.rect.centery))
        surface.blit(name_text, name_rect)

    def _render_status(self, surface: pygame.Surface) -> None:
        """Render scanned/not-scanned status as a large visual cue."""
        center = (
            self.rect.right - _STATUS_RIGHT_PADDING - _STATUS_SIZE // 2,
            self.rect.centery,
        )
        if self.checked:
            try:
                badge = get_asset("ui/recipe/recipe_complete_badge", "M")
                badge = pygame.transform.smoothscale(
                    badge, (_STATUS_SIZE, _STATUS_SIZE)
                )
                badge_rect = badge.get_rect(center=center)
                surface.blit(badge, badge_rect)
                return
            except FileNotFoundError:
                pass

            pygame.draw.circle(surface, SUCCESS, center, _STATUS_SIZE // 2)
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (center[0] - 12, center[1]),
                (center[0] - 4, center[1] + 10),
                6,
            )
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (center[0] - 4, center[1] + 10),
                (center[0] + 14, center[1] - 14),
                6,
            )
            return

        pygame.draw.circle(surface, (166, 148, 120), center, _STATUS_SIZE // 2, 3)

    def _fit_text(
        self, text: str, max_width: int, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Render text at the largest size that fits the row."""
        for size in (28, 25, 22, 20):
            text_surface = custom(size).render(text, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface

        clipped_text = text
        font = custom(19)
        while len(clipped_text) > 4:
            candidate = f"{clipped_text[:-1]}…"
            text_surface = font.render(candidate, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface
            clipped_text = clipped_text[:-1]

        return font.render(clipped_text[:4], True, color)
