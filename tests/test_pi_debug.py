"""Direct CLI coverage for the Raspberry Pi debug script."""

from contextlib import redirect_stdout
from dataclasses import dataclass
import io
import unittest
from unittest.mock import patch

from tools import pi_debug


class PiDebugScriptTests(unittest.TestCase):
    def test_main_prints_collected_debug_snapshot(self) -> None:
        snapshot = DebugSnapshotDouble(
            hostname="carolins-kasse",
            ip_address="192.168.1.139",
            admin_url="http://192.168.1.139:8080",
            ssh_command="ssh kasse@carolins-kasse.local",
            git_branch="codex/pi-ops-safety",
            git_commit="abc1234",
            db_path="/var/lib/carolins-kasse/kasse.db",
            db_exists=True,
            latest_backup="kasse-20260704.db",
            kiosk_service=ServiceSnapshotDouble(active="active"),
            update_service=ServiceSnapshotDouble(active="inactive"),
            backup_service=ServiceSnapshotDouble(active="failed"),
            logs="kiosk log line",
        )
        output = io.StringIO()

        with (
            patch.object(
                pi_debug,
                "collect_debug_snapshot",
                return_value=snapshot,
            ) as collect_debug_snapshot,
            redirect_stdout(output),
        ):
            result = pi_debug.main()

        collect_debug_snapshot.assert_called_once_with()
        self.assertEqual(0, result)
        self.assertEqual(
            [
                "Carolin's Kasse debug",
                "Hostname: carolins-kasse",
                "IP: 192.168.1.139",
                "Admin URL: http://192.168.1.139:8080",
                "SSH: ssh kasse@carolins-kasse.local",
                "Git: codex/pi-ops-safety abc1234",
                "Database: /var/lib/carolins-kasse/kasse.db",
                "Database exists: True",
                "Latest backup: kasse-20260704.db",
                "Kiosk service: active",
                "Update service: inactive",
                "Backup service: failed",
                "",
                "Last kiosk logs:",
                "kiosk log line",
            ],
            output.getvalue().splitlines(),
        )


@dataclass(frozen=True)
class ServiceSnapshotDouble:
    active: str


@dataclass(frozen=True)
class DebugSnapshotDouble:
    hostname: str
    ip_address: str
    admin_url: str
    ssh_command: str
    git_branch: str
    git_commit: str
    db_path: str
    db_exists: bool
    latest_backup: str
    kiosk_service: ServiceSnapshotDouble
    update_service: ServiceSnapshotDouble
    backup_service: ServiceSnapshotDouble
    logs: str


if __name__ == "__main__":
    unittest.main()
