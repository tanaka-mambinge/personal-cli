---
name: content-pipeline
description: Manage the personal content pipeline — blog posts, work/projects, public services, and private content pages. Use when the user asks to create, edit, update, list, or plan a blog post, project, service, idea, youtube note, or any private content page; when they mention categories like ideas/youtube/etc; or when they want to review a draft. Draft-first for articles and projects.
---

# Content pipeline skill

You manage three kinds of content for the personal site:

1. **Blog posts** — public writing. See `references/articles.md`.
2. **Work/projects** — public project entries. See `references/projects.md`.
3. **Pages** — private content (ideas, youtube notes, etc.) shown only on the dashboard at `/d`. See `references/pages.md`.
4. **Services** — public service offerings shown under `/services`. See `references/services.md`.

## How to route

- "write a blog post" / "article" / "essay" → load `references/articles.md`
- "project" / "work" / "showcase piece" → load `references/projects.md`
- "idea" / "youtube note" / "page" / "category page" / anything private → load `references/pages.md`
- "service" / "services" / "offer" → load `references/services.md`

Load the matching reference before acting. If a request spans multiple kinds (e.g. turn an idea page into a blog post), load both.

## Universal rules

- Default to **draft first** for blog posts and projects. Services are public immediately when created. A service record is a category; its structured offerings carry the individual services, explanations, and image references shown under that category.
- Use plain, readable typography. No decorative Unicode symbols, emoji, arrows, dingbats, or font icons unless the user explicitly asks for them.
- Prefer ordinary words, punctuation, and simple Markdown/MDX.
- Run all local commands through the repository's Docker runner; do not invoke a host-level checkout binary.
- Credential setup is interactive. If a Docker command reports missing credentials, keep the attached process alive and immediately relay the exact setup URL printed on stderr as a clickable Markdown link. Tell the user to enter the server URL, API key, and site URL there. Never ask them to paste credentials into chat, start a second setup session, or replace the URL while the current session is alive. After submission, let the original command retry and share its result and returned content link.
- Use `--json` when you need machine-readable output for further processing.
- After creating or updating a draft article/project, use the preview URL returned by the CLI and share it with the user automatically.
- For pages and categories, the CLI emits a `dashboard_url` field. Share that link with the user so they can review the page at `/d/<slug>` in the browser. If a browser pane is already open on that tab (ChatGPT desktop app), tell the user to reload it. The site uses `cache: "no-store"`, so a reload reflects the latest content immediately.
- For published articles/projects, share the returned public `url` automatically.
