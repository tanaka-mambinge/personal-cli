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

## Release workflow

The publish pipeline is tag-triggered. Do not use a manual workflow-dispatch
command.

1. Bump the package version in both `pyproject.toml` and `uv.lock`.
2. Commit the release:

   ```bash
   git add pyproject.toml uv.lock
   git commit -m "Release blog-cli 0.4.2"
   ```

3. Create an annotated tag matching that version:

   ```bash
   git tag -a v0.4.2 -m "Release blog-cli 0.4.2"
   ```

4. Push the branch and tag through the HTTPS `origin` remote:

   ```bash
   git push origin main
   git push origin v0.4.2
   ```

Pushing the `v*.*.*` tag triggers `.github/workflows/publish.yml`, which runs
the tests, builds the distributions, and publishes `blog-cli` to PyPI.

## Important

Always use `./scripts/docker-cli test` for tests and
`./scripts/docker-cli run ...` for local CLI commands. Never run the checkout
with a host-level CLI binary.

## User-facing skill boundary

The user-facing skill is `skills/blog-cli/SKILL.md`. Keep that file focused on
using the installed `blog-cli`: installation, credentials, content routing,
commands, and content workflow.

Never put Docker instructions, `scripts/docker-cli`, test commands, repository
setup, release procedures, or other maintainer-only details in the skill. Keep
those instructions in this `AGENTS.md` file instead.

## Content workflow skill

Whenever creating, editing, or updating articles/projects for the personal site, default to **draft first**. Keep any existing preview link stable unless the user explicitly asks for a new one.

Writing and presentation rules:

- Use plain, readable typography in article content. Never add decorative Unicode symbols, emoji, arrows, dingbats, or other funny-looking font icons unless the user explicitly requests them.
- Prefer ordinary words, punctuation, and simple Markdown.

Rules:

1. Create content as a draft unless the user explicitly says to publish / go live / ship it.
   - Blog: `./scripts/docker-cli run article blog create --title ... --description ... --markdown ...`
   - Project: `./scripts/docker-cli run article project create --title ... --description ... --markdown ...`
2. Draft article/project writes automatically return a preview URL. Always share it with the user.
3. When a preview already exists, keep using its existing URL. Never revoke or regenerate it just because content was updated; updating the article changes the content behind the existing preview URL.
4. After every successful article, project, or service operation, share the URL returned by the CLI without waiting for the user to ask.
5. Only publish when the user explicitly says to publish.
   - `./scripts/docker-cli run article publish <slug>`
6. Blogs cannot have tags. If the user asks for tags on a blog, warn them.
7. Only use `--pinned` / `--sort-order` for projects when the user asks.

## ChatGPT / Codex skill

The repository skill lives at `skills/blog-cli/SKILL.md`. It is loaded by agents from the repository and is not managed through CLI commands. If the user says “update the skill”, update that file.
