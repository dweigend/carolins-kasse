"""Runtime controls for the FastAPI remote admin server."""

import subprocess
import sys
import time
from atexit import register
from dataclasses import dataclass

from src.utils.network import ADMIN_SERVER_PORT, admin_url, is_port_open

STARTUP_TIMEOUT_SECONDS = 3.0
STARTUP_POLL_SECONDS = 0.15

_server_process: subprocess.Popen | None = None


@dataclass(frozen=True)
class AdminServerStatus:
    """Current state of the remote admin server."""

    running: bool
    managed: bool
    url: str | None
    message: str


def get_admin_server_status() -> AdminServerStatus:
    """Return whether the remote admin server is reachable."""
    url = admin_url()
    running = is_port_open("127.0.0.1", ADMIN_SERVER_PORT)
    managed = _server_process is not None and _server_process.poll() is None

    if running and managed:
        message = "Server läuft"
    elif running:
        message = "Server läuft extern"
    else:
        message = "Server aus"

    return AdminServerStatus(
        running=running,
        managed=managed,
        url=url,
        message=message,
    )


def start_admin_server() -> AdminServerStatus:
    """Start the FastAPI remote admin server if it is not already reachable."""
    global _server_process

    status = get_admin_server_status()
    if status.running:
        return status

    _server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.admin.server:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(ADMIN_SERVER_PORT),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _server_process.poll() is not None:
            break
        status = get_admin_server_status()
        if status.running:
            return status
        time.sleep(STARTUP_POLL_SECONDS)

    return get_admin_server_status()


def stop_admin_server() -> AdminServerStatus:
    """Stop the server when this process started it."""
    global _server_process

    if _server_process is None:
        return get_admin_server_status()

    if _server_process.poll() is None:
        _server_process.terminate()
        try:
            _server_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _server_process.kill()
            _server_process.wait(timeout=2)

    _server_process = None
    return get_admin_server_status()


def toggle_admin_server() -> AdminServerStatus:
    """Start or stop the managed admin server."""
    status = get_admin_server_status()
    if status.running and status.managed:
        return stop_admin_server()
    if status.running:
        return status
    return start_admin_server()


register(stop_admin_server)
