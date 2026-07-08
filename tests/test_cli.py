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


def test_article_cli_smoke(monkeypatch, runner: CliRunner, live_server: str) -> None:
    monkeypatch.setattr("personal_cli.cli.build_client", _build_client_mock(live_server))

    create_result = runner.invoke(
        app,
        [
            "article",
            "create",
            "--title",
            "CLI Article",
            "--description",
            "Created from the CLI",
            "--type",
            "blog",
            "--markdown",
            "# CLI Article\n\nBody.",
            "--tag",
            "build",
            "--tag",
            "indie",
            "--json",
        ],
    )
    assert create_result.exit_code == 0
    created = json.loads(create_result.stdout)
    assert created["slug"] == "cli-article"
    assert created["type"] == "blog"

    list_result = runner.invoke(app, ["article", "list", "--type", "blog", "--json"])
    assert list_result.exit_code == 0
    listed = json.loads(list_result.stdout)
    assert listed[0]["slug"] == "cli-article"

    publish_result = runner.invoke(app, ["article", "publish", "cli-article", "--published-by", "agent", "--json"])
    assert publish_result.exit_code == 0
    published = json.loads(publish_result.stdout)
    assert published["status"] == "published"

    delete_result = runner.invoke(app, ["article", "delete", "cli-article", "--json"])
    assert delete_result.exit_code == 0
    deleted = json.loads(delete_result.stdout)
    assert deleted["deleted"] is True
    assert deleted["slug"] == "cli-article"
    assert deleted["deleted_at"]

    unarchive_result = runner.invoke(app, ["article", "unarchive", "cli-article", "--json"])
    assert unarchive_result.exit_code == 0
    unarchived = json.loads(unarchive_result.stdout)
    assert unarchived["slug"] == "cli-article"
    assert unarchived["status"] == "published"

    empty_list = runner.invoke(app, ["article", "list", "--json"])
    assert empty_list.exit_code == 0
    assert json.loads(empty_list.stdout)[0]["slug"] == "cli-article"


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
