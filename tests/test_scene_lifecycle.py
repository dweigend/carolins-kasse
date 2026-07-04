"""Scene lifecycle regression tests for kiosk user changes."""

import importlib
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.scenes.base import Scene
from src.scenes.manager import SceneManager
from src.scenes.math_game import DEFAULT_DIFFICULTY, MathGameScene
from src.scenes.recipe import RecipeScene
from src.scenes.scan import ScanScene
from src.utils import state
from src.utils.database import Product, Recipe, User
from tests.db_isolation import isolated_database_module


class DummyScene(Scene):
    """Minimal scene double for manager transition tests."""

    def __init__(self, next_scene: str | None = None) -> None:
        self.next_scene = next_scene
        self.enter_count = 0

    def on_enter(self) -> None:
        """Track enter hook calls."""
        self.enter_count += 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Return the configured transition target."""
        return self.next_scene

    def update(self) -> None:
        """No-op update for lifecycle tests."""

    def render(self, screen: pygame.Surface) -> None:
        """No-op render for lifecycle tests."""


class SceneLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        state.set_current_user(None)
        state.set_selected_product(None)

    def tearDown(self) -> None:
        state.set_current_user(None)
        state.set_selected_product(None)

    def test_login_transition_resets_user_scoped_scene_state(self) -> None:
        product = create_product()
        scan_scene = ScanScene()
        scan_scene._cart.add(product)
        scan_scene._input_manager._barcode_buffer = "100"

        recipe_scene = RecipeScene()
        recipe_scene._recipe = Recipe("3000000000014", "Waffeln")
        recipe_scene._ingredients = [(product, 1)]
        recipe_scene._scanned_quantities = {product.barcode: 1}
        recipe_scene._complete = True
        recipe_scene._input_manager._barcode_buffer = "300"

        math_scene = MathGameScene()
        math_scene._current_answer = "9"
        math_scene._session_taler = 6
        math_scene._hint_visible = True
        math_scene._initialized = True

        state.set_current_user(User("2000000000022", "Annelie", difficulty=3))
        manager = SceneManager(
            {
                "login": DummyScene(next_scene="menu"),
                "menu": DummyScene(),
                "scan": scan_scene,
                "recipe": recipe_scene,
                "math_game": math_scene,
            },
            initial="login",
        )

        manager.handle_event(pygame.event.Event(pygame.USEREVENT))

        self.assertEqual(manager.current_name, "menu")
        self.assertTrue(scan_scene._cart.is_empty)
        self.assertEqual(scan_scene._input_manager.buffer, "")
        self.assertIsNone(recipe_scene._recipe)
        self.assertEqual(recipe_scene._ingredients, [])
        self.assertEqual(recipe_scene._scanned_quantities, {})
        self.assertFalse(recipe_scene._complete)
        self.assertEqual(recipe_scene._input_manager.buffer, "")
        self.assertEqual(math_scene._difficulty, 3)
        self.assertEqual(math_scene._session_taler, 0)
        self.assertEqual(math_scene._current_answer, "")
        self.assertFalse(math_scene._hint_visible)
        self.assertFalse(math_scene._initialized)

    def test_regular_scan_entry_keeps_cart_but_clears_partial_input(self) -> None:
        product = create_product()
        scan_scene = ScanScene()
        scan_scene._cart.add(product)
        scan_scene._input_manager._barcode_buffer = "partial"
        manager = SceneManager(
            {
                "menu": DummyScene(),
                "scan": scan_scene,
            },
            initial="menu",
        )

        manager.switch_to("scan")

        self.assertEqual(len(scan_scene._cart.items), 1)
        self.assertEqual(scan_scene._input_manager.buffer, "")

    def test_logout_switch_resets_user_scoped_scene_state(self) -> None:
        product = create_product()
        scan_scene = ScanScene()
        scan_scene._cart.add(product)
        recipe_scene = RecipeScene()
        recipe_scene._recipe = Recipe("3000000000014", "Waffeln")
        recipe_scene._ingredients = [(product, 1)]
        recipe_scene._scanned_quantities = {product.barcode: 1}
        recipe_scene._complete = True
        manager = SceneManager(
            {
                "login": DummyScene(),
                "menu": DummyScene(),
                "scan": scan_scene,
                "recipe": recipe_scene,
            },
            initial="menu",
        )

        manager.switch_to("login", reset_user_state=True)

        self.assertEqual(manager.current_name, "login")
        self.assertTrue(scan_scene._cart.is_empty)
        self.assertIsNone(recipe_scene._recipe)
        self.assertEqual(recipe_scene._scanned_quantities, {})
        self.assertFalse(recipe_scene._complete)

    def test_math_scene_resets_when_entered_by_a_different_user(self) -> None:
        math_scene = MathGameScene()
        state.set_current_user(User("2000000000015", "Carolin", difficulty=1))
        math_scene.on_enter()
        math_scene._init_ui()
        math_scene._session_taler = 4
        math_scene._current_answer = "7"

        state.set_current_user(User("2000000000022", "Annelie", difficulty=3))
        math_scene.on_enter()

        self.assertEqual(math_scene._difficulty, 3)
        self.assertEqual(math_scene._active_user_card_id, "2000000000022")
        self.assertEqual(math_scene._session_taler, 0)
        self.assertEqual(math_scene._current_answer, "")
        self.assertIsNone(math_scene._current_problem)
        self.assertFalse(math_scene._initialized)

    def test_math_scene_uses_default_difficulty_without_user(self) -> None:
        math_scene = MathGameScene()

        self.assertEqual(math_scene._difficulty, DEFAULT_DIFFICULTY)

    def test_start_session_clears_pending_picker_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "kasse.db"

            with isolated_database_module(db_path) as database:
                database.init_database()
                user = database.User("2000000000015", "Carolin", difficulty=2)
                product = database.Product(
                    barcode="1000000000016",
                    name="apple",
                    name_de="Apfel",
                    price=1.0,
                    category="obst",
                    has_barcode=False,
                )
                database.add_user(user)
                database.add_product(product)
                isolated_state = importlib.import_module("src.utils.state")

                isolated_state.set_selected_product(product)
                isolated_state.start_session(user)
                selected_product = isolated_state.get_and_clear_selected_product()
                isolated_state.logout()

            self.assertIsNone(selected_product)


def create_product() -> Product:
    """Return a small product object for scene state tests."""
    return Product(
        barcode="1000000000016",
        name="apple",
        name_de="Apfel",
        price=1.0,
        category="obst",
    )


if __name__ == "__main__":
    unittest.main()
