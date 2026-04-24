"""Math game scene - practice calculations with optional dot hints."""

import math
from dataclasses import dataclass

import pygame

from src.constants import (
    BLACK,
    DANGER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHELL_MONEY_ICON_X,
    SHELL_MONEY_ICON_Y,
    SUCCESS,
    TEXT_PRIMARY,
)
from src.scenes.base import Scene
from src.scenes.mixins import MessageMixin
from src.utils import assets as asset_loader
from src.utils import state
from src.utils.fonts import bold_custom, body, heading
from src.utils.math_generator import MathProblem, generate_problem

DEFAULT_DIFFICULTY = 1

EQUATION_CENTER_Y = 265
HELP_DOTS_TOP = 334

REWARD_WITHOUT_HELP = 2
REWARD_WITH_HELP = 1
MAX_WRONG_ATTEMPTS = 2
SUCCESS_CONFETTI_FRAMES = 20
REWARD_TRANSFER_FRAMES = 34
SUCCESS_ANIMATION_FRAMES = SUCCESS_CONFETTI_FRAMES + REWARD_TRANSFER_FRAMES
SUCCESS_PARTICLE_LIFETIME = 20

EQUATION_FONT_SIZE = 118
SYMBOL_FONT_SIZE = 104
ANSWER_SLOT_WIDTH = 74
ANSWER_SLOT_GAP = 28
EQUATION_GAP = 34
ANSWER_UNDERLINE_WIDTH = 58
ANSWER_UNDERLINE_HEIGHT = 8

FIRST_OPERAND_COLOR = (248, 198, 45)
SECOND_OPERAND_COLOR = (23, 128, 192)
ANSWER_COLOR = (237, 164, 179)
DOT_EMPTY_COLOR = (249, 238, 190)
DOT_EMPTY_SECOND_COLOR = (202, 222, 237)
DOT_SHADOW_COLOR = (224, 216, 202)
BADGE_COLOR = (63, 166, 144)
BADGE_SHADOW_COLOR = (37, 112, 98)
BADGE_DOT_COLORS = (
    (252, 207, 47),
    (239, 95, 72),
    (248, 147, 172),
    (244, 229, 91),
    (31, 128, 191),
)
REWARD_BADGE_CENTER = (820, 182)
REWARD_TRANSFER_TARGET = (SHELL_MONEY_ICON_X + 24, SHELL_MONEY_ICON_Y + 24)
REWARD_BADGE_SIZE = "XL"
REWARD_COIN_VARIANTS = {
    REWARD_WITH_HELP: (
        "ui/rewards/coin_1_a",
        "ui/rewards/coin_1_b",
        "ui/rewards/coin_1_c",
    ),
    REWARD_WITHOUT_HELP: (
        "ui/rewards/coin_2_a",
        "ui/rewards/coin_2_b",
        "ui/rewards/coin_2_c",
    ),
}
SUCCESS_PARTICLE_COLORS = (
    (252, 207, 47),
    (239, 95, 72),
    (248, 147, 172),
    (31, 128, 191),
    (63, 166, 144),
)
SUCCESS_PARTICLE_SPECS = (
    (-78, -10, -2.4, -3.9, "star", 0),
    (-46, -46, -1.4, -4.8, "confetti", 2),
    (-14, -62, -0.4, -4.2, "confetti", 4),
    (22, -52, 0.7, -4.5, "star", 1),
    (58, -30, 1.8, -4.0, "confetti", 3),
    (86, -2, 2.6, -3.3, "confetti", 5),
    (-66, 30, -2.0, -2.8, "star", 7),
    (-24, 44, -0.8, -3.0, "confetti", 6),
    (30, 42, 1.0, -3.1, "confetti", 8),
    (72, 28, 2.1, -2.7, "star", 6),
)


