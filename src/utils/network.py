"""Network helpers for the on-device admin screen."""

import socket

ADMIN_SERVER_PORT = 8080


def get_local_ip() -> str | None:
    """Return the best local network IP address, if one is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except OSError:
        return None

    if ip_address.startswith("127."):
        return None
    return ip_address


def admin_url() -> str | None:
    """Return the remote admin URL for the current network."""
    ip_address = get_local_ip()
    if not ip_address:
        return None
    return f"http://{ip_address}:{ADMIN_SERVER_PORT}"


def is_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    """Return True when a TCP port accepts connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
