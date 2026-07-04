"""Lazy scene package exports."""

from importlib import import_module

_SCENE_EXPORTS = {
    "Scene": ("src.scenes.base", "Scene"),
    "SceneManager": ("src.scenes.manager", "SceneManager"),
    "AdminScene": ("src.scenes.admin", "AdminScene"),
    "StartScene": ("src.scenes.start", "StartScene"),
    "LoginScene": ("src.scenes.login", "LoginScene"),
    "MenuScene": ("src.scenes.menu", "MenuScene"),
    "ScanScene": ("src.scenes.scan", "ScanScene"),
    "RecipeScene": ("src.scenes.recipe", "RecipeScene"),
    "MathGameScene": ("src.scenes.math_game", "MathGameScene"),
    "PickerScene": ("src.scenes.picker", "PickerScene"),
}

__all__ = list(_SCENE_EXPORTS)


def __getattr__(name: str) -> object:
    """Import exported scene classes only when they are requested."""
    try:
        module_name, attribute_name = _SCENE_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from error

    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return available lazy package exports for introspection."""
    return sorted([*globals(), *_SCENE_EXPORTS])
