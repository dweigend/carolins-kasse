"""Raspberry Pi setup, update, and debug helpers."""

import hmac
import os
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.utils.database import DB_PATH
from src.utils.network import admin_url, get_local_ip

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_ADMIN_PIN_PATH = Path("/etc/carolins-kasse/admin-pin")
DEFAULT_BACKUP_DIR = Path("/var/backups/carolins-kasse")
ADMIN_PIN_PATH = Path(
    os.environ.get("CAROLINS_KASSE_ADMIN_PIN_PATH", DEFAULT_ADMIN_PIN_PATH)
).expanduser()
BACKUP_DIR = Path(os.environ.get("CAROLINS_KASSE_BACKUP_DIR", DEFAULT_BACKUP_DIR))

KIOSK_SERVICE = "carolins-kasse.service"
UPDATE_SERVICE = "carolins-kasse-update.service"
BACKUP_SERVICE = "carolins-kasse-backup.service"


@dataclass(frozen=True)
class CommandResult:
    """Result of a short system command."""

    ok: bool
    output: str


@dataclass(frozen=True)
class ServiceSnapshot:
    """Current systemd service state."""

    name: str
    active: str
    enabled: str


@dataclass(frozen=True)
class DebugSnapshot:
    """Parent-facing debug information for the Pi installation."""

    hostname: str
    ip_address: str
    admin_url: str
    git_branch: str
    git_commit: str
    db_path: str
    db_exists: bool
    latest_backup: str
    pin_configured: bool
    kiosk_service: ServiceSnapshot
    update_service: ServiceSnapshot
    backup_service: ServiceSnapshot
    logs: str
    ssh_command: str


def collect_debug_snapshot() -> DebugSnapshot:
    """Collect read-only diagnostics for the web admin debug page."""
    hostname = socket.gethostname()
    ip_address = get_local_ip() or "Keine IP"
    latest_backup = _latest_backup()

    return DebugSnapshot(
        hostname=hostname,
        ip_address=ip_address,
        admin_url=admin_url() or "Nicht erreichbar",
        git_branch=_command_text(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        git_commit=_command_text(["git", "rev-parse", "--short", "HEAD"]),
        db_path=str(DB_PATH),
        db_exists=DB_PATH.exists(),
        latest_backup=latest_backup,
        pin_configured=ADMIN_PIN_PATH.exists(),
        kiosk_service=_service_snapshot(KIOSK_SERVICE),
        update_service=_service_snapshot(UPDATE_SERVICE),
        backup_service=_service_snapshot(BACKUP_SERVICE),
        logs=_journal_tail(KIOSK_SERVICE),
        ssh_command=f"ssh kasse@{hostname}.local",
    )


def verify_admin_pin(pin: str | None) -> bool:
    """Return True when the submitted web admin PIN matches the local PIN."""
    if not pin or not ADMIN_PIN_PATH.exists():
        return False
    try:
        expected_pin = ADMIN_PIN_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return hmac.compare_digest(pin.strip(), expected_pin)


def run_admin_action(action: str) -> CommandResult:
    """Run an allowed PIN-protected admin action."""
    commands = {
        "backup": ["sudo", "systemctl", "start", BACKUP_SERVICE],
        "restart": ["sudo", "systemctl", "restart", KIOSK_SERVICE],
        "update": ["sudo", "systemctl", "start", UPDATE_SERVICE],
    }
    command = commands.get(action)
    if not command:
        return CommandResult(False, "Unbekannte Aktion.")
    return _run(command, timeout=8)


def _service_snapshot(service_name: str) -> ServiceSnapshot:
    return ServiceSnapshot(
        name=service_name,
        active=_command_text(["systemctl", "is-active", service_name], default="n/a"),
        enabled=_command_text(["systemctl", "is-enabled", service_name], default="n/a"),
    )


def _latest_backup() -> str:
    try:
        backups = sorted(
            BACKUP_DIR.glob("kasse-*.db"), key=lambda path: path.stat().st_mtime
        )
    except OSError:
        return "Kein Backup"
    if not backups:
        return "Kein Backup"
    latest = backups[-1]
    timestamp = datetime.fromtimestamp(latest.stat().st_mtime).strftime(
        "%d.%m.%Y %H:%M"
    )
    return f"{latest.name} · {timestamp}"


def _journal_tail(service_name: str) -> str:
    result = _run(
        ["journalctl", "-u", service_name, "-n", "24", "--no-pager"],
        timeout=3,
    )
    return result.output if result.output else "Keine Logs verfügbar."


def _command_text(command: list[str], *, default: str = "n/a") -> str:
    result = _run(command, timeout=3)
    if not result.output:
        return default
    return result.output.splitlines()[-1].strip() or default


def _run(command: list[str], *, timeout: int) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(False, str(error))

    output = (completed.stdout + completed.stderr).strip()
    return CommandResult(completed.returncode == 0, output)
