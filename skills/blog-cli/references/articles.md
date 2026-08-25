# Blog posts reference

Blog posts are public articles on the personal site. They live under `/writing/<slug>` once published.

## Commands

```bash
# Create a draft (default)
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown "# My Post\n\nHello."

# Create from a markdown file
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown-file post.md

# List / show
blog-cli article list --type blog
blog-cli article show my-post

# Update
blog-cli article update my-post --title "A Better Title"
blog-cli article update my-post --markdown-file updated-post.md

# Preview link (returned automatically for drafts)
blog-cli article preview my-post

# Publish (only when the user explicitly says to publish / go live / ship it)
blog-cli article publish my-post --published-by agent

# Archive / restore
blog-cli article delete my-post
blog-cli article unarchive my-post
```

## Additional commands

```bash
# List all content or filter by type/status
blog-cli article list
blog-cli article list --type blog --status published

# Generate a preview link for a draft
blog-cli article preview my-post --ttl-hours 4

# Add or remove tags where supported
blog-cli article tags my-post
blog-cli article tag-add my-post --tag example
blog-cli article tag-remove my-post --tag example
```

## Response shapes

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
  "url": "<site-url>/writing/my-post?preview=abc123",
  "token": "abc123", "slug": "my-post",
  "expires_at": "2026-07-09T00:00:00Z"
}
```

## Slug rules

- The server slugifies the title or explicit slug input.
- Duplicate slugs receive `-2`, `-3` suffixes.
- Slugs are immutable after creation.
- Soft-deleted slugs remain reserved.
- Archived articles restore with their prior status.

## Rules

- Create as a **draft** unless the user explicitly says to publish.
- Blogs **cannot have tags**. If the user asks for tags on a blog, warn them. Tags are only for projects.
- Keep any existing preview link stable. Never revoke or regenerate a preview just because content was updated.
- Always share the returned article URL or preview URL with the user after a successful operation.
- Plain typography. No emoji, arrows, or dingbats unless explicitly requested.
- Plain Markdown for body content (no MDX components on blog posts in v1).
