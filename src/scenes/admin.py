"""On-device admin scene for quick parent tasks at the register."""

from collections.abc import Callable
from dataclasses import dataclass

import pygame
import qrcode

from src.constants import (
    BG_CARD,
    BLUE,
    DANGER,
    GREY_LIGHT,
    ORANGE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)
from src.scenes.base import Scene
from src.scenes.mixins import MessageMixin
from src.utils.admin_runtime import (
    AdminServerStatus,
    get_admin_server_status,
    toggle_admin_server,
)
from src.utils.database import (
    BalanceAdjustment,
    User,
    get_all_users,
    get_recent_balance_adjustments,
    update_user_admin_fields,
    update_user_balance,
)
from src.utils.fonts import bold_custom, custom
from src.utils.network import admin_url, get_local_ip
from src.utils.text_utils import truncate_text, wrap_text

CONTENT_RECT = pygame.Rect(42, 82, SCREEN_WIDTH - 84, SCREEN_HEIGHT - 212)
TAB_Y = CONTENT_RECT.y
TAB_H = 42
PANEL_Y = TAB_Y + TAB_H + 12
PANEL_H = CONTENT_RECT.bottom - PANEL_Y
BUTTON_RADIUS = 10
QR_SIZE = 170
USER_ROW_HEIGHT = 56
USER_ROW_GAP = 10
PANEL_GAP = 18
PANEL_INSET = 18
STATUS_PANEL_WIDTH = 444
STATUS_VALUE_X = 126
STATUS_VALUE_MAX_WIDTH = 324
ACTION_BUTTON_Y_OFFSET = 72
BALANCE_BUTTON_WIDTH = 58
BALANCE_BUTTON_HEIGHT = 38
BALANCE_BUTTON_GAP = 66
USER_ACTIONS_WIDTH = 520
TOGGLE_BUTTON_WIDTH = 88
DIFFICULTY_BUTTON_WIDTH = 58
ADJUSTMENT_SUMMARY_WIDTH = 370

TABS = (
    ("status", "Status"),
    ("users", "User & Konten"),
    ("notes", "Hinweise"),
)

HELP_LINES = [
    "Handy ins gleiche WLAN bringen.",
    "Server starten und QR-Code scannen.",
    "SSH bleibt über das Heimnetz erreichbar.",
    "Server nur bei Bedarf eingeschaltet lassen.",
    "Remote-Admin läuft ohne Web-Login.",
]


@dataclass(frozen=True)
class AdminButton:
    """Clickable rectangle registered during one admin render pass."""

    rect: pygame.Rect
    callback: Callable[[], None]


