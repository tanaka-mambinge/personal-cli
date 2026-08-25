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

Credentials are stored in the configured keyring backend. There is no API-key
argument and credentials must never be pasted into chat.

When a command needs credentials, run it normally, for example:

```bash
blog-cli article list --json
```

If credentials are missing, the command prints an exact one-time setup URL and
waits. Immediately relay that URL as a clickable link and tell the user to open
it in a browser. The user enters the server URL, API key, and site URL in the
setup form. The form validates the values and saves them to the configured
credential store; the original command then retries automatically.

Keep the original command attached while the user completes setup. Do not ask
the user to send the API key in chat, start a second setup command, or invent a
replacement URL. After setup completes, share the command's result.

If the server rejects an existing key with `401` or `403`, tell the user the
stored key was rejected, keep the command attached, and relay the replacement
credential setup URL. Follow the same browser-only flow.

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
