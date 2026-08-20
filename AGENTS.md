# AGENTS.md — blog-cli

## Testing

```bash
./scripts/docker-cli test
```

The full suite is service-free: it runs the real CLI command wiring against
in-memory fake API and keyring backends. It does not require the personal
server, MongoDB, stored credentials, a native OS keyring, a browser, or any
network service at test runtime. Docker caches the locked dependencies and the
test container runs with networking disabled.

## Running locally

Credentials are stored in the configured keyring backend, not `.env`. On first
run the CLI prints a setup URL to stderr:

```
Credentials are missing. Open this link in your browser: http://127.0.0.1:3234/setup?token=...
```

Run local commands through Docker. Docker uses a separate file-backed keyring
inside the persistent `personal-cli-credentials` volume and never mounts the
host keyring:

```bash
./scripts/docker-cli run article list
```

The Docker runner uses host networking for interactive commands so the setup
URL at `127.0.0.1` opens in the user's browser. Keep the command running until
the form has been submitted. The setup page remains reloadable while waiting
for valid credentials.

If a command reports missing credentials, treat that as an interactive setup
state, not a terminal failure. Immediately relay the exact setup URL printed on
stderr as a clickable Markdown link and tell the user to enter the server URL,
API key, and site URL there. Never ask the user to paste credentials into chat,
start a second setup session, or replace the URL while the current session is
alive. After the form succeeds, let the original command retry and share its
result and any returned content link.

Publishing the CLI package through GitHub Actions and PyPI does not read the
keyring or publish articles; a production automation job that runs `blog-cli`
must be provisioned with production credentials separately.

Revoke stored credentials with:

```bash
./scripts/docker-cli run keys revoke
```

Check what is stored (API key is masked) with:

```bash
./scripts/docker-cli run keys show
```

## Important

Always use `./scripts/docker-cli test` for tests and
`./scripts/docker-cli run ...` for local CLI commands. Never run the checkout
with a host-level CLI binary.

## Content workflow skill (the skill lives here)

Whenever creating, editing, or updating articles/projects for the personal site, default to **draft first**. Keep any existing preview link stable unless the user explicitly asks for a new one.

Writing and presentation rules:

- Use plain, readable typography in article content. Never add decorative Unicode symbols, emoji, arrows, dingbats, or other funny-looking font icons unless the user explicitly requests them.
- Prefer ordinary words, punctuation, and simple Markdown.

Rules:

1. Create content as a draft unless the user explicitly says to publish / go live / ship it.
   - Blog: `./scripts/docker-cli run article blog create --title ... --description ... --markdown ...`
   - Project: `./scripts/docker-cli run article project create --title ... --description ... --markdown ...`
   - Page (private dashboard): `./scripts/docker-cli run page create --title ... --description ... --category <slug> --markdown ...`
2. Draft article/project writes automatically return a preview URL. Always share it with the user.
3. When a preview already exists, keep using its existing URL. Never revoke or regenerate it just because content was updated; updating the article changes the content behind the existing preview URL.
4. After every successful page, article, project, or category operation, share the URL returned by the CLI without waiting for the user to ask.
5. Only publish when the user explicitly says to publish.
   - `./scripts/docker-cli run article publish <slug>`
6. Blogs cannot have tags. If the user asks for tags on a blog, warn them.
7. Only use `--pinned` / `--sort-order` for projects when the user asks.
8. Pages are always private (no publish step). Categories must exist before creating a page in them. Create the category first with `./scripts/docker-cli run category create --name <name>`.
9. After every page operation, share the `dashboard_url` from the CLI output with the user so they can open `/d/<slug>` in the browser. If a browser pane is already open on that tab, tell the user to reload it.

## ChatGPT / Codex skill

The CLI ships a bundled skill (`content-pipeline`) that routes blog/project/service/page tasks to the right reference. Install it with:

```bash
./scripts/docker-cli run skill install
```

This copies `SKILL.md` plus `references/articles.md`, `references/projects.md`, and `references/pages.md` into the configured agent skill directory. Uninstall with `./scripts/docker-cli run skill uninstall`.

This file is the source of truth for the skill. If the user says "update the skill", update this section.
