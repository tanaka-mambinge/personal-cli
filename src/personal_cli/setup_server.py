from __future__ import annotations

import html
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from .credentials import CredentialError, CredentialStore


SETUP_PATH = "/setup"
SETUP_PORT = 3234


def _page(
    message: str = "",
    *,
    error: bool = False,
    token: str = "",
    server_url: str = "",
    site_url: str = "",
    success: bool = False,
) -> bytes:
    action = f"{SETUP_PATH}?{urlencode({'token': token})}"
    if success:
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Personal CLI setup</title>
<style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; background: linear-gradient(135deg,#f4f7ff,#fff 55%,#eefbf7); color: #172033; }}
dialog {{ border: 0; border-radius: 1.25rem; padding: 0; max-width: 26rem; width: calc(100% - 2rem); box-shadow: 0 24px 60px rgba(24,39,75,.18); overflow: hidden; top: 50%; transform: translateY(-50%); margin: 0 auto; }}
dialog::backdrop {{ background: rgba(23,32,51,.45); backdrop-filter: blur(4px); }}
.modal {{ padding: 2.75rem 2rem 2.25rem; text-align: center; }}
.check {{ display: grid; place-items: center; width: 4rem; height: 4rem; margin: 0 auto 1.25rem; border-radius: 50%; background: #edfff6; color: #087443; }}
.check svg {{ width: 2.25rem; height: 2.25rem; }}
h2 {{ margin: 0 0 .5rem; font-size: 1.5rem; letter-spacing: -.02em; }}
.modal p {{ margin: 0; color: #667085; line-height: 1.55; font-size: .95rem; }}
</style></head>
<body>
<dialog open>
  <div class="modal">
    <div class="check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg></div>
    <h2>Credentials saved</h2>
    <p>Your server URL, API key, and site URL are stored in your operating system credential store. You can close this browser window.</p>
  </div>
</dialog>
</body></html>""".encode("utf-8")

    escaped_message = html.escape(message)
    message_html = (
        f'<p class="{"error" if error else "success"}">{escaped_message}</p>'
        if message
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Personal CLI setup</title>
<style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; background: linear-gradient(135deg,#f4f7ff,#fff 55%,#eefbf7); color: #172033; }}
.shell {{ max-width: 42rem; margin: 0 auto; padding: 4rem 1.25rem; }}
.eyebrow {{ color: #536dfe; font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
h1 {{ margin: .5rem 0 .75rem; font-size: clamp(2rem,5vw,2.75rem); letter-spacing: -.04em; }}
.intro {{ color: #667085; line-height: 1.6; margin: 0 0 2rem; }}
.card {{ padding: 1.5rem; border: 1px solid #e4e7ec; border-radius: 1rem; background: rgba(255,255,255,.86); box-shadow: 0 10px 30px rgba(24,39,75,.07); }}
label {{ display: block; margin: 1rem 0 .4rem; font-size: .85rem; font-weight: 700; }}
input {{ width: 100%; padding: .85rem 1rem; border: 1px solid #d0d5dd; border-radius: .65rem; font: inherit; background: #fff; }}
input:focus {{ outline: 3px solid #dfe3ff; border-color: #536dfe; }}
button {{ margin-top: 1.5rem; width: 100%; padding: .9rem 1rem; border: 0; border-radius: .65rem; background: #536dfe; color: white; font-weight: 750; cursor: pointer; box-shadow: 0 8px 18px rgba(83,109,254,.25); font: inherit; }}
button:hover {{ background: #4256d6; }}
.notice {{ margin: 1rem 0; padding: .85rem 1rem; border-radius: .65rem; }}
.error {{ color: #a4262c; background: #fff0f0; }} .success {{ color: #087443; background: #edfff6; }}
.footnote {{ color: #667085; font-size: .8rem; text-align: center; margin-top: 1.5rem; }}
</style></head>
<body><main class="shell"><div class="eyebrow">Personal CLI</div><h1>Connect your backend</h1>
<p class="intro">Enter your personal server URL, API key, and site URL. They are saved to your operating system credential store and never sent to the agent chat.</p>
{message_html}
<form method="post" action="{html.escape(action)}" class="card">
<label for="server-url">Server URL</label>
<input id="server-url" name="server_url" type="url" required placeholder="https://api.example.com" value="{html.escape(server_url)}">
<label for="api-key">API key</label>
<input id="api-key" name="api_key" type="password" autocomplete="off" required placeholder="Enter your API key">
<label for="site-url">Site URL</label>
<input id="site-url" name="site_url" type="url" required placeholder="https://example.com" value="{html.escape(site_url)}">
<button type="submit">Save credentials</button>
</form>
<div class="footnote">You can revoke later with <code>blog-cli keys revoke</code>.</div>
</main></body></html>""".encode("utf-8")


def _validate(server_url: str, api_key: str, site_url: str) -> str | None:
    """Hit the server to confirm the URL + key work. Returns error message or None."""
    try:
        with httpx.Client(
            base_url=server_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
            verify=True,
        ) as client:
            response = client.get("/api/v1/articles", params={"type": "all"})
    except httpx.HTTPError as exc:
        return f"Could not reach the server: {exc}"
    if response.status_code in (401, 403):
        return "The server rejected that API key."
    if response.status_code >= 500:
        return f"The server returned an error ({response.status_code})."
    return None


class _SetupServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        store: CredentialStore,
        token: str,
        port: int = SETUP_PORT,
        bind_host: str = "127.0.0.1",
    ) -> None:
        try:
            super().__init__((bind_host, port), _SetupHandler)
        except OSError:
            super().__init__((bind_host, 0), _SetupHandler)
        self.store = store
        self.token = token
        self.consumed = False


class _SetupHandler(BaseHTTPRequestHandler):
    server: _SetupServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def _authorized(self) -> bool:
        query = parse_qs(urlparse(self.path).query)
        return urlparse(self.path).path == SETUP_PATH and query.get("token") == [
            self.server.token
        ]

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not self._authorized():
            self._send(404, _page("Setup page not found.", error=True))
            return
        if self.server.consumed:
            self._send(410, _page("This setup link has already been used.", error=True))
            return
        self._send(200, _page(token=self.server.token))

    def do_POST(self) -> None:
        if not self._authorized():
            self._send(404, _page("Setup page not found.", error=True))
            return
        if self.server.consumed:
            self._send(410, _page("This setup link has already been used.", error=True))
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 64 * 1024)
            values = parse_qs(
                self.rfile.read(length).decode("utf-8"), keep_blank_values=True
            )
            server_url = values.get("server_url", [""])[0].strip().strip("\"'").strip()
            api_key = values.get("api_key", [""])[0].strip().strip("\"'").strip()
            site_url = values.get("site_url", [""])[0].strip().strip("\"'").strip()
            if not (server_url and api_key and site_url):
                raise CredentialError("All three fields are required.")

            error = _validate(server_url, api_key, site_url)
            if error:
                self._send(
                    400,
                    _page(
                        error,
                        error=True,
                        token=self.server.token,
                        server_url=server_url,
                        site_url=site_url,
                    ),
                )
                return
            self.server.store.add(
                server_url=server_url, api_key=api_key, site_url=site_url
            )
        except (ValueError, UnicodeDecodeError, CredentialError) as exc:
            self._send(400, _page(str(exc), error=True, token=self.server.token))
            return

        self.server.consumed = True
        self._send(200, _page(success=True))
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def run_setup(
    store: CredentialStore,
    output: Callable[[str], None] = print,
    prompt: str = "Credentials are missing. Open this link in your browser",
) -> None:
    """Serve the one-time local setup page until credentials are saved."""
    token = secrets.token_urlsafe(32)
    server = _SetupServer(
        store,
        token,
        bind_host=os.environ.get("PERSONAL_CLI_SETUP_BIND_HOST", "127.0.0.1"),
    )
    url = f"http://127.0.0.1:{server.server_port}{SETUP_PATH}?{urlencode({'token': token})}"
    output(f"{prompt}: {url}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
