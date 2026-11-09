#!/usr/bin/env bash
# Devcontainer setup. No runner CLI installs; authenticate runners inside the container yourself.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> tmux"
if command -v tmux >/dev/null 2>&1; then echo "tmux already installed"; else
  sudo apt-get update && sudo apt-get install -y tmux
fi

echo "==> uv sync"
uv sync

echo "==> sdlc doctor"
uv run sdlc doctor
