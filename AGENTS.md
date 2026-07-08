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

Requires `PERSONAL_SERVER_URL` in env or `.env`. No default URL — errors out if not set.

## Important

Always use `uv run blog-cli` for testing. Never install globally or use a system-level binary.
