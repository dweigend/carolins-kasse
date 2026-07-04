"""Focused rendering cache tests for Pi runtime hot paths."""

import importlib
import os
import sys
from unittest import mock
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.ui import texture as texture_module
from src.utils import assets, fonts


class RenderCachingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def tearDown(self) -> None:
        assets.clear_cache()
        fonts.clear_cache()

    def test_texture_module_imports_without_numpy_available(self) -> None:
        original_module = sys.modules.pop("src.ui.texture", None)
        try:
            with mock.patch.dict(sys.modules, {"numpy": None}):
                module = importlib.import_module("src.ui.texture")
                surface = module.generate_paper_texture(96, 64)
        finally:
            sys.modules.pop("src.ui.texture", None)
            if original_module:
                sys.modules["src.ui.texture"] = original_module

        self.assertEqual(surface.get_size(), (96, 64))

    def test_paper_texture_keeps_expected_size_and_base_color(self) -> None:
        surface = texture_module.generate_paper_texture(96, 64)

        self.assertEqual(surface.get_size(), (96, 64))
        self.assertEqual(surface.get_at((8, 8))[:3], texture_module.CREAM)

    def test_font_getters_reuse_loaded_font_objects(self) -> None:
        self.assertIs(fonts.heading(), fonts.heading())
        self.assertIs(fonts.bold(), fonts.bold())
        self.assertIs(fonts.custom(24), fonts.custom(24))
        self.assertIs(fonts.bold_custom(24), fonts.bold_custom(24))
        self.assertIsNot(fonts.custom(24), fonts.bold_custom(24))

    def test_scaled_asset_cache_reuses_exact_size_surfaces(self) -> None:
        first_coin = assets.get_scaled("products/taler", (44, 44))
        second_coin = assets.get_scaled("products/taler", (44, 44))
        larger_coin = assets.get_scaled("products/taler", (45, 45))

        self.assertIs(first_coin, second_coin)
        self.assertIsNot(first_coin, larger_coin)
        self.assertEqual(first_coin.get_size(), (44, 44))
        self.assertEqual(larger_coin.get_size(), (45, 45))


if __name__ == "__main__":
    unittest.main()
