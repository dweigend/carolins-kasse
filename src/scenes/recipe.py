"""Recipe mode scene - scan recipe card, collect ingredients, and checkout."""

import pygame

from src.components.button import Button
from src.components.checklist_item import ChecklistItem
from src.constants import (
    BG_CARD,
    SCREEN_WIDTH,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WHITE,
)
from src.scenes.base import Scene
from src.scenes.checkout_mixin import CheckoutMixin
from src.scenes.mixins import MessageMixin
from src.utils import assets, state
from src.utils.database import (
    Product,
    Recipe,
    get_product,
    get_recipe,
    get_recipe_ingredients,
)
from src.utils.fonts import body, bold_custom, custom
from src.utils.input import InputManager, InputType
from src.utils.text_utils import render_multiline, wrap_text

# Layout constants (inside shell content area)
CONTENT_TOP = 82
CONTENT_BOTTOM = 520
CONTENT_RIGHT = 994
LEFT_PANEL_WIDTH = 360
RIGHT_PANEL_X = LEFT_PANEL_WIDTH + 18

PANEL_LEFT_X = (LEFT_PANEL_WIDTH - 330) // 2
PANEL_WIDTH = 330
PANEL_HEIGHT = 420

LIST_WIDTH = CONTENT_RIGHT - RIGHT_PANEL_X
LIST_HEIGHT = CONTENT_BOTTOM - CONTENT_TOP
LIST_SIDE_PADDING = 18
CHECKLIST_X = RIGHT_PANEL_X + LIST_SIDE_PADDING
CHECKLIST_Y = CONTENT_TOP + 40
CHECKLIST_WIDTH = LIST_WIDTH - LIST_SIDE_PADDING * 2
CHECKLIST_GAP = 8

PAY_BUTTON_WIDTH = 210
PAY_BUTTON_HEIGHT = 68
PAY_BUTTON_RIGHT_PADDING = 26
PAY_BUTTON_BOTTOM_PADDING = 16


