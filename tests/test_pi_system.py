"""Tests for Raspberry Pi system diagnostics without real systemd calls."""

import subprocess
import unittest
from unittest.mock import patch

from src.utils import pi_system


class PiSystemSnapshotTests(unittest.TestCase):
    def test_collect_pi_ops_snapshot_reads_unit_status_logs_and_failed_units(
        self,
    ) -> None:
        calls: list[tuple[tuple[str, ...], int]] = []

        def fake_run(
            command: list[str],
            **kwargs,
        ) -> subprocess.CompletedProcess[str]:
            calls.append((tuple(command), kwargs["timeout"]))
            if command == ["systemctl", "is-system-running", "--no-pager"]:
                return completed(command, returncode=1, stdout="degraded\n")

            if command[:2] == ["systemctl", "show"]:
                return completed(command, stdout=systemctl_show_output(command[-1]))

            if command[:2] == ["journalctl", "--unit"]:
                unit_name = command[2]
                self.assertEqual(
                    command,
                    [
                        "journalctl",
                        "--unit",
                        unit_name,
                        "--lines",
                        str(pi_system.JOURNAL_LINES),
                        "--no-pager",
                        "--output",
                        "short-iso",
                    ],
                )
                return completed(command, stdout=f"{unit_name} log line\n")

            if command[:2] == ["systemctl", "--failed"]:
                return completed(
                    command,
                    stdout=(
                        "carolins-install.service loaded failed failed install\n"
                        "ssh.service loaded failed failed ssh\n"
                    ),
                )

            raise AssertionError(f"Unexpected command: {command!r}")

        with patch("src.utils.pi_system.subprocess.run", side_effect=fake_run):
            snapshot = pi_system.collect_pi_ops_snapshot()

        self.assertEqual(snapshot.system_state, "eingeschränkt")
        self.assertEqual(
            snapshot.install_service.status,
            "fehlgeschlagen · aktiviert",
        )
        self.assertEqual(
            snapshot.update_service.status,
            "inaktiv · gestoppt · statisch",
        )
        self.assertEqual(snapshot.backup_timer.status, "aktiv · wartet · aktiviert")
        self.assertIn(
            "carolins-kasse-update.service log line", snapshot.update_service.logs
        )
        self.assertEqual(snapshot.failed_units.summary, "2 fehlgeschlagene Units.")
        self.assertIn(
            "carolins-install.service loaded failed", snapshot.failed_units.output
        )
        self.assertTrue(
            all(
                timeout == pi_system.SYSTEMCTL_TIMEOUT_SECONDS
                for command, timeout in calls
                if command[0] == "systemctl"
            )
        )
        self.assertTrue(
            all(
                timeout == pi_system.JOURNAL_TIMEOUT_SECONDS
                for command, timeout in calls
                if command[0] == "journalctl"
            )
        )

    def test_collect_pi_ops_snapshot_skips_journal_when_systemd_is_unavailable(
        self,
    ) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
            calls.append(tuple(command))
            if command[0] == "systemctl":
                raise FileNotFoundError(
                    2,
                    "No such file or directory",
                    "systemctl",
                )
            raise AssertionError(f"Unexpected command: {command!r}")

        with patch("src.utils.pi_system.subprocess.run", side_effect=fake_run):
            snapshot = pi_system.collect_pi_ops_snapshot()

        self.assertEqual(snapshot.system_state, "nicht verfügbar")
        self.assertFalse(snapshot.install_service.available)
        self.assertIn("systemctl nicht gefunden", snapshot.install_service.status)
        self.assertIn("systemctl nicht gefunden", snapshot.install_service.logs)
        self.assertIn(
            "systemctl --failed nicht verfügbar", snapshot.failed_units.output
        )
        self.assertNotIn("journalctl", {command[0] for command in calls})


def completed(
    command: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def systemctl_show_output(unit_name: str) -> str:
    status_by_unit = {
        pi_system.INSTALL_SERVICE: {
            "Description": "Install Carolin's Kasse after first boot",
            "LoadState": "loaded",
            "ActiveState": "failed",
            "SubState": "failed",
            "UnitFileState": "enabled",
        },
        pi_system.UPDATE_SERVICE: {
            "Description": "Update Carolin's Kasse from GitHub",
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "static",
        },
        pi_system.BACKUP_SERVICE: {
            "Description": "Back up Carolin's Kasse database",
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "static",
        },
        pi_system.BACKUP_TIMER: {
            "Description": "Daily Carolin's Kasse database backup",
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "waiting",
            "UnitFileState": "enabled",
        },
    }
    properties = status_by_unit[unit_name]
    return "\n".join(f"{key}={value}" for key, value in properties.items())


if __name__ == "__main__":
    unittest.main()
