# Runner: Codex CLI

## What you will learn

- How sdlc-mux drives Codex CLI (`codex`).
- Which flags are used and what is UNVERIFIED.
- How to mix Codex with other runners.

**Codex CLI is not installed on the build machine.** Everything about Codex comes from web pages read on 2026-11-09, never from `codex --help` and never from a run. Treat every flag as unconfirmed until you check it on your machine. Sources are in the [runners reference](reference/runners.md).

## Install and log in

```bash
brew install codex
```
Run: no, install command (D1) and Codex is not installed here. UNVERIFIED. Other route: `npm install -g @openai/codex` (UNVERIFIED).

Login detection without reading credentials was not looked up (UNVERIFIED). Log in from Codex's own prompt.

## Flags sdlc-mux builds

| Purpose | Command shape | Status |
|---|---|---|
| Interactive with a starting prompt | `codex "<prompt>"` | VERIFIED (docs only) |
| Headless | `codex exec "<prompt>"` | VERIFIED (docs only) |
| Autonomous mode | `--sandbox workspace-write` | VERIFIED (docs only) as a documented value; the choice of it for autonomous is UNVERIFIED in practice |
| Unsafe (only with `--i-understand-the-risks`) | `--dangerously-bypass-approvals-and-sandbox` | VERIFIED (docs only) |
| `--full-auto` | not used | UNVERIFIED (not listed on the page) |

The argv sdlc builds (it only builds and prints; `codex` is never executed):

```bash
uv run python -c "
from pathlib import Path
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle
b = Bundle('backend-engineer','build','demo',Path('brief.md'),Path('out'))
r = RUNNERS['codex']()
print(r.build_command(b,'PROMPT','supervised',True))
print(r.build_command(b,'PROMPT','supervised',False))"
```
Run: yes, output below (prints argv only; Codex not executed)

```text
['codex', 'exec', 'PROMPT']
['codex', 'PROMPT']
```

## Quirks and open questions

- The build brief lists `~/.codex/skills/` as Codex's user skills folder. The Codex docs list `~/.agents/skills/` instead, so sdlc uses `.agents/skills/` (project) and never writes a home folder ([ADR 0009](adr/0009-reuse-agents-skills-dir.md)). The `~/.codex/skills/` path is UNVERIFIED and likely wrong.
- Whether Codex loads `AGENTS.md` was not confirmed (UNVERIFIED).
- The approvals page was truncated when read, so other `--ask-for-approval` values may exist.
- Superpowers for Codex is installed in the CLI with `/plugins` (README text, not executed). See [Superpowers](09-superpowers.md).

## Mixing runners in one team

The default `sdlc.yaml` uses only `claude`. To give the engineers to Codex, change their `runner:` to `codex`. Then `sdlc doctor` checks the `codex` binary:

```bash
uv run sdlc doctor --config codex.yaml
```
Run: yes, output below (a copy of sdlc.yaml edited as described, on a machine without Codex; trimmed)

```text
[ok]      runner claude (claude)
[MISSING] runner codex (codex)
          fix: npm install -g @openai/codex   (UNVERIFIED install route)
```

Here `codex.yaml` is a copy of `sdlc.yaml` with most `runner: claude` entries changed to `runner: codex`, so both runners are listed.

## Try it

Run `sdlc run examples/expense-splitter.md --runner codex` only after Codex is installed and logged in; the build did not run it.

```bash
uv run sdlc run examples/expense-splitter.md --runner codex --workspace /tmp/sdlc-codex
```
Run: no, Codex is not installed on the build machine.
