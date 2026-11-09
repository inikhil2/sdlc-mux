"""`sdlc skills sync`: copy the sdlc skills into each runner's project skill folders (ADR 0009)."""

import shutil
from pathlib import Path

# Project-scope targets: Claude Code reads .claude/skills; Codex and Copilot read .agents/skills.
TARGETS = (".claude/skills", ".agents/skills")
SKILLS_SRC = Path(__file__).resolve().parents[2] / "skills"


def sdlc_skill_dirs(src: Path = SKILLS_SRC) -> dict[str, Path]:
    """Return {installed folder name: source folder}: `sdlc-protocol` and `role-<slug>` per role."""
    found = {"sdlc-protocol": src / "sdlc-protocol"}
    found |= {f"role-{d.name}": d for d in sorted((src / "roles").iterdir()) if d.is_dir()}
    return found


def sync_skills(target_root: Path, src: Path = SKILLS_SRC) -> list[Path]:
    """Copy every sdlc skill into `<target_root>/.claude/skills` and `<target_root>/.agents/skills`.

    Each skill folder is replaced whole, so running it twice gives the same result. Only the sdlc
    skill folders are touched. Returns the folders written.
    """
    written = []
    for target in TARGETS:
        for name, source in sdlc_skill_dirs(src).items():
            dest = target_root / target / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
            written.append(dest)
    return written


def missing_sdlc_skills(
    target_root: Path, runners: list[str], roles: list[str]
) -> dict[str, list[str]]:
    """Return {skills folder: missing skill names} for the folders the runners in use read.

    Needs `sdlc-protocol` and `role-<role>` for each role in use. The mock runner needs none.
    """
    wanted = ["sdlc-protocol", *(f"role-{r}" for r in roles)]
    folders = {TARGETS[0] if r == "claude" else TARGETS[1] for r in runners if r != "mock"}
    out = {}
    for folder in sorted(folders):
        gone = [n for n in wanted if not (target_root / folder / n / "SKILL.md").is_file()]
        if gone:
            out[folder] = gone
    return out
