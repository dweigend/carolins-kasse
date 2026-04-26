#!/usr/bin/env python3
"""Print Raspberry Pi diagnostics for Carolin's Kasse."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.pi_system import collect_debug_snapshot


def main() -> int:
    """Print diagnostics as text for SSH sessions."""
    snapshot = collect_debug_snapshot()
    print("Carolin's Kasse debug")
    print(f"Hostname: {snapshot.hostname}")
    print(f"IP: {snapshot.ip_address}")
    print(f"Admin URL: {snapshot.admin_url}")
    print(f"SSH: {snapshot.ssh_command}")
    print(f"Git: {snapshot.git_branch} {snapshot.git_commit}")
    print(f"Database: {snapshot.db_path}")
    print(f"Database exists: {snapshot.db_exists}")
    print(f"Latest backup: {snapshot.latest_backup}")
    print(f"Kiosk service: {snapshot.kiosk_service.active}")
    print(f"Update service: {snapshot.update_service.active}")
    print(f"Backup service: {snapshot.backup_service.active}")
    print("\nLast kiosk logs:")
    print(snapshot.logs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
