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
INSTALL_SERVICE = "carolins-install.service"
UPDATE_SERVICE = "carolins-kasse-update.service"
BACKUP_SERVICE = "carolins-kasse-backup.service"
BACKUP_TIMER = "carolins-kasse-backup.timer"
SYSTEMCTL_TIMEOUT_SECONDS = 3
JOURNAL_TIMEOUT_SECONDS = 4
JOURNAL_LINES = 12
FAILED_UNITS_LIMIT = 8
SYSTEMD_UNIT_PROPERTIES = (
    "Description",
    "LoadState",
    "ActiveState",
    "SubState",
    "UnitFileState",
)
UNKNOWN_STATUS = "unbekannt"
UNAVAILABLE_STATUS = "nicht verfügbar"
NO_LOGS_MESSAGE = "Keine Logs verfügbar."
STATE_LABELS = {
    "active": "aktiv",
    "activating": "startet",
    "dead": "gestoppt",
    "deactivating": "stoppt",
    "degraded": "eingeschränkt",
    "disabled": "deaktiviert",
    "enabled": "aktiviert",
    "elapsed": "abgelaufen",
    "failed": "fehlgeschlagen",
    "inactive": "inaktiv",
    "loaded": "geladen",
    "masked": "maskiert",
    "not-found": "nicht installiert",
    "running": "läuft",
    "static": "statisch",
    "unknown": UNKNOWN_STATUS,
    "waiting": "wartet",
}


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
    load_state: str = UNKNOWN_STATUS
    sub_state: str = UNKNOWN_STATUS
    description: str = ""
    logs: str = NO_LOGS_MESSAGE
    available: bool = True
    unavailable_reason: str = ""

    @property
    def status(self) -> str:
        """Return a short German status line for the admin UI."""
        if not self.available:
            return self.unavailable_reason or UNAVAILABLE_STATUS
        if self.load_state == "not-found":
            return STATE_LABELS["not-found"]

        parts = [_state_label(self.active)]
        sub_state = _state_label(self.sub_state)
        if sub_state not in parts and sub_state != UNKNOWN_STATUS:
            parts.append(sub_state)
        enabled = _state_label(self.enabled)
        if enabled != UNKNOWN_STATUS:
            parts.append(enabled)
        return " · ".join(parts)


@dataclass(frozen=True)
class FailedUnitsSnapshot:
    """Summary of systemd units currently in the failed state."""

    ok: bool
    summary: str
    output: str


@dataclass(frozen=True)
class PiOpsSnapshot:
    """Install, update, and backup operation status."""

    system_state: str
    install_service: ServiceSnapshot
    update_service: ServiceSnapshot
    backup_service: ServiceSnapshot
    backup_timer: ServiceSnapshot
    failed_units: FailedUnitsSnapshot


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
    systemd_state: str
    kiosk_service: ServiceSnapshot
    install_service: ServiceSnapshot
    update_service: ServiceSnapshot
    backup_service: ServiceSnapshot
    backup_timer: ServiceSnapshot
    failed_units: FailedUnitsSnapshot
    logs: str
    ssh_command: str


def collect_debug_snapshot() -> DebugSnapshot:
    """Collect read-only diagnostics for the web admin debug page."""
    hostname = socket.gethostname()
    ip_address = get_local_ip() or "Keine IP"
    latest_backup = _latest_backup()
    systemd_state, systemd_unavailable_reason = _systemd_state()
    kiosk_service = _service_snapshot(
        KIOSK_SERVICE,
        systemd_unavailable_reason=systemd_unavailable_reason,
    )
    pi_ops = _collect_pi_ops_snapshot(systemd_state, systemd_unavailable_reason)

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
        systemd_state=systemd_state,
        kiosk_service=kiosk_service,
        install_service=pi_ops.install_service,
        update_service=pi_ops.update_service,
        backup_service=pi_ops.backup_service,
        backup_timer=pi_ops.backup_timer,
        failed_units=pi_ops.failed_units,
        logs=kiosk_service.logs,
        ssh_command=f"ssh kasse@{hostname}.local",
    )


def collect_pi_ops_snapshot() -> PiOpsSnapshot:
    """Collect read-only install, update, and backup status for the Pi."""
    systemd_state, systemd_unavailable_reason = _systemd_state()
    return _collect_pi_ops_snapshot(systemd_state, systemd_unavailable_reason)


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


def _collect_pi_ops_snapshot(
    systemd_state: str,
    systemd_unavailable_reason: str,
) -> PiOpsSnapshot:
    return PiOpsSnapshot(
        system_state=systemd_state,
        install_service=_service_snapshot(
            INSTALL_SERVICE,
            systemd_unavailable_reason=systemd_unavailable_reason,
        ),
        update_service=_service_snapshot(
            UPDATE_SERVICE,
            systemd_unavailable_reason=systemd_unavailable_reason,
        ),
        backup_service=_service_snapshot(
            BACKUP_SERVICE,
            systemd_unavailable_reason=systemd_unavailable_reason,
        ),
        backup_timer=_service_snapshot(
            BACKUP_TIMER,
            systemd_unavailable_reason=systemd_unavailable_reason,
        ),
        failed_units=_failed_units_snapshot(systemd_unavailable_reason),
    )


