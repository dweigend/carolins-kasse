"""Cold-path import regression tests for the kiosk entry point."""

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
        env = os.environ.copy()
        env.setdefault("SDL_AUDIODRIVER", "dummy")
        env.setdefault("SDL_VIDEODRIVER", "dummy")

        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
