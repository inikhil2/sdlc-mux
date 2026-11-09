# Troubleshooting

## What you will learn

- What every `sdlc doctor` line means and how to fix it.
- How to deal with tmux pane problems, WSL path problems, login problems, and missing skills.

The doctor prints one row per check: `[ok]` or `[MISSING]` plus `fix: <command>`. Any `[MISSING]` makes the exit code 1. Rows marked `(warning)` print as `[ok]` and never fail the check. The fix commands are written for macOS; on Ubuntu or WSL, install the same thing with `apt` or the vendor route.

## Doctor messages

| Message | Meaning | Fix |
|---|---|---|
| `python 3.12` missing | Python older than 3.12 | `uv python install 3.12`, then run through `uv run` |
| `uv` missing | uv not on PATH | `brew install uv` |
| `tmux` missing | the multiplexer is absent; `up` cannot work | `brew install tmux` (Ubuntu: `sudo apt install tmux`) |
| `runner claude (claude)` missing | `claude` not on PATH | the printed route is UNVERIFIED; see [Claude Code](06-runner-claude-code.md) |
| `runner codex (codex)` missing | `codex` not on PATH | printed route is UNVERIFIED; see [Codex](07-runner-codex.md) |
| `runner copilot (copilot)` missing | `copilot` not on PATH (needs Node 22+ for the npm route) | see [Copilot CLI](08-runner-copilot-cli.md) |
| `config <file>` missing, with a reason | `sdlc.yaml` is invalid | read the reason: unknown role, unknown stage, duplicate role in a section, unknown runner |
| `sdlc skills missing in <folder>: ... (warning)` | the role skills are not yet copied into `.claude/skills` or `.agents/skills` | `sdlc skills sync` |
| `superpowers for <runner> not verified ... (warning)` | sdlc cannot see a plugin install on disk | install the plugin and confirm inside the runner; see [Superpowers](09-superpowers.md). In `autonomous` mode this row fails instead of warning. |

Real examples:

```bash
uv run sdlc doctor --config codex.yaml
```
Run: yes, output below (a copy of sdlc.yaml with some runners switched to codex; Codex is not installed here)

```text
[MISSING] runner codex (codex)
          fix: npm install -g @openai/codex   (UNVERIFIED install route)
```

```bash
uv run sdlc doctor --config bad.yaml
```
Run: yes, output below (a copy with a misspelled role; trimmed)

```text
[MISSING] config bad.yaml
          fix: sections.0.agents.0.role: unknown role 'product-owner2'; known roles: product-owner, ...
```

## tmux pane problems

- **`no session 'sdlc'; run sdlc up`**: `attach`, `layout` or `chat` found no session. Run `sdlc up`.
- **Panes vanish instantly or the session dies on `up`**: a pane command failed to start, and tmux closes a pane when its command exits. The agent panes run `sdlc` from PATH, so install it with `uv tool install .` or check `which sdlc`. (While building these docs, a pane command with an unquoted path containing spaces did exactly this.)
- **Cannot scroll**: press the prefix (`Ctrl-b`) then `[`; `q` leaves. See [tmux keys](reference/tmux-keys.md).
- **Layout is a mess after resizing**: `sdlc layout --preset sections`, or `grid`, or `focus <section>`.
- **A pane shows an error trace**: run the same `sdlc agent-loop --role <role>` in a normal terminal to read it.

```bash
uv run sdlc attach
```
Run: yes, output below (no session was running; exit code 1)

```text
no session 'sdlc'; run `sdlc up`
```

## WSL path problems

- Keep the project under `~` in Ubuntu, not under `/mnt/c`: slower file access and file-watching problems. See [Windows with WSL2](04-install-windows-wsl.md). This guidance is UNVERIFIED on a real Windows machine.
- A tool installed on Windows is not visible inside WSL. Install runners inside Ubuntu.

## Login problems

`doctor` only checks that a binary exists, not that you are logged in. If a runner starts and immediately asks you to authenticate, start it by hand once (`claude`, `codex`, `copilot`) and log in at its own prompt. sdlc never reads or prints credentials. A headless `claude -p` run that needs approval is denied rather than asking ([Claude Code](06-runner-claude-code.md)).

## Missing skills

If an agent says it cannot find `sdlc-protocol` or `role-<name>`, run `sdlc skills sync` in the project root and rerun `sdlc doctor`. For Superpowers skills, see [Superpowers](09-superpowers.md).

## A work item stops with "needs a human"

After `max_retries` failed attempts the item is flagged `needs-human` and the run stops with exit code 1 and the reasons. Read `runs/logs/<item>/orchestrator.md`, fix the missing artifact, or record a human decision with `sdlc approve <item> <gate>` ([running a team](11-running-a-team.md)).

## Try it

Break your copy of `sdlc.yaml` on purpose (misspell a role), run `sdlc doctor --config <file>`, find the message in the table above, and fix it.
