# AGENTS.md — blog-cli

## Testing

```bash
uv run pytest -v
```

Uses an in-memory fake API client; no external server or MongoDB is required.

## Running locally

Credentials are stored in the OS keyring, not `.env`. On first run (or after
revoke) the CLI prints a one-time setup URL to stderr:

```
Credentials are missing. Open this link in your browser: http://127.0.0.1:3233/setup?token=...
```

Open the link, enter the server URL, API key, and site URL, and submit. They are
validated against `GET /api/v1/articles` and saved to the keyring. The agent
should relay the URL to the user; the CLI process stays alive until the user
submits the form.

For local development that must not touch production credentials, set
`PERSONAL_CLI_ENV=dev` — the keyring service becomes `personal-cli-dev`:

```bash
PERSONAL_CLI_ENV=dev uv run blog-cli article list
```

Revoke stored credentials with:

```bash
uv run blog-cli keys revoke
```

Check what is stored (API key is masked) with:

```bash
uv run blog-cli keys show
```

## Important

Always use `uv run blog-cli` for testing. Never install globally or use a system-level binary.

## Content workflow skill (the skill lives here)

Whenever creating, editing, or updating articles/projects for the personal site, default to **draft first**. Keep any existing preview link stable unless the user explicitly asks for a new one.

Writing and presentation rules:

- Use plain, readable typography in article content. Never add decorative Unicode symbols, emoji, arrows, dingbats, or other funny-looking font icons unless the user explicitly requests them.
- Prefer ordinary words, punctuation, and simple Markdown.

Rules:

1. Create content as a draft unless the user explicitly says to publish / go live / ship it.
   - Blog: `uv run blog-cli article blog create --title ... --description ... --markdown ...`
   - Project: `uv run blog-cli article project create --title ... --description ... --markdown ...`
   - Page (private dashboard): `uv run blog-cli page create --title ... --description ... --category <slug> --markdown ...`
2. After creating or updating, do not automatically generate a preview link. If the user explicitly asks for a preview link, run:
   - `uv run blog-cli article preview <slug>`
3. When a preview already exists, keep using its existing URL. Never revoke or regenerate it just because content was updated; updating the article changes the content behind the existing preview URL.
4. Show the user the preview URL only when they ask for it, and ask if they want changes.
5. Only publish when the user explicitly says to publish.
   - `uv run blog-cli article publish <slug>`
6. Blogs cannot have tags. If the user asks for tags on a blog, warn them.
7. Only use `--pinned` / `--sort-order` for projects when the user asks.
8. Pages are always private (no publish step). Categories must exist before creating a page in them. Create the category first with `uv run blog-cli category create --name <name>`.
9. After every write to a page, share the `dashboard_url` from the CLI output with the user so they can open `/d/<slug>` in the browser. If a browser pane is already open on that tab, tell the user to reload it.

## ChatGPT / Codex skill

The CLI ships a bundled skill (`content-pipeline`) that routes blog/project/page tasks to the right reference. Install it with:

```bash
uv run blog-cli skill install
```

This copies `SKILL.md` plus `references/articles.md`, `references/projects.md`, and `references/pages.md` into `~/.agents/skills/content-pipeline/`. Uninstall with `uv run blog-cli skill uninstall`.

This file is the source of truth for the skill. If the user says "update the skill", update this section.
