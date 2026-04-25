"""Checkout receipt overlay showing purchase confirmation.

Shows after successful checkout:
- Customer/payment row
- Cashier/earning row
- Auto-hides after timeout
"""

import pygame

from src.constants import BG_CARD, SCREEN_HEIGHT, SCREEN_WIDTH, SUCCESS, TEXT_PRIMARY
from src.utils.assets import get as get_asset
from src.utils.assets import get_raw as get_raw_asset
from src.utils.fonts import bold_custom, custom


class CheckoutReceipt:
    """Overlay showing who paid and who earned money."""

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

        self._card_width = 500
        self._card_height = 328
        self._card_x = (SCREEN_WIDTH - self._card_width) // 2
        self._card_y = (SCREEN_HEIGHT - self._card_height) // 2

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

        card_rect = pygame.Rect(
            self._card_x, self._card_y, self._card_width, self._card_height
        )
        try:
            card_bg = get_raw_asset("ui/cashier/checkout_card_bg")
            surface.blit(card_bg, card_rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(surface, BG_CARD, card_rect, border_radius=22)
            pygame.draw.rect(surface, SUCCESS, card_rect, width=4, border_radius=22)

        try:
            success_icon = get_asset("ui/cashier/checkout_success", "XL")
            success_rect = success_icon.get_rect(
                center=(SCREEN_WIDTH // 2, self._card_y + 64)
            )
            surface.blit(success_icon, success_rect)
        except FileNotFoundError:
            pygame.draw.circle(
                surface, SUCCESS, (SCREEN_WIDTH // 2, self._card_y + 64), 42
            )

        self._render_transfer_row(
            surface,
            self._card_y + 124,
            "checkout_payment_row_bg",
            self._customer_name,
            f"-{self._total}",
            (220, 38, 38),
        )

        if self._cashier_name and self._cashier_salary > 0:
            self._render_transfer_row(
                surface,
                self._card_y + 202,
                "checkout_earning_row_bg",
                self._cashier_name,
                f"+{self._cashier_salary}",
                SUCCESS,
            )

    def _render_transfer_row(
        self,
        surface: pygame.Surface,
        y: int,
        row_asset_name: str,
        child_name: str,
        value: str,
        color: tuple[int, int, int],
    ) -> None:
        """Render one checkout booking row: child icon, name, and signed amount."""
        row_x = self._card_x + 55
        row_rect = pygame.Rect(row_x, y, 390, 64)

        try:
            row_bg = get_raw_asset(f"ui/cashier/{row_asset_name}")
            surface.blit(row_bg, row_rect.topleft)
        except FileNotFoundError:
            pygame.draw.rect(surface, BG_CARD, row_rect, border_radius=16)

        self._render_child_icon(surface, child_name, (row_x + 38, y + 32))
        self._render_child_name(surface, child_name, row_x + 74, y + 32)
        self._render_signed_amount(surface, value, color, row_rect.right - 22, y + 32)

    def _render_child_icon(
        self, surface: pygame.Surface, child_name: str, center: tuple[int, int]
    ) -> None:
        """Render the best known avatar for a child name."""
        avatar_name = self._avatar_asset_name(child_name)
        try:
            avatar = get_asset(f"recipes/{avatar_name}", "M")
            avatar = pygame.transform.smoothscale(avatar, (48, 48))
            avatar_rect = avatar.get_rect(center=center)
            surface.blit(avatar, avatar_rect)
        except FileNotFoundError:
            pygame.draw.circle(surface, (219, 234, 254), center, 24)

    def _render_child_name(
        self, surface: pygame.Surface, child_name: str, x: int, center_y: int
    ) -> None:
        """Render child name inside the transfer row."""
        name_text = self._fit_text(child_name, max_width=170, color=TEXT_PRIMARY)
        name_rect = name_text.get_rect(midleft=(x, center_y))
        surface.blit(name_text, name_rect)

    def _render_signed_amount(
        self,
        surface: pygame.Surface,
        value: str,
        color: tuple[int, int, int],
        right: int,
        center_y: int,
    ) -> None:
        """Render signed amount with coin icon aligned to the right."""
        coin_size = 34
        value_font = bold_custom(42)
        value_text = value_font.render(value, True, color)
        gap = 8
        total_width = coin_size + gap + value_text.get_width()
        start_x = right - total_width

        try:
            coin = get_asset("products/taler", "M")
            coin = pygame.transform.smoothscale(coin, (coin_size, coin_size))
            surface.blit(coin, (start_x, center_y - coin_size // 2))
        except FileNotFoundError:
            pygame.draw.circle(
                surface, (245, 158, 11), (start_x + coin_size // 2, center_y), 16
            )

        value_rect = value_text.get_rect(
            midleft=(start_x + coin_size + gap, center_y - 2)
        )
        surface.blit(value_text, value_rect)

    def _fit_text(
        self, text: str, *, max_width: int, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Render text at the largest size that fits."""
        for size in (32, 29, 26, 23):
            text_surface = custom(size).render(text, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface

        clipped_text = text
        font = custom(22)
        while len(clipped_text) > 4:
            candidate = f"{clipped_text[:-1]}…"
            text_surface = font.render(candidate, True, color)
            if text_surface.get_width() <= max_width:
                return text_surface
            clipped_text = clipped_text[:-1]
        return font.render(clipped_text[:4], True, color)

    def _avatar_asset_name(self, child_name: str) -> str:
        """Map known child names to existing avatar artwork."""
        normalized_name = child_name.strip().lower()
        if normalized_name == "carolin":
            return "avata_carolin"
        if normalized_name == "annelie":
            return "avata_annelie"
        return "avata_kind_klein"
