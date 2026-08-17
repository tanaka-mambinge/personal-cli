# blog-cli

Agent-friendly CLI for managing a personal blog: create drafts, upload media, generate preview links, publish articles, and manage project tags.

## Install

From PyPI:

```bash
pip install blog-cli
```

Or install it as an isolated command-line tool:

```bash
pipx install blog-cli
uv tool install blog-cli
```

For development:

```bash
git clone https://github.com/tanaka-mambinge/personal-cli
cd personal-cli
uv sync --extra dev
```

## Configure

The CLI requires the API URL and API key. The site URL is required for preview links.

```bash
export PERSONAL_SERVER_URL="https://api.example.com"
export PERSONAL_API_KEY="your-api-key"
export PERSONAL_SITE_URL="https://example.com"
```

For local development, put the same variables in a `.env` file in the current directory. Do not commit that file.

Production installations use the same environment variables. For example:

```bash
PERSONAL_SERVER_URL="https://api.example.com" \
PERSONAL_API_KEY="your-production-api-key" \
PERSONAL_SITE_URL="https://example.com" \
blog-cli article list --type blog
```

All commands support `--json` for machine-readable output and `--server-url` to override the configured API URL for one command. Commands also support `--insecure` to skip TLS certificate verification when needed for local development.

Check the installed version:

```bash
blog-cli version
```

## Articles

### Create a blog post

Blog posts are drafts by default:

```bash
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown "# My Post\n\nHello."
```

Use a Markdown file instead:

```bash
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown-file post.md
```

### Create a project

```bash
blog-cli article project create \
  --title "My Project" \
  --description "A short summary" \
  --tag python \
  --tag agents \
  --markdown-file project.md
```

Projects can also use `--pinned` and `--sort-order`.

### List and show articles

```bash
# List all articles
blog-cli article list

# List published blog posts
blog-cli article list --type blog --status published

# List projects
blog-cli article list --type project

# Show one article
blog-cli article show my-post
```

### Update an article

```bash
blog-cli article update my-post --title "A Better Title"
blog-cli article update my-post --description "An updated summary"
blog-cli article update my-post --markdown-file updated-post.md
blog-cli article update my-post --cover-image hero-image
blog-cli article update my-post --clear-cover-image
```

The update command also accepts `--type`, `--status`, `--tag`, `--pinned`, `--not-pinned`, and `--sort-order`.

### Preview and publish

Generate a time-limited preview link:

```bash
blog-cli article preview my-post
blog-cli article preview my-post --ttl-hours 4
```

Override the configured site URL for a preview:

```bash
blog-cli article preview my-post --site-url https://preview.example.com
```

Revoke an existing preview link:

```bash
blog-cli article revoke-preview my-post
```

Publish an article explicitly:

```bash
blog-cli article publish my-post --published-by agent
```

Archive or restore an article:

```bash
blog-cli article delete my-post
blog-cli article unarchive my-post
```

### Project tags

```bash
# List tags on a project
blog-cli article tag-list my-project

# Add tags
blog-cli article tag-add my-project --tag python --tag agents

# Remove a tag
blog-cli article tag-remove my-project --tag agents
```

## Categories

Categories are first-class models that group private content pages. The slug is auto-derived from the name. A category cannot be deleted while pages still belong to it.

```bash
# Create (slug auto from name, e.g. "YouTube Notes" -> "youtube-notes")
blog-cli category create --name "Ideas" --icon bulb --description "Captured ideas"

# List / show / update / delete
blog-cli category list
blog-cli category show ideas
blog-cli category update ideas --name "Idea Box" --icon lightbulb
blog-cli category delete ideas
```

## Pages

Pages are private content shown only on the dashboard at `/d/<slug>`. They are for your eyes only. Each page belongs to a category and supports MDX with prebuilt components (`<Callout>`, `<Steps>`, `<ImageGrid>`, `<Video>`, `<Figure>`).

```bash
# Create a page
blog-cli page create \
  --title "An idea" \
  --description "Short summary" \
  --category ideas \
  --tag web --tag ai \
  --markdown-file idea.mdx

# List (optionally filter by category)
blog-cli page list
blog-cli page list --category ideas

# Show / update / delete
blog-cli page show an-idea
blog-cli page update an-idea --title "A better title"
blog-cli page update an-idea --markdown-file updated.mdx
blog-cli page delete an-idea
```

Page bodies are MDX. Referenced media uses names uploaded via `blog-cli media upload --name <name> <file>`; the site resolves names to media URLs at render time.

## ChatGPT / Codex skill

The CLI ships a bundled `content-pipeline` skill that routes blog, project, and page tasks to the right reference doc. Install it into the user-level skills directory:

```bash
blog-cli skill install
blog-cli skill uninstall
blog-cli skill path
```

## Media

Upload media using a stable name, then reference that name from article Markdown:

```bash
blog-cli media upload --name hero-image ./hero.jpg
```

Replace an existing file without changing its name:

```bash
blog-cli media update --name hero-image ./new-hero.jpg
```

Soft-delete media:

```bash
blog-cli media delete --name hero-image
```

Markdown references use the media name:

```markdown
![Hero image](hero-image)

<video controls width="100%" src="demo-video"></video>
```

The site resolves these names to their full media URLs.

## Publishing new CLI versions

The repository includes a GitHub Actions workflow at `.github/workflows/publish.yml`. It runs when you push a version tag matching `v*.*.*` and will:

1. Install dependencies with uv.
2. Run the test suite.
3. Build the wheel and source distribution with `uv build --no-sources`.
4. Publish both distributions to PyPI with `uv publish`.

After configuring PyPI Trusted Publishing for the GitHub Actions workflow, release a new version with:

```bash
uv version --bump patch
git add pyproject.toml uv.lock
git commit -m "Release blog-cli"
git tag v0.2.4
git push origin main --tags
```

Use the version from `pyproject.toml` when creating the tag.

## Testing

```bash
uv run pytest -v
```

The CLI tests use an in-memory fake API client, so they run without MongoDB or the personal server. The CLI architecture is:

```text
blog-cli (httpx) → FastAPI server → MongoDB/GridFS
```

## License

MIT