@dataclass(frozen=True)
class EquationLayout:
    """Positions for dynamic equation helpers."""

    first_operand_rect: pygame.Rect
    second_operand_rect: pygame.Rect
    answer_rect: pygame.Rect


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
        self._session_complete = False
        self._complete_timer = 0
        self._hint_visible = False
        self._wrong_attempts = 0
        self._problem_sequence = 0
        self._reward_variant_index = 0
        self._success_timer = 0
        self._success_reward = REWARD_WITHOUT_HELP
        self._pending_reward = 0

    def _init_ui(self) -> None:
        """Initialize UI elements."""
        if self._initialized:
            return

        self._next_problem()
        self._initialized = True

    def _next_problem(self) -> None:
        """Generate a new problem and reset transient answer state."""
        self._current_problem = generate_problem(self._difficulty)
        self._current_answer = ""
        self._hint_visible = False
        self._wrong_attempts = 0
        self._success_timer = 0
        self._pending_reward = 0
        self._problem_sequence += 1
        self._reward_variant_index = self._select_reward_variant(self._current_problem)

    def _select_reward_variant(self, problem: MathProblem) -> int:
        """Choose a stable reward coin variant for the current problem."""
        variant_count = len(REWARD_COIN_VARIANTS[REWARD_WITHOUT_HELP])
        operation_offset = list(type(problem.operation)).index(problem.operation)
        return (
            problem.a * 31
            + problem.b * 17
            + operation_offset * 7
            + self._problem_sequence
        ) % variant_count

    def _answer_slot_count(self) -> int:
        """Return how many answer slots the current problem should show."""
        if not self._current_problem:
            return 1
        return 1 if self._current_problem.answer < 10 else 2

    def _current_reward(self) -> int:
        """Return the reward for the current attempt state."""
        if self._hint_visible:
            return REWARD_WITH_HELP
        return REWARD_WITHOUT_HELP

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
            return

        self._handle_wrong_answer()

    def _handle_correct_answer(self) -> None:
        """Start reward feedback for a correct answer."""
        reward = self._current_reward()
        self._start_success_animation(reward)

    def _start_success_animation(self, reward: int) -> None:
        """Keep the solved problem visible briefly and trigger visual feedback."""
        self._success_timer = SUCCESS_ANIMATION_FRAMES
        self._success_reward = reward
        self._pending_reward = reward

    def _finish_success_animation(self) -> None:
        """Apply the pending reward after the transfer animation arrives."""
        if self._pending_reward:
            self._session_taler += self._pending_reward
            state.add_earning("math", self._pending_reward, "Aufgabe gelöst")
            self._pending_reward = 0

        if self._session_taler >= self._session_max:
            self._session_complete = True
            self._complete_timer = 120
            return

        self._next_problem()

    def _handle_wrong_answer(self) -> None:
        """Show help on first mistake, then advance on the second."""
        self._wrong_attempts += 1
        self._hint_visible = True
        self._current_answer = ""

        if self._wrong_attempts >= MAX_WRONG_ATTEMPTS:
            self._next_problem()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events."""
        self._init_ui()

        if self._session_complete:
            return self._consume_next_scene()

        if self._success_timer > 0:
            return self._consume_next_scene()

        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)

        return self._consume_next_scene()

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle USB numpad and keyboard input."""
        if event.unicode.isdigit():
            if len(self._current_answer) < self._answer_slot_count():
                self._update_answer(self._current_answer + event.unicode)
            return

        if event.key == pygame.K_BACKSPACE and self._current_answer:
            self._update_answer(self._current_answer[:-1])
            return

        if event.key == pygame.K_ESCAPE:
            self._update_answer("")
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._submit_answer(self._current_answer)

    def update(self) -> None:
        """Update scene state."""
        if self._session_complete:
            self._complete_timer -= 1
            if self._complete_timer <= 0:
                self._go_to("menu")
            return

        if self._success_timer > 0:
            self._success_timer -= 1
            if self._success_timer <= 0:
                self._finish_success_animation()
            return

        state.check_time_bonus()
        self._update_message_timer()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the math game screen (no background fill — shell handles it)."""
        self._init_ui()

        layout = self._render_equation(screen)

        if self._hint_visible and layout:
            self._render_operand_hints(screen, layout)

        self._render_reward_badge(screen)

        if self._success_timer > 0 and layout:
            self._render_success_animation(screen, layout)

        if self._session_complete:
            self._render_complete_overlay(screen)

    def _render_equation(self, screen: pygame.Surface) -> EquationLayout | None:
        """Render the central equation and return operand positions."""
        if not self._current_problem:
            return None

        number_font = bold_custom(EQUATION_FONT_SIZE)
        symbol_font = bold_custom(SYMBOL_FONT_SIZE)
        answer_font = bold_custom(EQUATION_FONT_SIZE)
        first_surface = number_font.render(
            str(self._current_problem.a), True, FIRST_OPERAND_COLOR
        )
        operator_surface = symbol_font.render(
            self._current_problem.operation.value, True, BLACK
        )
        second_surface = number_font.render(
            str(self._current_problem.b), True, SECOND_OPERAND_COLOR
        )
        equals_surface = symbol_font.render("=", True, BLACK)
        answer_width = self._answer_width()
        total_width = (
            first_surface.get_width()
            + operator_surface.get_width()
            + second_surface.get_width()
            + equals_surface.get_width()
            + answer_width
            + EQUATION_GAP * 4
        )

        x = (SCREEN_WIDTH - total_width) // 2
        first_rect = first_surface.get_rect(midleft=(x, EQUATION_CENTER_Y))
        screen.blit(first_surface, first_rect)
        x = first_rect.right + EQUATION_GAP

        operator_rect = operator_surface.get_rect(midleft=(x, EQUATION_CENTER_Y))
        screen.blit(operator_surface, operator_rect)
        x = operator_rect.right + EQUATION_GAP

        second_rect = second_surface.get_rect(midleft=(x, EQUATION_CENTER_Y))
        screen.blit(second_surface, second_rect)
        x = second_rect.right + EQUATION_GAP

        equals_rect = equals_surface.get_rect(midleft=(x, EQUATION_CENTER_Y))
        screen.blit(equals_surface, equals_rect)
        x = equals_rect.right + EQUATION_GAP

        answer_rect = self._render_answer_slots(screen, x, answer_font)
        return EquationLayout(first_rect, second_rect, answer_rect)

    def _answer_width(self) -> int:
        """Return the visual width of the answer slot area."""
        slot_count = self._answer_slot_count()
        return slot_count * ANSWER_SLOT_WIDTH + (slot_count - 1) * ANSWER_SLOT_GAP

    def _render_answer_slots(
        self, screen: pygame.Surface, start_x: int, answer_font: pygame.font.Font
    ) -> pygame.Rect:
        """Render one or two result slots with underscores."""
        slot_count = self._answer_slot_count()
        top = EQUATION_CENTER_Y - 72
        underline_y = EQUATION_CENTER_Y + 68
        answer_rect = pygame.Rect(start_x, top, self._answer_width(), 150)
        for index in range(slot_count):
            slot_x = start_x + index * (ANSWER_SLOT_WIDTH + ANSWER_SLOT_GAP)
            slot_center_x = slot_x + ANSWER_SLOT_WIDTH // 2

            visible_symbol = (
                self._current_answer[index]
                if index < len(self._current_answer)
                else "?"
            )
            symbol_color = (
                TEXT_PRIMARY if index < len(self._current_answer) else ANSWER_COLOR
            )
            symbol_surface = answer_font.render(visible_symbol, True, symbol_color)
            symbol_rect = symbol_surface.get_rect(
                center=(slot_center_x, EQUATION_CENTER_Y - 10)
            )
            screen.blit(symbol_surface, symbol_rect)

            pygame.draw.line(
                screen,
                ANSWER_COLOR,
                (slot_center_x - ANSWER_UNDERLINE_WIDTH // 2, underline_y),
                (slot_center_x + ANSWER_UNDERLINE_WIDTH // 2, underline_y),
                ANSWER_UNDERLINE_HEIGHT,
            )
        return answer_rect

    def _render_operand_hints(
        self, screen: pygame.Surface, layout: EquationLayout
    ) -> None:
        """Render dot hints below both operands after the first wrong answer."""
        if not self._current_problem:
            return

        self._draw_dot_frames(
            screen,
            layout.first_operand_rect.centerx,
            HELP_DOTS_TOP,
            self._current_problem.a,
            FIRST_OPERAND_COLOR,
            DOT_EMPTY_COLOR,
        )
        self._draw_dot_frames(
            screen,
            layout.second_operand_rect.centerx,
            HELP_DOTS_TOP,
            self._current_problem.b,
            SECOND_OPERAND_COLOR,
            DOT_EMPTY_SECOND_COLOR,
        )

    def _draw_dot_frames(
        self,
        screen: pygame.Surface,
        center_x: int,
        top_y: int,
        count: int,
        filled_color: tuple[int, int, int],
        empty_color: tuple[int, int, int],
    ) -> None:
        """Draw one or more ten-frames for a number."""
        dots_per_frame = 10
        frame_count = max(1, (count + dots_per_frame - 1) // dots_per_frame)
        dot_radius = 11
        dot_gap = 8
        frame_gap = 12
        frame_width = 5 * dot_radius * 2 + 4 * dot_gap
        total_width = frame_count * frame_width + (frame_count - 1) * frame_gap
        start_x = center_x - total_width // 2
        remaining = count
        for frame_index in range(frame_count):
            frame_x = start_x + frame_index * (frame_width + frame_gap)
            filled_count = min(remaining, dots_per_frame)
            self._draw_ten_frame(
                screen, frame_x, top_y, filled_count, filled_color, empty_color
            )
            remaining -= filled_count

    def _draw_ten_frame(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        filled_count: int,
        filled_color: tuple[int, int, int],
        empty_color: tuple[int, int, int],
    ) -> None:
        """Draw a 2x5 dot frame."""
        dot_radius = 11
        dot_gap = 8
        for index in range(10):
            col = index % 5
            row = index // 5
            center = (
                x + dot_radius + col * (dot_radius * 2 + dot_gap),
                y + dot_radius + row * (dot_radius * 2 + dot_gap),
            )
            color = filled_color if index < filled_count else empty_color
            self._draw_dot(screen, center, dot_radius, color)

    def _draw_dot(
        self,
        screen: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw one soft circular point."""
        shadow_center = (center[0], center[1] + 2)
        pygame.draw.circle(screen, DOT_SHADOW_COLOR, shadow_center, radius)
        pygame.draw.circle(screen, color, center, radius)

    def _render_reward_badge(self, screen: pygame.Surface) -> None:
        """Render the current reward as a coin asset with a drawn fallback."""
        reward = self._current_reward()
        coin = self._load_reward_coin(reward)
        if coin:
            coin = self._scale_reward_coin_for_animation(coin)
            coin_rect = coin.get_rect(center=REWARD_BADGE_CENTER)
            screen.blit(coin, coin_rect)
            return

        self._render_fallback_reward_badge(screen, reward)

    def _scale_reward_coin_for_animation(self, coin: pygame.Surface) -> pygame.Surface:
        """Pulse the reward coin while the transfer animation starts."""
        if self._success_timer <= 0:
            return coin

        elapsed = SUCCESS_ANIMATION_FRAMES - self._success_timer
        pulse = max(0.0, 1.0 - elapsed / 12)
        scale = 1.0 + pulse * 0.18
        target_size = int(coin.get_width() * scale)
        return pygame.transform.smoothscale(coin, (target_size, target_size))

    def _load_reward_coin(self, reward: int) -> pygame.Surface | None:
        """Load the stable coin variant for the current problem."""
        variants = REWARD_COIN_VARIANTS.get(reward)
        if not variants:
            return None

        asset_name = variants[self._reward_variant_index % len(variants)]
        try:
            return asset_loader.get(asset_name, REWARD_BADGE_SIZE)
        except FileNotFoundError:
            return None

    def _render_fallback_reward_badge(
        self, screen: pygame.Surface, reward: int
    ) -> None:
        """Render a simple reward badge if the PNG assets are unavailable."""
        center = REWARD_BADGE_CENTER
        radius = 42
        pygame.draw.circle(
            screen, BADGE_SHADOW_COLOR, (center[0], center[1] + 4), radius
        )
        pygame.draw.circle(screen, BADGE_COLOR, center, radius)
        pygame.draw.circle(screen, (49, 139, 121), center, radius, width=3)
        self._render_badge_sprinkles(screen, center)

        reward_font = bold_custom(42)
        reward_surface = reward_font.render(f"+{reward}", True, DANGER)
        reward_rect = reward_surface.get_rect(center=center)
        screen.blit(reward_surface, reward_rect)

    def _render_badge_sprinkles(
        self, screen: pygame.Surface, center: tuple[int, int]
    ) -> None:
        """Draw fixed confetti dots around the reward value."""
        offsets = [
            (-25, -13),
            (-14, -25),
            (3, -31),
            (22, -18),
            (29, 3),
            (18, 24),
            (0, 31),
            (-20, 23),
            (-31, 4),
            (13, -6),
            (-8, 9),
            (25, 14),
            (-26, -27),
            (8, 22),
        ]
        for index, offset in enumerate(offsets):
            color = BADGE_DOT_COLORS[index % len(BADGE_DOT_COLORS)]
            pygame.draw.circle(
                screen,
                color,
                (center[0] + offset[0], center[1] + offset[1]),
                4,
            )

    def _render_success_animation(
        self, screen: pygame.Surface, layout: EquationLayout
    ) -> None:
        """Render sequential success feedback: confetti, then reward transfer."""
        elapsed = SUCCESS_ANIMATION_FRAMES - self._success_timer
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        answer_center = (layout.answer_rect.centerx, EQUATION_CENTER_Y - 12)

        if elapsed < SUCCESS_CONFETTI_FRAMES:
            for index, spec in enumerate(SUCCESS_PARTICLE_SPECS):
                self._draw_success_particle(
                    overlay, answer_center, elapsed, index, spec
                )
        else:
            self._draw_reward_transfer(overlay, elapsed - SUCCESS_CONFETTI_FRAMES)

        screen.blit(overlay, (0, 0))

    def _draw_success_particle(
        self,
        overlay: pygame.Surface,
        origin: tuple[int, int],
        elapsed: int,
        index: int,
        spec: tuple[int, int, float, float, str, int],
    ) -> None:
        """Draw one deterministic success particle."""
        start_x, start_y, velocity_x, velocity_y, particle_type, delay = spec
        age = elapsed - delay
        if age < 0 or age > SUCCESS_PARTICLE_LIFETIME:
            return

        progress = age / SUCCESS_PARTICLE_LIFETIME
        alpha = int(255 * (1.0 - progress))
        x = int(origin[0] + start_x + velocity_x * age)
        y = int(origin[1] + start_y + velocity_y * age + age * age * 0.12)
        color = SUCCESS_PARTICLE_COLORS[index % len(SUCCESS_PARTICLE_COLORS)]
        draw_color = (*color, alpha)

        if particle_type == "star":
            points = self._star_points((x, y), 12, 5, progress * math.pi)
            pygame.draw.polygon(overlay, draw_color, points)
            return

        if particle_type == "confetti":
            end = (int(x + 12 * math.cos(progress * math.pi)), int(y + 10))
            pygame.draw.line(overlay, draw_color, (x, y), end, width=5)
            return

    def _draw_reward_transfer(self, overlay: pygame.Surface, elapsed: int) -> None:
        """Animate a small reward coin into the account area."""
        if self._pending_reward <= 0:
            return

        coin = self._load_reward_coin(self._success_reward)
        if not coin:
            return

        progress = min(1.0, elapsed / REWARD_TRANSFER_FRAMES)
        eased = 1.0 - (1.0 - progress) ** 3
        start_x, start_y = REWARD_BADGE_CENTER
        target_x, target_y = REWARD_TRANSFER_TARGET
        x = start_x + (target_x - start_x) * eased
        y = start_y + (target_y - start_y) * eased - math.sin(progress * math.pi) * 70
        scale = 0.7 - eased * 0.34
        size = max(28, int(coin.get_width() * scale))
        moving_coin = pygame.transform.smoothscale(coin, (size, size)).copy()

        if progress > 0.78:
            moving_coin.set_alpha(int(255 * (1.0 - (progress - 0.78) / 0.22)))

        coin_rect = moving_coin.get_rect(center=(int(x), int(y)))
        overlay.blit(moving_coin, coin_rect)

        if 0.15 < progress < 0.9:
            self._draw_transfer_trail(overlay, (int(x), int(y)), progress)

    def _draw_transfer_trail(
        self, overlay: pygame.Surface, center: tuple[int, int], progress: float
    ) -> None:
        """Draw tiny confetti flecks behind the moving coin."""
        offsets = ((-24, 9), (-14, -12), (-4, 16))
        for index, offset in enumerate(offsets):
            color = SUCCESS_PARTICLE_COLORS[(index + 2) % len(SUCCESS_PARTICLE_COLORS)]
            alpha = int(190 * (1.0 - progress))
            point = (center[0] + offset[0], center[1] + offset[1])
            end = (point[0] - 8, point[1] + 5)
            pygame.draw.line(overlay, (*color, alpha), point, end, width=4)

    def _star_points(
        self,
        center: tuple[int, int],
        outer_radius: int,
        inner_radius: int,
        rotation: float,
    ) -> list[tuple[int, int]]:
        """Return points for a small five-point success star."""
        points = []
        for index in range(10):
            radius = outer_radius if index % 2 == 0 else inner_radius
            angle = rotation - math.pi / 2 + index * math.pi / 5
            points.append(
                (
                    int(center[0] + math.cos(angle) * radius),
                    int(center[1] + math.sin(angle) * radius),
                )
            )
        return points

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
        pygame.draw.rect(screen, (255, 255, 255), card_rect, border_radius=20)
        pygame.draw.rect(screen, SUCCESS, card_rect, width=4, border_radius=20)

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
