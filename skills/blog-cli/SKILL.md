---
name: blog-cli
description: Use blog-cli to manage public articles, projects, services, and shared media. Load the matching reference for command details and content-specific rules.
---

# Blog CLI

Use this skill when managing the personal site's public content through
`blog-cli`: writing articles, work/projects, public services, or shared media.

## Install

```bash
pip install -U blog-cli
```

## Credentials

Credentials are stored in the configured keyring backend. On first run, or
when credentials are missing, the CLI prints a setup URL to stderr. Open it,
enter the server URL, API key, and site URL, and submit. They are validated
against the server before saving. Never paste credentials into chat.

## Content routing

Load the matching reference before acting:

- Articles and blog posts: `references/articles.md`
- Projects and work: `references/projects.md`
- Public services: `references/services.md`
- Shared media: `references/media.md`

If a request spans multiple content types, load each matching reference.

## Universal workflow

- Use `--json` when output will be inspected or passed to another command.
- Create articles and projects as drafts unless the user explicitly asks to publish.
- Services are public immediately when created.
- Keep existing preview links stable when content is updated.
- Share the returned public or preview URL after a successful operation.
- Use plain, readable typography and ordinary Markdown without emoji, arrows, or dingbats unless explicitly requested.
