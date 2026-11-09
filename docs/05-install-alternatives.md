# Install alternatives

## What you will learn

- Which multiplexer sdlc-mux uses, which one is only planned, and why.
- The other choices you have for packages, runtimes, Python tooling, the Windows path, runner installs, and the Superpowers install.

How to read the tables: the multiplexer facts come from the build's survey ([ADR 0001](adr/0001-tmux-primary-backend.md), [ADR 0007](adr/0007-zellij-planned-only.md)). The other tables are general guidance, not verified by this build, and are marked so. "Choose this if" is a judgment, not a measurement. Status words: **built** (code exists and has tests), **planned** (documented only, no working code), **not supported**.

## Multiplexer

| | tmux | Zellij | WezTerm mux |
|---|---|---|---|
| Status in sdlc-mux | **built, required** (v1) | **planned**, no working code (a stub raises "not implemented in v1") | not planned; not evaluated beyond being listed as an option in ADR 0001 |
| Setup effort | `brew install tmux` or `apt install tmux`; 3.7c is what the build tested | would need a KDL layout generator and tests | would need a backend written from scratch |
| Platform fit | macOS, Linux, WSL2 | macOS, Linux, WSL2 (not tested here) | not verified |
| Pros | Scriptable pane titles, borders and reflow; an isolated test server (`tmux -L sdlc-test`); verified by the integration tests in this repo | Layouts as files (KDL), one tab per section would map naturally | not verified |
| Cons | Keys are old-fashioned for new users ([tmux keys](reference/tmux-keys.md)) | Not built, so not tested; an extra surface to maintain | not verified |
| Choose this if | You want what works today | You want it later and can wait | You use WezTerm: it can still be your **host terminal** (it is listed as one in the install brief); tmux runs inside it |

Why tmux is built and Zellij is planned: one backend is enough for v1, and a second backend doubles the part of the code that must be kept correct and tested. tmux was built and is verified by tests here (pane count, titles, and section order are asserted on a private tmux server). Zellij would add KDL layouts as an extra surface, which needs its own generator and tests, and Zellij is not installed on the build machine. The backend interface in `multiplexer/base.py` leaves the door open. Nothing in the docs claims Zellij works.

## Package manager

Not verified by this build; general guidance.

| | Setup | Fits | Pros | Cons | Choose if |
|---|---|---|---|---|---|
| Homebrew | one installer script from brew.sh | macOS (also Linux) | what the macOS scripts and doctor fix messages assume | needs command line tools | you are on a Mac and want the default |
| MacPorts | installer package | macOS | alternative if you already use it | the doctor's fix commands name `brew`; translate them | you already run MacPorts |
| apt | built into Ubuntu | Ubuntu, WSL2 | no extra tool | package versions may lag | you are in WSL2 Ubuntu |
| winget | built into current Windows | Windows (host side only) | installs Windows Terminal | does not install anything inside WSL | you want a Windows host terminal |

## Runtime manager (Node, Python)

Not verified by this build. uv already manages Python for this project, so you mainly need Node, and only for runners installed through npm.

| | Pros | Cons | Choose if |
|---|---|---|---|
| mise | one tool for many runtimes | another tool to learn | you want one manager |
| asdf | long-established plugin model | slower, plugin-based | you already use it |
| fnm | fast, Node only | Node only | you only need Node on Linux or WSL |
| nvm | very common | slower shell start | you already use it |
| Volta | pins Node per project | more setup | you want per-project Node pins |

## Python tooling

| | Pros | Cons | Choose if |
|---|---|---|---|
| uv | the project's lockfile (`uv.lock`) and `uv run` are used throughout; installs Python 3.12 for you | one more tool | default |
| pipx | installs a CLI in isolation | does not manage Python versions; the docs and tests assume uv | you refuse uv (UNVERIFIED that it works end to end here) |
| plain venv | no extra tool | you manage Python 3.12 yourself | you cannot install uv (UNVERIFIED that it works end to end here) |

## Windows path

| | Status | Pros | Cons | Choose if |
|---|---|---|---|---|
| WSL2 | **supported in v1** ([guide](04-install-windows-wsl.md)); not tested by the build | real tmux | extra Linux install; runners must be installed inside it | you are on Windows |
| Devcontainer | files written, not run (see [installers](reference/installers.md)) | same environment on any OS with Docker | runner logins must be repeated inside, or config folders mounted read-only (trade-off: mounting shares your logins with the container) | you already use Docker Desktop |
| Native Windows | **not supported in v1** | none today | no tmux | do not choose |

## Runner install route

Install routes follow [runners reference](reference/runners.md): the Claude Code and Codex routes are UNVERIFIED; the Copilot routes are docs-verified, not run.

| | Pros | Cons | Choose if |
|---|---|---|---|
| native installer | vendor-supported path | pipes a script into a shell | you trust the vendor script |
| Homebrew | easy updates on macOS | cask vs formula names differ | you are on a Mac |
| npm | same command everywhere | needs Node (Copilot: Node 22+) | you already have Node |

## Superpowers install route

| | Pros | Cons | Choose if |
|---|---|---|---|
| runner-native plugin (built: `sdlc superpowers install` prints the commands) | no copy of Superpowers in this repo; the README documents each runner's route | `sdlc superpowers verify` cannot see plugin installs on disk, so it reports `[UNVERIFIED]` | default ([ADR 0008](adr/0008-reuse-superpowers-via-runner-plugins.md)) |
| vendored checkout (not built) | files visible on disk | not built; would copy another project's files | not available in v1 |

## Try it

Compare what is installed against what the doctor expects. This is the check that matters whichever route you pick:

```bash
uv run sdlc doctor
```
Run: yes, output below (trimmed; same as [start here](00-start-here.md))

```text
[ok]      python 3.12
[ok]      uv
[ok]      tmux
[ok]      runner claude (claude)
```

To see what the Zellij stub does, read `src/sdlc_mux/multiplexer/zellij.py`; it only raises the "planned" message.
