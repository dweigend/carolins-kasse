"""Math game scene - practice calculations with a clean reward-focused UI."""

import pygame

from src.components.numpad import Numpad
from src.constants import (
    BG_CARD,
    DANGER,
    EARNING_MATH,
    GREY_LIGHT,
    GREY_MEDIUM,
    ORANGE,
    PRIMARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SUCCESS,
    TEXT_PRIMARY,
    WARNING,
)
from src.scenes.base import Scene
from src.scenes.mixins import MessageMixin
from src.utils import state
from src.utils.fonts import bold_custom, body, caption, heading
from src.utils.math_generator import MathProblem, generate_problem

# Game settings
DEFAULT_DIFFICULTY = 1

# Layout (inside shell content area)
CONTENT_TOP = 80
CONTENT_BOTTOM = 540
LEFT_PANEL_X = 50
LEFT_PANEL_W = 320
RIGHT_PANEL_X = LEFT_PANEL_X + LEFT_PANEL_W + 30
RIGHT_PANEL_W = SCREEN_WIDTH - RIGHT_PANEL_X - 50


REWARD_BADGE_HEIGHT = 72
REWARD_BADGE_WIDTH = 128
REWARD_BADGE_GAP = 18
CARD_SHADOW_OFFSET = 4
CARD_SHADOW_COLOR = (0, 0, 0, 18)


