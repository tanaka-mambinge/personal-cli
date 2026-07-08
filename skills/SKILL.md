# Skill: Blog CLI Management

Use `blog-cli` as the canonical way to create and manage blog articles. The CLI talks to a FastAPI backend over HTTP.

## Auth

- The CLI sends `Authorization: Bearer <key>` automatically when `PERSONAL_API_KEY` is set
- Use `--insecure` if the server has a self-signed cert

## Commands

### `blog-cli article create`

- Required: `--title`, `--description`, `--type` (`blog` or `project`)
- Body: `--markdown` (inline) or `--markdown-file`
- Optional: `--slug`, repeated `--tag`, `--status` (defaults to `draft`)
- Output: full article JSON

### `blog-cli article list`

- Optional: `--type` (`all`, `blog`, `project`), `--status`
- Output: array of summaries

### `blog-cli article show <slug>`

- Output: full article JSON
- Returns 404 for drafts without preview token

### `blog-cli article update <slug>`

- Optional: `--title`, `--description`, `--type`, `--tag`, `--status`, markdown
- Output: updated article JSON

### `blog-cli article preview <slug>`

- Generates a time-limited preview URL for a draft
- `--ttl-hours` (default 24, max 168)
- Reuses existing valid token; creates new if expired
- Output: `{ url, token, slug, expires_at }`

### `blog-cli article publish <slug>`

- Optional: `--published-by`
- Output: full article with `status="published"`

### `blog-cli article unarchive <slug>`

- Restores a soft-deleted article

### `blog-cli article delete <slug>`

- Soft delete (archive). Output: `{ deleted, slug, deleted_at }`

### `blog-cli media upload --name <name> <path>`

- Name is the unique key used in markdown references
- Same name → 409 Conflict
- Output: `{ id, name, filename, content_type, url, length }`

### `blog-cli media update --name <name> <path>`

- Replaces file for existing media name
- Output: media object

### `blog-cli media delete --name <name>`

- Soft delete. Output: `{ deleted, name, deleted_at }`

## Markdown Media References

```markdown
![Hero image](hero-image)

<video controls width="100%" src="ambulance-video"></video>
```

Names map to `/api/v1/media/{name}`. The site resolves them to full URLs.

## JSON Shapes

### Full article
```json
{
  "id": "slug", "slug": "slug", "title": "Title",
  "description": "One line", "markdown": "# Body\n",
  "tags": ["tag"], "type": "blog", "status": "draft",
  "created_at": "2026-07-08T00:00:00Z",
  "updated_at": "2026-07-08T00:00:00Z",
  "published_at": null, "published_by": null,
  "preview_expires_at": null
}
```

### Article list item
```json
{
  "id": "slug", "slug": "slug", "title": "Title",
  "description": "One line", "type": "blog", "status": "draft",
  "updated_at": "2026-07-08T00:00:00Z", "published_at": null
}
```

### Preview response
```json
{
  "url": "https://personal.localhost:1355/blog/my-post?preview=abc123",
  "token": "abc123", "slug": "my-post",
  "expires_at": "2026-07-09T00:00:00Z"
}
```

### Media object
```json
{
  "id": "abc123", "name": "hero-image",
  "filename": "hero.jpg", "content_type": "image/jpeg",
  "url": "/api/v1/media/hero-image", "length": 123456
}
```

## Slug Rules

- Server slugifies title or explicit slug input
- Duplicate slugs get `-2`, `-3` suffix
- Slugs are immutable after creation
- Soft-deleted slugs remain reserved
- Archived articles restore with their prior status

## Agent Workflow

1. Create draft with `article create` (defaults to draft)
2. Upload media with `media upload --name <name> <path>`
3. Reference media by name in markdown
4. Generate preview link with `article preview <slug>`
5. Share link — recipient sees draft with countdown banner
6. Publish with `article publish <slug>`
7. Always pass `--json` for programmatic inspection
