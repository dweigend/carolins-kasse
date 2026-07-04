"""Input management for barcode scanner, numpad, and touch.

Barcode scanners emit characters rapidly followed by Enter.
This module buffers those characters and emits a complete barcode on Enter.
"""

from dataclasses import dataclass
from enum import Enum, auto

import pygame

KEY_DIGITS_BY_KEY: dict[int, str] = {
    pygame.K_0: "0",
    pygame.K_1: "1",
    pygame.K_2: "2",
    pygame.K_3: "3",
    pygame.K_4: "4",
    pygame.K_5: "5",
    pygame.K_6: "6",
    pygame.K_7: "7",
    pygame.K_8: "8",
    pygame.K_9: "9",
}

for _digit in range(10):
    _keypad_key = getattr(pygame, f"K_KP{_digit}", None)
    if _keypad_key is not None:
        KEY_DIGITS_BY_KEY[_keypad_key] = str(_digit)

ENTER_KEYS = {pygame.K_RETURN}
_keypad_enter_key = getattr(pygame, "K_KP_ENTER", None)
if _keypad_enter_key is not None:
    ENTER_KEYS.add(_keypad_enter_key)


def digit_from_key_event(event: pygame.event.Event) -> str:
    """Return the numeric digit from a KEYDOWN event, including keypad keys."""
    unicode_text = getattr(event, "unicode", "")
    if isinstance(unicode_text, str) and unicode_text.isdigit():
        return unicode_text

    return KEY_DIGITS_BY_KEY.get(getattr(event, "key", None), "")


def is_enter_key_event(event: pygame.event.Event) -> bool:
    """Return whether a KEYDOWN event is a regular or keypad Enter key."""
    return getattr(event, "key", None) in ENTER_KEYS


class InputType(Enum):
    """Types of input events."""

    BARCODE = auto()  # Complete barcode string (ends with Enter)
    NUMPAD = auto()  # Single digit 0-9, or *, +, -
    NUMPAD_ENTER = auto()  # Enter key (also triggers barcode flush)
    TOUCH = auto()  # Click position (x, y)


@dataclass
class InputEvent:
    """Normalized input event."""

    type: InputType
    value: str | tuple[int, int]


class InputManager:
    """Collects and normalizes input from barcode scanner, numpad, and touch.

    Barcode scanner behavior:
    - Emits characters rapidly (like a fast typist)
    - Ends with Enter/Return
    - Characters are buffered until Enter is received

    Numpad behavior:
    - Single digit presses are emitted immediately
    - Enter key triggers both NUMPAD_ENTER and potential BARCODE

    Touch behavior:
    - Mouse clicks are emitted with position
    """

    # Keys that count as numpad input
    NUMPAD_KEYS = set("0123456789*+-")

    def __init__(self) -> None:
        """Initialize input manager."""
        self._barcode_buffer: str = ""

    def process_event(self, event: pygame.event.Event) -> list[InputEvent]:
        """Process a pygame event and return normalized InputEvents.

        Args:
            event: pygame event to process

        Returns:
            List of InputEvents (may be empty, one, or multiple)
        """
        events: list[InputEvent] = []

        if event.type == pygame.KEYDOWN:
            events.extend(self._handle_keydown(event))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                events.append(InputEvent(InputType.TOUCH, event.pos))

        return events

    def _handle_keydown(self, event: pygame.event.Event) -> list[InputEvent]:
        """Handle keyboard events."""
        events: list[InputEvent] = []

        # Enter key
        if is_enter_key_event(event):
            # Emit numpad enter
            events.append(InputEvent(InputType.NUMPAD_ENTER, ""))

            # If we have buffered characters, emit as barcode
            if self._barcode_buffer:
                events.append(InputEvent(InputType.BARCODE, self._barcode_buffer))
                self._barcode_buffer = ""

        # Character input
        else:
            unicode_text = getattr(event, "unicode", "")
            char = unicode_text if isinstance(unicode_text, str) else ""
            if not char:
                char = digit_from_key_event(event)

            if not char:
                return events

            # Buffer for potential barcode
            if char.isalnum():
                self._barcode_buffer += char

            # Also emit numpad events for digits and operators
            if char in self.NUMPAD_KEYS:
                events.append(InputEvent(InputType.NUMPAD, char))

        return events

    def clear_buffer(self) -> None:
        """Clear the barcode buffer.

        Call this when changing scenes or after timeout.
        """
        self._barcode_buffer = ""

    @property
    def buffer(self) -> str:
        """Get current barcode buffer contents (for debugging)."""
        return self._barcode_buffer
