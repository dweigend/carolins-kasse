"""Filename sanitization utilities.

Provides consistent German-to-ASCII filename conversion.
"""


def sanitize_filename(name: str) -> str:
    """Convert name to safe filename.

    Replaces German umlauts, spaces, and special characters.

    Args:
        name: Original name (may contain German characters)

    Returns:
        ASCII-safe filename string
    """
    replacements = {
        " ": "_",
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
        "(": "",
        ")": "",
        "/": "_",
    }
    result = name
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result
