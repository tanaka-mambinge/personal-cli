from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class CLIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ArticleApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 30.0,
        verify: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.transport = transport
        self.timeout = timeout
        self.verify = verify

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        files: Any = None,
    ) -> Any:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            transport=self.transport,
            timeout=self.timeout,
            headers=self._headers(),
            verify=self.verify,
        ) as client:
            response = await client.request(method, path, json=json, params=params, files=files)
            if response.status_code >= 400:
                message = response.text.strip() or response.reason_phrase
                raise CLIError(f"{method} {path} failed: {response.status_code} {message}", status_code=response.status_code)
            if response.content:
                return response.json()
            return None

    async def list_articles(self, *, status: str | None = None, type_filter: str = "all") -> list[dict[str, Any]]:
        params: dict[str, Any] = {"type": type_filter}
        if status is not None:
            params["status_filter"] = status
        result = await self._request_json("GET", "/api/v1/articles", params=params)
        return list(result or [])

    async def get_article(self, slug: str) -> dict[str, Any]:
        result = await self._request_json("GET", f"/api/v1/articles/{slug}")
        return dict(result)

    async def create_article(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self._request_json("POST", "/api/v1/articles", json=payload)
        return dict(result)

    async def update_article(self, slug: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self._request_json("PATCH", f"/api/v1/articles/{slug}", json=payload)
        return dict(result)

    async def publish_article(self, slug: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = await self._request_json("POST", f"/api/v1/articles/{slug}/publish", json=payload)
        return dict(result)

    async def unarchive_article(self, slug: str) -> dict[str, Any]:
        result = await self._request_json("POST", f"/api/v1/articles/{slug}/unarchive")
        return dict(result)

    async def delete_article(self, slug: str) -> dict[str, Any]:
        result = await self._request_json("DELETE", f"/api/v1/articles/{slug}")
        return dict(result or {})

    async def upload_media(self, name: str, path: Path) -> dict[str, Any]:
        with path.open("rb") as handle:
            result = await self._request_json(
                "POST",
                "/api/v1/media",
                params={"name": name},
                files={"file": (path.name, handle, "application/octet-stream")},
            )
        return dict(result)

    async def update_media(self, name: str, path: Path) -> dict[str, Any]:
        with path.open("rb") as handle:
            result = await self._request_json(
                "PUT",
                f"/api/v1/media/{name}",
                files={"file": (path.name, handle, "application/octet-stream")},
            )
        return dict(result)

    async def delete_media(self, name: str) -> dict[str, Any]:
        result = await self._request_json("DELETE", f"/api/v1/media/{name}")
        return dict(result or {})

    async def generate_preview(self, slug: str, *, ttl_hours: int = 24, base_url: str = "http://localhost:3000") -> dict[str, Any]:
        result = await self._request_json(
            "POST",
            f"/api/v1/articles/{slug}/preview",
            params={"ttl_hours": ttl_hours, "base_url": base_url},
        )
        return dict(result)


def get_default_config() -> tuple[str, str | None, str]:
    import os
    _load_dotenv()
    server_url = os.environ.get("PERSONAL_SERVER_URL")
    if not server_url:
        raise CLIError("PERSONAL_SERVER_URL is not set.")
    api_key = os.environ.get("PERSONAL_API_KEY")
    if not api_key:
        raise CLIError("PERSONAL_API_KEY is not set.")
    site_url = os.environ.get("PERSONAL_SITE_URL", "")
    return (server_url, api_key, site_url)


def _load_dotenv() -> None:
    import os
    from pathlib import Path

    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]
    for env_path in candidates:
        if not env_path.exists():
            continue
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                os.environ[key] = value
        break
