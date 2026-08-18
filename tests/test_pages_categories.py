from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_cli.cli import app
from personal_cli.credentials import CredentialStore


VALID_CREDS = {
    "server_url": "http://testserver",
    "api_key": "test-key",
    "site_url": "http://testsite",
}


class FakeApiClient:
    def __init__(self) -> None:
        self.categories: dict[str, dict] = {}
        self.pages: dict[str, dict] = {}
        self._counter = 0

    @staticmethod
    def _slugify(value: str) -> str:
        return value.lower().replace(" ", "-")

    async def create_category(self, payload: dict) -> dict:
        slug = self._slugify(payload["name"])
        category = {
            "id": slug,
            "slug": slug,
            "name": payload["name"],
            "icon": payload.get("icon"),
            "description": payload.get("description"),
            "sort_order": payload.get("sort_order", 0),
            "created_at": "2026-01-01T00:00:00Z",
            "page_count": 0,
        }
        self.categories[slug] = category
        return category

    async def list_categories(self) -> list[dict]:
        return list(self.categories.values())

    async def get_category(self, slug: str) -> dict:
        return self.categories[slug]

    async def update_category(self, slug: str, payload: dict) -> dict:
        category = self.categories[slug]
        for key, value in payload.items():
            category[key] = value
        return category

    async def delete_category(self, slug: str) -> dict:
        if any(p["category_slug"] == slug for p in self.pages.values()):
            raise Exception("Category in use")
        self.categories.pop(slug, None)
        return {"deleted": True, "slug": slug, "deleted_at": "2026-01-01T00:00:00Z"}

    async def create_page(self, payload: dict) -> dict:
        slug = payload.get("slug") or self._slugify(payload["title"])
        if slug in self.pages:
            self._counter += 1
            slug = f"{slug}-{self._counter}"
        page = {
            "id": slug,
            "slug": slug,
            "title": payload["title"],
            "description": payload["description"],
            "markdown": payload["markdown"],
            "category_slug": payload["category_slug"],
            "sort_order": payload.get("sort_order", 0),
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        self.pages[slug] = page
        return page

    async def list_pages(self, *, category: str | None = None) -> list[dict]:
        pages = list(self.pages.values())
        if category is not None:
            pages = [p for p in pages if p["category_slug"] == category]
        return pages

    async def get_page(self, slug: str) -> dict:
        return self.pages[slug]

    async def update_page(self, slug: str, payload: dict) -> dict:
        page = self.pages[slug]
        for key, value in payload.items():
            page[key] = value
        return page

    async def delete_page(self, slug: str) -> dict:
        self.pages.pop(slug, None)
        return {"deleted": True, "slug": slug, "deleted_at": "2026-01-01T00:00:00Z"}


class FakeKeyringBackend:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}

    def set_password(self, service: str, account: str, password: str) -> None:
        self._store.setdefault(service, {})[account] = password

    def get_password(self, service: str, account: str) -> str | None:
        return self._store.get(service, {}).get(account)

    def delete_password(self, service: str, account: str) -> None:
        self._store.get(service, {}).pop(account, None)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def credential_store(monkeypatch: pytest.MonkeyPatch) -> FakeKeyringBackend:
    fake_backend = FakeKeyringBackend()
    real_init = CredentialStore.__init__

    def _init(self, backend=None):
        real_init(self, backend=fake_backend)

    monkeypatch.setattr(CredentialStore, "__init__", _init)
    store = CredentialStore(backend=fake_backend)
    store.add(
        server_url=VALID_CREDS["server_url"],
        api_key=VALID_CREDS["api_key"],
        site_url=VALID_CREDS["site_url"],
    )
    return fake_backend


@pytest.fixture(autouse=True)
def stub_run_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    def _noop(*args, **kwargs):
        raise AssertionError("run_setup called during test")

    monkeypatch.setattr("personal_cli.cli.run_setup", _noop)


def _build_client_mock(client):
    return lambda server_url=None, insecure=False: client


def test_category_lifecycle(monkeypatch, runner):
    client = FakeApiClient()
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))

    create = runner.invoke(
        app,
        [
            "category", "create",
            "--name", "Ideas",
            "--icon", "bulb",
            "--description", "Captured ideas",
            "--json",
        ],
    )
    assert create.exit_code == 0
    body = json.loads(create.stdout)
    assert body["slug"] == "ideas"
    assert body["name"] == "Ideas"
    assert body["icon"] == "bulb"

    listing = runner.invoke(app, ["category", "list", "--json"])
    assert listing.exit_code == 0
    assert json.loads(listing.stdout)[0]["slug"] == "ideas"

    show = runner.invoke(app, ["category", "show", "ideas", "--json"])
    assert show.exit_code == 0
    assert json.loads(show.stdout)["name"] == "Ideas"

    update = runner.invoke(
        app,
        ["category", "update", "ideas", "--name", "Idea Box", "--icon", "lightbulb", "--json"],
    )
    assert update.exit_code == 0
    updated = json.loads(update.stdout)
    assert updated["name"] == "Idea Box"
    assert updated["icon"] == "lightbulb"


def test_page_lifecycle(monkeypatch, runner):
    client = FakeApiClient()
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(client))

    runner.invoke(app, ["category", "create", "--name", "Ideas", "--json"])

    create = runner.invoke(
        app,
        [
            "page", "create",
            "--title", "An idea",
            "--description", "A captured thought",
            "--category", "ideas",
            "--markdown", "# An idea\n\nUse <Callout type=\"info\">note</Callout>",
            "--json",
        ],
    )
    assert create.exit_code == 0
    page = json.loads(create.stdout)
    assert page["slug"] == "an-idea"
    assert page["category_slug"] == "ideas"

    listing = runner.invoke(app, ["page", "list", "--json"])
    assert listing.exit_code == 0
    assert json.loads(listing.stdout)[0]["slug"] == "an-idea"

    filtered = runner.invoke(
        app, ["page", "list", "--category", "ideas", "--json"],
    )
    assert filtered.exit_code == 0
    assert json.loads(filtered.stdout)[0]["slug"] == "an-idea"

    show = runner.invoke(app, ["page", "show", "an-idea", "--json"])
    assert show.exit_code == 0
    assert json.loads(show.stdout)["title"] == "An idea"

    update = runner.invoke(
        app, ["page", "update", "an-idea", "--description", "Refined", "--json"],
    )
    assert update.exit_code == 0
    assert json.loads(update.stdout)["description"] == "Refined"

    delete = runner.invoke(app, ["page", "delete", "an-idea", "--json"])
    assert delete.exit_code == 0
    assert json.loads(delete.stdout)["deleted"] is True


def test_skill_path_and_install(monkeypatch, runner, tmp_path):
    target = tmp_path / "skills"
    path_result = runner.invoke(app, ["skill", "path", "--dir", str(target), "--json"])
    assert path_result.exit_code == 0
    assert json.loads(path_result.stdout)["path"].endswith("content-pipeline")

    install = runner.invoke(app, ["skill", "install", "--dir", str(target), "--json"])
    assert install.exit_code == 0
    installed = json.loads(install.stdout)
    assert installed["installed"] is True
    skill_root = tmp_path / "skills" / "content-pipeline"
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "references" / "pages.md").exists()
    assert (skill_root / "agents" / "openai.yaml").exists()

    uninstall = runner.invoke(app, ["skill", "uninstall", "--dir", str(target), "--json"])
    assert uninstall.exit_code == 0
    assert json.loads(uninstall.stdout)["uninstalled"] is True
    assert not skill_root.exists()
