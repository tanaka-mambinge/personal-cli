from __future__ import annotations

import asyncio
import importlib.metadata
from pathlib import Path
from typing import Callable, TypeVar

import typer

from personal_cli.client import ArticleApiClient, CLIError, get_config
from personal_cli.credentials import (
    CredentialError,
    CredentialStore,
    MissingCredentialError,
)
from personal_cli.formatting import emit_result, read_markdown_from_source
from personal_cli.setup_server import run_setup

app = typer.Typer(help="Agent-facing article CLI.")
article_app = typer.Typer(help="Manage articles.")
blog_app = typer.Typer(help="Manage blog posts.")
project_app = typer.Typer(help="Manage projects.")
media_app = typer.Typer(help="Manage media uploads.")
keys_app = typer.Typer(help="Manage stored credentials.")
category_app = typer.Typer(help="Manage content categories.")
page_app = typer.Typer(help="Manage private content pages.")
service_app = typer.Typer(help="Manage public services.")

app.add_typer(article_app, name="article")
article_app.add_typer(blog_app, name="blog")
article_app.add_typer(project_app, name="project")
app.add_typer(media_app, name="media")
app.add_typer(keys_app, name="keys")
app.add_typer(category_app, name="category")
app.add_typer(page_app, name="page")
app.add_typer(service_app, name="service")

Result = TypeVar("Result")


def get_version() -> str:
    try:
        return importlib.metadata.version("blog-cli")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


@app.command("version")
def cli_version() -> None:
    typer.echo(get_version())


def _emit(message: str) -> None:
    typer.echo(message, err=True)


def build_client(
    server_url: str | None = None, insecure: bool = False
) -> ArticleApiClient:
    url, api_key, _ = get_config()
    return ArticleApiClient(server_url or url, api_key=api_key, verify=not insecure)


def _site_url() -> str:
    _, _, site_url = get_config()
    return site_url.rstrip("/")


def _dashboard_url(slug: str) -> str:
    return f"{_site_url()}/d/{slug}"


def _category_dashboard_url(slug: str) -> str:
    return f"{_site_url()}/d?category={slug}"


def _article_url(article: dict) -> str:
    prefix = "/work" if article.get("type") == "project" else "/writing"
    return f"{_site_url()}{prefix}/{article['slug']}"


def _with_article_url(article: dict) -> dict:
    article["url"] = _article_url(article)
    return article


def _service_url(service: dict) -> str:
    return f"{_site_url()}/services/{service['slug']}"


def _with_service_url(service: dict) -> dict:
    service["url"] = _service_url(service)
    return service


def _parse_examples(values: list[str]) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    for value in values:
        title, separator, href = value.partition("|")
        if not separator or not title.strip() or not href.strip():
            raise CLIError("Examples must use the format: Title|https://example.com")
        examples.append({"title": title.strip(), "href": href.strip()})
    return examples


def _parse_offerings(values: list[str]) -> list[dict[str, str | None]]:
    offerings: list[dict[str, str | None]] = []
    for value in values:
        parts = [part.strip() for part in value.split("|", 2)]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise CLIError("Offerings must use the format: Title|Explanation[|MediaNameOrImageURL]")
        offerings.append({
            "title": parts[0],
            "summary": parts[1],
            "cover_image": parts[2] if len(parts) == 3 and parts[2] else None,
            "image_alt": None,
        })
    return offerings


def _preview_if_draft(
    client: ArticleApiClient,
    article: dict,
    *,
    ttl_hours: int = 24,
) -> dict:
    if article.get("status") == "draft":
        preview = run(client.generate_preview(article["slug"], ttl_hours=ttl_hours, base_url=_site_url()))
        article["url"] = preview["url"]
        article["preview_url"] = preview["url"]
        article["preview_token"] = preview["token"]
        article["preview_expires_at"] = preview["expires_at"]
    else:
        _with_article_url(article)
    return article


def run(coro):
    return asyncio.run(coro)


