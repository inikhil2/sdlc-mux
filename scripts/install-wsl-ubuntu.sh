#!/usr/bin/env bash
# sdlc-mux installer for WSL2 Ubuntu. Windows requires WSL2 in v1 (docs/adr/0005-wsl2-windows-path.md).
# Keep the repo in the Linux filesystem (~), not /mnt/c. Idempotent: each step checks first.
set -euo pipefail

step() { printf '\n==> %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

cd "$(dirname "$0")/.."

step "1/5 tmux (apt)"
if have tmux; then echo "tmux already installed"; else
  sudo apt-get update && sudo apt-get install -y tmux curl
fi

step "2/5 uv"
if have uv; then echo "uv already installed"; else
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

step "3/5 Python deps (uv sync)"
uv sync

step "4/5 Optional, printed only (not run): runner CLIs and Superpowers"
cat <<'MSG'
Install runner CLIs inside WSL, not on Windows (no shared PATH or login).
Claude Code is the Phase 0 default runner. Install it yourself, then log in once:
  curl -fsSL https://claude.ai/install.sh | bash   # UNVERIFIED (runners.md)
  npm install -g @anthropic-ai/claude-code         # UNVERIFIED (runners.md)
Superpowers for Claude Code, from inside `claude` (docs/reference/superpowers.md):
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
Optional later runners:
  Codex:   npm install -g @openai/codex    # UNVERIFIED
  Copilot: npm install -g @github/copilot  # docs only (Node 22+), not run here
MSG

step "5/5 sdlc doctor"
uv run sdlc doctor
