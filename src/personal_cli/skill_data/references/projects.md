# Projects / work reference

Projects are public showcase entries on the personal site. They live under `/work/<slug>` once published.

## Commands

```bash
# Create a project draft (a cover image is required)
uv run blog-cli article project create \
  --title "My Project" \
  --description "A short summary" \
  --cover-image hero-image \
  --tag python \
  --tag agents \
  --markdown-file project.md

# List / show
uv run blog-cli article list --type project
uv run blog-cli article show my-project

# Update (can change title, description, tags, cover image, status, pinned, sort-order)
uv run blog-cli article update my-project --title "A Better Title"
uv run blog-cli article update my-project --cover-image new-hero
uv run blog-cli article update my-project --clear-cover-image

# Project tags
uv run blog-cli article tag-list my-project
uv run blog-cli article tag-add my-project --tag python --tag agents
uv run blog-cli article tag-remove my-project --tag agents

# Preview link (only when the user asks)
uv run blog-cli article preview my-project

# Publish (only when the user explicitly says to publish)
uv run blog-cli article publish my-project --published-by agent

# Archive / restore
uv run blog-cli article delete my-project
uv run blog-cli article unarchive my-project
```

## Rules

- Create as a **draft** unless the user explicitly says to publish.
- Projects **must have a cover image**. Use `--cover-image <name>` with a name previously uploaded via `blog-cli media upload`.
- Projects can have tags; blogs cannot.
- Only use `--pinned` / `--sort-order` when the user asks. Lower `--sort-order` sorts first among pinned projects.
- Keep existing preview links stable. Never revoke or regenerate just because content was updated.
- Plain typography. No emoji, arrows, or dingbats unless explicitly requested.
- Plain Markdown for body content (no MDX components on projects in v1).
