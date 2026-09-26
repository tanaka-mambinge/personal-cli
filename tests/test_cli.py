from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_cli.cli import app
from personal_cli.client import CLIError
from personal_cli.credentials import (
    CredentialError,
    CredentialStore,
    MissingCredentialError,
)


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _plain_output(value: str) -> str:
    return _ANSI_ESCAPE.sub("", value)


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
        self.services: dict[str, dict] = {}

    def _slugify(self, value: str) -> str:
        return value.lower().replace(" ", "-")

    async def list_articles(self, *, status: str | None = None, type_filter: str = "all") -> list[dict]:
        articles = list(self.articles.values())
        if type_filter != "all":
            articles = [article for article in articles if article["type"] == type_filter]
        if status is not None:
            articles = [article for article in articles if article["status"] == status]
        return articles

    async def get_article(self, slug: str, *, preview: str | None = None) -> dict:
        if slug not in self.articles:
            raise CLIError(f"GET /api/v1/articles/{slug} failed: 404 Article not found.", status_code=404)
        return self.articles[slug]

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
        prefix = "work" if self.articles[slug]["type"] == "project" else "writing"
        return {
            "url": f"{base_url}/{prefix}/{slug}?preview=test-token",
            "token": "test-token",
            "expires_at": "2026-01-02T00:00:00Z",
        }

    async def upload_media(self, name: str, path: Path) -> dict:
        media = {"name": name, "url": f"/api/v1/media/{name}"}
        self.media[name] = media
        return media

    async def update_media(self, name: str, path: Path) -> dict:
        return self.media[name]

    async def delete_media(self, name: str) -> dict:
        self.media.pop(name, None)
        return {"deleted": True, "name": name}

    # Services
    async def create_service(self, payload: dict) -> dict:
        slug = payload.get("slug") or self._slugify(payload["title"])
        service = {
            "slug": slug,
            "title": payload["title"],
            "summary": payload["summary"],
            "markdown": payload["markdown"],
            "category": payload["category"],
            "types": payload.get("types", []),
            "offerings": payload.get("offerings", []),
            "examples": payload.get("examples", []),
            "featured": payload.get("featured", False),
            "sort_order": payload.get("sort_order", 0),
        }
        self.services[slug] = service
        return service

    async def list_services(self, *, category: str | None = None) -> list[dict]:
        services = list(self.services.values())
        if category is not None:
            services = [service for service in services if service["category"] == category]
        return services

    async def get_service(self, slug: str) -> dict:
        return self.services[slug]

    async def update_service(self, slug: str, payload: dict) -> dict:
        self.services[slug].update(payload)
        return self.services[slug]

    async def delete_service(self, slug: str) -> dict:
        self.services.pop(slug, None)
        return {"deleted": True, "slug": slug, "deleted_at": "2026-01-01T00:00:00Z"}


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
    assert created["url"] == "http://testsite/writing/cli-blog?preview=test-token"
    assert created["preview_url"] == created["url"]

    list_result = runner.invoke(app, ["article", "list", "--type", "blog", "--json"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["slug"] == "cli-blog"


def test_article_show_supports_drafts_and_published_articles(
    monkeypatch, runner: CliRunner, client: FakeApiClient
) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    draft_create = runner.invoke(
        app,
        [
            "article", "blog", "create",
            "--title", "Draft to Show",
            "--description", "Draft details",
            "--markdown", "# Draft to Show\n\nDraft body.",
            "--json",
        ],
    )
    assert draft_create.exit_code == 0

    draft_show = runner.invoke(app, ["article", "show", "draft-to-show", "--json"])
    assert draft_show.exit_code == 0
    draft = json.loads(draft_show.stdout)
    assert draft["status"] == "draft"
    assert draft["markdown"] == "# Draft to Show\n\nDraft body."
    assert draft["url"] == "http://testsite/writing/draft-to-show?preview=test-token"
    assert draft["preview_url"] == draft["url"]
    draft_show_text = runner.invoke(app, ["article", "show", "draft-to-show"])
    assert draft_show_text.exit_code == 0
    assert "'status': 'draft'" in draft_show_text.stdout

    published_create = runner.invoke(
        app,
        [
            "article", "blog", "create",
            "--title", "Published to Show",
            "--description", "Published details",
            "--markdown", "# Published to Show\n\nPublished body.",
            "--status", "published",
            "--json",
        ],
    )
    assert published_create.exit_code == 0

    published_show = runner.invoke(app, ["article", "show", "published-to-show", "--json"])
    assert published_show.exit_code == 0
    published = json.loads(published_show.stdout)
    assert published["status"] == "published"
    assert published["markdown"] == "# Published to Show\n\nPublished body."
    assert published["url"] == "http://testsite/writing/published-to-show"

    missing_show = runner.invoke(app, ["article", "show", "missing-article", "--json"])
    assert missing_show.exit_code == 1
    assert "GET /api/v1/articles/missing-article failed: 404 Article not found." in missing_show.stderr


def test_project_cli_smoke(monkeypatch, runner: CliRunner, client: FakeApiClient) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    create_result = runner.invoke(
        app,
        [
            "article", "project", "create",
            "--title", "CLI Project",
            "--description", "Created from the CLI",
            "--cover-image", "cli-project-cover",
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
    assert created["url"] == "http://testsite/work/cli-project?preview=test-token"

    list_result = runner.invoke(app, ["article", "list", "--type", "project", "--json"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["slug"] == "cli-project"

    publish_result = runner.invoke(app, ["article", "publish", "cli-project", "--published-by", "agent", "--json"])
    assert publish_result.exit_code == 0
    published = json.loads(publish_result.stdout)
    assert published["status"] == "published"
    assert published["url"] == "http://testsite/work/cli-project"

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
    assert unarchived["url"] == "http://testsite/work/cli-project"

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

def test_project_cli_requires_cover_image(monkeypatch, runner: CliRunner, client: FakeApiClient) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))
    result = runner.invoke(
        app,
        [
            "article", "project", "create",
            "--title", "Missing Cover",
            "--description", "This should fail",
            "--markdown", "# Missing Cover",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option '--cover-image'" in _plain_output(result.output)

    create_result = runner.invoke(
        app,
        [
            "article", "project", "create",
            "--title", "Covered Project",
            "--description", "This has a cover",
            "--cover-image", "covered-project",
            "--markdown", "# Covered Project",
        ],
    )
    assert create_result.exit_code == 0

    clear_result = runner.invoke(app, ["article", "update", "covered-project", "--clear-cover-image"])
    assert clear_result.exit_code != 0
    assert "Projects must have a cover image" in clear_result.output


def test_service_cli_lifecycle(monkeypatch, runner: CliRunner, client: FakeApiClient) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))

    create_result = runner.invoke(
        app,
        [
            "service", "create",
            "--title", "Web",
            "--summary", "Websites and web apps.",
            "--category", "Web",
            "--type", "Static websites",
            "--type", "Web apps with a database",
            "--offering", "Static websites|Fast, focused sites for a clear message.|/stock/web.webp",
            "--example", "Example project|/work/example-project",
            "--markdown", "## Web\n\nDetails.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0
    created = json.loads(create_result.stdout)
    assert created["slug"] == "web"
    assert created["url"] == "http://testsite/services?service=web"
    assert created["types"] == ["Static websites", "Web apps with a database"]
    assert created["offerings"][0]["title"] == "Static websites"

    update_result = runner.invoke(app, ["service", "update", "web", "--clear-examples", "--json"])
    assert update_result.exit_code == 0
    assert json.loads(update_result.stdout)["examples"] == []

    list_result = runner.invoke(app, ["service", "list", "--category", "Web", "--json"])
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)[0]["url"] == "http://testsite/services?service=web"


def test_service_cli_does_not_expose_homepage_options(runner: CliRunner) -> None:
    create_help = runner.invoke(app, ["service", "create", "--help"])
    update_help = runner.invoke(app, ["service", "update", "--help"])

    assert create_help.exit_code == 0
    assert update_help.exit_code == 0
    for output in (create_help.output, update_help.output):
        assert "--featured" not in output
        assert "--home-title" not in output
        assert "--home-summary" not in output
        assert "--home-next-step" not in output
        assert "--home-sort-order" not in output


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


def test_authentication_required_is_structured_and_does_not_start_setup(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
    credential_store: FakeKeyringBackend,
) -> None:
    credential_store.delete_password("personal-cli", "default")

    setup_calls: list[int] = []
    monkeypatch.setattr("personal_cli.cli.run_setup", lambda *args, **kwargs: setup_calls.append(1))
    monkeypatch.setattr("personal_cli.cli.build_client", lambda *args, **kwargs: (_ for _ in ()).throw(MissingCredentialError("missing")))

    for args in (["article", "list"], ["article", "list", "--json"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 2
        error = json.loads(result.stderr.strip())
        assert error["error"]["code"] == "authentication_required"
        assert error["error"]["setup_command"] == "blog-cli keys setup"
        assert "http" not in result.stderr

    assert not setup_calls


def test_keys_setup_runs_attached_setup_server(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
    credential_store: FakeKeyringBackend,
) -> None:
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

    result = runner.invoke(app, ["keys", "setup", "--json"])

    assert result.exit_code == 0
    assert setup_calls == [1]
    assert "http://127.0.0.1:3233/setup?token=fake" in result.stderr
    assert json.loads(result.stdout)["configured"] is True


def test_keys_revoke_removes_stored_credentials(
    runner: CliRunner,
    credential_store: FakeKeyringBackend,
) -> None:
    result = runner.invoke(app, ["keys", "revoke", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "revoked": True,
        "message": "Credentials revoked.",
    }
    assert credential_store.get_password("personal-cli", "default") is None


def test_json_credential_store_error_is_structured(
    monkeypatch: pytest.MonkeyPatch,
    runner: CliRunner,
) -> None:
    def _credential_store_failure(server_url=None, insecure=False):
        raise CredentialError("Could not access the operating system credential store.")

    monkeypatch.setattr("personal_cli.cli.build_client", _credential_store_failure)

    result = runner.invoke(app, ["article", "list", "--json"])

    assert result.exit_code == 2
    error = json.loads(result.stderr.strip())
    assert error == {
        "error": {
            "code": "credential_store_unavailable",
            "message": "Could not access the operating system credential store.",
        }
    }
    assert "Traceback" not in result.output
