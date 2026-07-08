# AGENTS.md — blog-cli

## Testing

```bash
uv run pytest -v
```

Spins up a temp mongod + server automatically via test fixtures.

## Running locally

```bash
uv run blog-cli article list
```

The CLI auto-loads `.env` from the project directory. `.env` values override system env vars.

When installed globally (`pipx install` / `uv tool install`), set env vars in `~/.zshrc`:

```bash
export PERSONAL_SERVER_URL="https://api.personal.localhost:1355"
export PERSONAL_API_KEY="your-api-key"
export PERSONAL_SITE_URL="https://personal.localhost:1355"
```

## Important

**Always use `uv run blog-cli` for testing. Never install globally or use a system-level binary.** The CLI should be invoked via `uv run` from the project directory so it picks up the local environment and source code.
