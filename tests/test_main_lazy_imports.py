"""Cold-path import regression tests for the kiosk entry point."""

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_main_subprocess(code: str) -> subprocess.CompletedProcess[str]:
    """Run a kiosk startup smoke in an isolated dummy SDL process."""
    env = os.environ.copy()
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class MainLazyImportTests(unittest.TestCase):
    def test_import_main_keeps_admin_qrcode_and_pillow_out_of_cold_path(
        self,
    ) -> None:
        code = textwrap.dedent(
            """
            import sys

            import main

            registry = main.create_scene_registry()
            eager_scene_names = [
                scene_name
                for scene_name, scene_definition in registry.items()
                if not callable(scene_definition)
            ]
            if eager_scene_names != ["start"]:
                raise SystemExit(f"unexpected eager scenes: {eager_scene_names!r}")

            unexpected_imports = [
                module_name
                for module_name in ("src.scenes.admin", "qrcode", "PIL.Image")
                if module_name in sys.modules
            ]
            if unexpected_imports:
                raise SystemExit(f"unexpected cold imports: {unexpected_imports!r}")
            """
        )
        result = run_main_subprocess(code)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_main_hides_mouse_cursor_after_display_setup(self) -> None:
        code = textwrap.dedent(
            """
            from unittest.mock import patch

            import pygame

            import main

            quit_event = pygame.event.Event(pygame.QUIT)
            with (
                patch.object(main, "init_database"),
                patch.object(pygame.event, "get", return_value=[quit_event]),
                patch.object(pygame.mouse, "set_visible") as set_visible,
            ):
                main.main()

            set_visible.assert_called_once_with(False)
            """
        )
        result = run_main_subprocess(code)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
