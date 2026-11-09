# Install on macOS

## What you will learn

- What you need on a Mac (Apple silicon or Intel) and why.
- The primary path with Homebrew and uv.
- How to check the result with `sdlc doctor`.

Status of this page: the build machine is a Mac and already had tmux, uv, and Claude Code. **No install command on this page was run by the build** (decision D1: no system installs). Commands marked `UNVERIFIED` were not looked up on the vendor's site. The commands that only use the project folder (`uv sync`, `sdlc doctor`) were run.

## What you need and why

| Need | Why |
|---|---|
| Command line tools | git and a compiler toolchain for Homebrew. |
| Homebrew | Installs tmux, uv, and the others. |
| tmux | The multiplexer sdlc-mux requires. |
| uv | Manages Python 3.12 and the project environment, so you need no system Python. |
| git, gh, node | git is needed by the agents; node is only needed if you install a runner through npm. |
| At least one runner CLI | Claude Code, Codex CLI, or Copilot CLI. Not needed for the offline mock runner. |

## Primary path

1. Command line tools:

```bash
xcode-select --install
```
Run: no, install command (D1)

2. Homebrew: install from https://brew.sh (run the installer shown there).

3. Tools:

```bash
brew install git gh tmux uv node
```
Run: no, install command (D1). The build machine already has these.

4. Python 3.12 through uv:

```bash
uv python install 3.12
```
Run: no, install command (D1). The project pins Python in `.python-version`.

5. Runner CLIs (only the ones you have access to), then log in once from each CLI's own prompt:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```
Run: no, install command (D1). UNVERIFIED route; alternatives `brew install --cask claude-code` and `npm install -g @anthropic-ai/claude-code` are also UNVERIFIED. See [Claude Code](06-runner-claude-code.md).

```bash
brew install codex
```
Run: no, install command and Codex is not installed here. UNVERIFIED (`npm install -g @openai/codex` is the other route). See [Codex](07-runner-codex.md).

```bash
brew install --cask copilot-cli
```
Run: no, install command and Copilot CLI is not installed here. Per GitHub's getting-started page (read 2026-11-09, docs only); `npm install -g @github/copilot` needs Node 22+. See [Copilot CLI](08-runner-copilot-cli.md).

6. Superpowers. sdlc prints the plugin route for each runner and does not run it:

```bash
uv run sdlc superpowers install --runner claude
```
Run: yes, output below

```text
Superpowers is installed through each runner's plugin route. sdlc does not run these:
claude:
  /plugin install superpowers@claude-plugins-official  (inside Claude Code)
```

7. The project environment (this creates `.venv/` inside the folder only):

```bash
uv sync
```
Run: yes, output below

```text
Resolved 25 packages in 2ms
Checked 24 packages in 0.59ms
```

To get `sdlc` on your PATH outside the project folder:

```bash
uv tool install .
```
Run: no, it installs into your home directory (D1). Inside the folder use `uv run sdlc ...` instead.

8. Check:

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

A missing item prints `[MISSING]` and the exact fix command; the exit code is 1. All messages are explained in [troubleshooting](13-troubleshooting.md).

## The one-shot script

`scripts/install-macos.sh` does the check-then-install steps for Homebrew, uv, and tmux, runs `uv sync`, prints the runner and Superpowers steps, and ends with `sdlc doctor`. It is **written, not executed**; shellcheck was not run. See [installers](reference/installers.md).

## Other choices

MacPorts, mise, asdf, pipx, Zellij, and other terminals are compared in [install alternatives](05-install-alternatives.md).

## Try it

Run the offline smoke test (no runner CLI needed): `sdlc run examples/expense-splitter.md --runner mock`, as shown in [start here](00-start-here.md). Then open the room as shown in [running a team](11-running-a-team.md).
