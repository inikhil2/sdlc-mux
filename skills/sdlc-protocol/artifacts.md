# Artifact standards

## Paths
- Everything goes under `workspace/runs/<item>/`. Never write outside it.
- Fixed names and folders: `vision.md`, `stories/`, `business-rules.md`, `screen-specs.md`, `plan.md`, `retro.md`, and the folders `design/`, `build/`, `test/`, `review/`, `release/`.
- Use the file names in your role skill exactly. Gates look for those names.

## Naming
- Name new free-form files `<item>-<artifact>.md`. Stories use `stories/<id>.md`. Build reports use `build/<task>-report.md`.

## Templates
- Start from the template your role skill names (they live in `src/sdlc_mux/templates/`). Keep every heading the template has. Fill each one. Do not leave `{{placeholders}}`.

## Style
- Plain Markdown. Short sentences. One idea per bullet.
- Headings for sections, bullets for lists, tables only for real tables.
- Diagrams are Mermaid in a fenced `mermaid` block. No images.
- Record facts you ran or read. If you did not run it, say "not run".
