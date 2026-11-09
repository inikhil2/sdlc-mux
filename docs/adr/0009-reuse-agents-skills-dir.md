# ADR 0009: Prefer one shared .agents/skills directory where runners allow it

Status: accepted (2026-11-09)

## Context

Docs (2026-11-09) show Codex reads `.agents/skills` and `~/.agents/skills`, and Copilot CLI reads `.github/skills`, `.claude/skills`, `.agents/skills`, `~/.copilot/skills` and `~/.agents/skills`. Claude Code reads `.claude/skills` and `~/.claude/skills` (no `.agents` path found).

## Decision

`skills_sync.py` copies role and protocol skills into `.claude/skills/` (Claude) and `.agents/skills/` (Codex and Copilot). It does not use `~/.codex/skills`, which Prompt.md lists but the Codex docs do not.

## Consequences

Two target directories instead of three. Behaviour for Codex and Copilot is from docs only, not a live run.
