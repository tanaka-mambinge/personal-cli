# Blog posts reference

Blog posts are public articles on the personal site. They live under `/writing/<slug>` once published.

## Commands

```bash
# Create a draft (default)
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown "# My Post\n\nHello."

# Create from a markdown file
blog-cli article blog create \
  --title "My Post" \
  --description "A short summary" \
  --markdown-file post.md

# List / show
blog-cli article list --type blog
blog-cli article show my-post

# Update
blog-cli article update my-post --title "A Better Title"
blog-cli article update my-post --markdown-file updated-post.md

# Preview link (only when the user asks)
blog-cli article preview my-post

# Publish (only when the user explicitly says to publish / go live / ship it)
blog-cli article publish my-post --published-by agent

# Archive / restore
blog-cli article delete my-post
blog-cli article unarchive my-post
```

## Rules

- Create as a **draft** unless the user explicitly says to publish.
- Blogs **cannot have tags**. If the user asks for tags on a blog, warn them. Tags are only for projects.
- Keep any existing preview link stable. Never revoke or regenerate a preview just because content was updated.
- Only show the user the preview URL when they ask, and ask if they want changes.
- Plain typography. No emoji, arrows, or dingbats unless explicitly requested.
- Plain Markdown for body content (no MDX components on blog posts in v1).
