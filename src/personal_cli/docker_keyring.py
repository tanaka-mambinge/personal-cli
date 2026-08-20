from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from keyring.backend import KeyringBackend


class DockerFileKeyring(KeyringBackend):
    """Small file-backed keyring used only by the Docker development image."""

    priority = 1
    path = Path("/var/lib/personal-cli/credentials.json")

    def _read(self) -> dict[str, dict[str, str]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read Docker credential store: {exc}") from exc

    def _write(self, values: dict[str, dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="credentials.", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(values, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def get_password(self, service: str, username: str) -> str | None:
        return self._read().get(service, {}).get(username)

    def set_password(self, service: str, username: str, password: str) -> None:
        values = self._read()
        values.setdefault(service, {})[username] = password
        self._write(values)

    def delete_password(self, service: str, username: str) -> None:
        values = self._read()
        try:
            del values[service][username]
        except KeyError as exc:
            from keyring.errors import PasswordDeleteError

            raise PasswordDeleteError("credential not found") from exc
        if not values[service]:
            del values[service]
        self._write(values)
