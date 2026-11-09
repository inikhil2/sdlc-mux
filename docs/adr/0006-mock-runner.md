# ADR 0006: Mock runner for offline use

Status: accepted (2026-11-09)

## Context

The pipeline must be demonstrable and testable with no AI account, no network and no cost. Real runners are non-deterministic and Codex and Copilot are not installed here.

## Decision

Ship a deterministic `MockRunner` that reads the task and writes the role's template artifacts from the brief. It is the default for demos, tests and CI.

## Consequences

End-to-end tests are repeatable and free. Mock output proves the orchestrator, board and gates work, not that real agents produce good work. Real-runner behaviour stays UNVERIFIED until a smoke test is run.
