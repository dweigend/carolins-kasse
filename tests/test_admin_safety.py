"""Admin write-route safety tests with isolated temp state."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from http.cookies import SimpleCookie
import asyncio
import importlib
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from urllib.parse import urlencode, urlsplit
import unittest

from tests.db_isolation import isolated_database_module


ADMIN_PIN = "2468"
USER_CARD_ID = "2000000000015"
ADMIN_PIN_ENV_VAR = "CAROLINS_KASSE_ADMIN_PIN_PATH"
BACKUP_DIR_ENV_VAR = "CAROLINS_KASSE_BACKUP_DIR"
ADMIN_MODULES = (
    "src.admin.server",
    "src.admin.printables",
    "src.utils.pi_system",
)


@dataclass
class AsgiResponse:
    status_code: int
    headers: list[tuple[str, str]]
    body: bytes
    cookies: dict[str, str]

    @property
    def text(self) -> str:
        return self.body.decode("utf-8")

    @property
    def location(self) -> str | None:
        return self.header("location")

    def header(self, name: str) -> str | None:
        lower_name = name.lower()
        for header_name, value in self.headers:
            if header_name.lower() == lower_name:
                return value
        return None

    def headers_for(self, name: str) -> list[str]:
        lower_name = name.lower()
        return [
            value
            for header_name, value in self.headers
            if header_name.lower() == lower_name
        ]


class AsgiTestClient:
    """Small ASGI test client for the admin safety checks."""

    def __init__(self, app) -> None:
        self.app = app
        self.cookies: dict[str, str] = {}

    def get(self, path: str) -> AsgiResponse:
        return asyncio.run(self._request("GET", path, body=b""))

    def post(self, path: str, data: Mapping[str, str]) -> AsgiResponse:
        body = urlencode(data).encode("utf-8")
        return asyncio.run(
            self._request(
                "POST",
                path,
                body=body,
                extra_headers=[
                    (b"content-type", b"application/x-www-form-urlencoded"),
                ],
            )
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes,
        extra_headers: list[tuple[bytes, bytes]] | None = None,
    ) -> AsgiResponse:
        split_url = urlsplit(path)
        response_status = 500
        response_headers: list[tuple[str, str]] = []
        response_body = bytearray()
        request_sent = False

        headers = [
            (b"host", b"testserver"),
            (b"content-length", str(len(body)).encode("ascii")),
        ]
        if self.cookies:
            cookie_header = "; ".join(
                f"{name}={value}" for name, value in sorted(self.cookies.items())
            )
            headers.append((b"cookie", cookie_header.encode("utf-8")))
        if extra_headers:
            headers.extend(extra_headers)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": split_url.path,
            "raw_path": split_url.path.encode("utf-8"),
            "query_string": split_url.query.encode("utf-8"),
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        async def receive() -> dict:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict) -> None:
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = [
                    (
                        header_name.decode("latin-1"),
                        header_value.decode("latin-1"),
                    )
                    for header_name, header_value in message["headers"]
                ]
                return

            if message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        await self.app(scope, receive, send)
        response = AsgiResponse(
            status_code=response_status,
            headers=response_headers,
            body=bytes(response_body),
            cookies=self._response_cookies(response_headers),
        )
        self.cookies.update(response.cookies)
        return response

    def _response_cookies(self, headers: list[tuple[str, str]]) -> dict[str, str]:
        response_cookies = {}
        for header_name, set_cookie_header in headers:
            if header_name.lower() != "set-cookie":
                continue
            cookie = SimpleCookie()
            cookie.load(set_cookie_header)
            for name, morsel in cookie.items():
                response_cookies[name] = morsel.value
        return response_cookies


@contextmanager
def isolated_admin_server(pin_path: Path, backup_dir: Path) -> Iterator[ModuleType]:
    previous_env_values = {
        ADMIN_PIN_ENV_VAR: os.environ.get(ADMIN_PIN_ENV_VAR),
        BACKUP_DIR_ENV_VAR: os.environ.get(BACKUP_DIR_ENV_VAR),
    }
    previous_sys_path = sys.path.copy()
    previous_modules = {
        module_name: sys.modules[module_name]
        for module_name in ADMIN_MODULES
        if module_name in sys.modules
    }

    os.environ[ADMIN_PIN_ENV_VAR] = str(pin_path)
    os.environ[BACKUP_DIR_ENV_VAR] = str(backup_dir)
    for module_name in ADMIN_MODULES:
        sys.modules.pop(module_name, None)

    try:
        yield importlib.import_module("src.admin.server")
    finally:
        for module_name in ADMIN_MODULES:
            sys.modules.pop(module_name, None)

        for name, previous_value in previous_env_values.items():
            if previous_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous_value

        sys.path[:] = previous_sys_path
        sys.modules.update(previous_modules)


class AdminSafetyTests(unittest.TestCase):
    def test_mutating_admin_post_without_pin_cookie_redirects(self) -> None:
        with admin_test_context() as context:
            response = context.client.post(
                f"/users/{USER_CARD_ID}/balance/adjust",
                data={"delta": "5", "note": "Should fail"},
            )

            self.assertSecurityRedirect(response)
            self.assertIn("Bitte%20PIN%20eingeben", response.location or "")
            self.assertEqual(context.user_balance(), 10.0)

    def test_mutating_admin_post_with_pin_requires_matching_csrf(self) -> None:
        with admin_test_context() as context:
            context.client.cookies[context.server.DEBUG_COOKIE] = ADMIN_PIN
            context.client.cookies[context.server.CSRF_COOKIE] = "csrf-token"

            missing_response = context.client.post(
                f"/users/{USER_CARD_ID}/balance/adjust",
                data={"delta": "5", "note": "Missing CSRF"},
            )
            wrong_response = context.client.post(
                f"/users/{USER_CARD_ID}/balance/adjust",
                data={
                    context.server.CSRF_FIELD: "wrong-token",
                    "delta": "5",
                    "note": "Wrong CSRF",
                },
            )

            self.assertSecurityRedirect(missing_response)
            self.assertSecurityRedirect(wrong_response)
            self.assertIn(
                "Bitte%20Seite%20neu%20laden", missing_response.location or ""
            )
            self.assertIn("Bitte%20Seite%20neu%20laden", wrong_response.location or "")
            self.assertEqual(context.user_balance(), 10.0)

    def test_mutating_admin_post_with_pin_and_csrf_adjusts_balance(self) -> None:
        with admin_test_context() as context:
            context.client.cookies[context.server.DEBUG_COOKIE] = ADMIN_PIN
            context.client.cookies[context.server.CSRF_COOKIE] = "csrf-token"

            response = context.client.post(
                f"/users/{USER_CARD_ID}/balance/adjust",
                data={
                    context.server.CSRF_FIELD: "csrf-token",
                    "delta": "5",
                    "note": "Safety test",
                },
            )

            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.location, "/users")
            self.assertEqual(context.user_balance(), 15.0)
            adjustments = context.database.get_recent_balance_adjustments()
            self.assertEqual(len(adjustments), 1)
            self.assertEqual(adjustments[0].note, "Safety test")

    def test_debug_unlock_accepts_pin_only_with_valid_csrf(self) -> None:
        with admin_test_context() as context:
            no_csrf_response = context.client.post(
                "/debug/unlock",
                data={"pin": ADMIN_PIN},
            )

            context.client.cookies[context.server.CSRF_COOKIE] = "csrf-token"
            wrong_csrf_response = context.client.post(
                "/debug/unlock",
                data={
                    context.server.CSRF_FIELD: "wrong-token",
                    "pin": ADMIN_PIN,
                },
            )

            context.client.cookies.pop(context.server.DEBUG_COOKIE, None)
            context.client.cookies[context.server.CSRF_COOKIE] = "csrf-token"
            valid_response = context.client.post(
                "/debug/unlock",
                data={
                    context.server.CSRF_FIELD: "csrf-token",
                    "pin": ADMIN_PIN,
                },
            )

            self.assertSecurityRedirect(no_csrf_response)
            self.assertSecurityRedirect(wrong_csrf_response)
            self.assertNotEqual(
                no_csrf_response.cookies.get(context.server.DEBUG_COOKIE),
                ADMIN_PIN,
            )
            self.assertNotEqual(
                wrong_csrf_response.cookies.get(context.server.DEBUG_COOKIE),
                ADMIN_PIN,
            )
            self.assertEqual(valid_response.status_code, 303)
            self.assertEqual(valid_response.location, "/debug")
            self.assertEqual(
                context.client.cookies.get(context.server.DEBUG_COOKIE),
                ADMIN_PIN,
            )

    def test_debug_page_shows_pi_ops_status_only_after_unlock(self) -> None:
        with admin_test_context() as context:
            collected = False

            def fake_collect_debug_snapshot():
                nonlocal collected
                collected = True
                return fake_debug_snapshot()

            setattr(
                context.server,
                "collect_debug_snapshot",
                fake_collect_debug_snapshot,
            )

            locked_response = context.client.get("/debug")

            self.assertEqual(locked_response.status_code, 200)
            self.assertFalse(collected)
            self.assertNotIn("Pi-Ops", locked_response.text)

            context.client.cookies[context.server.DEBUG_COOKIE] = ADMIN_PIN
            unlocked_response = context.client.get("/debug")

            self.assertEqual(unlocked_response.status_code, 200)
            self.assertTrue(collected)
            self.assertIn("Pi-Ops", unlocked_response.text)
            self.assertIn("Install-Log", unlocked_response.text)
            self.assertIn("Update-Log", unlocked_response.text)
            self.assertIn("Backup-Timer-Log", unlocked_response.text)
            self.assertIn("2 fehlgeschlagene Units.", unlocked_response.text)
            self.assertIn("install log line", unlocked_response.text)

    def assertSecurityRedirect(self, response: AsgiResponse) -> None:
        self.assertEqual(response.status_code, 303)
        self.assertIsNotNone(response.location)
        self.assertTrue((response.location or "").startswith("/debug?message="))


@dataclass
class AdminTestContext:
    client: AsgiTestClient
    database: ModuleType
    server: ModuleType

    def user_balance(self) -> float:
        user = self.database.get_user(USER_CARD_ID)
        if user is None:
            raise AssertionError(f"Missing test user {USER_CARD_ID}")
        return user.balance


@contextmanager
def admin_test_context() -> Iterator[AdminTestContext]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        db_path = temp_path / "kasse.db"
        pin_path = temp_path / "admin-pin"
        backup_dir = temp_path / "backups"
        pin_path.write_text(ADMIN_PIN, encoding="utf-8")
        backup_dir.mkdir()

        with isolated_database_module(db_path) as database:
            database.init_database()
            database.add_user(
                database.User(
                    card_id=USER_CARD_ID,
                    name="Carolin",
                    balance=10.0,
                )
            )

            with isolated_admin_server(pin_path, backup_dir) as server:
                yield AdminTestContext(
                    client=AsgiTestClient(server.app),
                    database=database,
                    server=server,
                )


def fake_debug_snapshot() -> SimpleNamespace:
    service_status = {
        "kiosk_service": fake_service("aktiv", "kiosk log line"),
        "install_service": fake_service("fehlgeschlagen", "install log line"),
        "update_service": fake_service("inaktiv", "update log line"),
        "backup_service": fake_service("inaktiv", "backup log line"),
        "backup_timer": fake_service("aktiv", "timer log line"),
    }
    return SimpleNamespace(
        hostname="carolins-kasse",
        ip_address="192.168.1.139",
        admin_url="http://192.168.1.139:8080",
        git_branch="codex/pi-ops-safety",
        git_commit="abc1234",
        db_path="/tmp/kasse.db",
        db_exists=True,
        latest_backup="kasse-20260704.db",
        pin_configured=True,
        systemd_state="eingeschränkt",
        failed_units=SimpleNamespace(
            summary="2 fehlgeschlagene Units.",
            output="carolins-install.service loaded failed failed install",
        ),
        logs="kiosk log line",
        ssh_command="ssh kasse@carolins-kasse.local",
        **service_status,
    )


def fake_service(status: str, logs: str) -> SimpleNamespace:
    return SimpleNamespace(status=status, logs=logs)


if __name__ == "__main__":
    unittest.main()
