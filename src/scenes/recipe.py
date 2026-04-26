"""Recipe mode scene - scan recipe card, collect ingredients, and checkout."""

from dataclasses import dataclass

import pygame

from src.components.button import Button
from src.components.checklist_item import ChecklistItem
from src.components.icon_pay_button import render_icon_pay_button
from src.constants import (
    BG_CARD,
    SCREEN_WIDTH,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from src.scenes.base import Scene
from src.scenes.checkout_mixin import CheckoutMixin
from src.scenes.mixins import MessageMixin
from src.utils import assets, state
from src.utils.barcodes import RECIPE_PREFIX
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


@dataclass(frozen=True)
class RecipeLayout:
    """Fixed recipe content geometry inside the shared shell."""

    top: int = 84
    bottom: int = 520
    left: int = 28
    right: int = 996
    panel_width: int = 330
    panel_height: int = 420
    panel_gap: int = 26
    list_padding_x: int = 20
    checklist_top_padding: int = 40
    checklist_gap: int = 8
    pay_button_width: int = 210
    pay_button_height: int = 68
    pay_button_right_padding: int = 26
    pay_button_bottom_padding: int = 16

    @property
    def panel_rect(self) -> pygame.Rect:
        """Return the left recipe summary panel."""
        return pygame.Rect(self.left, self.top, self.panel_width, self.panel_height)

    @property
    def list_rect(self) -> pygame.Rect:
        """Return the right ingredient panel."""
        list_x = self.left + self.panel_width + self.panel_gap
        return pygame.Rect(
            list_x, self.top, self.right - list_x, self.bottom - self.top
        )

    @property
    def checklist_x(self) -> int:
        """Return the ingredient row x-position."""
        return self.list_rect.x + self.list_padding_x

    @property
    def checklist_y(self) -> int:
        """Return the first ingredient row y-position."""
        return self.top + self.checklist_top_padding

    @property
    def checklist_width(self) -> int:
        """Return the ingredient row width."""
        return self.list_rect.width - self.list_padding_x * 2

    @property
    def pay_button_rect(self) -> pygame.Rect:
        """Return the checkout button rect."""
        return pygame.Rect(
            self.right - self.pay_button_width - self.pay_button_right_padding,
            self.bottom - self.pay_button_height - self.pay_button_bottom_padding,
            self.pay_button_width,
            self.pay_button_height,
        )


LAYOUT = RecipeLayout()
SCAN_HINT_SIZE = (420, 320)


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
            LAYOUT.pay_button_rect.x,
            LAYOUT.pay_button_rect.y,
            LAYOUT.pay_button_rect.width,
            LAYOUT.pay_button_rect.height,
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
            y = LAYOUT.checklist_y + index * (
                ChecklistItem.HEIGHT + LAYOUT.checklist_gap
            )
            checked = product.barcode in self._checked_barcodes
            item = ChecklistItem(
                LAYOUT.checklist_x,
                y,
                LAYOUT.checklist_width,
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

        if barcode.startswith(RECIPE_PREFIX):
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
            LAYOUT.bottom - 10,
            TEXT_PRIMARY,
            center_x=True,
        )

    def _render_waiting_state(self, screen: pygame.Surface) -> None:
        """Render the waiting for recipe state."""
        try:
            scan_hint = assets.get_raw("ui/recipe/recipe_scan_hint")
            if scan_hint.get_size() != SCAN_HINT_SIZE:
                scan_hint = pygame.transform.smoothscale(scan_hint, SCAN_HINT_SIZE)
            hint_rect = scan_hint.get_rect(center=(SCREEN_WIDTH // 2, 292))
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

        panel_rect = LAYOUT.panel_rect
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
            checked = len(self._checked_barcodes)
            total = len(self._ingredients)
            progress_center_y = max(name_y + name_height + 30, panel_rect.y + 332)
            self._render_progress_value(
                screen, panel_rect.centerx, progress_center_y, checked, total
            )
            self._render_cost_badge(
                screen,
                panel_rect.centerx,
                min(progress_center_y + 54, panel_rect.bottom - 36),
                self._get_checkout_total(),
            )

    def _render_checklist(self, screen: pygame.Surface) -> None:
        """Render the ingredient checklist."""
        list_rect = LAYOUT.list_rect
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

    def _render_progress_value(
        self,
        screen: pygame.Surface,
        center_x: int,
        center_y: int,
        checked: int,
        total: int,
    ) -> None:
        """Render gathered ingredient progress."""
        color = SUCCESS if self._complete else TEXT_MUTED
        progress_text = bold_custom(34).render(f"{checked}/{total}", True, color)
        progress_rect = progress_text.get_rect(center=(center_x, center_y))
        screen.blit(progress_text, progress_rect)

    def _render_cost_badge(
        self, screen: pygame.Surface, center_x: int, center_y: int, value: int
    ) -> None:
        """Render recipe total as a compact coin badge."""
        badge_rect = pygame.Rect(0, 0, 132, 54)
        badge_rect.center = (center_x, center_y)
        pygame.draw.rect(screen, (248, 252, 255), badge_rect, border_radius=22)
        pygame.draw.rect(screen, (219, 234, 254), badge_rect, 2, border_radius=22)

        coin_size = 34
        gap = 10
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

        render_icon_pay_button(
            screen,
            self._pay_button.rect,
            background_asset="ui/recipe/recipe_pay_button_bg",
            fallback_color=SUCCESS,
        )
