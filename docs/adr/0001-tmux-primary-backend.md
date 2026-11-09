# ADR 0001: tmux as the primary multiplexer backend

Status: accepted (2026-11-09)

## Context

sdlc-mux needs one window with many labelled, coloured panes that a script can create, retitle and reflow. The options are tmux, Zellij and WezTerm mux. tmux 3.7c is installed here, runs on macOS and Linux (so also WSL2), has scriptable pane titles (`pane-border-status`, `pane-border-format`), and supports an isolated test server (`tmux -L sdlc-test`). Reusing it means we write no terminal code ourselves.

## Decision

Use tmux as the only working backend. Session `sdlc`, one window `room`. Build a thin `multiplexer/base.py` interface so another backend can be added later. Build nothing that replaces tmux.

## Consequences

Integration tests can run on a private tmux server and skip when tmux is absent. Users must install tmux. Native Windows is out (see ADR 0005). Zellij is planned only (ADR 0007).
