"""Product picker scene for touch selection of items without barcodes."""

import pygame

from src.components.product_tile import ProductTile
from src.constants import (
    PRIMARY,
    SCREEN_WIDTH,
    TEXT_PRIMARY,
    WHITE,
)
from src.scenes.base import Scene
from src.utils import assets
from src.utils.database import Product, get_picker_products
from src.utils.fonts import caption, custom
from src.utils.state import set_selected_product

# Layout (inside shell content area)
CONTENT_TOP = 80
TAB_HEIGHT = 50
TAB_Y = CONTENT_TOP
GRID_Y = TAB_Y + TAB_HEIGHT + 18
GRID_COLS = 3
GRID_ROWS = 2
TILE_WIDTH = 170
TILE_HEIGHT = 168
TILE_GAP = 24

# Category display names
CATEGORY_NAMES = {
    "obst": "Obst",
    "gemuese": "Gemüse",
    "backwaren": "Backwaren",
    "suesses": "Süßes",
}

CATEGORY_ICONS = {
    "backwaren": "croissant",
    "gemuese": "carrot",
    "obst": "apple",
    "suesses": "muffin",
}


class PickerScene(Scene):
    """Product picker for items without barcodes (fruits, vegetables, etc.)."""

    def __init__(self) -> None:
        """Initialize picker scene."""
        self._products_by_category: dict[str, list[Product]] = {}
        self._categories: list[str] = []
        self._active_category: str = ""
        self._tiles: list[ProductTile] = []
        self._tab_rects: list[tuple[pygame.Rect, str]] = []

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        self._products_by_category = get_picker_products()
        self._categories = list(self._products_by_category.keys())

        if self._categories:
            self._active_category = self._categories[0]
            self._build_tab_rects()
            self._build_tiles()

        self._initialized = True

    def _build_tab_rects(self) -> None:
        """Build clickable tab rectangles."""
        self._tab_rects.clear()
        num_tabs = len(self._categories)
        if num_tabs == 0:
            return

        tab_width = min(170, (SCREEN_WIDTH - 60) // num_tabs - 10)
        total_width = num_tabs * tab_width + (num_tabs - 1) * 10
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, cat in enumerate(self._categories):
            x = start_x + i * (tab_width + 10)
            rect = pygame.Rect(x, TAB_Y, tab_width, TAB_HEIGHT)
            self._tab_rects.append((rect, cat))

    def _build_tiles(self) -> None:
        """Build product tiles for current category."""
        self._tiles.clear()
        products = self._products_by_category.get(self._active_category, [])

        grid_width = GRID_COLS * TILE_WIDTH + (GRID_COLS - 1) * TILE_GAP
        start_x = (SCREEN_WIDTH - grid_width) // 2

        for i, product in enumerate(products[: GRID_COLS * GRID_ROWS]):
            row = i // GRID_COLS
            col = i % GRID_COLS
            x = start_x + col * (TILE_WIDTH + TILE_GAP)
            y = GRID_Y + row * (TILE_HEIGHT + TILE_GAP)

            image = None
            if product.image_path:
                try:
                    image = assets.get(f"products/{product.image_path}", "L")
                except FileNotFoundError:
                    pass

            tile = ProductTile(
                x,
                y,
                TILE_WIDTH,
                TILE_HEIGHT,
                product_id=i,
                name=product.name_de,
                image=image,
                on_click=lambda pid, p=product: self._select_product(p),
            )
            self._tiles.append(tile)

    def _select_product(self, product: Product) -> None:
        """Handle product selection."""
        set_selected_product(product)
        self._go_to("scan")

    def _switch_category(self, category: str) -> None:
        """Switch to a different category."""
        if category != self._active_category:
            self._active_category = category
            self._build_tiles()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()

        # Tab clicks
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for rect, category in self._tab_rects:
                if rect.collidepoint(event.pos):
                    self._switch_category(category)
                    break

        # Tile events
        for tile in self._tiles:
            tile.handle_event(event)

        return self._consume_next_scene()

    def update(self) -> None:
        """Update scene state."""

    def render(self, screen: pygame.Surface) -> None:
        """Draw the picker screen (no background fill — shell handles it)."""
        self._init_ui()

        self._render_tabs(screen)

        for tile in self._tiles:
            tile.render(screen)

        if not self._categories:
            font = caption()
            empty_text = font.render(
                "Keine Produkte ohne Barcode gefunden", True, TEXT_PRIMARY
            )
            screen.blit(
                empty_text,
                ((SCREEN_WIDTH - empty_text.get_width()) // 2, GRID_Y + 50),
            )

    def _render_tabs(self, screen: pygame.Surface) -> None:
        """Render category tabs."""
        for rect, category in self._tab_rects:
            is_active = category == self._active_category
            bg_color = PRIMARY if is_active else (255, 252, 244)
            border_color = PRIMARY if is_active else (231, 219, 198)
            pygame.draw.rect(screen, bg_color, rect, border_radius=14)
            pygame.draw.rect(screen, border_color, rect, width=2, border_radius=14)

            icon_name = CATEGORY_ICONS.get(category)
            icon = None
            if icon_name:
                try:
                    icon = assets.get(f"products/{icon_name}", "S")
                except FileNotFoundError:
                    icon = None

            display_name = CATEGORY_NAMES.get(category, category.capitalize())
            text_color = WHITE if is_active else TEXT_PRIMARY
            self._render_tab_content(screen, rect, display_name, text_color, icon)

    def _render_tab_content(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        text_color: tuple[int, int, int],
        icon: pygame.Surface | None,
    ) -> None:
        """Render tab icon and label as one centered group."""
        max_text_width = rect.width - 22
        icon_gap = 8 if icon else 0
        if icon:
            max_text_width -= icon.get_width() + icon_gap

        text_surface = self._fit_tab_text(text, text_color, max_text_width)
        icon_width = icon.get_width() if icon else 0
        group_width = icon_width + icon_gap + text_surface.get_width()
        start_x = rect.centerx - group_width // 2

        if icon:
            icon_y = rect.centery - icon.get_height() // 2
            screen.blit(icon, (start_x, icon_y))
            start_x += icon_width + icon_gap

        text_rect = text_surface.get_rect(midleft=(start_x, rect.centery))
        screen.blit(text_surface, text_rect)

    def _fit_tab_text(
        self, text: str, color: tuple[int, int, int], max_width: int
    ) -> pygame.Surface:
        """Render tab text at the largest size that fits."""
        for size in (28, 25, 22, 20, 18):
            text_surface = custom(size).render(text, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface

        clipped_text = text
        font = custom(18)
        while len(clipped_text) > 4:
            candidate = f"{clipped_text[:-1]}…"
            text_surface = font.render(candidate, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface
            clipped_text = clipped_text[:-1]

        return font.render(clipped_text[:4], True, color)