class MathGameScene(MessageMixin, Scene):
    """Math game where kids solve problems and see one clear reward cue."""

    def __init__(self) -> None:
        """Initialize math game scene."""
        user = state.get_current_user()
        self._difficulty = user.difficulty if user else DEFAULT_DIFFICULTY
        self._current_problem: MathProblem | None = None
        self._current_answer: str = ""
        self._session_taler = 0
        self._session_max = 15
        self._bonus_threshold = 10
        self._bonus_awarded = False
        self._session_complete = False
        self._complete_timer = 0

        # UI components
        self._numpad: Numpad | None = None

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        # Numpad on left panel
        numpad_width = Numpad.width()
        numpad_x = LEFT_PANEL_X + (LEFT_PANEL_W - numpad_width) // 2
        numpad_y = CONTENT_TOP + 18

        self._numpad = Numpad(
            numpad_x,
            numpad_y,
            on_enter=self._submit_answer,
            on_change=self._update_answer,
            max_digits=2,
        )

        self._next_problem()
        self._initialized = True

    def _next_problem(self) -> None:
        """Generate a new problem."""
        self._current_problem = generate_problem(self._difficulty)
        self._current_answer = ""
        if self._numpad:
            self._numpad.set_max_digits(self._answer_slot_count())
            self._numpad.clear()

    def _answer_slot_count(self) -> int:
        """Return how many answer slots the current problem should show."""
        if not self._current_problem:
            return 1
        return 1 if self._current_problem.answer < 10 else 2

    def _current_reward(self) -> int:
        """Return the reward for the currently active difficulty."""
        return EARNING_MATH.get(self._difficulty, 1)

    def _update_answer(self, value: str) -> None:
        """Update current answer from numpad."""
        self._current_answer = value

    def _submit_answer(self, value: str) -> None:
        """Check the submitted answer."""
        if not self._current_problem or not value:
            return

        try:
            answer = int(value)
        except ValueError:
            return

        if self._current_problem.check(answer):
            self._handle_correct_answer()
            self._next_problem()
            return

        correct = self._current_problem.answer
        self._show_message(f"Falsch! ({correct})", 60, color=DANGER)
        self._next_problem()

    def _handle_correct_answer(self) -> None:
        """Apply rewards and feedback for a correct answer."""
        reward = self._current_reward()
        self._session_taler += reward
        state.add_earning("math", reward, "Aufgabe gelöst")

        if self._session_taler >= self._bonus_threshold and not self._bonus_awarded:
            self._bonus_awarded = True
            bonus = 1
            state.add_earning("math", bonus, "Bonus: Ziel erreicht!")
            self._session_taler += bonus
            self._show_message("Bonus freigeschaltet!", 90, color=SUCCESS)
        else:
            self._show_message("Richtig!", 75, color=SUCCESS)

        if self._session_taler >= self._session_max:
            self._session_complete = True
            self._complete_timer = 120

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()

        if self._session_complete:
            return self._consume_next_scene()

        if self._numpad:
            self._numpad.handle_event(event)

        return self._consume_next_scene()

    def update(self) -> None:
        """Update scene state."""
        if self._session_complete:
            self._complete_timer -= 1
            if self._complete_timer <= 0:
                self._go_to("menu")
            return

        state.check_time_bonus()
        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the math game screen (no background fill — shell handles it)."""
        self._init_ui()

        # Left panel: Numpad
        if self._numpad:
            self._numpad.render(screen)

        self._render_problem_card(screen)
        self._render_answer_section(screen)

        # Feedback message
        score_font = caption()
        self._render_message(
            screen,
            score_font,
            RIGHT_PANEL_X + RIGHT_PANEL_W // 2,
            CONTENT_BOTTOM - 80,
            center_x=True,
        )

        # Session complete overlay
        if self._session_complete:
            self._render_complete_overlay(screen)

    def _render_problem_card(self, screen: pygame.Surface) -> None:
        """Render the current math problem inside a single prominent card."""
        if not self._current_problem:
            return

        card_rect = pygame.Rect(
            RIGHT_PANEL_X + 28, CONTENT_TOP + 42, RIGHT_PANEL_W - 56, 118
        )
        self._draw_card(screen, card_rect, GREY_LIGHT, border_width=2)
        problem_font = bold_custom(64)
        problem_text = problem_font.render(
            self._current_problem.display, True, TEXT_PRIMARY
        )
        text_rect = problem_text.get_rect(center=card_rect.center)
        screen.blit(problem_text, text_rect)

    def _render_answer_section(self, screen: pygame.Surface) -> None:
        """Render the answer box and the single visible reward indicator."""
        slot_count = self._answer_slot_count()
        input_width = 240 if slot_count == 1 else 310
        input_height = 92
        input_y = CONTENT_TOP + 212
        section_width = input_width + REWARD_BADGE_GAP + REWARD_BADGE_WIDTH
        section_x = RIGHT_PANEL_X + (RIGHT_PANEL_W - section_width) // 2
        input_x = section_x

        input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        self._draw_card(screen, input_rect, PRIMARY, radius=22, border_width=4)

        slot_width = 50
        slot_gap = 26
        total_slot_width = slot_count * slot_width + (slot_count - 1) * slot_gap
        start_x = input_rect.centerx - total_slot_width // 2
        digit_y = input_rect.y + 16
        underline_y = input_rect.bottom - 20

        answer_font = bold_custom(52)
        for index in range(slot_count):
            slot_x = start_x + index * (slot_width + slot_gap)
            slot_rect = pygame.Rect(slot_x, digit_y, slot_width, 48)

            if index < len(self._current_answer):
                digit_surface = answer_font.render(
                    self._current_answer[index], True, TEXT_PRIMARY
                )
                digit_rect = digit_surface.get_rect(center=slot_rect.center)
                screen.blit(digit_surface, digit_rect)

            underline_color = (
                PRIMARY if index < len(self._current_answer) else GREY_MEDIUM
            )
            pygame.draw.line(
                screen,
                underline_color,
                (slot_x + 4, underline_y),
                (slot_x + slot_width - 4, underline_y),
                6,
            )

        reward_rect = pygame.Rect(
            input_rect.right + REWARD_BADGE_GAP,
            input_rect.y + (input_rect.height - REWARD_BADGE_HEIGHT) // 2,
            REWARD_BADGE_WIDTH,
            REWARD_BADGE_HEIGHT,
        )
        self._render_reward_badge(screen, reward_rect)

    def _render_reward_badge(
        self, screen: pygame.Surface, reward_rect: pygame.Rect
    ) -> None:
        """Render a compact reward badge next to the answer input."""
        self._draw_card(screen, reward_rect, WARNING, border_width=3)

        coin_center = (reward_rect.x + 28, reward_rect.centery)
        pygame.draw.circle(screen, WARNING, coin_center, 16)
        pygame.draw.circle(screen, ORANGE, coin_center, 16, width=3)

        reward_font = bold_custom(34)
        reward_text = reward_font.render(
            f"+{self._current_reward()}", True, TEXT_PRIMARY
        )
        reward_rect_text = reward_text.get_rect(
            midleft=(reward_rect.x + 52, reward_rect.centery)
        )
        screen.blit(reward_text, reward_rect_text)

    def _draw_card(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        border_color: tuple[int, int, int],
        *,
        radius: int = 24,
        border_width: int = 3,
    ) -> None:
        """Draw a reusable elevated white card with a colored border."""
        pygame.draw.rect(
            screen,
            CARD_SHADOW_COLOR,
            rect.move(0, CARD_SHADOW_OFFSET),
            border_radius=radius,
        )
        pygame.draw.rect(screen, BG_CARD, rect, border_radius=radius)
        pygame.draw.rect(
            screen,
            border_color,
            rect,
            width=border_width,
            border_radius=radius,
        )

    def _render_complete_overlay(self, screen: pygame.Surface) -> None:
        """Render session complete overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        card_width = 400
        card_height = 200
        card_x = (SCREEN_WIDTH - card_width) // 2
        card_y = (SCREEN_HEIGHT - card_height) // 2
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        self._draw_card(screen, card_rect, SUCCESS, radius=20, border_width=4)

        title_font = heading()
        star_text = title_font.render("SUPER GEMACHT!", True, SUCCESS)
        star_rect = star_text.get_rect(
            centerx=card_rect.centerx, centery=card_rect.y + 70
        )
        screen.blit(star_text, star_rect)

        body_font = body()
        stats_text = body_font.render(
            f"{self._session_taler} Taler verdient!", True, TEXT_PRIMARY
        )
        stats_rect = stats_text.get_rect(
            centerx=card_rect.centerx, centery=card_rect.y + 130
        )
        screen.blit(stats_text, stats_rect)
