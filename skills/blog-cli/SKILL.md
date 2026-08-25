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

Credentials are stored in the configured keyring backend. On first run the CLI
prints a setup URL to stderr. Open it, enter the server URL, API key, and site
URL, and submit. They are validated against the server before saving.

Local development commands use the repository's Docker runner, which has its
own file-backed keyring and never accesses the host keyring.

When credentials are missing during a Docker run, keep the interactive command
attached and relay the exact setup URL from stderr as a clickable link. The user
enters credentials on that page; never ask them to paste secrets into chat or
start a second setup session. After submission, allow the original command to
retry and share its result.

## Content routing

Load the matching reference before acting:

- Articles and blog posts: `references/articles.md`
- Projects and work: `references/projects.md`
- Public services: `references/services.md`
- Shared media: `references/media.md`

If a request spans multiple content types, load each matching reference.

## Universal workflow

- Run local commands through `scripts/docker-cli`.
- Use `--json` when output will be inspected or passed to another command.
- Create articles and projects as drafts unless the user explicitly asks to publish.
- Services are public immediately when created.
- Keep existing preview links stable when content is updated.
- Share the returned public or preview URL after a successful operation.
- Use plain, readable typography and ordinary Markdown without emoji, arrows, or dingbats unless explicitly requested.
