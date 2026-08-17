"""Math difficulty and problem generation regression tests."""

import unittest
from unittest.mock import patch

from src.utils.math_generator import (
    DIFFICULTY_SETTINGS,
    MathProblem,
    Operation,
    generate_problem,
)


class MathGeneratorTests(unittest.TestCase):
    def test_level_one_generates_addition_up_to_ten(self) -> None:
        with patch(
            "src.utils.math_generator.random.choice", return_value=Operation.ADD
        ):
            for _ in range(50):
                problem = generate_problem(1)

                self.assertEqual(problem.operation, Operation.ADD)
                self.assertGreaterEqual(problem.a, 1)
                self.assertGreaterEqual(problem.b, 1)
                self.assertLessEqual(problem.answer, 10)

    def test_level_two_supports_addition_and_subtraction_up_to_ten(self) -> None:
        self._assert_operations_for_level(2, max_number=10)

    def test_level_three_supports_addition_and_subtraction_up_to_twenty(self) -> None:
        self._assert_operations_for_level(3, max_number=20)

    def test_difficulty_is_clamped_to_available_levels(self) -> None:
        with (
            patch("src.utils.math_generator.random.choice") as choose_operation,
            patch("src.utils.math_generator.random.randint") as choose_maximum,
        ):
            choose_operation.side_effect = lambda operations: operations[0]
            choose_maximum.side_effect = lambda _minimum, maximum: maximum

            easy_problem = generate_problem(0)
            hard_problem = generate_problem(99)

        self.assertEqual(easy_problem.operation, Operation.ADD)
        self.assertEqual(easy_problem.answer, 10)
        self.assertEqual(hard_problem.operation, Operation.ADD)
        self.assertEqual(hard_problem.answer, 20)

    def test_math_problem_formats_and_checks_supported_operations(self) -> None:
        addition = MathProblem(4, 5, Operation.ADD)
        subtraction = MathProblem(9, 3, Operation.SUBTRACT)

        self.assertEqual(addition.answer, 9)
        self.assertEqual(addition.display, "4 + 5 = ?")
        self.assertTrue(addition.check(9))
        self.assertEqual(subtraction.answer, 6)
        self.assertEqual(subtraction.display, "9 - 3 = ?")
        self.assertFalse(subtraction.check(5))

    def _assert_operations_for_level(self, difficulty: int, max_number: int) -> None:
        for operation in (Operation.ADD, Operation.SUBTRACT):
            with self.subTest(difficulty=difficulty, operation=operation):
                self.assertIn(
                    operation,
                    DIFFICULTY_SETTINGS[difficulty].operations,
                )
                with patch(
                    "src.utils.math_generator.random.choice",
                    return_value=operation,
                ):
                    for _ in range(50):
                        problem = generate_problem(difficulty)

                        self.assertEqual(problem.operation, operation)
                        self.assertGreaterEqual(problem.a, 1)
                        self.assertGreaterEqual(problem.b, 1)
                        self.assertLessEqual(max(problem.a, problem.b), max_number)
                        if operation == Operation.ADD:
                            self.assertLessEqual(problem.answer, max_number)
                        else:
                            self.assertGreater(problem.answer, 0)


if __name__ == "__main__":
    unittest.main()
