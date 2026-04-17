"""Math problem generator for the math game."""

import random
from dataclasses import dataclass
from enum import Enum


class Operation(Enum):
    """Math operation types."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "×"


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
        elif self.operation == Operation.SUBTRACT:
            return self.a - self.b
        else:  # MULTIPLY
            return self.a * self.b

    @property
    def display(self) -> str:
        """Format the problem for display."""
        return f"{self.a} {self.operation.value} {self.b} = ?"

    def check(self, answer: int) -> bool:
        """Check if the given answer is correct."""
        return answer == self.answer


def generate_problem(difficulty: int) -> MathProblem:
    """Generate a math problem based on difficulty level.

    Args:
        difficulty: 1-3 difficulty level
            1: Addition up to 10
            2: Addition/Subtraction up to 20
            3: Multiplication with max answer 99

    Returns:
        A MathProblem instance
    """
    if difficulty == 1:
        # Addition up to 10
        a = random.randint(1, 9)
        b = random.randint(1, 10 - a)
        return MathProblem(a, b, Operation.ADD)

    elif difficulty == 2:
        # Addition or Subtraction up to 20
        operation = random.choice([Operation.ADD, Operation.SUBTRACT])

        if operation == Operation.ADD:
            a = random.randint(1, 15)
            b = random.randint(1, 20 - a)
        else:
            # Subtraction - ensure positive result
            a = random.randint(5, 20)
            b = random.randint(1, a - 1)

        return MathProblem(a, b, operation)

    else:  # difficulty >= 3
        # Multiplication with at most two-digit results
        while True:
            a = random.randint(2, 10)
            b = random.randint(2, 10)
            problem = MathProblem(a, b, Operation.MULTIPLY)
            if problem.answer <= 99:
                return problem
