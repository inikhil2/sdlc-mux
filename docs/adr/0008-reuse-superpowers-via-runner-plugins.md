# ADR 0008: Reuse Superpowers through each runner's own plugin route

Status: accepted (2026-11-09)

## Context

Prompt.md section 9 assumes a vendored clone copied into skill dirs for runners without a native route. The survey (docs/reference/superpowers.md) found all three runners have a documented plugin route, and the README says each harness needs its own install. Superpowers is MIT licensed.

## Decision

Do not copy or vendor Superpowers into this repo. `sdlc superpowers install` prints (and may run, when asked) the runner's plugin commands. A vendored checkout is a fallback only. Pin `v7.0.2`.

## Consequences

Less code and no licence-redistribution concern. `sdlc superpowers verify` cannot rely on a fixed skill directory, because plugin install locations are UNVERIFIED. T7 must resolve this.
