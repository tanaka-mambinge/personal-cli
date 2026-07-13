# AGENTS.md — blog-cli

## Testing

```bash
uv run pytest -v
```

Spins up a temp mongod + server automatically via test fixtures.

## Running locally

```bash
unset PERSONAL_SERVER_URL PERSONAL_API_KEY PERSONAL_SITE_URL
set -a
source .env
set +a
uv run blog-cli article list
```

Use this repository's `.env` as the local source of truth. It contains the local `PERSONAL_SERVER_URL`, `PERSONAL_API_KEY`, and `PERSONAL_SITE_URL`. No default URL — errors out if not set.

## Important

Always use `uv run blog-cli` for testing. Never install globally or use a system-level binary.

## Content workflow skill (the skill lives here)

Whenever creating, editing, or updating articles/projects for the personal site, default to **draft first** and share a **preview link**.

Rules:

1. Create content as a draft unless the user explicitly says to publish / go live / ship it.
   - Blog: `uv run blog-cli article blog create --title ... --description ... --markdown ...`
   - Project: `uv run blog-cli article project create --title ... --description ... --markdown ...`
2. After creating or updating, generate a preview link:
   - `uv run blog-cli article preview <slug>`
3. Show the user the preview URL and ask if they want changes.
4. Only publish when the user explicitly says to publish.
   - `uv run blog-cli article publish <slug>`
5. Blogs cannot have tags. If the user asks for tags on a blog, warn them.
6. Only use `--pinned` / `--sort-order` for projects when the user asks.

This file is the source of truth for the skill. If the user says "update the skill", update this section.
