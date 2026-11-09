# ADR 0003: Orchestrator-owned gates

Status: accepted (2026-11-09)

## Context

An LLM agent can claim a gate passed when it did not. Process rules must hold even when an agent is wrong or over-confident. Prompt.md section 1 rule 6 requires plain Python to own state transitions, gate checks and retries.

## Decision

Gates are Python validators in `gates.py`. The orchestrator runs them after an agent reports done and advances or retries the item. Agents produce artifacts and report status. They never write a gate status and the protocol skill says so. The one override is a human running `sdlc approve`, which is logged.

## Consequences

Gate results are deterministic and testable with pass and fail fixtures. Role skills must name only output paths that a validator checks (a test enforces this). A gate that checks too little can pass bad work, so validators must be reviewed like code.
