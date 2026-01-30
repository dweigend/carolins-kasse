"""Asset loader with caching for pygame surfaces."""

from pathlib import Path

import pygame

# Cache for loaded surfaces
_cache: dict[str, pygame.Surface] = {}

# Base path for assets
_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

# Categories that don't use size variants (loaded from nobg/)
_NO_SIZE_CATEGORIES = {"frames", "menue"}


def get(name: str, size: str = "M") -> pygame.Surface:
    """Load asset by name and optional size.

    Args:
        name: Asset path without extension (e.g., "products/milk", "menue/einkauf")
        size: Size variant - "S" (30px), "M" (60px), "L" (120px). Ignored for frames/menue.

    Returns:
        Loaded pygame.Surface

    Raises:
        FileNotFoundError: If asset doesn't exist

    Examples:
        get("products/milk", "M")  → assets/M/products/milk.png
        get("frames/frame_red")    → assets/nobg/frames/frame_red.png
        get("menue/einkauf")       → assets/nobg/menue/einkauf.png
    """
    # Determine category from path
    category = name.split("/")[0] if "/" in name else ""

    # Build cache key
    if category in _NO_SIZE_CATEGORIES:
        cache_key = f"nobg/{name}"
    else:
        cache_key = f"{size}/{name}"

    # Return cached surface if available
    if cache_key in _cache:
        return _cache[cache_key]

    # Build file path
    if category in _NO_SIZE_CATEGORIES:
        file_path = _ASSETS_DIR / "nobg" / f"{name}.png"
    else:
        file_path = _ASSETS_DIR / size / f"{name}.png"

    # Load and cache
    if not file_path.exists():
        raise FileNotFoundError(f"Asset not found: {file_path}")

    surface = pygame.image.load(str(file_path)).convert_alpha()
    _cache[cache_key] = surface

    return surface


def preload(names: list[str], size: str = "M") -> None:
    """Preload multiple assets into cache.

    Args:
        names: List of asset paths
        size: Size variant for assets that support it
    """
    for name in names:
        get(name, size)


def clear_cache() -> None:
    """Clear the asset cache."""
    _cache.clear()
