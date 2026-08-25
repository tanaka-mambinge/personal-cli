# Shared media reference

Media is shared by articles, projects, and services. Upload it before
referencing it by name in Markdown or structured service offerings.

## Commands

```bash
# Upload a new file
blog-cli media upload --name hero-image ./hero.jpg

# Upload a replacement under a new cache-busting name
blog-cli media upload --name hero-image-20260825 ./new-hero.jpg

# Soft-delete a file
blog-cli media delete --name hero-image
```

## Rules

- The media name is the unique key used in Markdown references.
- Uploading an existing name returns `409 Conflict`; choose a new cache-busting
  name for replacements.
- Names are part of the media URL and are used for cache busting. When replacing
  media that is already referenced by live content, append a unique version or
  timestamp to the name, such as `service-ai-cover-17483874`.
- After uploading the replacement, update every article, project, or service
  reference to the new name and verify the live page before deleting the old
  asset.
- Do not use `media update` for a live replacement because it keeps the old
  cacheable URL. Use a new name and `media upload` instead.
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