def _run(operation: Callable[[], Result]) -> Result:
    """Run an operation, opening the setup page when credentials are missing/rejected."""
    while True:
        try:
            return operation()
        except MissingCredentialError:
            run_setup(
                CredentialStore(),
                output=_emit,
                prompt="Credentials are missing. Open this link in your browser",
            )
        except CLIError as exc:
            if exc.status_code not in (401, 403):
                raise
            _emit("The server rejected the stored API key. Re-enter it in the setup page.")
            run_setup(
                CredentialStore(),
                output=_emit,
                prompt="Enter replacement credentials in your browser",
            )


@article_app.command("list")
def article_list(
    type_filter: str = typer.Option("all", "--type", help="all, blog, or project."),
    status: str | None = typer.Option(None, "--status", help="Filter by article status."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        articles = run(client.list_articles(status=status, type_filter=type_filter))
        for article in articles:
            _with_article_url(article)
        emit_result(articles, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        article = run(client.get_article(slug))
        _with_article_url(article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@blog_app.command("create")
def blog_create(
    title: str = typer.Option(..., "--title", help="Article title."),
    description: str = typer.Option(..., "--description", help="Short summary."),
    slug: str | None = typer.Option(None, "--slug", help="Optional slug override."),
    cover_image: str | None = typer.Option(None, "--cover-image", help="Uploaded media name for the article cover image."),
    status: str = typer.Option("draft", "--status", help="draft or published."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        body = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        client = build_client(server_url, insecure=insecure)
        payload = {
            "title": title,
            "description": description,
            "slug": slug,
            "tags": [],
            "cover_image": cover_image,
            "type": "blog",
            "status": status,
            "pinned": False,
            "sort_order": 0,
            "markdown": body,
        }
        article = run(client.create_article(payload))
        _preview_if_draft(client, article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@project_app.command("create")
def project_create(
    title: str = typer.Option(..., "--title", help="Project title."),
    description: str = typer.Option(..., "--description", help="Short summary."),
    slug: str | None = typer.Option(None, "--slug", help="Optional slug override."),
    tag: list[str] = typer.Option([], "--tag", help="Repeat for each tag."),
    cover_image: str = typer.Option(..., "--cover-image", help="Uploaded media name for the project banner image."),
    status: str = typer.Option("draft", "--status", help="draft or published."),
    pinned: bool = typer.Option(False, "--pinned/--not-pinned", help="Pin to the home page."),
    sort_order: int = typer.Option(0, "--sort-order", help="Order among pinned projects (lower first)."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        body = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        client = build_client(server_url, insecure=insecure)
        payload = {
            "title": title,
            "description": description,
            "slug": slug,
            "tags": tag,
            "cover_image": cover_image,
            "type": "project",
            "status": status,
            "pinned": pinned,
            "sort_order": sort_order,
            "markdown": body,
        }
        article = run(client.create_article(payload))
        _preview_if_draft(client, article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@article_app.command("update")
def article_update(
    slug: str,
    title: str | None = typer.Option(None, "--title", help="New title."),
    description: str | None = typer.Option(None, "--description", help="New summary."),
    tag: list[str] | None = typer.Option(None, "--tag", help="Repeat for each tag."),
    cover_image: str | None = typer.Option(None, "--cover-image", help="Uploaded media name for the article cover image."),
    clear_cover_image: bool = typer.Option(False, "--clear-cover-image", help="Remove the article cover image."),
    article_type: str | None = typer.Option(None, "--type", help="blog or project."),
    status: str | None = typer.Option(None, "--status", help="draft or published."),
    pinned: bool | None = typer.Option(None, "--pinned/--not-pinned", help="Pin or unpin a project."),
    sort_order: int | None = typer.Option(None, "--sort-order", help="Order among pinned projects (lower first)."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        if cover_image is not None and clear_cover_image:
            raise CLIError("Use either --cover-image or --clear-cover-image, not both.")
        client = build_client(server_url, insecure=insecure)
        current = next(
            (article for article in run(client.list_articles(type_filter="all")) if article.get("slug") == slug),
            None,
        )
        if current is None:
            raise CLIError(f"Article not found: {slug}")
        target_type = article_type or current.get("type")
        resulting_cover = cover_image if cover_image is not None else current.get("cover_image")
        if target_type == "project" and (clear_cover_image or not resulting_cover):
            raise CLIError("Projects must have a cover image. Use --cover-image or keep the existing cover image.")
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if tag is not None:
            payload["tags"] = tag
        if cover_image is not None:
            payload["cover_image"] = cover_image
        elif clear_cover_image:
            payload["cover_image"] = None
        if article_type is not None:
            payload["type"] = article_type
        if status is not None:
            payload["status"] = status
        if pinned is not None:
            payload["pinned"] = pinned
        if sort_order is not None:
            payload["sort_order"] = sort_order
        if markdown is not None or markdown_file is not None:
            payload["markdown"] = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        article = run(client.update_article(slug, payload))
        _preview_if_draft(client, article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        article = run(client.publish_article(slug, {"published_by": published_by} if published_by else None))
        _with_article_url(article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_article(slug))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        article = run(client.unarchive_article(slug))
        _preview_if_draft(client, article)
        emit_result(article, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        _, _, default_site_url = get_config()
        resolved_site_url = site_url or default_site_url
        client = build_client(server_url, insecure=insecure)
        result = run(client.generate_preview(slug, ttl_hours=ttl_hours, base_url=resolved_site_url))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.list_tags(slug))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.attach_tags(slug, tag))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        for t in tag:
            run(client.remove_tag(slug, t))
        result = run(client.list_tags(slug))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.upload_media(name, path))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.update_media(name, path))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
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
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_media(name))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@keys_app.command("revoke")
def keys_revoke(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Revoke the stored personal-cli credentials."""
    try:
        revoked = CredentialStore().remove()
        emit_result(
            {"revoked": revoked, "message": "Credentials revoked." if revoked else "No credentials were stored."},
            json_output=json_output,
        )
    except CredentialError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@keys_app.command("show")
def keys_show(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Show whether credentials are stored (API key is masked)."""
    try:
        server_url, api_key, site_url = get_config()
        emit_result(
            {
                "server_url": server_url,
                "api_key": f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****",
                "site_url": site_url,
            },
            json_output=json_output,
        )
    except MissingCredentialError:
        emit_result({"stored": False}, json_output=json_output)
    except CredentialError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@category_app.command("create")
def category_create(
    name: str = typer.Option(..., "--name", help="Display name. Slug is derived from this."),
    icon: str | None = typer.Option(None, "--icon", help="Tabler icon name, e.g. bulb."),
    description: str | None = typer.Option(None, "--description", help="Short description."),
    sort_order: int = typer.Option(0, "--sort-order", help="Lower sorts first."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        payload: dict[str, object] = {"name": name, "sort_order": sort_order}
        if icon is not None:
            payload["icon"] = icon
        if description is not None:
            payload["description"] = description
        result = run(client.create_category(payload))
        result["dashboard_url"] = _category_dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@category_app.command("list")
def category_list(
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.list_categories())
        for category in result:
            category["dashboard_url"] = _category_dashboard_url(category["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@category_app.command("show")
def category_show(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.get_category(slug))
        result["dashboard_url"] = _category_dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@category_app.command("update")
def category_update(
    slug: str,
    name: str | None = typer.Option(None, "--name", help="New display name."),
    icon: str | None = typer.Option(None, "--icon", help="New tabler icon name."),
    description: str | None = typer.Option(None, "--description", help="New description."),
    sort_order: int | None = typer.Option(None, "--sort-order", help="Lower sorts first."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        payload: dict[str, object] = {}
        if name is not None:
            payload["name"] = name
        if icon is not None:
            payload["icon"] = icon
        if description is not None:
            payload["description"] = description
        if sort_order is not None:
            payload["sort_order"] = sort_order
        if not payload:
            raise CLIError("No update fields provided.")
        result = run(client.update_category(slug, payload))
        result["dashboard_url"] = _category_dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@category_app.command("delete")
def category_delete(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_category(slug))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@page_app.command("create")
def page_create(
    title: str = typer.Option(..., "--title", help="Page title."),
    description: str = typer.Option(..., "--description", help="Short summary."),
    category: str = typer.Option(..., "--category", help="Category slug the page belongs to."),
    slug: str | None = typer.Option(None, "--slug", help="Optional slug override."),
    sort_order: int = typer.Option(0, "--sort-order", help="Lower sorts first."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline MDX body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        body = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        client = build_client(server_url, insecure=insecure)
        payload = {
            "title": title,
            "description": description,
            "category_slug": category,
            "slug": slug,
            "sort_order": sort_order,
            "markdown": body,
        }
        result = run(client.create_page(payload))
        result["dashboard_url"] = _dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@page_app.command("list")
def page_list(
    category: str | None = typer.Option(None, "--category", help="Filter by category slug."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.list_pages(category=category))
        for page in result:
            page["dashboard_url"] = _dashboard_url(page["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@page_app.command("show")
def page_show(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.get_page(slug))
        result["dashboard_url"] = _dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@page_app.command("update")
def page_update(
    slug: str,
    title: str | None = typer.Option(None, "--title", help="New title."),
    description: str | None = typer.Option(None, "--description", help="New summary."),
    category: str | None = typer.Option(None, "--category", help="New category slug."),
    sort_order: int | None = typer.Option(None, "--sort-order", help="Lower sorts first."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline MDX body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if category is not None:
            payload["category_slug"] = category
        if sort_order is not None:
            payload["sort_order"] = sort_order
        if markdown is not None or markdown_file is not None:
            payload["markdown"] = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        if not payload:
            raise CLIError("No update fields provided.")
        result = run(client.update_page(slug, payload))
        result["dashboard_url"] = _dashboard_url(result["slug"])
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@page_app.command("delete")
def page_delete(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.delete_page(slug))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@service_app.command("create")
def service_create(
    title: str = typer.Option(..., "--title", help="Service title."),
    summary: str = typer.Option(..., "--summary", help="Short service summary."),
    category: str = typer.Option(..., "--category", help="Service category, such as web, ai, or automation."),
    slug: str | None = typer.Option(None, "--slug", help="Optional slug override."),
    service_type: list[str] = typer.Option([], "--type", help="A short requestable service label. Repeat as needed."),
    offering: list[str] = typer.Option([], "--offering", help="Offering as Title|Explanation[|MediaNameOrImageURL]. Repeat as needed."),
    example: list[str] = typer.Option([], "--example", help="Example as Title|https://example.com. Repeat as needed."),
    cover_image: str | None = typer.Option(None, "--cover-image", help="Media name or public image path."),
    image_alt: str | None = typer.Option(None, "--image-alt", help="Accessible image description."),
    featured: bool = typer.Option(False, "--featured/--not-featured", help="Show in the homepage services preview."),
    sort_order: int = typer.Option(0, "--sort-order", help="Lower sorts first."),
    next_step: str | None = typer.Option(None, "--next-step", help="Optional homepage call-to-action label."),
    home_title: str | None = typer.Option(None, "--home-title", help="Optional homepage card title."),
    home_summary: str | None = typer.Option(None, "--home-summary", help="Optional homepage card summary."),
    home_next_step: str | None = typer.Option(None, "--home-next-step", help="Optional homepage card action label."),
    home_sort_order: int | None = typer.Option(None, "--home-sort-order", help="Homepage card ordering."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline Markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        body = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        client = build_client(server_url, insecure=insecure)
        payload = {
            "title": title,
            "summary": summary,
            "category": category,
            "slug": slug,
            "examples": _parse_examples(example),
            "cover_image": cover_image,
            "image_alt": image_alt,
            "featured": featured,
            "sort_order": sort_order,
            "next_step": next_step,
            "home_title": home_title,
            "home_summary": home_summary,
            "home_next_step": home_next_step,
            "home_sort_order": home_sort_order,
            "markdown": body,
        }
        payload["types"] = service_type
        payload["offerings"] = _parse_offerings(offering)
        result = _with_service_url(run(client.create_service(payload)))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@service_app.command("list")
def service_list(
    category: str | None = typer.Option(None, "--category", help="Filter by category."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = run(client.list_services(category=category))
        for service in result:
            _with_service_url(service)
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@service_app.command("show")
def service_show(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        result = _with_service_url(run(client.get_service(slug)))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@service_app.command("update")
def service_update(
    slug: str,
    title: str | None = typer.Option(None, "--title", help="New service title."),
    summary: str | None = typer.Option(None, "--summary", help="New service summary."),
    category: str | None = typer.Option(None, "--category", help="New category."),
    service_type: list[str] = typer.Option([], "--type", help="Replace short requestable labels. Repeat as needed."),
    clear_types: bool = typer.Option(False, "--clear-types", help="Remove all requestable types."),
    offering: list[str] = typer.Option([], "--offering", help="Replace offerings with Title|Explanation[|MediaNameOrImageURL] entries."),
    clear_offerings: bool = typer.Option(False, "--clear-offerings", help="Remove all offerings."),
    example: list[str] = typer.Option([], "--example", help="Replace examples with Title|https://example.com entries."),
    clear_examples: bool = typer.Option(False, "--clear-examples", help="Remove all example links."),
    cover_image: str | None = typer.Option(None, "--cover-image", help="New media name or public image path."),
    clear_cover_image: bool = typer.Option(False, "--clear-cover-image", help="Remove the cover image."),
    image_alt: str | None = typer.Option(None, "--image-alt", help="New accessible image description."),
    featured: bool | None = typer.Option(None, "--featured/--not-featured", help="Set homepage featured state."),
    sort_order: int | None = typer.Option(None, "--sort-order", help="Lower sorts first."),
    next_step: str | None = typer.Option(None, "--next-step", help="New homepage call-to-action label."),
    home_title: str | None = typer.Option(None, "--home-title", help="Homepage card title."),
    home_summary: str | None = typer.Option(None, "--home-summary", help="Homepage card summary."),
    home_next_step: str | None = typer.Option(None, "--home-next-step", help="Homepage card action label."),
    home_sort_order: int | None = typer.Option(None, "--home-sort-order", help="Homepage card ordering."),
    markdown: str | None = typer.Option(None, "--markdown", help="Inline Markdown body."),
    markdown_file: Path | None = typer.Option(None, "--markdown-file", exists=True, readable=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if summary is not None:
            payload["summary"] = summary
        if category is not None:
            payload["category"] = category
        if service_type:
            payload["types"] = service_type
        elif clear_types:
            payload["types"] = []
        if offering:
            payload["offerings"] = _parse_offerings(offering)
        elif clear_offerings:
            payload["offerings"] = []
        if example:
            payload["examples"] = _parse_examples(example)
        elif clear_examples:
            payload["examples"] = []
        if cover_image is not None:
            payload["cover_image"] = cover_image
        elif clear_cover_image:
            payload["cover_image"] = None
        if image_alt is not None:
            payload["image_alt"] = image_alt
        if featured is not None:
            payload["featured"] = featured
        if sort_order is not None:
            payload["sort_order"] = sort_order
        if next_step is not None:
            payload["next_step"] = next_step
        if home_title is not None:
            payload["home_title"] = home_title
        if home_summary is not None:
            payload["home_summary"] = home_summary
        if home_next_step is not None:
            payload["home_next_step"] = home_next_step
        if home_sort_order is not None:
            payload["home_sort_order"] = home_sort_order
        if markdown is not None or markdown_file is not None:
            payload["markdown"] = read_markdown_from_source(markdown=markdown, markdown_file=markdown_file)
        if not payload:
            raise CLIError("No update fields provided.")
        client = build_client(server_url, insecure=insecure)
        result = _with_service_url(run(client.update_service(slug, payload)))
        emit_result(result, json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@service_app.command("delete")
def service_delete(
    slug: str,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    insecure: bool = typer.Option(False, "--insecure", help="Skip SSL verification."),
    server_url: str | None = typer.Option(None, "--server-url", help="FastAPI base URL."),
) -> None:
    def _op() -> None:
        client = build_client(server_url, insecure=insecure)
        emit_result(run(client.delete_service(slug)), json_output=json_output)

    try:
        _run(_op)
    except CLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
