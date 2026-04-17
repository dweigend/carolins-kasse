"""Checkout mixin for scenes that handle payment flows."""

from abc import abstractmethod

import pygame

from src.components.checkout_receipt import CheckoutReceipt
from src.components.insufficient_funds_popup import InsufficientFundsPopup
from src.constants import (
    BG_CARD,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from src.utils.database import get_user, process_checkout
from src.utils.earnings import award_cashier_salary
from src.utils.fonts import body, caption


class CheckoutMixin:
    """Mixin providing checkout functionality for shopping scenes.

    Scene must implement:
        _get_checkout_total() -> int
        _get_checkout_items() -> list[dict]
        _on_checkout_complete() -> None
        _show_message(text, frames, color) - from MessageMixin

    Mixin provides:
        _checkout_mode: bool
        _checkout_receipt: CheckoutReceipt
        _insufficient_funds_popup: InsufficientFundsPopup
        _init_checkout_ui()
        _enter_checkout_mode()
        _exit_checkout_mode()
        _handle_checkout_barcode(barcode) -> bool
        _render_checkout_overlays(screen)
    """

    _checkout_mode: bool
    _checkout_receipt: CheckoutReceipt | None
    _insufficient_funds_popup: InsufficientFundsPopup | None
    _checkout_font: pygame.font.Font | None
    _checkout_small_font: pygame.font.Font | None

    def _init_checkout_ui(self) -> None:
        """Initialize checkout UI components."""
        self._checkout_mode = False
        self._checkout_receipt = CheckoutReceipt()
        self._insufficient_funds_popup = InsufficientFundsPopup()
        self._checkout_font = None
        self._checkout_small_font = None

    def _init_checkout_fonts(self) -> None:
        """Initialize fonts lazily."""
        if self._checkout_font is None:
            self._checkout_font = body()
            self._checkout_small_font = caption()

    @abstractmethod
    def _get_checkout_total(self) -> int:
        """Return total amount for checkout."""
        ...

    @abstractmethod
    def _get_checkout_items(self) -> list[dict]:
        """Return items for transaction record.

        Each dict should have: barcode, name, qty, price
        """
        ...

    @abstractmethod
    def _on_checkout_complete(self) -> None:
        """Called after successful checkout. Clear cart, reset state, etc."""
        ...

    @abstractmethod
    def _show_message(
        self, text: str, frames: int = 60, color: tuple = TEXT_PRIMARY
    ) -> None:
        """Show a feedback message."""
        ...

    def _enter_checkout_mode(self) -> bool:
        """Enter checkout mode. Returns False if checkout not possible."""
        if not hasattr(self, "_checkout_mode"):
            return False

        total = self._get_checkout_total()
        if total <= 0:
            self._show_message("Nichts zu bezahlen!")
            return False

        self._checkout_mode = True
        self._show_message("💳 Kunde: Bitte Badge scannen!")
        return True

    def _exit_checkout_mode(self) -> None:
        """Exit checkout mode."""
        if hasattr(self, "_checkout_mode"):
            self._checkout_mode = False

    def _cancel_checkout(self) -> None:
        """Cancel checkout and show message."""
        self._exit_checkout_mode()
        self._show_message("Bezahlung abgebrochen")

    def _handle_checkout_barcode(self, barcode: str) -> bool:
        """Handle barcode during checkout mode.

        Args:
            barcode: Scanned barcode

        Returns:
            True if barcode was handled (consumed)
        """
        if not hasattr(self, "_checkout_mode") or not self._checkout_mode:
            return False

        # Only accept user badges (200 prefix)
        if not barcode.startswith("200"):
            self._show_message("Bitte Kunden-Badge scannen!")
            return True

        # Look up customer
        customer = get_user(barcode)
        if not customer:
            self._show_message("Karte nicht erkannt!")
            return True

        total = self._get_checkout_total()

        # Check balance
        if customer.balance < total:
            if self._insufficient_funds_popup:
                self._insufficient_funds_popup.show(total, int(customer.balance))
            self._exit_checkout_mode()
            return True

        # Process payment atomically
        new_balance = customer.balance - total
        items_data = self._get_checkout_items()
        process_checkout(customer.card_id, new_balance, total, items_data)

        # Pay cashier salary
        salary, cashier_name = award_cashier_salary(customer.name)

        # Show receipt (with cashier salary info)
        if self._checkout_receipt:
            self._checkout_receipt.show(
                customer.name, total, int(new_balance), cashier_name, salary
            )

        # Cleanup
        self._exit_checkout_mode()
        self._on_checkout_complete()

        return True

    def _handle_checkout_event(self, event: pygame.event.Event) -> bool:
        """Handle events during checkout mode.

        Args:
            event: pygame event

        Returns:
            True if event was consumed
        """
        # Guard: only handle if initialized
        if not hasattr(self, "_checkout_mode"):
            return False

        # Handle insufficient funds popup
        if (
            hasattr(self, "_insufficient_funds_popup")
            and self._insufficient_funds_popup
            and self._insufficient_funds_popup.is_visible()
        ):
            return self._insufficient_funds_popup.handle_event(event)

        # Allow canceling checkout with Backspace
        if self._checkout_mode:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                self._cancel_checkout()
                return True

        return False

    def _update_checkout_ui(self) -> None:
        """Update checkout UI components."""
        # Guard: only update if initialized
        if hasattr(self, "_checkout_receipt") and self._checkout_receipt:
            self._checkout_receipt.update()

    def _render_checkout_overlay(self, screen: pygame.Surface) -> None:
        """Render the checkout mode overlay (waiting for badge)."""
        if not hasattr(self, "_checkout_mode") or not self._checkout_mode:
            return

        self._init_checkout_fonts()

        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Dialog card
        card_width = 450
        card_height = 250
        card_x = (SCREEN_WIDTH - card_width) // 2
        card_y = (SCREEN_HEIGHT - card_height) // 2 - 30

        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(screen, BG_CARD, card_rect, border_radius=16)
        pygame.draw.rect(screen, SUCCESS, card_rect, width=3, border_radius=16)

        if self._checkout_font:
            # Title
            title = self._checkout_font.render("BEZAHLEN", True, SUCCESS)
            title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=card_y + 30)
            screen.blit(title, title_rect)

            # Total
            total = self._get_checkout_total()
            total_str = f"Gesamt: {total} Taler"
            total_text = self._checkout_font.render(total_str, True, TEXT_PRIMARY)
            total_rect = total_text.get_rect(centerx=SCREEN_WIDTH // 2, y=card_y + 80)
            screen.blit(total_text, total_rect)

            # Icon
            icon_font = pygame.font.Font(None, 72)
            icon = icon_font.render("💳", True, SUCCESS)
            icon_rect = icon.get_rect(centerx=SCREEN_WIDTH // 2, y=card_y + 130)
            screen.blit(icon, icon_rect)

        if self._checkout_small_font:
            # Instruction
            hint = self._checkout_small_font.render(
                "Kunde: Bitte Badge vor Scanner halten!", True, TEXT_MUTED
            )
            hint_rect = hint.get_rect(centerx=SCREEN_WIDTH // 2, y=card_y + 190)
            screen.blit(hint, hint_rect)

    def _render_checkout_overlays(self, screen: pygame.Surface) -> None:
        """Render all checkout-related overlays."""
        # Guard: only render if initialized
        if not hasattr(self, "_checkout_mode"):
            return

        # Checkout mode overlay
        self._render_checkout_overlay(screen)

        # Receipt overlay (after successful payment)
        if hasattr(self, "_checkout_receipt") and self._checkout_receipt:
            self._checkout_receipt.render(screen)

        # Insufficient funds popup
        if (
            hasattr(self, "_insufficient_funds_popup")
            and self._insufficient_funds_popup
        ):
            self._insufficient_funds_popup.render(screen)
