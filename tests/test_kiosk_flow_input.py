"""Kiosk navigation and keyboard input regression tests."""

import importlib
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.components.numpad import Numpad
from src.utils.input import InputManager, InputType
from tests.db_isolation import isolated_database_module


SCANNED_PRODUCT_BARCODE = "1000000000016"
PICKER_PRODUCT_BARCODE = "1000000000023"

KEYPAD_DIGITS = {
    "0": pygame.K_KP0,
    "1": pygame.K_KP1,
    "2": pygame.K_KP2,
    "3": pygame.K_KP3,
    "4": pygame.K_KP4,
    "5": pygame.K_KP5,
    "6": pygame.K_KP6,
    "7": pygame.K_KP7,
    "8": pygame.K_KP8,
    "9": pygame.K_KP9,
}


class KioskFlowInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def test_menu_scan_picker_flow_preserves_scan_cart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                scanned_product = database.Product(
                    barcode=SCANNED_PRODUCT_BARCODE,
                    name="milk",
                    name_de="Milch",
                    price=2.0,
                    category="getraenke",
                    has_barcode=True,
                )
                picker_product = database.Product(
                    barcode=PICKER_PRODUCT_BARCODE,
                    name="apple",
                    name_de="Apfel",
                    price=1.0,
                    category="obst",
                    has_barcode=False,
                )
                database.add_product(scanned_product)
                database.add_product(picker_product)

                manager_module = importlib.import_module("src.scenes.manager")
                menu_module = importlib.import_module("src.scenes.menu")
                picker_module = importlib.import_module("src.scenes.picker")
                scan_module = importlib.import_module("src.scenes.scan")
                state = importlib.import_module("src.utils.state")

                menu_scene = menu_module.MenuScene()
                scan_scene = scan_module.ScanScene()
                picker_scene = picker_module.PickerScene()
                manager = manager_module.SceneManager(
                    {
                        "menu": menu_scene,
                        "scan": scan_scene,
                        "picker": picker_scene,
                    },
                    initial="menu",
                )

                menu_scene._init_ui()
                self._click(manager, menu_scene._buttons[1].rect.center)

                self.assertEqual(manager.current_name, "scan")

                scan_scene._cart.add(scanned_product)
                scan_scene._init_ui()
                picker_button = scan_scene._picker_button
                if picker_button is None:
                    raise AssertionError("Expected picker button")
                self._click(manager, picker_button.rect.center)

                self.assertEqual(manager.current_name, "picker")

                picker_scene._init_ui()
                self.assertEqual(len(picker_scene._tiles), 1)
                self._click(manager, picker_scene._tiles[0].rect.center)
                manager.update()

                cart_quantities = {
                    item.product.barcode: item.quantity
                    for item in scan_scene._cart.items
                }

                self.assertEqual(manager.current_name, "scan")
                self.assertEqual(
                    cart_quantities,
                    {
                        SCANNED_PRODUCT_BARCODE: 1,
                        PICKER_PRODUCT_BARCODE: 1,
                    },
                )
                self.assertIsNone(state.get_and_clear_selected_product())

    def test_input_manager_accepts_unicode_empty_keypad_digits(self) -> None:
        for digit, key in KEYPAD_DIGITS.items():
            with self.subTest(digit=digit):
                input_manager = InputManager()

                input_events = input_manager.process_event(self._key_event(key))

                self.assertEqual(len(input_events), 1)
                self.assertEqual(input_events[0].type, InputType.NUMPAD)
                self.assertEqual(input_events[0].value, digit)
                self.assertEqual(input_manager.buffer, digit)

    def test_input_manager_keeps_barcode_scanner_flow(self) -> None:
        input_manager = InputManager()
        input_events = []

        for digit in SCANNED_PRODUCT_BARCODE:
            input_events.extend(input_manager.process_event(self._digit_event(digit)))
        input_events.extend(
            input_manager.process_event(self._key_event(pygame.K_RETURN))
        )

        self.assertEqual(input_events[-2].type, InputType.NUMPAD_ENTER)
        self.assertEqual(input_events[-1].type, InputType.BARCODE)
        self.assertEqual(input_events[-1].value, SCANNED_PRODUCT_BARCODE)
        self.assertEqual(input_manager.buffer, "")

    def test_numpad_accepts_unicode_empty_keypad_digit_and_enter(self) -> None:
        changes: list[str] = []
        submits: list[str] = []
        numpad = Numpad(
            0,
            0,
            on_change=changes.append,
            on_enter=submits.append,
            max_digits=2,
        )

        self.assertTrue(numpad.handle_event(self._key_event(pygame.K_KP5)))
        self.assertEqual(numpad.value, "5")
        self.assertEqual(changes, ["5"])

        self.assertTrue(numpad.handle_event(self._key_event(pygame.K_KP_ENTER)))
        self.assertEqual(submits, ["5"])

    def test_math_ignores_barcode_length_numeric_burst_with_enter(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            6,
            4,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        self._send_digit_burst(scene, "1000000000016")
        scene.handle_event(self._key_event(pygame.K_RETURN))

        self.assertEqual(scene._wrong_attempts, 0)
        self.assertFalse(scene._hint_visible)
        self.assertEqual(scene._current_answer, "")
        self.assertEqual(scene._success_timer, 0)
        self.assertEqual(scene._keyboard_digit_buffer, "")
        self.assertFalse(scene._barcode_digit_burst_active)

    def test_math_accepts_keypad_answer_after_unterminated_barcode_burst(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            7,
            5,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        self._send_digit_burst(scene, "1000000000016")
        scene.handle_event(self._digit_event("1", keypad=True, timestamp=1000))
        scene.handle_event(self._digit_event("2", keypad=True, timestamp=1100))
        scene.handle_event(self._key_event(pygame.K_KP_ENTER))

        self.assertEqual(scene._current_answer, "12")
        self.assertEqual(scene._wrong_attempts, 0)
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def test_math_backspace_clears_unterminated_barcode_burst(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            7,
            5,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        self._send_digit_burst(scene, "1000000000016")
        scene.handle_event(self._key_event(pygame.K_BACKSPACE))
        scene.handle_event(self._digit_event("1", keypad=True))
        scene.handle_event(self._digit_event("2", keypad=True))
        scene.handle_event(self._key_event(pygame.K_KP_ENTER))

        self.assertEqual(scene._keyboard_digit_buffer, "")
        self.assertFalse(scene._barcode_digit_burst_active)
        self.assertEqual(scene._current_answer, "12")
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def test_math_escape_clears_unterminated_barcode_burst(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            4,
            5,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        self._send_digit_burst(scene, "1000000000016")
        scene.handle_event(self._key_event(pygame.K_ESCAPE))
        scene.handle_event(self._digit_event("9"))
        scene.handle_event(self._key_event(pygame.K_RETURN))

        self.assertEqual(scene._keyboard_digit_buffer, "")
        self.assertFalse(scene._barcode_digit_burst_active)
        self.assertEqual(scene._current_answer, "9")
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def test_math_still_accepts_short_keypad_answer(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            7,
            5,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        scene.handle_event(self._digit_event("1", keypad=True))
        scene.handle_event(self._digit_event("2", keypad=True))
        scene.handle_event(self._key_event(pygame.K_KP_ENTER))

        self.assertEqual(scene._current_answer, "12")
        self.assertEqual(scene._wrong_attempts, 0)
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def test_math_accepts_unicode_empty_keypad_answer(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            7,
            5,
            math_generator.Operation.ADD,
        )
        scene._initialized = True

        scene.handle_event(self._key_event(pygame.K_KP1, timestamp=1000))
        scene.handle_event(self._key_event(pygame.K_KP2, timestamp=1100))
        scene.handle_event(self._key_event(pygame.K_KP_ENTER))

        self.assertEqual(scene._current_answer, "12")
        self.assertEqual(scene._wrong_attempts, 0)
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def test_math_accepts_three_digit_answer_when_problem_needs_it(self) -> None:
        math_module = importlib.import_module("src.scenes.math_game")
        math_generator = importlib.import_module("src.utils.math_generator")
        scene = math_module.MathGameScene()
        scene._current_problem = math_generator.MathProblem(
            10,
            10,
            math_generator.Operation.MULTIPLY,
        )
        scene._initialized = True

        scene.handle_event(self._digit_event("1", keypad=True))
        scene.handle_event(self._digit_event("0", keypad=True))
        scene.handle_event(self._digit_event("0", keypad=True))
        scene.handle_event(self._key_event(pygame.K_KP_ENTER))

        self.assertEqual(scene._answer_slot_count(), 3)
        self.assertEqual(scene._current_answer, "100")
        self.assertEqual(
            scene._success_timer,
            math_module.SUCCESS_ANIMATION_FRAMES,
        )

    def _click(self, manager, pos: tuple[int, int]) -> None:
        manager.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": pos, "button": 1},
            )
        )
        manager.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {"pos": pos, "button": 1},
            )
        )

    def _digit_event(
        self,
        digit: str,
        *,
        keypad: bool = False,
        timestamp: int | None = None,
    ) -> pygame.event.Event:
        key = KEYPAD_DIGITS[digit] if keypad else ord(digit)
        return self._key_event(key, digit, timestamp=timestamp)

    def _key_event(
        self,
        key: int,
        text: str = "",
        *,
        timestamp: int | None = None,
    ) -> pygame.event.Event:
        attributes = {"key": key, "unicode": text}
        if timestamp is not None:
            attributes["timestamp"] = timestamp

        return pygame.event.Event(
            pygame.KEYDOWN,
            attributes,
        )

    def _send_digit_burst(
        self,
        scene,
        digits: str,
        *,
        start_ms: int = 0,
        step_ms: int = 5,
    ) -> None:
        for index, digit in enumerate(digits):
            scene.handle_event(
                self._digit_event(digit, timestamp=start_ms + index * step_ms)
            )


if __name__ == "__main__":
    unittest.main()
