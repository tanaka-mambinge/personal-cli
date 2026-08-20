from __future__ import annotations

import json
import threading
from urllib.parse import urlencode

import httpx

from personal_cli.credentials import CredentialStore
from personal_cli.setup_server import SETUP_PATH, _SetupServer


class FakeKeyringBackend:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str) -> str | None:
        return self.values.get((service, account))

    def set_password(self, service: str, account: str, password: str) -> None:
        self.values[(service, account)] = password

    def delete_password(self, service: str, account: str) -> None:
        self.values.pop((service, account), None)


def _start_server(store: CredentialStore, token: str) -> tuple[_SetupServer, threading.Thread, str]:
    server = _SetupServer(store, token, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}{SETUP_PATH}?{urlencode({'token': token})}"
    return server, thread, url


def test_setup_page_can_be_reloaded_and_preserves_fields_after_validation_error(monkeypatch) -> None:
    backend = FakeKeyringBackend()
    store = CredentialStore(backend=backend)
    monkeypatch.setattr("personal_cli.setup_server._validate", lambda *_: "bad credentials")
    server, thread, url = _start_server(store, "stable-token")
    try:
        first = httpx.get(url)
        second = httpx.get(url)
        assert first.status_code == 200
        assert second.status_code == 200

        response = httpx.post(
            url,
            data={
                "server_url": "https://api.example.com",
                "api_key": "wrong",
                "site_url": "https://example.com",
            },
        )
        assert response.status_code == 400
        assert "https://api.example.com" in response.text
        assert "https://example.com" in response.text
        assert httpx.get(url).status_code == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_setup_page_saves_credentials_and_stops_after_success(monkeypatch) -> None:
    backend = FakeKeyringBackend()
    store = CredentialStore(backend=backend)
    monkeypatch.setattr("personal_cli.setup_server._validate", lambda *_: None)
    server, thread, url = _start_server(store, "save-token")
    try:
        response = httpx.post(
            url,
            data={
                "server_url": "https://api.example.com",
                "api_key": "secret",
                "site_url": "https://example.com",
            },
        )
        assert response.status_code == 200
        assert json.loads(backend.values[("personal-cli", "default")]) == {
            "server_url": "https://api.example.com",
            "api_key": "secret",
            "site_url": "https://example.com",
        }
        thread.join(timeout=2)
        assert not thread.is_alive()
    finally:
        server.server_close()
