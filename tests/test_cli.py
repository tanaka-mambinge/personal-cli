from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_cli.cli import app
from personal_cli.credentials import (
    CredentialError,
    CredentialStore,
    MissingCredentialError,
)


class FakeKeyringBackend:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}

    def set_password(self, service: str, account: str, password: str) -> None:
        self._store.setdefault(service, {})[account] = password

    def get_password(self, service: str, account: str) -> str | None:
        return self._store.get(service, {}).get(account)

    def delete_password(self, service: str, account: str) -> None:
        if account not in self._store.get(service, {}):
            from keyring.errors import PasswordDeleteError

            raise PasswordDeleteError("not found")
        del self._store[service][account]


class FakeApiClient:
    def __init__(self) -> None:
        self.articles: dict[str, dict] = {}
        self.media: dict[str, dict] = {}

    async def list_articles(self, *, status: str | None = None, type_filter: str = "all") -> list[dict]:
        articles = list(self.articles.values())
        if type_filter != "all":
            articles = [article for article in articles if article["type"] == type_filter]
        if status is not None:
            articles = [article for article in articles if article["status"] == status]
        return articles

    async def create_article(self, payload: dict) -> dict:
        slug = payload["slug"] or payload["title"].lower().replace(" ", "-")
        article = {
            "slug": slug,
            "title": payload["title"],
            "description": payload["description"],
            "markdown": payload["markdown"],
            "type": payload["type"],
            "status": payload["status"],
            "tags": payload["tags"],
            "pinned": payload["pinned"],
            "sort_order": payload["sort_order"],
            "cover_image": payload["cover_image"],
            "deleted": False,
            "deleted_at": None,
        }
        self.articles[slug] = article
        return article

    async def publish_article(self, slug: str, payload: dict | None = None) -> dict:
        article = self.articles[slug]
        article["status"] = "published"
        return article

    async def delete_article(self, slug: str) -> dict:
        article = self.articles[slug]
        article["deleted"] = True
        article["deleted_at"] = "2026-01-01T00:00:00Z"
        return {"deleted": True, "slug": slug, "deleted_at": article["deleted_at"]}

    async def unarchive_article(self, slug: str) -> dict:
        article = self.articles[slug]
        article["deleted"] = False
        article["deleted_at"] = None
        return article

    async def generate_preview(self, slug: str, *, ttl_hours: int, base_url: str) -> dict:
        return {"url": f"{base_url}/work/{slug}?token=test-token", "token": "test-token"}

    async def revoke_preview(self, slug: str) -> dict:
        return {"revoked": 1}

    async def upload_media(self, name: str, path: Path) -> dict:
        media = {"name": name, "url": f"/api/v1/media/{name}"}
        self.media[name] = media
        return media

    async def update_media(self, name: str, path: Path) -> dict:
        return self.media[name]

    async def delete_media(self, name: str) -> dict:
        self.media.pop(name, None)
        return {"deleted": True, "name": name}


VALID_CREDS = {
    "server_url": "http://testserver",
    "api_key": "test-key",
    "site_url": "http://testsite",
}


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def fake_backend() -> FakeKeyringBackend:
    return FakeKeyringBackend()


@pytest.fixture(autouse=True)
def credential_store(monkeypatch: pytest.MonkeyPatch, fake_backend: FakeKeyringBackend) -> FakeKeyringBackend:
    """Every CredentialStore() instance uses the fake in-memory backend."""
    real_init = CredentialStore.__init__

    def _init(self, backend=None):
        real_init(self, backend=fake_backend)

    monkeypatch.setattr(CredentialStore, "__init__", _init)
    return fake_backend


@pytest.fixture(autouse=True)
def seeded_credentials(credential_store: FakeKeyringBackend) -> None:
    """Pre-seed valid credentials so commands can build a client."""
    credential_store.set_password(
        "personal-cli",
        "default",
        json.dumps(VALID_CREDS),
    )


