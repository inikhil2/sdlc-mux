# ADR 0005: WSL2 as the Windows path

Status: accepted (2026-11-09)

## Context

tmux does not run natively on Windows. Options: WSL2, a devcontainer, or a Windows-native multiplexer. No Windows-native multiplexer has been verified to support the layout code.

## Decision

Support Windows only through WSL2 with Ubuntu in v1. Native Windows is unsupported and the README says so. A devcontainer is a documented secondary path. Agent CLIs are installed inside WSL.

## Consequences

The same Linux code path serves WSL and Linux CI. Windows users need WSL2 and must keep repos on the Linux filesystem. CI on windows-latest runs non-tmux unit tests only.
