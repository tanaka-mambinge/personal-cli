from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from personal_cli.client import ArticleApiClient, CLIError, get_default_config
from personal_cli.formatting import emit_result, read_markdown_from_source

app = typer.Typer(help="Agent-facing article CLI.")
article_app = typer.Typer(help="Manage articles.")
media_app = typer.Typer(help="Manage media uploads.")

app.add_typer(article_app, name="article")
app.add_typer(media_app, name="media")


def build_client(server_url: str | None = None, insecure: bool = False) -> ArticleApiClient:
    url, api_key, _ = get_default_config()
    return ArticleApiClient(server_url or url, api_key=api_key, verify=not insecure)


def run(coro):
    return asyncio.run(coro)


@article_app.command("list")
def article_list(
    type_filter: str = typer.Option("all", "--type", help="all, blog, or project."),
    status: str | None = typer.Option(None, "--status", help="Filter by article status."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        articles = run(client.list_articles(status=status, type_filter=type_filter))
        emit_result(articles, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("show")
def article_show(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        article = run(client.get_article(slug))
        emit_result(article, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("create")
def article_create(
    title: str = typer.Option(..., "--title", help="Article title."),
    description: str = typer.Option(..., "--description", help="Short summary."),
    slug: str | None = typer.Option(None, "--slug", help="Optional slug override."),
    tag: list[str] = typer.Option([], "--tag", help="Repeat for each tag."),
    article_type: str = typer.Option(..., "--type", help="blog or project."),
    status: str = typer.Option("draft", "--status", help="draft or published."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        body = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        client = build_client(server_url, insecure=insecure)
        payload = {
            "title": title,
            "description": description,
            "slug": slug,
            "tags": tag,
            "type": article_type,
            "status": status,
            "markdown": body,
        }
        article = run(client.create_article(payload))
        emit_result(article, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("update")
def article_update(
    slug: str,
    title: str | None = typer.Option(None, "--title", help="New title."),
    description: str | None = typer.Option(None, "--description", help="New summary."),
    tag: list[str] | None = typer.Option(None, "--tag", help="Repeat for each tag."),
    article_type: str | None = typer.Option(None, "--type", help="blog or project."),
    status: str | None = typer.Option(None, "--status", help="draft or published."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if tag is not None:
            payload["tags"] = tag
        if article_type is not None:
            payload["type"] = article_type
        if status is not None:
            payload["status"] = status
        if markdown is not None or markdown_file is not None:
            payload["markdown"] = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        article = run(client.update_article(slug, payload))
        emit_result(article, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("publish")
def article_publish(
    slug: str,
    published_by: str | None = typer.Option(None, "--published-by", help="Who published the article."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        article = run(client.publish_article(slug, {"published_by": published_by} if published_by else None))
        emit_result(article, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("delete")
def article_delete(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_article(slug))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("unarchive")
def article_unarchive(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        article = run(client.unarchive_article(slug))
        emit_result(article, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("preview")
def article_preview(
    slug: str,
    ttl_hours: int = typer.Option(24, "--ttl-hours", help="Hours until the preview link expires."),
    site_url: str | None = typer.Option(None, "--site-url", help="Base URL of the personal site."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        _, _, default_site_url = get_default_config()
        resolved_site_url = site_url or default_site_url
        client = build_client(server_url, insecure=insecure)
        result = run(client.generate_preview(slug, ttl_hours=ttl_hours, base_url=resolved_site_url))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("tag-list")
@article_app.command("tags")
def tag_list(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.list_tags(slug))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("tag-add")
def tag_add(
    slug: str,
    tag: list[str] = typer.Option(..., "--tag", help="Tag to attach. Repeat for multiple."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.attach_tags(slug, tag))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("tag-remove")
def tag_remove(
    slug: str,
    tag: list[str] = typer.Option(..., "--tag", help="Tag to remove. Repeat for multiple."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        for t in tag:
            run(client.remove_tag(slug, t))
        result = run(client.list_tags(slug))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@media_app.command("upload")
def media_upload(
    name: str = typer.Option(..., "--name", help="Unique name for the media (e.g. hero-image)."),
    path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.upload_media(name, path))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@media_app.command("update")
def media_update(
    name: str = typer.Option(..., "--name", help="Name of the media to replace."),
    path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.update_media(name, path))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@media_app.command("delete")
def media_delete(
    name: str = typer.Option(..., "--name", help="Name of the media to delete."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    try:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_media(name))
        emit_result(result, json_output=json_output)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
