# ADR 0004: AGENTS.md as shared instructions for all runners

Status: accepted (2026-11-09)

## Context

Three runners each have an instruction-file convention. Copilot CLI documents `AGENTS.md` support (docs, 2026-11-09). Codex `AGENTS.md` support and Claude Code's `@AGENTS.md` import were not confirmed in this survey (UNVERIFIED, see docs/reference/runners.md).

## Decision

Write shared rules once in `AGENTS.md`, under 300 lines. `CLAUDE.md` holds `@AGENTS.md` plus Claude-specific notes. Only the runner adapter layer may know runner-specific details.

## Consequences

One file to maintain. If the Claude import or Codex loading turns out not to work, T2 must change `CLAUDE.md` or the bootstrap prompt to inline the content; check before relying on it.
