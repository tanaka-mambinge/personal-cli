# Services reference

Services are public offerings on the personal site. They live under `/services/<slug>` immediately after creation.

## Commands

```bash
# Create a published service category
blog-cli service create \
  --title "Web" \
  --summary "Websites and web apps for clear public-facing information." \
  --category web \
  --offering "Static websites|Focused, fast sites for a clear message.|web-category-image" \
  --offering "Web apps|Useful software with the workflows and data needed to run it.|web-apps-image" \
  --markdown-file service.md

# Homepage feature and ordering controls
blog-cli service update web --featured --home-title "Build the first version of your idea" \
  --home-summary "You have an idea but are not ready for a big build." \
  --home-sort-order 3

# Example links can be repeated; use an empty list until examples exist
blog-cli service update static-websites \
  --example "Project name|https://example.com"

# List / show
blog-cli service list
blog-cli service list --category web
blog-cli service show static-websites

# Remove a service category
blog-cli service delete static-websites
```

## Rules

- Services are published immediately; there is no draft or publish step.
- A service record represents one category, such as `web`, `ai`, `chatbots`, or `automation`.
- Use repeated `--offering` values for the individual services under that category.
- Offering values use `Title|Explanation[|MediaNameOrImageURL]`. The explanation and image are stored with the service record and rendered dynamically.
- `--type` remains available for short labels while existing records are being expanded into structured offerings.
- `--home-title`, `--home-summary`, `--home-next-step`, and `--home-sort-order` control the featured homepage presentation without changing the category detail page.
- Example values use `Title|URL` and can be repeated. Use `--clear-examples` to remove them.
- Always share the returned public URL after a successful operation.
- Plain Markdown for service details; do not add pricing unless requested.
