"""Asset loader with caching and runtime scaling for pygame surfaces."""

from pathlib import Path

import pygame

# Cache for loaded + scaled surfaces
_cache: dict[str, pygame.Surface] = {}

# Base path for assets
_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

# Category → source directory mapping
_CATEGORY_DIR: dict[str, str] = {
    "products": "340er",
    "recipes": "680er",
    "ui": "ui",
}

# Size label → target pixels
_SIZE_PX: dict[str, int] = {
    "S": 30,
    "CART": 54,
    "M": 60,
    "BUTTON": 72,
    "XL": 96,
    "L": 120,
    "HERO": 180,
    "PANEL": 220,
}


def get(name: str, size: str = "M") -> pygame.Surface:
    """Load asset by category/name and scale to requested size.

    Args:
        name: Asset path as "category/filename" (e.g., "products/milk", "recipes/recipe_pancakes")
        size: Size variant - "S" (30px), "M" (60px), "XL" (96px), "L" (120px)

    Returns:
        Scaled pygame.Surface

    Raises:
        FileNotFoundError: If asset doesn't exist

    Examples:
        get("products/milk", "M")           → assets/340er/milk.png → scaled to 60×60
        get("recipes/recipe_pancakes", "L")  → assets/680er/recipe_pancakes.png → scaled to 120×120
        get("ui/rewards/coin_2_a", "XL")     → assets/ui/rewards/coin_2_a.png → scaled to 96×96
    """
    target_px = _SIZE_PX.get(size, 60)
    cache_key = f"{name}@{target_px}"

    if cache_key in _cache:
        return _cache[cache_key]

    file_path = _resolve_asset_path(name)

    # Load original and scale to target size
    original = pygame.image.load(str(file_path)).convert_alpha()
    scaled = pygame.transform.smoothscale(original, (target_px, target_px))
    _cache[cache_key] = scaled

    return scaled


def get_raw(name: str) -> pygame.Surface:
    """Load asset by category/name without resizing."""
    cache_key = f"{name}@raw"
    if cache_key in _cache:
        return _cache[cache_key]

    file_path = _resolve_asset_path(name)
    original = pygame.image.load(str(file_path)).convert_alpha()
    _cache[cache_key] = original
    return original


def _resolve_asset_path(name: str) -> Path:
    """Resolve an asset name to an existing PNG path."""
    category, _, filename = name.partition("/")
    if not filename:
        raise FileNotFoundError(f"Invalid asset name (need category/filename): {name}")

    source_dir = _CATEGORY_DIR.get(category)
    if not source_dir:
        raise FileNotFoundError(f"Unknown asset category: {category}")

    file_path = _ASSETS_DIR / source_dir / f"{filename}.png"
    if not file_path.exists():
        raise FileNotFoundError(f"Asset not found: {file_path}")
    return file_path


def preload(names: list[str], size: str = "M") -> None:
    """Preload multiple assets into cache."""
    for name in names:
        get(name, size)


def clear_cache() -> None:
    """Clear the asset cache."""
    _cache.clear()
