# Install on Windows with WSL2

## What you will learn

- Why **Windows requires WSL2 in v1** and native Windows is not supported.
- The steps from a clean Windows machine to a working `sdlc doctor`.
- Why the project must live in the Linux filesystem.

Status of this page: no command here was run by the build. The build machine is a Mac, so nothing on Windows or Ubuntu was executed or tested. Everything below is written from the build brief and is **UNVERIFIED on a real Windows machine**.

## Why WSL2

sdlc-mux needs tmux, and tmux runs on Linux and macOS. WSL2 gives Windows a real Ubuntu. Native Windows without WSL is not supported in v1 ([ADR 0005](adr/0005-wsl2-windows-path.md)). A future Windows-native backend would need a multiplexer that supports the layout code (a labelled pane per agent, retitling, reflow); none has been verified, so none is named as a plan.

## Steps

1. In an Administrator PowerShell, install Ubuntu, then reboot and create the Linux user when Ubuntu opens:

```powershell
wsl --install -d Ubuntu-24.04
```
Run: no, Windows-only install command (not available on the build machine). UNVERIFIED.

2. Optional host terminal:

```powershell
winget install Microsoft.WindowsTerminal
```
Run: no, Windows-only install command. UNVERIFIED. (`scripts/install-windows.ps1` does not install terminals; see [installers](reference/installers.md).)

3. Inside Ubuntu, install the tools:

```bash
sudo apt update && sudo apt install -y git tmux curl build-essential gh
```
Run: no, install command (D1) and the build machine is not Linux.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Run: no, install command (D1). UNVERIFIED URL (from the build brief).

Node.js LTS is only needed for npm-installed runners; use `fnm`, `nvm`, or the NodeSource apt repository.

4. Install the runner CLIs **inside WSL**, using the Linux commands in the runner pages ([Claude Code](06-runner-claude-code.md), [Codex](07-runner-codex.md), [Copilot CLI](08-runner-copilot-cli.md)). A Windows install does not share PATH or login state with WSL.

5. Keep the repository under your Linux home (`~`), not `/mnt/c`. It is faster and avoids file-watching problems. Then:

```bash
scripts/install-wsl-ubuntu.sh
```
Run: no, install script, written but not executed (D1); shellcheck not run (D6).

6. Check:

```bash
uv run sdlc doctor
```
Run: yes, output below (this is the macOS output; not run in WSL)

```text
[ok]      python 3.12
[ok]      uv
[ok]      tmux
[ok]      runner claude (claude)
```

On Ubuntu the same rows appear; the fix commands printed for missing items are the macOS (`brew`) ones, so on Ubuntu use `apt` or the vendor route instead. This is a known gap (the doctor always prints macOS fixes).

## Windows-side helper

`scripts/install-windows.ps1` checks that `wsl.exe` exists, lists distributions, and prints the commands to run inside Ubuntu. It does not install WSL. Written, not executed; PSScriptAnalyzer not run.

## Try it

Inside Ubuntu, after step 6, run the offline demo: `uv run sdlc run examples/expense-splitter.md --runner mock`. If that reaches `done`, the Linux side works. Problems: [troubleshooting](13-troubleshooting.md).
