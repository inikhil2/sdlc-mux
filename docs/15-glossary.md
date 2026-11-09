# Glossary

## What you will learn

Short definitions of the words used across the docs, in alphabetical order. The longer explanations are in [concepts](01-concepts.md).

- **ADR**: architecture decision record, a short file in `docs/adr/` that records one decision and why.
- **Agent**: a running instance of a role bound to one runner.
- **AGENTS.md**: the shared instruction file for all runners ([ADR 0004](adr/0004-agents-md-shared-instructions.md)).
- **Artifact**: a file an agent produces, for example `vision.md`.
- **Autonomous mode**: headless runs without prompts; opt-in.
- **Board**: the SQLite database holding each work item's state.
- **Devcontainer**: a Docker-based dev environment; files written, not run.
- **Doctor**: `sdlc doctor`, the prerequisite check.
- **Gate**: a machine-checked condition required to leave a stage.
- **Handoff**: a Markdown message between roles.
- **Headless**: a runner invoked without an interactive screen (`claude -p`, `codex exec`, `copilot -p`).
- **Mock runner**: the offline deterministic runner.
- **Mode**: `supervised` or `autonomous`.
- **Multiplexer**: a terminal tool that splits one window into many panes; tmux here.
- **Orchestrator**: the plain Python driver that moves work items and checks gates.
- **Pane**: one rectangle in the tmux window.
- **Planned**: documented but with no working code (Zellij).
- **Role**: an agent type with a mission and a definition of done.
- **Runner**: the CLI that powers an agent.
- **Section**: a group of roles shown in one column.
- **Skill**: a folder with a `SKILL.md`.
- **Stage**: one step of the pipeline.
- **Superpowers**: the external skills library by obra, used as the process layer.
- **Supervised mode**: the runner's default approvals; the default.
- **tmux**: the required multiplexer.
- **UNVERIFIED**: not confirmed against a real `--help` or run; do not rely on it.
- **Work item**: a feature or story that moves through the pipeline.
- **Workspace**: the folder (default `workspace/`) holding the board and `runs/`.
- **WSL2**: Windows Subsystem for Linux 2, the supported Windows path in v1.
- **Zellij**: a terminal multiplexer; planned as an optional backend, not built.

## Try it

Look up a term from the terminal:

```bash
grep -n "^- \*\*Gate\*\*" docs/15-glossary.md
```
Run: yes, output below

```text
15:- **Gate**: a machine-checked condition required to leave a stage.
```
