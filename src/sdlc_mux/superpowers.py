"""`sdlc superpowers install|verify`. Superpowers is never vendored or copied (ADR 0008).

Every runner installs Superpowers as a plugin (docs/reference/superpowers.md, verified 2026-11-09),
and the plugin install location is UNVERIFIED. So `verify` can only confirm a skill that sits in a
project skills folder; for anything else it says "cannot check" and never claims "found".
"""

from pathlib import Path
from typing import NamedTuple

# Role -> Superpowers skills, in order (Prompt.md 8.1). The engineers also run
# verification-before-completion (the 8.2 example does) because the build gate needs an exit code.
_BUILD = (
    "using-git-worktrees",
    "writing-plans",
    "executing-plans",
    "test-driven-development",
    "systematic-debugging",
    "verification-before-completion",
    "requesting-code-review",
    "finishing-a-development-branch",
)
ROLE_SKILLS: dict[str, tuple[str, ...]] = {
    "product-owner": ("brainstorming", "writing-plans", "verification-before-completion"),
    "business-analyst": ("brainstorming", "verification-before-completion"),
    "ux-designer": ("brainstorming", "verification-before-completion"),
    "solution-architect": ("brainstorming", "writing-plans", "verification-before-completion"),
    "scrum-master": (
        "writing-plans",
        "dispatching-parallel-agents",
        "subagent-driven-development",
    ),
    "backend-engineer": _BUILD,
    "frontend-engineer": _BUILD,
    "sdet": (
        "writing-plans",
        "test-driven-development",
        "systematic-debugging",
        "verification-before-completion",
    ),
    "qa-analyst": ("brainstorming", "systematic-debugging", "verification-before-completion"),
    "code-reviewer": (
        "requesting-code-review",
        "receiving-code-review",
        "verification-before-completion",
    ),
    "security-engineer": (
        "brainstorming",
        "systematic-debugging",
        "verification-before-completion",
    ),
    "release-engineer": (
        "writing-plans",
        "executing-plans",
        "finishing-a-development-branch",
        "verification-before-completion",
    ),
}
SKILLS = sorted({s for names in ROLE_SKILLS.values() for s in names})

RUNNERS = ("claude", "codex", "copilot")
# Verified plugin routes (README, 2026-11-09). Printed, never executed by sdlc.
PLUGIN_COMMANDS: dict[str, tuple[str, ...]] = {
    "claude": ("/plugin install superpowers@claude-plugins-official  (inside Claude Code)",),
    "codex": ("/plugins, search 'superpowers', choose Install Plugin  (inside Codex)",),
    "copilot": (
        "copilot plugin marketplace add obra/superpowers-marketplace",
        "copilot plugin install superpowers@superpowers-marketplace",
    ),
}
# Project skills folders each runner reads (docs/reference/runners.md, ADR 0009).
SKILL_DIRS: dict[str, tuple[str, ...]] = {
    "claude": (".claude/skills",),
    "codex": (".agents/skills",),
    "copilot": (".github/skills", ".claude/skills", ".agents/skills"),
}


class Finding(NamedTuple):
    """One skill for one runner: `found_at` is a SKILL.md path, or None when not checkable."""

    runner: str
    skill: str
    found_at: Path | None
    fix: str


def pick_runners(runner: str) -> list[str]:
    """Return the runner list for `--runner`: one name or `all`; ValueError for anything else."""
    if runner == "all":
        return list(RUNNERS)
    if runner not in RUNNERS:
        raise ValueError(f"unknown runner '{runner}'; use one of: {', '.join(RUNNERS)}, all")
    return [runner]


def install_text(runners: list[str]) -> str:
    """Return the verified plugin commands for `runners`. Nothing is run."""
    lines = [
        "Superpowers is installed through each runner's plugin route. sdlc does not run these:"
    ]
    for r in runners:
        lines += [f"{r}:", *(f"  {c}" for c in PLUGIN_COMMANDS[r])]
    return "\n".join(lines)


def verify(root: Path, runners: list[str]) -> list[Finding]:
    """Check each referenced Superpowers skill for each runner in `root`'s project skill folders.

    A skill is found only if `<folder>/<skill>/SKILL.md` exists. Otherwise `found_at` is None:
    the plugin location cannot be checked, so the skill is neither found nor proven missing.
    """
    out = []
    for r in runners:
        fix = "; ".join(PLUGIN_COMMANDS[r])
        for skill in SKILLS:
            hits = [root / d / skill / "SKILL.md" for d in SKILL_DIRS[r]]
            out.append(Finding(r, skill, next((h for h in hits if h.is_file()), None), fix))
    return out


def verified(root: Path, runner: str) -> bool:
    """True only if every referenced skill is found on disk for `runner`."""
    return all(f.found_at for f in verify(root, [runner]))


def report(findings: list[Finding]) -> str:
    """Render findings: `found` with the path, or `UNVERIFIED` with the fix command."""
    lines = []
    for f in findings:
        if f.found_at:
            lines.append(f"[found]      {f.runner:8} {f.skill}  ({f.found_at})")
        else:
            lines.append(
                f"[UNVERIFIED] {f.runner:8} {f.skill}  cannot check on disk (plugin install); "
                f"fix: {f.fix}"
            )
    return "\n".join(lines)