class AdminScene(MessageMixin, Scene):
    """Admin screen shown after scanning the existing Admin card."""

    def __init__(self) -> None:
        """Initialize the on-device admin scene."""
        self._active_tab = "status"
        self._buttons: list[AdminButton] = []
        self._users: list[User] = []
        self._adjustments: list[BalanceAdjustment] = []
        self._status: AdminServerStatus = get_admin_server_status()
        self._qr_surface: pygame.Surface | None = None
        self._qr_url: str | None = None
        self._font_title = bold_custom(26)
        self._font_body = custom(22)
        self._font_small = custom(18)
        self._font_tiny = custom(15)
        self._refresh_data()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle touch events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in reversed(self._buttons):
                if button.rect.collidepoint(event.pos):
                    button.callback()
                    return self._consume_next_scene()
        return self._consume_next_scene()

    def update(self) -> None:
        """Refresh temporary messages."""
        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Render the admin surface."""
        self._buttons.clear()
        self._draw_tabs(screen)

        if self._active_tab == "status":
            self._draw_status_tab(screen)
        elif self._active_tab == "users":
            self._draw_users_tab(screen)
        else:
            self._draw_notes_tab(screen)

        self._render_message(
            screen,
            self._font_small,
            CONTENT_RECT.centerx,
            CONTENT_RECT.bottom + 8,
            center_x=True,
        )

    def _refresh_data(self) -> None:
        self._users = get_all_users(include_inactive=True)
        self._adjustments = get_recent_balance_adjustments(limit=8)
        self._status = get_admin_server_status()
        self._refresh_qr()

    def _refresh_qr(self) -> None:
        url = admin_url()
        if not url:
            self._qr_surface = None
            self._qr_url = None
            return
        if url == self._qr_url and self._qr_surface:
            return

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        image = image.resize((QR_SIZE, QR_SIZE))
        self._qr_surface = pygame.image.fromstring(
            image.tobytes(), image.size, image.mode
        )
        self._qr_url = url

    def _draw_tabs(self, screen: pygame.Surface) -> None:
        tab_w = 176
        gap = 10
        x = CONTENT_RECT.x
        for key, label in TABS:
            rect = pygame.Rect(x, TAB_Y, tab_w, TAB_H)
            active = key == self._active_tab
            color = ORANGE if active else BG_CARD
            text_color = WHITE if active else TEXT_PRIMARY
            self._draw_button(
                screen,
                rect,
                label,
                color,
                text_color,
                lambda k=key: self._set_tab(k),
            )
            x += tab_w + gap

    def _draw_status_tab(self, screen: pygame.Surface) -> None:
        left = pygame.Rect(CONTENT_RECT.x, PANEL_Y, STATUS_PANEL_WIDTH, PANEL_H)
        right = pygame.Rect(
            left.right + PANEL_GAP,
            PANEL_Y,
            CONTENT_RECT.right - left.right - PANEL_GAP,
            PANEL_H,
        )
        self._draw_panel(screen, left, "Remote Admin")
        self._draw_panel(screen, right, "QR-Code")
        self._draw_status_rows(screen, left)
        self._draw_server_controls(screen, left)
        self._draw_qr_area(screen, right)

    def _draw_status_rows(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        ip_address = get_local_ip() or "Keine IP"
        url = self._status.url or "Nicht erreichbar"
        status_color = SUCCESS if self._status.running else DANGER
        rows = [
            ("WLAN", ip_address),
            ("Server", self._status.message),
            ("URL", url),
        ]
        y = panel.y + 58
        for label, value in rows:
            self._draw_text(
                screen,
                label,
                panel.x + PANEL_INSET,
                y,
                self._font_small,
                TEXT_SECONDARY,
            )
            value_color = status_color if label == "Server" else TEXT_PRIMARY
            self._draw_text(
                screen,
                truncate_text(value, self._font_small, STATUS_VALUE_MAX_WIDTH),
                panel.x + STATUS_VALUE_X,
                y,
                self._font_small,
                value_color,
            )
            y += 38

    def _draw_server_controls(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        button_text = (
            "Server stoppen"
            if self._status.running and self._status.managed
            else "Server starten"
        )
        if self._status.running and not self._status.managed:
            button_text = "Server läuft extern"
        button_color = (
            DANGER if self._status.running and self._status.managed else SUCCESS
        )
        self._draw_button(
            screen,
            pygame.Rect(
                panel.x + PANEL_INSET, panel.bottom - ACTION_BUTTON_Y_OFFSET, 190, 48
            ),
            button_text,
            button_color,
            WHITE,
            self._toggle_server,
            enabled=not (self._status.running and not self._status.managed),
        )
        self._draw_button(
            screen,
            pygame.Rect(panel.x + 222, panel.bottom - ACTION_BUTTON_Y_OFFSET, 130, 48),
            "Aktualisieren",
            BLUE,
            WHITE,
            self._refresh_data,
        )

    def _draw_qr_area(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        if self._qr_surface:
            screen.blit(self._qr_surface, (panel.centerx - QR_SIZE // 2, panel.y + 58))
            self._draw_text(
                screen,
                self._qr_url or "",
                panel.centerx,
                panel.y + 244,
                self._font_tiny,
                TEXT_PRIMARY,
                center=True,
            )
        else:
            self._draw_wrapped(
                screen,
                "Keine Netzwerkadresse gefunden. Pi mit dem Heim-WLAN verbinden.",
                panel.x + 22,
                panel.y + 76,
                panel.width - 44,
                DANGER,
            )

    def _draw_users_tab(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(CONTENT_RECT.x, PANEL_Y, CONTENT_RECT.width, PANEL_H)
        self._draw_panel(screen, panel, "User & Konten")
        self._draw_latest_adjustment_summary(screen, panel)

        y = panel.y + 56
        for user in self._users:
            row = pygame.Rect(
                panel.x + 16,
                y,
                panel.width - 32,
                USER_ROW_HEIGHT,
            )
            self._draw_user_row(screen, row, user)
            y += USER_ROW_HEIGHT + USER_ROW_GAP

    def _draw_user_row(
        self, screen: pygame.Surface, row: pygame.Rect, user: User
    ) -> None:
        pygame.draw.rect(screen, GREY_LIGHT, row, border_radius=10)
        self._draw_user_summary(screen, row, user)
        self._draw_balance_buttons(screen, row, user)
        self._draw_user_admin_buttons(screen, row, user)

    def _draw_user_summary(
        self, screen: pygame.Surface, row: pygame.Rect, user: User
    ) -> None:
        status = "aktiv" if user.active else "inaktiv"
        role = "Admin" if user.is_admin else f"Stufe {user.difficulty}"
        self._draw_text(
            screen, user.name, row.x + 14, row.y + 6, self._font_body, TEXT_PRIMARY
        )
        self._draw_text(
            screen,
            f"{int(user.balance)} Taler · {role} · {status}",
            row.x + 14,
            row.y + 32,
            self._font_tiny,
            TEXT_SECONDARY,
        )

    def _draw_balance_buttons(
        self, screen: pygame.Surface, row: pygame.Rect, user: User
    ) -> None:
        x = row.right - USER_ACTIONS_WIDTH
        for delta in (-1, 1, 5, 10):
            self._draw_button(
                screen,
                pygame.Rect(x, row.y + 9, BALANCE_BUTTON_WIDTH, BALANCE_BUTTON_HEIGHT),
                f"{delta:+d}",
                DANGER if delta < 0 else SUCCESS,
                WHITE,
                lambda u=user, d=delta: self._adjust_balance(u, d),
            )
            x += BALANCE_BUTTON_GAP

    def _draw_user_admin_buttons(
        self, screen: pygame.Surface, row: pygame.Rect, user: User
    ) -> None:
        button_y = row.y + 9
        self._draw_button(
            screen,
            pygame.Rect(
                row.right - 242, button_y, TOGGLE_BUTTON_WIDTH, BALANCE_BUTTON_HEIGHT
            ),
            "Admin" if user.is_admin else "An/Aus",
            ORANGE,
            WHITE,
            lambda u=user: self._toggle_user_active(u),
            enabled=not user.is_admin,
        )
        self._draw_difficulty_button(screen, row.right - 144, button_y, "S-", user, -1)
        self._draw_difficulty_button(screen, row.right - 78, button_y, "S+", user, 1)

    def _draw_difficulty_button(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        label: str,
        user: User,
        delta: int,
    ) -> None:
        self._draw_button(
            screen,
            pygame.Rect(x, y, DIFFICULTY_BUTTON_WIDTH, BALANCE_BUTTON_HEIGHT),
            label,
            BLUE,
            WHITE,
            lambda u=user, d=delta: self._change_difficulty(u, d),
        )

    def _draw_latest_adjustment_summary(
        self, screen: pygame.Surface, panel: pygame.Rect
    ) -> None:
        if not self._adjustments:
            text = "Keine letzten Änderungen"
        else:
            adjustment = self._adjustments[0]
            delta = f"{adjustment.delta:+.0f}"
            text = f"Letzte Änderung: {adjustment.user_name} {delta} -> {adjustment.new_balance:.0f}"

        self._draw_text(
            screen,
            truncate_text(text, self._font_tiny, ADJUSTMENT_SUMMARY_WIDTH),
            panel.right - ADJUSTMENT_SUMMARY_WIDTH - 20,
            panel.y + 24,
            self._font_tiny,
            TEXT_SECONDARY,
        )

    def _draw_notes_tab(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(CONTENT_RECT.x, PANEL_Y, CONTENT_RECT.width, PANEL_H)
        self._draw_panel(screen, panel, "Wichtige Hinweise")
        y = panel.y + 62
        for line in HELP_LINES:
            self._draw_text(
                screen, f"• {line}", panel.x + 34, y, self._font_small, TEXT_PRIMARY
            )
            y += 42

    def _set_tab(self, tab: str) -> None:
        self._active_tab = tab
        self._refresh_data()

    def _toggle_server(self) -> None:
        self._status = toggle_admin_server()
        self._refresh_data()
        self._show_message(self._status.message)

    def _adjust_balance(self, user: User, delta: int) -> None:
        new_balance = max(0, user.balance + delta)
        update_user_balance(user.card_id, new_balance, f"Kassen-Admin {delta:+d}")
        self._refresh_data()
        self._show_message(f"{user.name}: {int(new_balance)} Taler")

    def _toggle_user_active(self, user: User) -> None:
        if user.is_admin:
            self._show_message("Admin bleibt aktiv")
            return

        update_user_admin_fields(
            user.card_id,
            user.name,
            user.difficulty,
            not user.active,
        )
        self._refresh_data()

    def _change_difficulty(self, user: User, delta: int) -> None:
        difficulty = max(1, min(3, user.difficulty + delta))
        update_user_admin_fields(user.card_id, user.name, difficulty, user.active)
        self._refresh_data()

    def _draw_panel(
        self, screen: pygame.Surface, rect: pygame.Rect, title: str
    ) -> None:
        pygame.draw.rect(screen, BG_CARD, rect, border_radius=14)
        pygame.draw.rect(screen, ORANGE, rect, width=3, border_radius=14)
        self._draw_text(
            screen, title, rect.x + 18, rect.y + 16, self._font_title, TEXT_PRIMARY
        )

    def _draw_button(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        callback: Callable[[], None],
        *,
        enabled: bool = True,
    ) -> None:
        final_color = color if enabled else TEXT_SECONDARY
        pygame.draw.rect(screen, final_color, rect, border_radius=BUTTON_RADIUS)
        text = self._font_small.render(label, True, text_color)
        screen.blit(text, text.get_rect(center=rect.center))
        if enabled:
            self._buttons.append(AdminButton(rect, callback))

    def _draw_text(
        self,
        screen: pygame.Surface,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        *,
        center: bool = False,
    ) -> None:
        surface = font.render(text, True, color)
        rect = (
            surface.get_rect(center=(x, y))
            if center
            else surface.get_rect(topleft=(x, y))
        )
        screen.blit(surface, rect)

    def _draw_wrapped(
        self,
        screen: pygame.Surface,
        text: str,
        x: int,
        y: int,
        max_width: int,
        color: tuple[int, int, int],
    ) -> None:
        for line in wrap_text(text, self._font_small, max_width):
            self._draw_text(screen, line, x, y, self._font_small, color)
            y += 28
