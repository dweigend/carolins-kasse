"""Direct regression tests for the touch-friendly numpad component."""

import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.components.numpad import Numpad


class NumpadComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def test_accepts_top_row_digit(self) -> None:
        changes: list[str] = []
        numpad = Numpad(0, 0, on_change=changes.append)

        handled = numpad.handle_event(self._key_event(pygame.K_7, "7"))

        self.assertTrue(handled)
        self.assertEqual(numpad.value, "7")
        self.assertEqual(changes, ["7"])

    def test_accepts_keypad_digit_with_empty_unicode(self) -> None:
        changes: list[str] = []
        numpad = Numpad(0, 0, on_change=changes.append)

        handled = numpad.handle_event(self._key_event(pygame.K_KP5))

        self.assertTrue(handled)
        self.assertEqual(numpad.value, "5")
        self.assertEqual(changes, ["5"])

    def test_backspace_removes_last_digit(self) -> None:
        changes: list[str] = []
        numpad = Numpad(0, 0, on_change=changes.append)
        numpad.handle_event(self._key_event(pygame.K_4, "4"))
        numpad.handle_event(self._key_event(pygame.K_2, "2"))

        handled = numpad.handle_event(self._key_event(pygame.K_BACKSPACE))

        self.assertTrue(handled)
        self.assertEqual(numpad.value, "4")
        self.assertEqual(changes, ["4", "42", "4"])

    def test_enter_submits_current_value(self) -> None:
        submits: list[str] = []
        numpad = Numpad(0, 0, on_enter=submits.append)
        numpad.handle_event(self._key_event(pygame.K_1, "1"))
        numpad.handle_event(self._key_event(pygame.K_2, "2"))

        handled = numpad.handle_event(self._key_event(pygame.K_RETURN))

        self.assertTrue(handled)
        self.assertEqual(numpad.value, "12")
        self.assertEqual(submits, ["12"])

    def test_escape_clears_value(self) -> None:
        changes: list[str] = []
        numpad = Numpad(0, 0, on_change=changes.append)
        numpad.handle_event(self._key_event(pygame.K_9, "9"))

        handled = numpad.handle_event(self._key_event(pygame.K_ESCAPE))

        self.assertTrue(handled)
        self.assertEqual(numpad.value, "")
        self.assertEqual(changes, ["9", ""])

    def test_touch_down_up_on_button_updates_value_with_callback(self) -> None:
        changes: list[str] = []
        numpad = Numpad(10, 20, on_change=changes.append)
        button_center = self._button_center(numpad, "8")

        down_handled = numpad.handle_event(
            self._mouse_event(pygame.MOUSEBUTTONDOWN, button_center)
        )
        up_handled = numpad.handle_event(
            self._mouse_event(pygame.MOUSEBUTTONUP, button_center)
        )

        self.assertFalse(down_handled)
        self.assertTrue(up_handled)
        self.assertEqual(numpad.value, "8")
        self.assertEqual(changes, ["8"])

    def _key_event(self, key: int, text: str = "") -> pygame.event.Event:
        return pygame.event.Event(
            pygame.KEYDOWN,
            {"key": key, "unicode": text},
        )

    def _mouse_event(
        self,
        event_type: int,
        pos: tuple[int, int],
    ) -> pygame.event.Event:
        return pygame.event.Event(
            event_type,
            {"pos": pos, "button": 1},
        )

    def _button_center(self, numpad: Numpad, label: str) -> tuple[int, int]:
        for rect, button_label, _ in numpad._buttons:
            if button_label == label:
                return rect.center

        self.fail(f"Button {label!r} was not found")


if __name__ == "__main__":
    unittest.main()