class RecipeScene(CheckoutMixin, MessageMixin, Scene):
    """Recipe mode where kids follow a recipe checklist and pay for ingredients."""

    def __init__(self) -> None:
        """Initialize recipe scene."""
        self._input_manager = InputManager()
        self._recipe: Recipe | None = None
        self._ingredients: list[tuple[Product, int]] = []
        self._checked_barcodes: set[str] = set()
        self._checklist_items: list[ChecklistItem] = []
        self._recipe_image: pygame.Surface | None = None
        self._pay_button: Button | None = None
        self._complete: bool = False

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        self._init_checkout_ui()

        self._pay_button = Button(
            CONTENT_RIGHT - PAY_BUTTON_WIDTH - PAY_BUTTON_RIGHT_PADDING,
            CONTENT_BOTTOM - PAY_BUTTON_HEIGHT - PAY_BUTTON_BOTTOM_PADDING,
            PAY_BUTTON_WIDTH,
            PAY_BUTTON_HEIGHT,
            color=SUCCESS,
            on_click=self._handle_pay,
        )

        self._initialized = True

    # --- CheckoutMixin implementation ---

    def _get_checkout_total(self) -> int:
        """Return total cost of recipe ingredients."""
        return sum(int(product.price) * qty for product, qty in self._ingredients)

    def _get_checkout_items(self) -> list[dict]:
        """Return ingredients for transaction record."""
        return [
            {
                "barcode": product.barcode,
                "name": product.name_de,
                "qty": quantity,
                "price": int(product.price),
            }
            for product, quantity in self._ingredients
        ]

    def _on_checkout_complete(self) -> None:
        """Reset recipe state after successful checkout."""
        self._recipe = None
        self._ingredients.clear()
        self._checked_barcodes.clear()
        self._checklist_items.clear()
        self._recipe_image = None
        self._complete = False
        self._show_message("Zutaten bezahlt! Neues Rezept scannen.")

    # --- Recipe logic ---

    def _load_recipe(self, barcode: str) -> bool:
        """Load a recipe by barcode."""
        recipe = get_recipe(barcode)
        if not recipe:
            return False

        self._recipe = recipe
        self._ingredients = get_recipe_ingredients(barcode)
        self._checked_barcodes.clear()
        self._complete = False

        self._recipe_image = None
        if recipe.image_path:
            try:
                self._recipe_image = assets.get(f"recipes/{recipe.image_path}", "PANEL")
            except FileNotFoundError:
                pass

        self._rebuild_checklist()
        return True

    def _rebuild_checklist(self) -> None:
        """Rebuild checklist items from current ingredients."""
        self._checklist_items.clear()
        for index, (product, quantity) in enumerate(self._ingredients):
            y = CHECKLIST_Y + index * (ChecklistItem.HEIGHT + CHECKLIST_GAP)
            checked = product.barcode in self._checked_barcodes
            item = ChecklistItem(
                CHECKLIST_X,
                y,
                CHECKLIST_WIDTH,
                name=product.name_de,
                quantity=quantity,
                image_path=product.image_path,
                checked=checked,
            )
            self._checklist_items.append(item)

    def _handle_barcode(self, barcode: str) -> None:
        """Process a scanned barcode."""
        if self._checkout_mode:
            self._handle_checkout_barcode(barcode)
            return

        if barcode.startswith("300"):
            if self._load_recipe(barcode):
                self._show_message(f"Rezept geladen: {self._recipe.name}")
            else:
                self._show_message("Rezept nicht gefunden!")
            return

        if not self._recipe:
            self._show_message("Scanne zuerst ein Rezept!")
            return

        if self._complete:
            self._show_message("Jetzt bezahlen!")
            return

        product = get_product(barcode)
        if not product:
            self._show_message("Produkt nicht gefunden!")
            return

        is_ingredient = any(p.barcode == barcode for p, _ in self._ingredients)
        if not is_ingredient:
            self._show_message(f"{product.name_de} ist nicht im Rezept!")
            return

        if barcode in self._checked_barcodes:
            self._show_message(f"{product.name_de} schon gescannt!")
            return

        self._checked_barcodes.add(barcode)
        self._rebuild_checklist()
        self._show_message(f"✓ {product.name_de}")

        if len(self._checked_barcodes) == len(self._ingredients):
            self._complete = True
            self._show_message("Alle Zutaten gesammelt! Jetzt bezahlen.")

    def _handle_pay(self) -> None:
        """Handle pay button click."""
        if not self._complete:
            self._show_message("Sammle erst alle Zutaten!")
            return
        self._enter_checkout_mode()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()

        if self._handle_checkout_event(event):
            return self._consume_next_scene()

        if self._pay_button and self._complete and not self._checkout_mode:
            self._pay_button.handle_event(event)

        input_events = self._input_manager.process_event(event)
        for inp in input_events:
            if inp.type == InputType.BARCODE:
                self._handle_barcode(str(inp.value))

        return self._consume_next_scene()

    def update(self) -> None:
        """Update scene state."""
        state.check_time_bonus()
        self._update_checkout_ui()
        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the recipe screen (no background fill — shell handles it)."""
        self._init_ui()

        if self._recipe:
            self._render_recipe_panel(screen)
            self._render_checklist(screen)
        else:
            self._render_waiting_state(screen)

        self._render_checkout_overlays(screen)

        msg_font = body()
        self._render_message(
            screen,
            msg_font,
            SCREEN_WIDTH // 2,
            CONTENT_BOTTOM - 10,
            TEXT_PRIMARY,
            center_x=True,
        )

    def _render_waiting_state(self, screen: pygame.Surface) -> None:
        """Render the waiting for recipe state."""
        try:
            scan_hint = assets.get("ui/recipe/recipe_scan_hint", "PANEL")
            hint_rect = scan_hint.get_rect(center=(SCREEN_WIDTH // 2, 284))
            screen.blit(scan_hint, hint_rect)
        except FileNotFoundError:
            font = body()
            prompt = font.render("Scanne eine Rezept-Karte", True, TEXT_PRIMARY)
            prompt_x = (SCREEN_WIDTH - prompt.get_width()) // 2
            screen.blit(prompt, (prompt_x, 270))

    def _render_recipe_panel(self, screen: pygame.Surface) -> None:
        """Render the recipe info panel on the left."""
        if not self._recipe:
            return

        panel_rect = pygame.Rect(PANEL_LEFT_X, CONTENT_TOP, PANEL_WIDTH, PANEL_HEIGHT)
        self._render_recipe_panel_bg(screen, panel_rect)

        if self._recipe_image:
            image_rect = self._recipe_image.get_rect(
                center=(panel_rect.centerx, panel_rect.y + 128)
            )
            screen.blit(self._recipe_image, image_rect)
        else:
            placeholder_rect = pygame.Rect(0, 0, 150, 150)
            placeholder_rect.center = (panel_rect.centerx, panel_rect.y + 128)
            pygame.draw.rect(
                screen, (220, 220, 220), placeholder_rect, border_radius=18
            )

        max_text_width = panel_rect.width - 36
        name_font = custom(28)
        name_lines = wrap_text(self._recipe.name, name_font, max_text_width)
        name_y = panel_rect.y + 242
        name_height = render_multiline(
            screen,
            name_lines,
            name_font,
            panel_rect.x,
            name_y,
            TEXT_PRIMARY,
            center_x=True,
            max_width=panel_rect.width,
        )

        if self._ingredients:
            progress_y = name_y + name_height + 16
            checked = len(self._checked_barcodes)
            total = len(self._ingredients)
            color = SUCCESS if self._complete else TEXT_MUTED
            progress_text = bold_custom(30).render(f"{checked} / {total}", True, color)
            progress_x = (
                panel_rect.x + (panel_rect.width - progress_text.get_width()) // 2
            )
            screen.blit(progress_text, (progress_x, progress_y))

            total_cost = self._get_checkout_total()
            self._render_coin_value(
                screen, panel_rect.centerx, progress_y + 46, total_cost
            )

    def _render_checklist(self, screen: pygame.Surface) -> None:
        """Render the ingredient checklist."""
        list_rect = pygame.Rect(RIGHT_PANEL_X, CONTENT_TOP, LIST_WIDTH, LIST_HEIGHT)
        self._render_ingredient_list_bg(screen, list_rect)

        for item in self._checklist_items:
            item.render(screen)

        if self._complete:
            self._render_pay_button(screen)

    def _render_recipe_panel_bg(
        self, screen: pygame.Surface, panel_rect: pygame.Rect
    ) -> None:
        """Render recipe panel background from the recipe asset set."""
        try:
            panel = assets.get_raw("ui/recipe/recipe_panel_bg")
            screen.blit(panel, panel_rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(screen, BG_CARD, panel_rect, border_radius=18)

    def _render_ingredient_list_bg(
        self, screen: pygame.Surface, list_rect: pygame.Rect
    ) -> None:
        """Render ingredient list panel background from the recipe asset set."""
        try:
            panel = assets.get_raw("ui/recipe/ingredient_list_bg")
            screen.blit(panel, list_rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(screen, BG_CARD, list_rect, border_radius=18)

    def _render_coin_value(
        self, screen: pygame.Surface, center_x: int, center_y: int, value: int
    ) -> None:
        """Render recipe total as coin plus number."""
        coin_size = 38
        gap = 8
        value_font = bold_custom(34)
        value_text = value_font.render(str(value), True, (33, 99, 210))
        total_width = coin_size + gap + value_text.get_width()
        start_x = center_x - total_width // 2

        try:
            coin = assets.get("products/taler", "M")
            coin = pygame.transform.smoothscale(coin, (coin_size, coin_size))
            screen.blit(coin, (start_x, center_y - coin_size // 2))
        except FileNotFoundError:
            pygame.draw.circle(screen, (245, 158, 11), (start_x + 19, center_y), 18)

        text_rect = value_text.get_rect(midleft=(start_x + coin_size + gap, center_y))
        screen.blit(value_text, text_rect)

    def _render_pay_button(self, screen: pygame.Surface) -> None:
        """Render the visual recipe pay button."""
        if not self._pay_button:
            return

        try:
            button_bg = assets.get_raw("ui/recipe/recipe_pay_button_bg")
            screen.blit(button_bg, self._pay_button.rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(screen, SUCCESS, self._pay_button.rect, border_radius=18)

        icon_center_x = self._pay_button.rect.x + 70
        try:
            register = assets.get("recipes/kasse", "M")
            register_rect = register.get_rect(
                center=(icon_center_x, self._pay_button.rect.centery)
            )
            screen.blit(register, register_rect)
        except FileNotFoundError:
            fallback_rect = pygame.Rect(0, 0, 54, 38)
            fallback_rect.center = (icon_center_x, self._pay_button.rect.centery)
            pygame.draw.rect(screen, WHITE, fallback_rect, width=4, border_radius=8)

        self._draw_pay_arrow(
            screen,
            self._pay_button.rect.right - 54,
            self._pay_button.rect.centery,
        )

    def _draw_pay_arrow(
        self, screen: pygame.Surface, center_x: int, center_y: int
    ) -> None:
        """Draw the checkout arrow without relying on font glyph support."""
        pygame.draw.line(
            screen,
            WHITE,
            (center_x - 24, center_y),
            (center_x + 18, center_y),
            9,
        )
        pygame.draw.polygon(
            screen,
            WHITE,
            [
                (center_x + 26, center_y),
                (center_x + 6, center_y - 18),
                (center_x + 6, center_y + 18),
            ],
        )
