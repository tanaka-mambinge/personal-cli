---
name: content-pipeline
description: Manage the personal content pipeline — blog posts, work/projects, and private content pages. Use when the user asks to create, edit, update, list, publish, or plan a blog post, project, idea, youtube note, or any private content page; when they mention categories like ideas/youtube/etc; or when they want to review a draft in the dashboard. Draft-first. Reload the dashboard tab after each write.
---

# Content pipeline skill

You manage three kinds of content for the personal site:

1. **Blog posts** — public writing. See `references/articles.md`.
2. **Work/projects** — public project entries. See `references/projects.md`.
3. **Pages** — private content (ideas, youtube notes, etc.) shown only on the dashboard at `/d`. See `references/pages.md`.

## How to route

- "write a blog post" / "article" / "essay" → load `references/articles.md`
- "project" / "work" / "showcase piece" → load `references/projects.md`
- "idea" / "youtube note" / "page" / "category page" / anything private → load `references/pages.md`

Load the matching reference before acting. If a request spans multiple kinds (e.g. turn an idea page into a blog post), load both.

## Universal rules

- Default to **draft first**. Only publish / go live / ship when the user explicitly says to.
- Use plain, readable typography. No decorative Unicode symbols, emoji, arrows, dingbats, or font icons unless the user explicitly asks for them.
- Prefer ordinary words, punctuation, and simple Markdown/MDX.
- Run all commands with the installed `blog-cli ...` executable; do not assume the repository checkout is present.
- Use `--json` when you need machine-readable output for further processing.
- After creating or updating content, do NOT automatically generate a preview link. Only do so when the user asks.
- For pages and categories, the CLI emits a `dashboard_url` field. Share that link with the user so they can review the page at `/d/<slug>` in the browser. If a browser pane is already open on that tab (ChatGPT desktop app), tell the user to reload it. The site uses `cache: "no-store"`, so a reload reflects the latest content immediately.
