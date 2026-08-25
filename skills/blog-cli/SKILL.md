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

If a command reports that authentication is required, start the credential
setup server separately:

```bash
blog-cli keys setup
```

Keep the setup command attached until it exits. Relay the exact setup URL it
prints as a clickable link. The user enters the server URL, API key, and site
URL in the browser form. The server stays running while invalid values are
corrected and exits only after valid credentials are saved. Then rerun the
original command. Never ask the user to send the API key in chat or start a
second setup server.

If the credential store is unavailable, report that setup cannot continue in
the current environment instead of asking for the API key in chat. If the
server rejects an existing key, run the same setup command to replace it.

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
