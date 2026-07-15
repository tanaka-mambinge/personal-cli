from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from personal_cli.cli import app


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


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


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
