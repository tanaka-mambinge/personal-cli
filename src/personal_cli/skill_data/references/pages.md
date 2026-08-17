# Private content pages reference

Pages are private content shown only on the dashboard at `/d/<slug>`. They are for your eyes only. Each page belongs to a category (e.g. `ideas`, `youtube`). Pages support MDX with prebuilt components.

## Commands

### Categories

A category is a first-class model. The slug is auto-derived from the name. Categories cannot be deleted while pages still reference them.

```bash
# Create a category (slug auto from name, e.g. "YouTube Notes" -> "youtube-notes")
uv run blog-cli category create --name "Ideas" --icon bulb --description "Captured ideas"
uv run blog-cli category create --name "YouTube" --icon video

# List / show
uv run blog-cli category list
uv run blog-cli category show ideas

# Update
uv run blog-cli category update ideas --name "Idea Box" --icon lightbulb --sort-order 1

# Delete (fails if pages still belong to it; reassign or delete those pages first)
uv run blog-cli category delete ideas
```

### Pages

```bash
# Create a page (draft-first still applies — no separate publish step exists for pages,
# but write the content as if it is for your eyes only)
uv run blog-cli page create \
  --title "An idea" \
  --description "Short summary" \
  --category ideas \
  --markdown-file idea.mdx

# List (optionally filter by category)
uv run blog-cli page list
uv run blog-cli page list --category ideas

# Show one
uv run blog-cli page show an-idea

# Update
uv run blog-cli page update an-idea --title "A better title"
uv run blog-cli page update an-idea --markdown-file updated-idea.mdx
uv run blog-cli page update an-idea --category youtube

# Delete
uv run blog-cli page delete an-idea
```

## MDX components

Page bodies are MDX. These prebuilt components are available. Use them as JSX inside the MDX body.

### `<Callout>`

A highlighted note box.

```mdx
<Callout type="info">
This is an informational note.
</Callout>

<Callout type="warning">
Be careful with this.
</Callout>

<Callout type="danger">
This will break things.
</Callout>
```

### `<Steps>`

A numbered step sequence. Wrap each `<Step>`.

```mdx
<Steps>
  <Step>First do this.</Step>
  <Step>Then do that.</Step>
  <Step>Finally ship it.</Step>
</Steps>
```

### `<ImageGrid>`

A 2 or 3 column image grid. Children are `<img>` tags referencing media names.

```mdx
<ImageGrid cols={2}>
  <img src="hero-image" alt="Hero" />
  <img src="screenshot-1" alt="Screenshot" />
</ImageGrid>
```

### `<Video>`

Embed a video from the media library by name.

```mdx
<Video src="demo-video" poster="poster-image" />
```

### `<Figure>`

A captioned figure.

```mdx
<Figure src="chart-1" caption="Q3 growth compared to Q2.">
</Figure>
```

## Media references

Images and videos referenced from MDX use media names (uploaded via `blog-cli media upload --name <name> <file>`). The site resolves the names to media URLs at render time. Do not paste full URLs.

```mdx
![Hero image](hero-image)

<Video src="demo-video" />
```

## Rules

- Pages are always private. There is no publish/archive step — they exist as soon as you create them.
- Categories must exist before you can create a page in them. Create the category first if it does not exist.
- Default to creating the page; do not ask for confirmation unless the user is clearly unsure.
- Plain typography. No emoji, arrows, or dingbats unless explicitly requested. MDX component props (e.g. `type="info"`) are fine.
- **Share the dashboard link with the user after every create/update/show.** The CLI output includes a `dashboard_url` field (JSON) or prints the page dict containing it. Pass that link to the user so they can open `/d/<slug>` in the browser to review. If a browser pane is already open on that tab (ChatGPT desktop app), tell the user to reload it — the site uses `cache: "no-store"`, so a reload reflects the latest content immediately.
