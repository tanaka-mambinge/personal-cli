# Shared media reference

Media is shared by articles, projects, and services. Upload it before
referencing it by name in Markdown or structured service offerings.

## Commands

```bash
# Upload a new file
blog-cli media upload --name hero-image ./hero.jpg

# Replace an existing file
blog-cli media update --name hero-image ./new-hero.jpg

# Soft-delete a file
blog-cli media delete --name hero-image
```

## Rules

- The media name is the unique key used in Markdown references.
- Uploading an existing name returns `409 Conflict`; use `media update` to replace it.
- Media deletion is soft deletion.

## Markdown references

```markdown
![Hero image](hero-image)

<video controls width="100%" src="ambulance-video"></video>
```

Names map to `/api/v1/media/{name}` and the site resolves them to full URLs.

## Response shape

```json
{
  "id": "abc123", "name": "hero-image",
  "filename": "hero.jpg", "content_type": "image/jpeg",
  "url": "/api/v1/media/hero-image", "length": 123456
}
```
