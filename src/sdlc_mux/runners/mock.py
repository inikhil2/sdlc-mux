"""Offline deterministic runner: writes each role's template artifacts from the task brief.

No network, no clock, no randomness: the same bundle always yields byte-identical files.
Run as `python -m sdlc_mux.runners.mock --role R --stage S --item I --brief F --out D`.
"""

import argparse
import re
import sys
from pathlib import Path

from .base import Bundle, Profile, Runner

TEMPLATES = Path(__file__).parent.parent / "templates"

# (role, stage) -> [(output path, template, literal replacements)]
Out = tuple[str, str, dict[str, str]]
PLAN_REPLACEMENTS = {"approve | changes-requested": "approve", "GO | NO-GO": "GO"}
OUTPUTS: dict[tuple[str, str], list[Out]] = {
    ("product-owner", "discover"): [("vision.md", "vision", {}), ("stories/S1.md", "story", {})],
    ("business-analyst", "discover"): [
        ("business-rules.md", "business-rules", {}),
        ("process-flow.md", "process-flow", {}),
        ("data-dictionary.md", "data-dictionary", {}),
    ],
    ("ux-designer", "discover"): [
        ("user-flows.md", "user-flows", {}),
        ("screen-specs.md", "screen-specs", {}),
        ("accessibility-checklist.md", "accessibility-checklist", {}),
    ],
    ("solution-architect", "design"): [
        ("design/design-doc.md", "design-doc", {}),
        (
            "design/adr/0001-architecture.md",
            "adr",
            {"proposed | accepted | superseded": "accepted"},
        ),
    ],
    ("scrum-master", "plan"): [("plan.md", "plan", {})],
    ("scrum-master", "retro"): [("retro.md", "retro", {})],
    ("sdet", "plan"): [("test/test-plan.md", "test-plan", {})],
    ("sdet", "test"): [("test/test-report.md", "test-report", {})],
    ("qa-analyst", "test"): [("test/qa-signoff.md", "qa-signoff", {})],
    ("code-reviewer", "review"): [("review/review-report.md", "review-report", PLAN_REPLACEMENTS)],
    ("security-engineer", "review"): [("review/security-review.md", "security-review", {})],
    ("release-engineer", "release"): [
        ("release/release-plan.md", "release-plan", {}),
        ("release/release-notes.md", "release-notes", {}),
        ("release/go-no-go.md", "go-no-go", PLAN_REPLACEMENTS),
    ],
}
for _role in ("backend-engineer", "frontend-engineer"):
    OUTPUTS[(_role, "build")] = [("build/{task}-report.md", "build-report", {})]

_TRIPLE = re.compile(r"given\s+(.+?),?\s+when\s+(.+?),?\s+then\s+(.+)", re.IGNORECASE)


def parse_brief(text: str) -> dict[str, str]:
    """Extract title, bold-labelled fields (`- **Goal**: ...`) and Given/When/Then criteria.

    Keys: title, goal, users, in scope, constraints (as present) and criteria (one criterion per
    line, 'Given x / When y / Then z'; three generic ones if the brief has none).
    """
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    out = {"title": m.group(1).strip() if m else "Untitled"}
    for k, v in re.findall(r"^\s*[-*]\s*\*\*(.+?)\*\*:?\s*(.*)$", text, re.MULTILINE):
        out.setdefault(k.strip().lower(), v.strip())
    crit = [
        f"Given {a} / When {b} / Then {c.rstrip('.')}"
        for a, b, c in (m.groups() for m in _TRIPLE.finditer(text))
    ]
    out["criteria"] = "\n".join(
        crit or [f"Given {out['title']} is set up / When a user uses it / Then it works"] * 3
    )
    return out


def _story(brief: dict[str, str]) -> str:
    lines = []
    for c in brief["criteria"].splitlines():
        lines += [f"- {p.strip()}" for p in c.split(" / ")]
    return (
        f"# Story S1: {brief['title']}\n\nAs a user, I want {brief['goal']}, "
        f"so that the goal is met.\n\n## Acceptance criteria\n" + "\n".join(lines) + "\n"
    )


def _render(template: str, brief: dict[str, str], task: str) -> str:
    """Fill `{{key}}` placeholders from the brief; unknown keys get a title-based phrase."""
    title, goal = brief["title"], brief.get("goal", brief["title"])
    scope = brief.get("in scope", goal)
    first = scope.split(";")[0].strip()
    values = {
        "item": title, "problem": goal, "users": brief.get("users", "users"),
        "measure": f"All {len(brief['criteria'].splitlines())} acceptance criteria pass",
        "rule": first, "source": "product brief", "context": goal,
        "options": "Monolith with SQLite; hosted service",
        "decision": f"Monolith. {brief.get('constraints', 'Keep it simple.')}",
        "consequences": "One deployable; limited horizontal scale", "risks": "Rounding in splits",
        "test_strategy": "Unit tests per rule, one end-to-end test per criterion",
        "task": task, "branch": f"feat/{task}", "n": "3", "command": "pytest",
        "name": "mock-qa", "charters": "all", "issues": "none", "finding": "none found",
        "severity": "Low", "status": "accepted", "change": first, "issue": "none",
        "scope": scope, "number": "0001", "title": f"Architecture for {title}",
    }  # fmt: skip
    return re.sub(
        r"\{\{([^}]*)\}\}", lambda m: values.get(m.group(1), f"{m.group(1)} for {title}"), template
    )


class MockRunner(Runner):
    """Offline runner; its 'command' is this module, so the agent loop treats it like any CLI."""

    name = "mock"
    binary = sys.executable
    config_dir = "."
    project_skills = ".agents/skills"
    user_skills = ".agents/skills"

    def _flags(self, profile: Profile, headless: bool) -> list[str]:
        return []

    def build_command(
        self,
        bundle: Bundle,
        prompt: str,
        mode: Profile,
        headless: bool,
        i_understand_the_risks: bool = False,
    ) -> list[str]:
        """argv that re-invokes this module for `bundle`; `prompt` is unused (offline)."""
        self.permission_flags(mode, headless, i_understand_the_risks)
        return [
            sys.executable, "-m", "sdlc_mux.runners.mock",
            "--role", bundle.role, "--stage", bundle.stage, "--item", bundle.item,
            "--brief", str(bundle.brief), "--out", str(bundle.outputs_dir), "--task", bundle.task,
        ]  # fmt: skip

    def run(self, bundle: Bundle) -> list[Path]:
        """Write the role's artifacts for the stage into outputs_dir; return the paths written.

        Unknown (role, stage) pairs write nothing. Output is a pure function of the brief text.
        """
        brief = parse_brief(bundle.brief.read_text(encoding="utf-8"))
        written = []
        for rel, tpl, repl in OUTPUTS.get((bundle.role, bundle.stage), []):
            text = (TEMPLATES / f"{tpl}.md").read_text(encoding="utf-8")
            for old, new in repl.items():
                text = text.replace(old, new)
            body = _story(brief) if tpl == "story" else _render(text, brief, bundle.task)
            f = bundle.outputs_dir / rel.format(task=bundle.task)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(body.encode("utf-8"))
            written.append(f)
        return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry: write the artifacts for one task; print each path written."""
    p = argparse.ArgumentParser()
    for flag in ("role", "stage", "item", "brief", "out"):
        p.add_argument(f"--{flag}", required=True)
    p.add_argument("--task", default="T1")
    a = p.parse_args(argv)
    b = Bundle(a.role, a.stage, a.item, Path(a.brief), Path(a.out), a.task)
    for f in MockRunner().run(b):
        print(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
