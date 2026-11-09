# Runner: GitHub Copilot CLI

## What you will learn

- How sdlc-mux drives Copilot CLI (`copilot`).
- Which flags are used and what is UNVERIFIED.
- How to mix Copilot with other runners.

**Copilot CLI is not installed on the build machine.** Everything here comes from GitHub's documentation read on 2026-11-09, never from `copilot --help` or a run. Sources are in the [runners reference](reference/runners.md).

## Install and log in

```bash
brew install --cask copilot-cli
```
Run: no, install command (D1) and Copilot CLI is not installed here. Docs-verified only. Other routes from the same page: `npm install -g @github/copilot` (Node 22+) and `winget install GitHub.Copilot`. Note the build brief says `brew install copilot-cli`; the docs say `--cask`.

Login detection without reading credentials was not looked up (UNVERIFIED). Log in from Copilot's own prompt.

## Flags sdlc-mux builds

| Purpose | Command shape | Status |
|---|---|---|
| Interactive with a starting prompt | `copilot -i "<prompt>"` | VERIFIED (docs only) |
| Headless | `copilot -p "<prompt>"` | VERIFIED (docs only) |
| Autonomous mode | `--allow-tool=write` (Copilot has no sandbox, so only file writes are pre-approved) | the flag is documented; whether `write` is the right tool name is UNVERIFIED |
| Unsafe (only with `--i-understand-the-risks`) | `--allow-all-tools` | VERIFIED (docs only) |
| `--yolo` | not used | UNVERIFIED as a CLI flag (documented only as the slash command `/yolo`) |

The argv sdlc builds (it only builds and prints; `copilot` is never executed):

```bash
uv run python -c "
from pathlib import Path
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle
b = Bundle('backend-engineer','build','demo',Path('brief.md'),Path('out'))
r = RUNNERS['copilot']()
print(r.build_command(b,'PROMPT','supervised',True))
print(r.build_command(b,'PROMPT','supervised',False))"
```
Run: yes, output below (prints argv only; Copilot not executed)

```text
['copilot', '-p', 'PROMPT']
['copilot', '-i', 'PROMPT']
```

## Quirks

- Copilot reads skills from `.github/skills`, `.claude/skills` and `.agents/skills` (docs). sdlc syncs to `.claude/skills` and `.agents/skills` only ([ADR 0009](adr/0009-reuse-agents-skills-dir.md)).
- `AGENTS.md` is supported according to the command reference (`--no-custom-instructions` turns it off).
- Superpowers for Copilot: `copilot plugin marketplace add obra/superpowers-marketplace`, then `copilot plugin install superpowers@superpowers-marketplace` (README text, not executed). See [Superpowers](09-superpowers.md).

## Mixing runners in one team

The Prompt design gives the `sdet` role to Copilot. In `sdlc.yaml` that is one line, after Copilot is installed:

```yaml
- {role: sdet, runner: copilot}
```
Run: no, this is a configuration snippet, not a command. Copilot CLI is not installed here.

## Try it

After installing and logging in, run `sdlc doctor` and look for `runner copilot (copilot)`. The build could not do this.

```bash
uv run sdlc doctor
```
Run: yes, output below (the build machine has no `copilot`, and the default config does not use it, so the output is the same as in [start here](00-start-here.md); no copilot row appears)

```text
[ok]      runner claude (claude)
```
