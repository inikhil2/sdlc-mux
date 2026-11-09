# ADR 0007: Zellij as a planned-only optional backend

Status: accepted (2026-11-09)

## Context

Zellij is a possible second backend (KDL layouts, one tab per section). Building and testing it is a large extra scope, and it is not installed here. Plan decision D7 limits it to documentation.

## Decision

Do not write a working Zellij backend in v1. `multiplexer/zellij.py` raises a clear 'not implemented in v1' error. Docs label it `planned`.

## Consequences

No false claims of Zellij support. The base interface keeps the door open. Users who prefer Zellij cannot use it yet.
