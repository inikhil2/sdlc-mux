# Runner: Claude Code

## What you will learn

- How to install and log in to Claude Code (`claude`).
- The exact flags sdlc-mux uses and why.
- Quirks to know, and how to mix Claude Code with other runners.

Source of truth: [runners reference](reference/runners.md) (verified 2026-11-09 against `claude --help`, saved in [claude-help.txt](reference/claude-help.txt), and the Claude Code docs). Claude Code is the only real runner installed on the build machine, so it is the only one whose flags were checked against a real `--help`.

## Install and log in

Three routes exist; all three are UNVERIFIED (not looked up on the vendor site). `claude install` and `claude update` do exist per `claude --help`.

```bash
curl -fsSL https://claude.ai/install.sh | bash
```
Run: no, install command (D1). UNVERIFIED. Others: `brew install --cask claude-code`, `npm install -g @anthropic-ai/claude-code`.

Log in once by starting `claude` and following its prompt. sdlc-mux never reads or prints credentials; `doctor` only checks that the binary is on PATH.

```bash
claude --version
```
Run: yes, output below

```text
2.1.319 (Claude Code)
```

## Flags sdlc-mux uses

| Purpose | Command shape | Status |
|---|---|---|
| Interactive with a starting prompt | `claude "<prompt>"` | VERIFIED |
| Headless | `claude -p "<prompt>"` | VERIFIED |
| Supervised mode | no extra flags (the runner's default approval behaviour) | VERIFIED |
| Autonomous mode, headless | `--permission-mode acceptEdits --permission-prompts none` | VERIFIED (`--permission-prompts none` needs v2.1.259+) |
| Autonomous mode, interactive | `--permission-mode acceptEdits` | VERIFIED |
| Unsafe (only with `--i-understand-the-risks`) | `--dangerously-skip-permissions` | VERIFIED |

The argv sdlc builds (nothing is executed):

```bash
uv run python -c "
from pathlib import Path
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle
b = Bundle('backend-engineer','build','demo',Path('brief.md'),Path('out'))
r = RUNNERS['claude']()
print(r.build_command(b,'PROMPT','supervised',True))
print(r.build_command(b,'PROMPT','supervised',False))
print(r.build_command(b,'PROMPT','autonomous',True))"
```
Run: yes, output below (prints argv only)

```text
['claude', '-p', 'PROMPT']
['claude', 'PROMPT']
['claude', '--permission-mode', 'acceptEdits', '--permission-prompts', 'none', '-p', 'PROMPT']
```

Refusal without the risk flag:

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

## Quirks

- With `-p` and nothing setting a mode, Claude Code starts in Manual mode and a call that needs approval is denied (v2.1.302+). That is why headless autonomous runs set `acceptEdits`.
- Do **not** use `--bare` with a subscription login: it skips CLAUDE.md, hooks and skills and uses `ANTHROPIC_API_KEY`.
- Project skills go in `.claude/skills/<name>/SKILL.md`; `sdlc skills sync` copies them there ([roles and skills](10-roles-and-skills.md)).
- `CLAUDE.md` importing `@AGENTS.md` is UNVERIFIED (not looked up).

## Mixing runners in one team

Each agent in `sdlc.yaml` has its own `runner:`. Change one line to use another runner for one role, or override everything for a run with `--runner`:

```yaml
- {role: backend-engineer, runner: codex, instances: 2}
```
Run: no, this is a configuration snippet, not a command. Codex must be installed first; `sdlc doctor` then reports it.

## Try it

Confirm `claude` is found and see the headless argv above. To actually use Claude Code as the engine, run `sdlc run examples/expense-splitter.md` without `--runner mock`. That makes real model calls and was **not run** by the build.

```bash
uv run sdlc run examples/expense-splitter.md --workspace /tmp/sdlc-real
```
Run: no, it calls the real Claude Code and spends usage; not part of the build gates.