def _service_snapshot(
    service_name: str,
    *,
    systemd_unavailable_reason: str = "",
) -> ServiceSnapshot:
    if systemd_unavailable_reason:
        return _unavailable_service_snapshot(service_name, systemd_unavailable_reason)

    properties = _systemctl_show(service_name)
    if properties is None:
        return _unavailable_service_snapshot(service_name, "Status nicht lesbar")

    return ServiceSnapshot(
        name=service_name,
        active=properties.get("ActiveState", UNKNOWN_STATUS) or UNKNOWN_STATUS,
        enabled=properties.get("UnitFileState", UNKNOWN_STATUS) or UNKNOWN_STATUS,
        load_state=properties.get("LoadState", UNKNOWN_STATUS) or UNKNOWN_STATUS,
        sub_state=properties.get("SubState", UNKNOWN_STATUS) or UNKNOWN_STATUS,
        description=properties.get("Description", service_name) or service_name,
        logs=_journal_tail(service_name),
    )


def _unavailable_service_snapshot(
    service_name: str,
    reason: str,
) -> ServiceSnapshot:
    return ServiceSnapshot(
        name=service_name,
        active=UNAVAILABLE_STATUS,
        enabled=UNAVAILABLE_STATUS,
        load_state=UNAVAILABLE_STATUS,
        sub_state=UNAVAILABLE_STATUS,
        description=service_name,
        logs=f"Logs nicht verfügbar: {reason}.",
        available=False,
        unavailable_reason=reason,
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
        [
            "journalctl",
            "--unit",
            service_name,
            "--lines",
            str(JOURNAL_LINES),
            "--no-pager",
            "--output",
            "short-iso",
        ],
        timeout=JOURNAL_TIMEOUT_SECONDS,
    )
    if not result.output:
        return NO_LOGS_MESSAGE
    if not result.ok:
        return f"Logs nicht verfügbar: {result.output}"
    return result.output


def _systemd_state() -> tuple[str, str]:
    result = _run(
        ["systemctl", "is-system-running", "--no-pager"],
        timeout=SYSTEMCTL_TIMEOUT_SECONDS,
    )
    unavailable_reason = _systemd_unavailable_reason(result.output)
    if unavailable_reason:
        return UNAVAILABLE_STATUS, unavailable_reason
    if not result.output:
        return UNKNOWN_STATUS, ""
    return _state_label(result.output.splitlines()[-1].strip()), ""


def _systemctl_show(unit_name: str) -> dict[str, str] | None:
    command = ["systemctl", "show"]
    for property_name in SYSTEMD_UNIT_PROPERTIES:
        command.append(f"--property={property_name}")
    command.append(unit_name)

    result = _run(command, timeout=SYSTEMCTL_TIMEOUT_SECONDS)
    if _systemd_unavailable_reason(result.output):
        return None
    if not result.output:
        return None
    properties = _parse_systemctl_properties(result.output)
    if properties:
        return properties
    if result.ok:
        return {}
    return None


def _failed_units_snapshot(systemd_unavailable_reason: str) -> FailedUnitsSnapshot:
    if systemd_unavailable_reason:
        message = f"systemctl --failed nicht verfügbar: {systemd_unavailable_reason}."
        return FailedUnitsSnapshot(False, UNAVAILABLE_STATUS, message)

    result = _run(
        ["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"],
        timeout=SYSTEMCTL_TIMEOUT_SECONDS,
    )
    unavailable_reason = _systemd_unavailable_reason(result.output)
    if unavailable_reason:
        message = f"systemctl --failed nicht verfügbar: {unavailable_reason}."
        return FailedUnitsSnapshot(False, UNAVAILABLE_STATUS, message)

    failed_lines = [line.strip() for line in result.output.splitlines() if line.strip()]
    if not failed_lines:
        summary = "Keine fehlgeschlagenen Units."
        return FailedUnitsSnapshot(result.ok, summary, summary)

    shown_lines = failed_lines[:FAILED_UNITS_LIMIT]
    remaining_count = len(failed_lines) - len(shown_lines)
    if remaining_count:
        shown_lines.append(f"... und {remaining_count} weitere.")
    summary = _failed_units_summary(len(failed_lines))
    return FailedUnitsSnapshot(result.ok, summary, "\n".join(shown_lines))


def _command_text(command: list[str], *, default: str = "n/a") -> str:
    result = _run(command, timeout=3)
    if not result.output:
        return default
    return result.output.splitlines()[-1].strip() or default


def _parse_systemctl_properties(output: str) -> dict[str, str]:
    properties = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        properties[key] = value.strip()
    return properties


def _systemd_unavailable_reason(output: str) -> str:
    lower_output = output.lower()
    if "no such file or directory" in lower_output:
        return "systemctl nicht gefunden"
    if "not been booted with systemd" in lower_output:
        return "systemd ist hier nicht aktiv"
    if "failed to connect to bus" in lower_output:
        return "systemd ist hier nicht erreichbar"
    if "timed out" in lower_output or "timeout" in lower_output:
        return "systemd-Abfrage hat zu lange gedauert"
    return ""


def _state_label(value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        return UNKNOWN_STATUS
    return STATE_LABELS.get(normalized_value, normalized_value)


def _failed_units_summary(failed_count: int) -> str:
    if failed_count == 1:
        return "1 fehlgeschlagene Unit."
    return f"{failed_count} fehlgeschlagene Units."


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
    except subprocess.TimeoutExpired:
        return CommandResult(False, f"Timeout nach {timeout} Sekunden.")
    except OSError as error:
        return CommandResult(False, str(error))

    output = (completed.stdout + completed.stderr).strip()
    return CommandResult(completed.returncode == 0, output)
