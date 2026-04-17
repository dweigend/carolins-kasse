"""Checkout receipt overlay showing purchase confirmation and new balance.

Shows after successful checkout:
- Customer name
- Purchase total
- New balance with visual bar
- Auto-hides after timeout
"""

import pygame

from src.components.balance_bar import BalanceBar
from src.constants import BG_CARD, SCREEN_HEIGHT, SCREEN_WIDTH, SUCCESS, TEXT_PRIMARY
from src.utils.fonts import heading, body, caption


class CheckoutReceipt:
    """Overlay showing successful checkout with balance update.

    Visual design:
    ┌─────────────────────────────────────────────┐
    │                                             │
    │            ✅ Bezahlt!                      │
    │                                             │
    │     ┌─────────────────────────────────┐     │
    │     │  👤 Annelie                     │     │
    │     │                                 │     │
    │     │  Einkauf:        -8 Taler       │     │
    │     │  ───────────────────────        │     │
    │     │  Neuer Stand:    32 Taler       │     │
    │     │                                 │     │
    │     │  ████████████░░░░░░░░░░░        │     │
    │     └─────────────────────────────────┘     │
    │                                             │
    └─────────────────────────────────────────────┘
    """

    DISPLAY_DURATION_MS = 3000  # 3 seconds

    def __init__(self) -> None:
        """Create checkout receipt overlay."""
        self._visible = False
        self._show_time = 0
        self._customer_name = ""
        self._total = 0
        self._new_balance = 0
        self._cashier_name: str | None = None
        self._cashier_salary: int = 0

        # Card dimensions
        self._card_width = 400
        self._card_height = 320
        self._card_x = (SCREEN_WIDTH - self._card_width) // 2
        self._card_y = (SCREEN_HEIGHT - self._card_height) // 2

        # Balance bar
        self._balance_bar = BalanceBar(
            self._card_x + 50,
            self._card_y + 200,
            width=300,
            height=24,
            show_text=False,
        )

    def show(
        self,
        customer_name: str,
        total: int,
        new_balance: int,
        cashier_name: str | None = None,
        cashier_salary: int = 0,
    ) -> None:
        """Show the receipt overlay.

        Args:
            customer_name: Name of customer who paid
            total: Purchase total in Taler
            new_balance: Customer's new balance after purchase
            cashier_name: Name of cashier who earned salary (optional)
            cashier_salary: Amount cashier earned for this checkout
        """
        self._visible = True
        self._show_time = pygame.time.get_ticks()
        self._customer_name = customer_name
        self._total = total
        self._new_balance = new_balance
        self._cashier_name = cashier_name
        self._cashier_salary = cashier_salary
        self._balance_bar.set_balance(new_balance)

    def hide(self) -> None:
        """Hide the receipt overlay."""
        self._visible = False

    def is_visible(self) -> bool:
        """Check if receipt is currently visible."""
        return self._visible

    def update(self) -> None:
        """Update receipt state (check for auto-hide)."""
        if self._visible:
            elapsed = pygame.time.get_ticks() - self._show_time
            if elapsed >= self.DISPLAY_DURATION_MS:
                self.hide()

    def render(self, surface: pygame.Surface) -> None:
        """Draw the receipt overlay.

        Args:
            surface: Surface to draw on
        """
        if not self._visible:
            return

        # Semi-transparent background overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # White card
        card_rect = pygame.Rect(
            self._card_x, self._card_y, self._card_width, self._card_height
        )
        pygame.draw.rect(surface, BG_CARD, card_rect, border_radius=16)

        # Header: ✅ Bezahlt!
        header_font = heading()
        header_text = header_font.render("Bezahlt!", True, SUCCESS)
        header_x = self._card_x + (self._card_width - header_text.get_width()) // 2
        surface.blit(header_text, (header_x, self._card_y + 20))

        body_font = body()

        # Customer name
        name_text = body_font.render(
            f"Kunde: {self._customer_name}", True, TEXT_PRIMARY
        )
        surface.blit(name_text, (self._card_x + 50, self._card_y + 70))

        # Purchase total
        total_label = body_font.render("Einkauf:", True, TEXT_PRIMARY)
        total_value = body_font.render(f"-{self._total} Taler", True, (220, 38, 38))
        surface.blit(total_label, (self._card_x + 50, self._card_y + 110))
        surface.blit(
            total_value,
            (
                self._card_x + self._card_width - 50 - total_value.get_width(),
                self._card_y + 110,
            ),
        )

        # Divider line
        pygame.draw.line(
            surface,
            (200, 200, 200),
            (self._card_x + 50, self._card_y + 145),
            (self._card_x + self._card_width - 50, self._card_y + 145),
            2,
        )

        # New balance
        balance_label = body_font.render("Neuer Stand:", True, TEXT_PRIMARY)
        balance_value = body_font.render(
            f"{self._new_balance} Taler", True, TEXT_PRIMARY
        )
        surface.blit(balance_label, (self._card_x + 50, self._card_y + 160))
        surface.blit(
            balance_value,
            (
                self._card_x + self._card_width - 50 - balance_value.get_width(),
                self._card_y + 160,
            ),
        )

        # Balance bar
        self._balance_bar.render(surface)

        # Cashier salary info (if applicable)
        if self._cashier_name and self._cashier_salary > 0:
            small_font = caption()
            salary_text = small_font.render(
                f"★ +{self._cashier_salary} Taler für {self._cashier_name}",
                True,
                SUCCESS,
            )
            salary_x = self._card_x + (self._card_width - salary_text.get_width()) // 2
            surface.blit(salary_text, (salary_x, self._card_y + 240))

        # Auto-hide countdown hint
        small_font = caption()
        remaining = max(
            0,
            self.DISPLAY_DURATION_MS - (pygame.time.get_ticks() - self._show_time),
        )
        remaining_sec = remaining // 1000 + 1
        hint = small_font.render(
            f"(schließt in {remaining_sec}s)", True, (150, 150, 150)
        )
        hint_x = self._card_x + (self._card_width - hint.get_width()) // 2
        surface.blit(hint, (hint_x, self._card_y + self._card_height - 30))
