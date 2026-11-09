"""Prerequisite checks for `sdlc doctor`."""

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from sdlc_mux import superpowers
from sdlc_mux.config import RUNNER_BINARIES, ConfigError, load_config
from sdlc_mux.skills_sync import missing_sdlc_skills

# Fix commands for macOS. Entries marked UNVERIFIED are not confirmed in docs/reference/runners.md.
FIXES = {
    "uv": "brew install uv",
    "tmux": "brew install tmux",
    "claude": "brew install --cask claude-code   (UNVERIFIED install route)",
    "codex": "npm install -g @openai/codex   (UNVERIFIED install route)",
    "copilot": "npm install -g @github/copilot   (needs Node 22+)",
}


def run_checks(
    config_path: Path,
    which: Callable[[str], str | None] = shutil.which,
    root: Path = Path("."),
) -> list[tuple[str, bool, str]]:
    """Return (item, ok, detail) rows; `detail` is the exact fix command when not ok.

    Also checks, under `root`, that the sdlc skills are synced (warning only) and that Superpowers
    is verified for each runner in use: a warning in supervised mode, a failure in autonomous.
    """
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
        cfg = load_config(config_path)
        runners = cfg.runners_used()
    except ConfigError as e:
        return [*rows, (f"config {config_path}", False, "; ".join(e.errors))]
    for r in runners:
        binary = RUNNER_BINARIES[r]
        if binary:
            rows.append((f"runner {r} ({binary})", bool(which(binary)), FIXES[binary]))
    for folder, gone in missing_sdlc_skills(root, runners, cfg.roles_used()).items():
        rows.append((f"sdlc skills missing in {folder}: {', '.join(gone)} (warning)", True,
                     "sdlc skills sync"))  # fmt: skip
    strict = cfg.mode == "autonomous"
    for r in (r for r in runners if r in superpowers.RUNNERS):
        if not superpowers.verified(root, r):
            fix = "; ".join(superpowers.PLUGIN_COMMANDS[r])
            label = f"superpowers for {r} not verified (cannot check plugin installs on disk)"
            rows.append((label if strict else f"{label} (warning)", not strict, fix))
    return rows
