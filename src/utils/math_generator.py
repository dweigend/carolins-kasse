"""Math problem generator for the math game."""

import random
from dataclasses import dataclass
from enum import Enum


class Operation(Enum):
    """Math operation types."""

    ADD = "+"
    SUBTRACT = "-"


@dataclass(frozen=True)
class DifficultySettings:
    """Allowed operations and number range for one difficulty level."""

    operations: tuple[Operation, ...]
    max_number: int


DIFFICULTY_SETTINGS = {
    1: DifficultySettings((Operation.ADD,), max_number=10),
    2: DifficultySettings(
        (Operation.ADD, Operation.SUBTRACT),
        max_number=10,
    ),
    3: DifficultySettings(
        (Operation.ADD, Operation.SUBTRACT),
        max_number=20,
    ),
}
MIN_DIFFICULTY = min(DIFFICULTY_SETTINGS)
MAX_DIFFICULTY = max(DIFFICULTY_SETTINGS)


@dataclass
class MathProblem:
    """A math problem with operands, operation, and answer."""

    a: int
    b: int
    operation: Operation

    @property
    def answer(self) -> int:
        """Calculate the correct answer."""
        if self.operation == Operation.ADD:
            return self.a + self.b
        return self.a - self.b

    @property
    def display(self) -> str:
        """Format the problem for display."""
        return f"{self.a} {self.operation.value} {self.b} = ?"

    def check(self, answer: int) -> bool:
        """Check if the given answer is correct."""
        return answer == self.answer


def normalize_difficulty(difficulty: int) -> int:
    """Clamp a difficulty value to the configured math levels."""
    return max(MIN_DIFFICULTY, min(difficulty, MAX_DIFFICULTY))


def generate_problem(difficulty: int) -> MathProblem:
    """Generate a math problem based on difficulty level.

    Args:
        difficulty: 1-3 difficulty level
            1: Addition up to 10
            2: Addition/Subtraction up to 10
            3: Addition/Subtraction up to 20

    Returns:
        A MathProblem instance
    """
    normalized_difficulty = normalize_difficulty(difficulty)
    settings = DIFFICULTY_SETTINGS[normalized_difficulty]
    operation = random.choice(settings.operations)

    if operation == Operation.ADD:
        first_operand = random.randint(1, settings.max_number - 1)
        second_operand = random.randint(1, settings.max_number - first_operand)
        return MathProblem(first_operand, second_operand, operation)

    first_operand = random.randint(2, settings.max_number)
    second_operand = random.randint(1, first_operand - 1)
    return MathProblem(first_operand, second_operand, operation)
