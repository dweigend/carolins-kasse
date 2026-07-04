"""Static checks for systemd unit configuration."""

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
KIOSK_SERVICE_PATH = REPO_ROOT / "systemd" / "carolins-kasse.service"


class SystemdUnitTests(unittest.TestCase):
    def test_kiosk_service_does_not_wait_for_network_online(self) -> None:
        service_text = KIOSK_SERVICE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("network-online.target", service_text)


if __name__ == "__main__":
    unittest.main()
