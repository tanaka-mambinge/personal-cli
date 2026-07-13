from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from personal_cli.client import ArticleApiClient
from personal_cli.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _build_client_mock(live_server: str):
    return lambda server_url=None, insecure=False: ArticleApiClient(live_server)


def test_blog_cli_smoke(monkeypatch, runner: CliRunner, live_server: str) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(live_server))

    create_result = runner.invoke(
        app,
        [
            "article",
            "blog",
            "create",
            "--title",
            "CLI Blog",
            "--description",
            "Created from the CLI",
            "--markdown",
            "# CLI Blog\n\nBody.",
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
    listed = json.loads(list_result.stdout)
    assert listed[0]["slug"] == "cli-blog"



def test_project_cli_smoke(monkeypatch, runner: CliRunner, live_server: str) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(live_server))

    create_result = runner.invoke(
        app,
        [
            "article",
            "project",
            "create",
            "--title",
            "CLI Project",
            "--description",
            "Created from the CLI",
            "--markdown",
            "# CLI Project\n\nBody.",
            "--tag",
            "build",
            "--pinned",
            "--sort-order",
            "1",
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
    listed = json.loads(list_result.stdout)
    assert listed[0]["slug"] == "cli-project"

    publish_result = runner.invoke(app, ["article", "publish", "cli-project", "--published-by", "agent", "--json"])
    assert publish_result.exit_code == 0
    published = json.loads(publish_result.stdout)
    assert published["status"] == "published"

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
    revoked = json.loads(revoke_result.stdout)
    assert revoked["revoked"] == 1


def test_media_cli_smoke(monkeypatch, runner: CliRunner, live_server: str, tmp_path) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(live_server))

    media_file = tmp_path / "test-image.png"
    media_file.write_bytes(b"fake-image-data")

    upload_result = runner.invoke(
        app,
        [
            "media",
            "upload",
            "--name",
            "hero-image",
            str(media_file),
            "--json",
        ],
    )
    assert upload_result.exit_code == 0
    uploaded = json.loads(upload_result.stdout)
    assert uploaded["name"] == "hero-image"
    assert uploaded["url"] == "/api/v1/media/hero-image"

    updated_file = tmp_path / "test-image-v2.png"
    updated_file.write_bytes(b"fake-image-data-v2")

    update_result = runner.invoke(
        app,
        [
            "media",
            "update",
            "--name",
            "hero-image",
            str(updated_file),
            "--json",
        ],
    )
    assert update_result.exit_code == 0
    updated = json.loads(update_result.stdout)
    assert updated["name"] == "hero-image"

    delete_result = runner.invoke(
        app,
        [
            "media",
            "delete",
            "--name",
            "hero-image",
            "--json",
        ],
    )
    assert delete_result.exit_code == 0
    deleted = json.loads(delete_result.stdout)
    assert deleted["deleted"] is True
    assert deleted["name"] == "hero-image"
