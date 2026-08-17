from __future__ import annotations

import json
import os
from typing import Any

import keyring
from keyring.errors import PasswordDeleteError


SERVICE_NAME = "personal-cli"
ACCOUNT_NAME = "default"
_REQUIRED_FIELDS = ("server_url", "api_key", "site_url")


class CredentialError(RuntimeError):
    """An actionable error accessing the operating system credential store."""


class MissingCredentialError(CredentialError):
    """No credentials have been stored yet."""


def _service_name() -> str:
    if os.environ.get("PERSONAL_CLI_ENV", "").strip().lower() == "dev":
        return f"{SERVICE_NAME}-dev"
    return SERVICE_NAME


def _normalize(value: str) -> str:
    return value.strip().strip("\"'").strip()


class CredentialStore:
    """Store the personal-cli server credentials in the OS credential store.

    The three values (server_url, api_key, site_url) are serialized as JSON
    under a single keyring entry so they stay atomic. The service name is
    suffixed with ``-dev`` when ``PERSONAL_CLI_ENV=dev`` so local testing
    never touches production credentials.
    """

    def __init__(self, backend: Any | None = None) -> None:
        self._backend = backend or keyring

    def add(self, *, server_url: str, api_key: str, site_url: str) -> None:
        server_url = _normalize(server_url)
        api_key = _normalize(api_key)
        site_url = _normalize(site_url)
        if not server_url:
            raise CredentialError("Server URL cannot be empty.")
        if not api_key:
            raise CredentialError("API key cannot be empty.")
        if not site_url:
            raise CredentialError("Site URL cannot be empty.")
        payload = json.dumps(
            {"server_url": server_url, "api_key": api_key, "site_url": site_url}
        )
        try:
            self._backend.set_password(_service_name(), ACCOUNT_NAME, payload)
        except Exception as exc:
            raise CredentialError(
                "Could not access the operating system credential store. "
                "Configure a native keyring backend and try again."
            ) from exc

    def get(self) -> tuple[str, str, str]:
        try:
            raw = self._backend.get_password(_service_name(), ACCOUNT_NAME)
        except Exception as exc:
            raise CredentialError(
                "Could not access the operating system credential store. "
                "Configure a native keyring backend and try again."
            ) from exc
        if not raw:
            raise MissingCredentialError(
                "No credentials are stored. Run a command to trigger the setup page."
            )
        try:
            values = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CredentialError("Stored credentials are corrupted.") from exc
        missing = [field for field in _REQUIRED_FIELDS if not values.get(field)]
        if missing:
            raise MissingCredentialError(
                f"Stored credentials are incomplete (missing: {', '.join(missing)})."
            )
        return values["server_url"], values["api_key"], values["site_url"]

    def remove(self) -> bool:
        try:
            self._backend.delete_password(_service_name(), ACCOUNT_NAME)
        except PasswordDeleteError:
            return False
        except Exception as exc:
            raise CredentialError(
                "Could not access the operating system credential store. "
                "Configure a native keyring backend and try again."
            ) from exc
        return True
