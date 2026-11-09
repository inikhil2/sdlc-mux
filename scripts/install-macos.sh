#!/usr/bin/env bash
# sdlc-mux installer for macOS (Phase 0 default: Claude Code runner).
# Idempotent: each step checks first. Run from anywhere; it cd's to the repo root.
set -euo pipefail

step() { printf '\n==> %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

cd "$(dirname "$0")/.."

step "1/5 Homebrew"
if have brew; then echo "already installed"; else
  echo "Homebrew is missing. Install it from https://brew.sh, then re-run this script."
  exit 1
fi

step "2/5 uv and tmux"
for pkg in uv tmux; do
  if have "$pkg"; then echo "$pkg already installed"; else brew install "$pkg"; fi
done

step "3/5 Python deps (uv sync)"
uv sync

step "4/5 Optional, printed only (not run): runner CLIs and Superpowers"
cat <<'MSG'
Claude Code is the Phase 0 default runner. Install it yourself, then log in once:
  brew install --cask claude-code                  # UNVERIFIED (runners.md)
  curl -fsSL https://claude.ai/install.sh | bash   # UNVERIFIED (runners.md)
Superpowers for Claude Code, from inside `claude` (docs/reference/superpowers.md):
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
Optional later runners:
  Codex:   brew install codex  or  npm install -g @openai/codex   # UNVERIFIED
  Copilot: brew install --cask copilot-cli                         # docs only, not run here
MSG

step "5/5 sdlc doctor"
uv run sdlc doctor
