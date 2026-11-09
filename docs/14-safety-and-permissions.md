# Safety and permissions

## What you will learn

- The two modes, and which things are enforced by code versus only asked of the agents.
- How the `--i-understand-the-risks` flag works.
- What the build did **not** build.

## Two modes

| Mode | What it means | Where it is set |
|---|---|---|
| `supervised` (default) | Each runner's normal approval behaviour: the agent asks before risky actions. | `mode:` in `sdlc.yaml` |
| `autonomous` (opt-in) | Headless runs without prompts, limited to what the runner allows in its workspace. | `mode: autonomous` |

In autonomous mode the runner flags are: Claude Code `--permission-mode acceptEdits` (with `--permission-prompts none` when headless); Codex `--sandbox workspace-write` (UNVERIFIED in practice); Copilot `--allow-tool=write` (UNVERIFIED). Details and status per flag: [runners reference](reference/runners.md). The doctor also fails autonomous mode when Superpowers is not verified for a runner in use ([Superpowers](09-superpowers.md)).

## Enforced by code

- **The risk flag.** A profile that turns off approvals or sandboxing (`unsafe`) is refused unless you pass `--i-understand-the-risks`. Tested for all three runners.

```bash
uv run python -c "
from pathlib import Path
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle
b = Bundle('x','build','d',Path('b'),Path('o'))
RUNNERS['claude']().build_command(b,'P','unsafe',True)" 2>&1 | tail -1
```
Run: yes, output below

```text
sdlc_mux.runners.base.RiskRefusal: profile 'unsafe' disables sandboxing or approvals for claude; pass --i-understand-the-risks to allow it
```

- **sdlc's own writes stay inside the workspace.** Paths are resolved and a path that escapes is rejected.

```bash
uv run python -c "
from pathlib import Path
from sdlc_mux.agent_loop import safe_path
safe_path(Path('/tmp/sdlc-demo'), '..', 'etc', 'passwd')" 2>&1 | tail -1
```
Run: yes, output below

```text
ValueError: path '../etc/passwd' escapes the workspace /private/tmp/sdlc-demo
```

- **Time and retry limits.** `limits.max_minutes_per_task` (default 30) becomes the process timeout; `limits.max_retries` (default 2) caps retries, after which the item is flagged `needs-human`.
- **Gates and the board** are Python; an agent cannot mark a gate passed ([architecture](02-architecture.md)).
- **Human overrides are logged** by `sdlc approve` in `runs/logs/<item>/orchestrator.md`.
- **The mock runner makes no network calls.**

## Asked of the agents, not enforced

The `sdlc-protocol` skill tells every agent: write only to your role's outputs; never merge, push, or touch another agent's worktree; never read or print secrets or login files; do not call the network without approval; escalate by writing `needs-human.md`. These are instructions in a prompt. A runner that ignores them is limited only by the runner's own permission system, so prefer `supervised` mode with real runners.

## Not built

- A doctor warning for `.env` files in the workspace (the original brief asks for it; there is no such check in the code).
- Token-usage recording.
- The `sdlc board list|show|update` commands the protocol mentions.

## Native tools and `--bare`

sdlc does not pass Claude Code's `--bare`, which would skip CLAUDE.md, hooks and skills.

## Try it

Run the refusal command above, then confirm the default mode:

```bash
grep -n "^mode:" sdlc.yaml
```
Run: yes, output below

```text
7:mode: supervised                  # supervised | autonomous
```
