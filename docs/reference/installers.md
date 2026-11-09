# Installers

Status of every file below: **written, not executed (D1)**. shellcheck and PSScriptAnalyzer **not run (D6)**. The only check was `bash -n` on the `.sh` files and a JSON parse of `devcontainer.json`; the `.ps1` was reviewed by hand.

All scripts are idempotent (each step checks first), print each step, and end with `sdlc doctor`. Runner CLIs and Superpowers are printed, never run. Install commands marked UNVERIFIED follow [runners.md](runners.md).

| File | Steps |
|---|---|
| `scripts/install-macos.sh` | Check Homebrew (exit with a pointer to brew.sh if missing); `brew install uv tmux` if absent; `uv sync`; print Claude Code and Superpowers steps; `uv run sdlc doctor`. |
| `scripts/install-wsl-ubuntu.sh` | `apt-get install tmux curl` if tmux absent; install uv with the astral.sh script if absent; `uv sync`; print runner and Superpowers steps; `uv run sdlc doctor`. Windows requires WSL2 in v1 ([ADR 0005](../adr/0005-wsl2-windows-path.md)). |
| `scripts/install-windows.ps1` | Check `wsl.exe` exists, list distributions, print the commands to run inside Ubuntu. Does not install WSL (needs admin and a reboot). Deviation from Prompt.md 15.2: no winget terminal installs. |
| `.devcontainer/devcontainer.json` | Python 3.12 image; uv feature `ghcr.io/va-h/devcontainers-features/uv:1` (UNVERIFIED feature name, not looked up); `postCreateCommand` runs `post-create.sh`. Plain JSON, no comments. |
| `.devcontainer/post-create.sh` | Install tmux with apt if absent; `uv sync`; `uv run sdlc doctor`. No runner CLI installs. |
