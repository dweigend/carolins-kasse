"""Recipe mode scene - scan recipe card, collect ingredients, and checkout."""

import pygame

from src.components.button import Button
from src.components.checklist_item import ChecklistItem
from src.constants import (
    BG_CARD,
    SCREEN_HEIGHT,
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
from src.utils.fonts import body, caption
from src.utils.input import InputManager, InputType
from src.utils.text_utils import render_multiline, wrap_text

# Layout constants (inside shell content area)
CONTENT_TOP = 80
CONTENT_BOTTOM = 540
CONTENT_RIGHT = 994
PADDING = 20

RECIPE_PANEL_WIDTH = 300
CHECKLIST_X = RECIPE_PANEL_WIDTH + 60
CHECKLIST_Y = CONTENT_TOP + 40
CHECKLIST_WIDTH = CONTENT_RIGHT - CHECKLIST_X - PADDING


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

        # Pay button (bottom right of checklist area)
        pay_btn_width = 180
        pay_btn_height = 50
        pay_btn_x = CHECKLIST_X + (CHECKLIST_WIDTH - pay_btn_width) // 2
        pay_btn_y = CONTENT_BOTTOM - pay_btn_height - 20
        self._pay_button = Button(
            pay_btn_x,
            pay_btn_y,
            pay_btn_width,
            pay_btn_height,
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
                self._recipe_image = assets.get(f"recipes/{recipe.image_path}", "L")
            except FileNotFoundError:
                pass

        self._rebuild_checklist()
        return True

    def _rebuild_checklist(self) -> None:
        """Rebuild checklist items from current ingredients."""
        self._checklist_items.clear()
        for i, (product, quantity) in enumerate(self._ingredients):
            y = CHECKLIST_Y + i * ChecklistItem.HEIGHT
            checked = product.barcode in self._checked_barcodes
            item = ChecklistItem(
                CHECKLIST_X,
                y,
                CHECKLIST_WIDTH,
                name=product.name_de,
                quantity=quantity,
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
        font = body()
        prompt = font.render("Scanne eine Rezept-Karte", True, TEXT_PRIMARY)
        prompt_x = (SCREEN_WIDTH - prompt.get_width()) // 2
        prompt_y = SCREEN_HEIGHT // 2 - 30
        screen.blit(prompt, (prompt_x, prompt_y))

        hint_font = caption()
        hint = hint_font.render("(Rezepte haben einen 300-Barcode)", True, TEXT_MUTED)
        hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
        screen.blit(hint, (hint_x, prompt_y + 50))

    def _render_recipe_panel(self, screen: pygame.Surface) -> None:
        """Render the recipe info panel on the left."""
        if not self._recipe:
            return

        font = body()
        small_font = caption()

        panel_rect = pygame.Rect(
            PADDING,
            CONTENT_TOP,
            RECIPE_PANEL_WIDTH - PADDING,
            CONTENT_BOTTOM - CONTENT_TOP,
        )
        pygame.draw.rect(screen, BG_CARD, panel_rect, border_radius=12)

        img_y = panel_rect.y + 20
        if self._recipe_image:
            img_x = (
                panel_rect.x + (panel_rect.width - self._recipe_image.get_width()) // 2
            )
            screen.blit(self._recipe_image, (img_x, img_y))
            img_y += self._recipe_image.get_height() + 20
        else:
            placeholder_size = 100
            placeholder_rect = pygame.Rect(
                panel_rect.x + (panel_rect.width - placeholder_size) // 2,
                img_y,
                placeholder_size,
                placeholder_size,
            )
            pygame.draw.rect(screen, (220, 220, 220), placeholder_rect, border_radius=8)
            img_y += placeholder_size + 20

        # Recipe name
        max_text_width = panel_rect.width - 20
        name_lines = wrap_text(self._recipe.name, font, max_text_width)
        name_height = render_multiline(
            screen,
            name_lines,
            font,
            panel_rect.x,
            img_y,
            TEXT_PRIMARY,
            center_x=True,
            max_width=panel_rect.width,
        )

        # Progress indicator
        if self._ingredients:
            progress_y = img_y + name_height + 20
            checked = len(self._checked_barcodes)
            total = len(self._ingredients)
            color = SUCCESS if self._complete else TEXT_MUTED

            prog = small_font.render(f"{checked} / {total} Zutaten", True, color)
            prog_x = panel_rect.x + (panel_rect.width - prog.get_width()) // 2
            screen.blit(prog, (prog_x, progress_y))

            cost_y = progress_y + 30
            total_cost = self._get_checkout_total()
            cost = small_font.render(f"Gesamt: {total_cost} Taler", True, TEXT_MUTED)
            cost_x = panel_rect.x + (panel_rect.width - cost.get_width()) // 2
            screen.blit(cost, (cost_x, cost_y))

    def _render_checklist(self, screen: pygame.Surface) -> None:
        """Render the ingredient checklist."""
        font = body()

        title = font.render("Zutaten", True, TEXT_PRIMARY)
        screen.blit(title, (CHECKLIST_X, CONTENT_TOP))

        for item in self._checklist_items:
            item.render(screen)

        if self._complete:
            if self._pay_button:
                pygame.draw.rect(
                    screen, SUCCESS, self._pay_button.rect, border_radius=8
                )
                pay_text = font.render("BEZAHLEN", True, WHITE)
                pay_rect = pay_text.get_rect(center=self._pay_button.rect.center)
                screen.blit(pay_text, pay_rect)
        else:
            hint_font = caption()
            hint = hint_font.render("Scanne die Zutaten...", True, TEXT_MUTED)
            hint_y = (
                CHECKLIST_Y + len(self._checklist_items) * ChecklistItem.HEIGHT + 20
            )
            screen.blit(hint, (CHECKLIST_X, hint_y))
