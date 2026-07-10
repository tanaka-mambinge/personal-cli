# blog-cli

Agent-friendly CLI for managing a personal blog. Create drafts, upload media, generate time-limited preview links — all from the command line.

Designed for use by both humans and AI agents.

## Install

```bash
pip install blog-cli
```

Or via pipx/uv:

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

All three are required:

```bash
export PERSONAL_SERVER_URL="<your-server-url>"
export PERSONAL_API_KEY="<your-api-key>"
export PERSONAL_SITE_URL="<your-site-url>"
```

## Usage

### Articles

```bash
# Create a draft
blog-cli article create \
  --title "My Post" \
  --description "A short summary" \
  --type blog \
  --cover-image my-post-cover \
  --markdown "# My Post\n\nHello."

# List published blog posts
blog-cli article list --type blog

# Show an article
blog-cli article show my-post

# Update an article
blog-cli article update my-post --title "Better Title"

# Set or clear the cover image
blog-cli article update my-post --cover-image my-post-cover
blog-cli article update my-post --clear-cover-image

# Generate a 24h preview link for a draft
blog-cli article preview my-post

# Custom TTL (1–168 hours)
blog-cli article preview my-post --ttl-hours 4

# Publish
blog-cli article publish my-post --published-by agent

# Delete (soft)
blog-cli article delete my-post

# Unarchive (restore deleted)
blog-cli article unarchive my-post
```

All commands support `--json` for machine-readable output and `--server-url` to override the server.

### Media

```bash
# Upload (name is the unique key used in markdown)
blog-cli media upload --name hero-image ./hero.jpg

# Update (replace the file, keep the name)
blog-cli media update --name hero-image ./new-hero.jpg

# Delete (soft)
blog-cli media delete --name hero-image
```

### Markdown Image References

Upload media with a name, then reference it in article markdown:

```markdown
![Hero image](hero-image)

<video controls width="100%" src="ambulance-video"></video>
```

The site resolves these to full URLs automatically.

## Testing

```bash
uv run pytest -v
```

Spins up a temp MongoDB + server via test fixtures. No external deps needed.

## Architecture

```
CLI (httpx) → FastAPI server → Motor/GridFS → MongoDB
```

- **Public endpoints** (GET) — list and read published articles, download media
- **Protected endpoints** (POST/PATCH/PUT/DELETE) — require `Authorization: Bearer <key>`

## License

MIT
