"""Test scene for verifying the pygame setup."""

import pygame

from src.constants import BLACK, PINK, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from src.scenes.base import Scene


class TestScene(Scene):
    """Simple test scene showing title and instructions."""

    def __init__(self) -> None:
        """Initialize fonts for rendering."""
        self.title_font = pygame.font.Font(None, 72)
        self.instruction_font = pygame.font.Font(None, 36)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle key presses."""
        if event.type == pygame.KEYDOWN:
            print(f"🎹 Taste gedrückt: {pygame.key.name(event.key)}")
            if event.key == pygame.K_RETURN:
                print("✨ ENTER gedrückt - bereit zum Starten!")
        return None

    def update(self) -> None:
        """No state updates needed for test scene."""
        pass

    def render(self, screen: pygame.Surface) -> None:
        """Render title and instructions."""
        screen.fill(PINK)

        # Title
        title = self.title_font.render("Carolin's Kasse", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(title, title_rect)

        # Instruction
        instruction = self.instruction_font.render(
            "Drücke ENTER zum Starten", True, BLACK
        )
        instruction_rect = instruction.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)
        )
        screen.blit(instruction, instruction_rect)
