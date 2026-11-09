# ADR 0002: SQLite board as the source of truth

Status: accepted (2026-11-09)

## Context

Items, states and assignments must survive `sdlc down`, be updated by several agent panes at once, and reject illegal state transitions. Options: Markdown files, JSON files, SQLite. Concurrent writers to flat files risk corruption; SQLite gives transactions and locking, and `sqlite3` is in the Python standard library, so there is no dependency.

## Decision

Keep all item state in a SQLite database. `BOARD.md` is a generated, read-only mirror for humans. Agents change state only through `sdlc board ...`, never by editing files.

## Consequences

One place to look for truth; transitions are enforceable in code and testable. Humans must not edit `BOARD.md` expecting changes to stick. Schema changes need a migration step.
