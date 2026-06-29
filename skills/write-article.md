# Skill: Write Article

Write articles for `personal-content` repo.

## articles.json (source of truth)

Add entry with:

```json
{
  "id": "next-number",
  "title": "Title",
  "description": "One-liner",
  "slug": "kebab-case",
  "date": "YYYY-MM-DD",
  "tags": ["tag"],
  "filename": "slug.md",
  "draft": true
}
```

`draft: true` = skip from published list.

## Article file

Path: `articles/{filename}`

Required frontmatter:

```yaml
---
title: "Title"
description: "One-liner"
date: YYYY-MM-DD
tags: [tag1, tag2]
---
```

Frontmatter fields must match `articles.json`.

## Rules

- Short paragraphs. 2-4 sentences.
- Active voice. No fluff.
- `##` and `###` headings only.
- Code blocks need language tag.
- No emojis unless needed.
- One sentence per line in source.

## Workflow

1. Write markdown in `articles/` with frontmatter
2. Add entry to `articles.json`
3. Commit together: `feat: add article "Title"`