@pytest.fixture(autouse=True)
def stub_run_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never start the real setup server during tests."""
    def _noop_run_setup(*args, **kwargs):
        raise AssertionError("run_setup was called during a test that pre-seeded credentials.")

    monkeypatch.setattr("personal_cli.cli.run_setup", _noop_run_setup)


@pytest.fixture()
def client() -> FakeApiClient:
    return FakeApiClient()


def _build_client_mock(client: FakeApiClient):
    return lambda server_url=None, insecure=False: client


def test_blog_cli_smoke(monkeypatch, runner: CliRunner, client: FakeApiClient) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    create_result = runner.invoke(
        app,
        [
            "article", "blog", "create",
            "--title", "CLI Blog",
            "--description", "Created from the CLI",
            "--markdown", "# CLI Blog\n\nBody.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0
    created = json.loads(create_result.stdout)
    assert created["slug"] == "cli-blog"
    assert created["type"] == "blog"
    assert created["tags"] == []

    list_result = runner.invoke(app, ["article", "list", "--type", "blog", "--json"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["slug"] == "cli-blog"


def test_project_cli_smoke(monkeypatch, runner: CliRunner, client: FakeApiClient) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    create_result = runner.invoke(
        app,
        [
            "article", "project", "create",
            "--title", "CLI Project",
            "--description", "Created from the CLI",
            "--markdown", "# CLI Project\n\nBody.",
            "--tag", "build",
            "--pinned",
            "--sort-order", "1",
            "--json",
        ],
    )
    assert create_result.exit_code == 0
    created = json.loads(create_result.stdout)
    assert created["slug"] == "cli-project"
    assert created["type"] == "project"
    assert created["pinned"] is True
    assert created["sort_order"] == 1
    assert "build" in created["tags"]

    list_result = runner.invoke(app, ["article", "list", "--type", "project", "--json"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["slug"] == "cli-project"

    publish_result = runner.invoke(app, ["article", "publish", "cli-project", "--published-by", "agent", "--json"])
    assert publish_result.exit_code == 0
    assert json.loads(publish_result.stdout)["status"] == "published"

    delete_result = runner.invoke(app, ["article", "delete", "cli-project", "--json"])
    assert delete_result.exit_code == 0
    deleted = json.loads(delete_result.stdout)
    assert deleted["deleted"] is True
    assert deleted["slug"] == "cli-project"
    assert deleted["deleted_at"]

    unarchive_result = runner.invoke(app, ["article", "unarchive", "cli-project", "--json"])
    assert unarchive_result.exit_code == 0
    unarchived = json.loads(unarchive_result.stdout)
    assert unarchived["slug"] == "cli-project"
    assert unarchived["status"] == "published"

    all_list = runner.invoke(app, ["article", "list", "--json"])
    assert all_list.exit_code == 0
    assert json.loads(all_list.stdout)[0]["slug"] == "cli-project"

    preview_result = runner.invoke(
        app,
        ["article", "preview", "cli-project", "--site-url", "http://testserver", "--json"],
    )
    assert preview_result.exit_code == 0
    preview = json.loads(preview_result.stdout)
    assert preview["url"].startswith("http://testserver/work/cli-project")
    assert preview["token"]

    revoke_result = runner.invoke(app, ["article", "revoke-preview", "cli-project", "--json"])
    assert revoke_result.exit_code == 0
    assert json.loads(revoke_result.stdout)["revoked"] == 1


def test_media_cli_smoke(monkeypatch, runner: CliRunner, client: FakeApiClient, tmp_path: Path) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    media_file = tmp_path / "test-image.png"
    media_file.write_bytes(b"fake-image-data")
    upload_result = runner.invoke(app, ["media", "upload", "--name", "hero-image", str(media_file), "--json"])
    assert upload_result.exit_code == 0
    uploaded = json.loads(upload_result.stdout)
    assert uploaded["name"] == "hero-image"
    assert uploaded["url"] == "/api/v1/media/hero-image"

    updated_file = tmp_path / "test-image-v2.png"
    updated_file.write_bytes(b"fake-image-data-v2")
    update_result = runner.invoke(app, ["media", "update", "--name", "hero-image", str(updated_file), "--json"])
    assert update_result.exit_code == 0
    assert json.loads(update_result.stdout)["name"] == "hero-image"

    delete_result = runner.invoke(app, ["media", "delete", "--name", "hero-image", "--json"])
    assert delete_result.exit_code == 0
    deleted = json.loads(delete_result.stdout)
    assert deleted["deleted"] is True
    assert deleted["name"] == "hero-image"


def test_keys_show_reports_stored_credentials(runner: CliRunner) -> None:
    result = runner.invoke(app, ["keys", "show", "--json"])
    assert result.exit_code == 0
    shown = json.loads(result.stdout)
    assert shown["server_url"] == "http://testserver"
    assert shown["site_url"] == "http://testsite"
    assert "api_key" in shown
    assert shown["api_key"] != "test-key"


def test_keys_revoke_clears_credentials(
    runner: CliRunner, credential_store: FakeKeyringBackend
) -> None:
    revoke_result = runner.invoke(app, ["keys", "revoke", "--json"])
    assert revoke_result.exit_code == 0
    revoked = json.loads(revoke_result.stdout)
    assert revoked["revoked"] is True

    assert credential_store.get_password("personal-cli", "default") is None

    second_revoke = runner.invoke(app, ["keys", "revoke", "--json"])
    assert second_revoke.exit_code == 0
    assert json.loads(second_revoke.stdout)["revoked"] is False


def test_keys_show_when_empty(runner: CliRunner, credential_store: FakeKeyringBackend) -> None:
    credential_store.delete_password("personal-cli", "default")
    result = runner.invoke(app, ["keys", "show", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"stored": False}


def test_missing_credentials_triggers_setup(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
    credential_store: FakeKeyringBackend,
) -> None:
    credential_store.delete_password("personal-cli", "default")

    setup_calls: list[int] = []

    def _fake_run_setup(store, output=None, prompt=""):
        output(f"{prompt}: http://127.0.0.1:3233/setup?token=fake")
        setup_calls.append(1)
        store.add(
            server_url=VALID_CREDS["server_url"],
            api_key=VALID_CREDS["api_key"],
            site_url=VALID_CREDS["site_url"],
        )

    monkeypatch.setattr("personal_cli.cli.run_setup", _fake_run_setup)

    attempts: list[int] = []

    def _flaky_build_client(server_url=None, insecure=False):
        attempts.append(1)
        if len(attempts) == 1:
            raise MissingCredentialError("missing")
        return FakeApiClient()

    monkeypatch.setattr("personal_cli.cli.build_client", _flaky_build_client)
    monkeypatch.setattr("personal_cli.cli.run", lambda coro: __import__("asyncio").run(coro))

    result = runner.invoke(app, ["article", "list", "--json"])
    assert setup_calls, "run_setup should have been called"
    assert result.exit_code == 0
