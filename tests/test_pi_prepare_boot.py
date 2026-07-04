"""Temp-bootfs coverage for the Raspberry Pi first-boot preparation tool."""

from argparse import Namespace
from contextlib import redirect_stdout
import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from tools import pi_prepare_boot


BASE_CMDLINE = "console=serial0,115200 root=PARTUUID=abc rootwait quiet"
CONFIG_TEXT = "# Raspberry Pi config fixture\n"


class PiPrepareBootTests(unittest.TestCase):
    def test_validate_bootfs_reports_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_bootfs = temp_path / "missing"
            bootfs = temp_path / "bootfs"

            self.assertEqual(
                f"Bootfs path does not exist: {missing_bootfs}",
                pi_prepare_boot.validate_bootfs(missing_bootfs),
            )

            bootfs.mkdir()
            self.assertEqual(
                f"Missing cmdline.txt in {bootfs}",
                pi_prepare_boot.validate_bootfs(bootfs),
            )

            (bootfs / "cmdline.txt").write_text(BASE_CMDLINE + "\n", encoding="utf-8")
            self.assertEqual(
                f"Missing config.txt in {bootfs}",
                pi_prepare_boot.validate_bootfs(bootfs),
            )

            (bootfs / "config.txt").write_text(CONFIG_TEXT, encoding="utf-8")
            self.assertIsNone(pi_prepare_boot.validate_bootfs(bootfs))

    def test_main_copies_firstboot_files_and_writes_quoted_env(self) -> None:
        repo_url = 'https://example.invalid/carolins "kasse".git'
        repo_ref = r"feature\first-boot"

        with tempfile.TemporaryDirectory() as temp_dir:
            bootfs = create_bootfs(Path(temp_dir))

            result, output = run_prepare_boot(
                bootfs,
                repo_url=repo_url,
                repo_ref=repo_ref,
            )

            self.assertEqual(result, 0, output)
            self.assertIn(f"Prepared {bootfs.resolve()}", output)
            self.assert_bootfs_file_matches_source(
                bootfs / "carolins-firstboot.sh",
                pi_prepare_boot.FIRSTBOOT_SCRIPT_PATH,
            )
            self.assert_bootfs_file_matches_source(
                bootfs / "carolins-pi-bootstrap.sh",
                pi_prepare_boot.REPO_ROOT / "tools" / "pi_bootstrap.sh",
            )
            self.assert_bootfs_file_matches_source(
                bootfs / "carolins-install.service",
                pi_prepare_boot.REPO_ROOT / "systemd" / "carolins-install.service",
                executable=False,
            )
            self.assertEqual(
                [
                    f"CAROLINS_KASSE_REPO_URL={pi_prepare_boot.quote_systemd_env(repo_url)}",
                    f"CAROLINS_KASSE_REPO_REF={pi_prepare_boot.quote_systemd_env(repo_ref)}",
                ],
                (bootfs / "carolins-install.env")
                .read_text(encoding="utf-8")
                .splitlines(),
            )

    def test_update_cmdline_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bootfs = create_bootfs(Path(temp_dir))
            cmdline_path = bootfs / "cmdline.txt"

            pi_prepare_boot.update_cmdline(cmdline_path)
            first_cmdline = cmdline_path.read_text(encoding="utf-8")
            pi_prepare_boot.update_cmdline(cmdline_path)
            second_cmdline = cmdline_path.read_text(encoding="utf-8")

            self.assertEqual(first_cmdline, second_cmdline)
            self.assertTrue(second_cmdline.endswith("\n"))
            tokens = second_cmdline.split()
            for expected_token in pi_prepare_boot.CMDLINE_TOKENS:
                self.assertEqual(tokens.count(expected_token), 1)
            self.assertEqual(
                [token for token in tokens if token.startswith("systemd.run=")],
                [pi_prepare_boot.CMDLINE_TOKENS[0]],
            )

    def test_write_install_env_removes_stale_file_without_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bootfs = create_bootfs(Path(temp_dir))
            install_env_path = bootfs / "carolins-install.env"
            install_env_path.write_text("STALE=1\n", encoding="utf-8")

            pi_prepare_boot.write_install_env(bootfs, repo_url="", repo_ref="")

            self.assertFalse(install_env_path.exists())

    def test_main_refuses_foreign_systemd_run_without_force(self) -> None:
        foreign_cmdline = f"{BASE_CMDLINE} systemd.run=/boot/custom-firstboot.sh"

        with tempfile.TemporaryDirectory() as temp_dir:
            bootfs = create_bootfs(Path(temp_dir), cmdline=foreign_cmdline)
            cmdline_path = bootfs / "cmdline.txt"

            result, output = run_prepare_boot(bootfs)

            self.assertEqual(result, 1)
            self.assertIn("different systemd.run hook", output)
            self.assertEqual(foreign_cmdline + "\n", cmdline_path.read_text())
            self.assertFalse((bootfs / "carolins-firstboot.sh").exists())

    def test_force_replaces_foreign_systemd_run(self) -> None:
        foreign_cmdline = (
            f"{BASE_CMDLINE} "
            "systemd.run=/boot/custom-firstboot.sh "
            "systemd.run_success_action=poweroff"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            bootfs = create_bootfs(Path(temp_dir), cmdline=foreign_cmdline)

            result, output = run_prepare_boot(bootfs, force=True)

            self.assertEqual(result, 0, output)
            tokens = (bootfs / "cmdline.txt").read_text(encoding="utf-8").split()
            self.assertNotIn("systemd.run=/boot/custom-firstboot.sh", tokens)
            self.assertNotIn("systemd.run_success_action=poweroff", tokens)
            for expected_token in pi_prepare_boot.CMDLINE_TOKENS:
                self.assertIn(expected_token, tokens)
            self.assertTrue((bootfs / "carolins-firstboot.sh").exists())

    def assert_bootfs_file_matches_source(
        self,
        bootfs_path: Path,
        source_path: Path,
        *,
        executable: bool = True,
    ) -> None:
        self.assertEqual(source_path.read_bytes(), bootfs_path.read_bytes())
        if executable:
            self.assertTrue(bootfs_path.stat().st_mode & stat.S_IXUSR)


def create_bootfs(root: Path, *, cmdline: str = BASE_CMDLINE) -> Path:
    bootfs = root / "bootfs"
    bootfs.mkdir()
    (bootfs / "cmdline.txt").write_text(cmdline + "\n", encoding="utf-8")
    (bootfs / "config.txt").write_text(CONFIG_TEXT, encoding="utf-8")
    return bootfs


def run_prepare_boot(
    bootfs: Path,
    *,
    force: bool = False,
    repo_url: str = "",
    repo_ref: str = "",
) -> tuple[int, str]:
    output = io.StringIO()
    args = Namespace(
        bootfs=bootfs,
        force=force,
        repo_url=repo_url,
        repo_ref=repo_ref,
    )
    with (
        patch.object(pi_prepare_boot, "parse_args", return_value=args),
        redirect_stdout(output),
    ):
        result = pi_prepare_boot.main()

    return result, output.getvalue()


if __name__ == "__main__":
    unittest.main()
