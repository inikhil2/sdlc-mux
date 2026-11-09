# sdlc-mux

## What you will learn

- What sdlc-mux is and what it looks like when it runs.
- A 60-second quickstart for macOS, WSL2 Ubuntu, and a devcontainer.
- Where each doc lives, and who to credit.

**Windows requires WSL2 in v1.** Native Windows without WSL is not supported.

## What it is

sdlc-mux runs a small virtual software team in one tmux window. Each team member is an AI coding agent (Claude Code, Codex CLI, GitHub Copilot CLI, or an offline `mock` runner) with a role such as product owner, backend engineer, or security engineer. A work item moves through eight stages (discover, design, plan, build, test, review, release, retro). Plain Python moves the item and checks every gate; the agents only produce files and report. `sdlc up` opens a dashboard band on top and one column per section below.

Status, honestly: written and tested on macOS with Claude Code and the offline mock runner. The Codex and Copilot adapters are built from documentation and **never executed** (those CLIs were not installed); their flags are marked UNVERIFIED in the [runners reference](docs/reference/runners.md). The install scripts and the devcontainer are written but were not executed. The Zellij backend is **planned**, not built; tmux is the only working multiplexer.

## Quickstart (about 60 seconds)

### macOS (primary)

```bash
brew install tmux uv
```
Run: no, install command (D1). The build machine already had both.

```bash
git clone https://github.com/inikhil2/sdlc-mux && cd sdlc-mux && uv sync
```
Run: no, a clone of the remote; `uv sync` alone was run inside the existing checkout (output in [macOS install](docs/03-install-macos.md)).

```bash
uv run sdlc doctor
```
Run: yes, output below (the long skills line is trimmed)

```text
[ok]      python 3.12
[ok]      uv
[ok]      tmux
[ok]      runner claude (claude)
[ok]      sdlc skills missing in .claude/skills: sdlc-protocol, role-backend-engineer, ... (warning)
[ok]      superpowers for claude not verified (cannot check plugin installs on disk) (warning)
```

```bash
uv run sdlc run examples/expense-splitter.md --runner mock --workspace /tmp/sdlc-demo
```
Run: yes, output below (last line; the eight `gate ...: passed` lines come first)

```text
expense-splitter: done
```

Full steps: [install on macOS](docs/03-install-macos.md).

### WSL2 Ubuntu (Windows)

Windows requires WSL2 in v1. Install Ubuntu with WSL2, then inside Ubuntu:

```bash
sudo apt update && sudo apt install -y git tmux curl build-essential gh
```
Run: no, install command (D1) and not a Linux machine. Untested on Windows or Ubuntu.

Then install uv, clone this repo under `~` (not `/mnt/c`), run `uv sync` and `uv run sdlc doctor`. Full steps: [install on Windows with WSL2](docs/04-install-windows-wsl.md).

### Devcontainer (any OS with Docker)

Open the folder in VS Code and choose "Reopen in Container". `.devcontainer/post-create.sh` installs tmux, runs `uv sync` and `sdlc doctor`. Written, not executed; the uv feature name in `devcontainer.json` is UNVERIFIED. Runner logins must be repeated inside the container. See [installers](docs/reference/installers.md).

## Learn in the terminal

```bash
uv run sdlc learn
```
Run: yes, output below (first lines of 125; it prints docs 00 and 01, with diagrams replaced by a pointer)

```text
=== Part 1 of 2: docs/00-start-here.md ===

# Start here

## What you will learn

- What sdlc-mux is, in plain words, and what you see on screen when it runs.
- What "success" looks like after ten minutes.
- Which doc to read next.
```

## Docs index

| Doc | About |
|---|---|
| [00 Start here](docs/00-start-here.md) | ten-minute overview |
| [01 Concepts](docs/01-concepts.md) | every term, with a diagram |
| [02 Architecture](docs/02-architecture.md) | components, data flow, why SQLite, why code owns process |
| [03 macOS install](docs/03-install-macos.md) | primary path |
| [04 Windows with WSL2](docs/04-install-windows-wsl.md) | the Windows path |
| [05 Install alternatives](docs/05-install-alternatives.md) | tmux vs Zellij vs WezTerm mux, and other choices |
| [06 Claude Code](docs/06-runner-claude-code.md), [07 Codex](docs/07-runner-codex.md), [08 Copilot CLI](docs/08-runner-copilot-cli.md) | runner pages |
| [09 Superpowers](docs/09-superpowers.md) | the process layer |
| [10 Roles and skills](docs/10-roles-and-skills.md) | twelve roles, the pipeline |
| [11 Running a team](docs/11-running-a-team.md) | up, run, chat, approve, down |
| [12 Adding a role and runner](docs/12-adding-a-role-and-runner.md) | extending the team |
| [13 Troubleshooting](docs/13-troubleshooting.md) | every doctor message |
| [14 Safety and permissions](docs/14-safety-and-permissions.md) | modes and limits |
| [15 Glossary](docs/15-glossary.md) | terms |
| [Reference](docs/reference/runners.md) | verified commands, [Superpowers](docs/reference/superpowers.md), [installers](docs/reference/installers.md), [tmux keys](docs/reference/tmux-keys.md) |
| [ADRs](docs/adr/0001-tmux-primary-backend.md) | decision records (0001 to 0009) |

Every command block in the docs carries a `Run:` line saying whether the build ran it and why not.

## Diagrams

[Architecture infographic](docs/architecture-infographic.html): what was built (tmux built, Zellij planned, Codex and Copilot runners UNVERIFIED). Open it in a browser.

## Try it

Run `uv run sdlc doctor` and `uv run sdlc learn` as above, then open [start here](docs/00-start-here.md).

## Credit and license

sdlc-mux relies on [Superpowers](https://github.com/obra/superpowers) by obra for the process skills its agents follow. Superpowers is MIT licensed (checked against [docs/reference/superpowers.md](docs/reference/superpowers.md), 2026-11-09, which records "MIT license" for the repository; the LICENSE file in that repository was not opened by this build). No Superpowers file is copied or vendored into this repository; it is installed through each runner's own plugin route.

License of this project: there is no `LICENSE` file in this repository, so no license is granted by this README. Add one before sharing the code.
