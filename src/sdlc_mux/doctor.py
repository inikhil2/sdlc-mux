"""Prerequisite checks for `sdlc doctor`."""

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from sdlc_mux.config import RUNNER_BINARIES, ConfigError, load_config

# Fix commands for macOS. Entries marked UNVERIFIED are not confirmed in docs/reference/runners.md.
FIXES = {
    "uv": "brew install uv",
    "tmux": "brew install tmux",
    "claude": "brew install --cask claude-code   (UNVERIFIED install route)",
    "codex": "npm install -g @openai/codex   (UNVERIFIED install route)",
    "copilot": "npm install -g @github/copilot   (needs Node 22+)",
}


def run_checks(
    config_path: Path, which: Callable[[str], str | None] = shutil.which
) -> list[tuple[str, bool, str]]:
    """Return (item, ok, detail) rows; `detail` is the exact fix command when not ok."""
    py = sys.version_info
    rows = [
        (
            f"python {py.major}.{py.minor}",
            py >= (3, 12),
            "uv python install 3.12",
        ),
        ("uv", bool(which("uv")), FIXES["uv"]),
        ("tmux", bool(which("tmux")), FIXES["tmux"]),
    ]
    try:
        runners = load_config(config_path).runners_used()
    except ConfigError as e:
        return [*rows, (f"config {config_path}", False, "; ".join(e.errors))]
    for r in runners:
        binary = RUNNER_BINARIES[r]
        if binary:
            rows.append((f"runner {r} ({binary})", bool(which(binary)), FIXES[binary]))
    return rows
