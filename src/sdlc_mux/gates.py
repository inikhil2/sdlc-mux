"""Gate validators. Only this module decides gate status (orchestrator-owned, ADR 0003).

Each validator takes the item's artifact directory and returns a GateResult. Layout:
vision.md, business-rules.md, screen-specs.md, plan.md, retro.md and stories/*.md at the root;
design/, test/, build/, review/, release/ subfolders as in the role catalogue.

plan.md task format, one bullet per task under any heading:
    - <id> | owner: <role> | deps: <id>, <id> or - | test: <test reference>
build/<task>-report.md records, one per line: `Branch: <name>`, `Commits: <n>`,
`Test command: <cmd>`, `Exit code: <n>`.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DESIGN_SECTIONS = ("Context", "Options", "Decision", "Consequences", "Risks", "Test strategy")


@dataclass(frozen=True)
class GateResult:
    """Outcome of one gate: `passed` and, when failed, the `reasons`."""

    passed: bool
    reasons: tuple[str, ...] = ()


def _result(reasons: list[str]) -> GateResult:
    return GateResult(not reasons, tuple(reasons))


def _need(d: Path, rel: str, reasons: list[str]) -> str | None:
    """Return the text of d/rel, or record a 'missing' reason and return None."""
    f = d / rel
    if not f.is_file():
        reasons.append(f"{rel} is missing")
        return None
    return f.read_text(encoding="utf-8")


def _field(text: str, name: str) -> str | None:
    m = re.search(rf"^\s*(?:[-*]\s*)?{name}:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
    return m.group(1) if m else None


def _gwt_ok(text: str) -> bool:
    """True if the story has three or more Given/When/Then criteria."""
    counts = [
        len(re.findall(rf"^\s*(?:[-*]\s*)?\**{w}\b", text, re.MULTILINE))
        for w in ("Given", "When", "Then")
    ]
    return min(counts) >= 3


def check_discovered(d: Path) -> GateResult:
    """vision.md, business-rules.md; >=1 story with >=3 Given/When/Then criteria;
    screen-specs.md only when the item has a UI (a `ui` marker file in `d`)."""
    r: list[str] = []
    _need(d, "vision.md", r)
    _need(d, "business-rules.md", r)
    stories = sorted((d / "stories").glob("*.md"))
    if not any(_gwt_ok(s.read_text(encoding="utf-8")) for s in stories):
        r.append("no story in stories/ has three or more Given/When/Then criteria")
    if (d / "ui").exists():
        _need(d, "screen-specs.md", r)
    return _result(r)


def check_designed(d: Path) -> GateResult:
    """design/design-doc.md has all six required sections and design/adr/ has an ADR."""
    r: list[str] = []
    text = _need(d, "design/design-doc.md", r)
    if text is not None:
        for sec in DESIGN_SECTIONS:
            if not re.search(rf"^#+\s*{sec}\s*$", text, re.MULTILINE | re.IGNORECASE):
                r.append(f"design-doc.md lacks section '{sec}'")
    if not list((d / "design" / "adr").glob("*.md")):
        r.append("design/adr/ has no ADR")
    return _result(r)


def parse_plan(text: str) -> dict[str, tuple[str, list[str], str]]:
    """Parse plan.md task bullets into {id: (owner, deps, test)}; missing keys give ''/[]."""
    tasks: dict[str, tuple[str, list[str], str]] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith(("- ", "* ")) or "|" not in line:
            continue
        cells = [c.strip() for c in line.lstrip()[2:].split("|")]
        kv = {k.strip().lower(): v.strip() for k, _, v in (c.partition(":") for c in cells[1:])}
        deps = [x.strip() for x in kv.get("deps", "").split(",") if x.strip() not in ("", "-")]
        tasks[cells[0]] = (kv.get("owner", ""), deps, kv.get("test", ""))
    return tasks


def _has_cycle(deps: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}  # 1 = visiting, 2 = done

    def visit(n: str) -> bool:
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        if any(visit(m) for m in deps.get(n, []) if m in deps):
            return True
        state[n] = 2
        return False

    return any(visit(n) for n in deps)


def check_planned(d: Path) -> GateResult:
    """plan.md: unique task ids, owner and test per task, known deps forming a DAG;
    test/test-plan.md exists."""
    r: list[str] = []
    text = _need(d, "plan.md", r)
    if text is not None:
        ids = [
            ln.lstrip()[2:].split("|")[0].strip()
            for ln in text.splitlines()
            if ln.lstrip().startswith(("- ", "* ")) and "|" in ln
        ]
        r += [f"duplicate task id '{i}'" for i in sorted({i for i in ids if ids.count(i) > 1})]
        tasks = parse_plan(text)
        if not tasks:
            r.append("plan.md lists no tasks")
        for tid, (owner, deps, test) in tasks.items():
            if not owner:
                r.append(f"task {tid} has no owner")
            if not test:
                r.append(f"task {tid} has no test reference")
            r += [f"task {tid} depends on unknown task '{x}'" for x in deps if x not in tasks]
        if _has_cycle({t: v[1] for t, v in tasks.items()}):
            r.append("task dependencies contain a cycle")
    _need(d, "test/test-plan.md", r)
    return _result(r)


def check_built(d: Path) -> GateResult:
    """Every build/*-report.md records a branch, >=1 commit and a test command with exit 0;
    when plan.md exists, every planned task has a report."""
    r: list[str] = []
    reports = sorted((d / "build").glob("*-report.md"))
    if not reports:
        r.append("build/ has no *-report.md")
    for f in reports:
        t = f.read_text(encoding="utf-8")
        commits = _field(t, "Commits") or ""
        if not _field(t, "Branch"):
            r.append(f"{f.name} records no branch")
        if not commits.isdigit() or int(commits) < 1:
            r.append(f"{f.name} records no commits")
        if not _field(t, "Test command"):
            r.append(f"{f.name} records no test command")
        elif _field(t, "Exit code") != "0":
            r.append(f"{f.name} test command did not exit 0")
    if (d / "plan.md").is_file():
        planned = parse_plan((d / "plan.md").read_text(encoding="utf-8"))
        r += [
            f"task {t} has no build report"
            for t in planned
            if not (d / "build" / f"{t}-report.md").is_file()
        ]
    return _result(r)


def check_tested(d: Path) -> GateResult:
    """test/test-report.md shows `Passed: <n>` and `Open P1 bugs: 0`; test/qa-signoff.md exists."""
    r: list[str] = []
    t = _need(d, "test/test-report.md", r)
    if t is not None:
        if not (_field(t, "Passed") or "").isdigit():
            r.append("test-report.md shows no pass count")
        if _field(t, "Open P1 bugs") != "0":
            r.append("test-report.md does not show zero open P1 bugs")
    _need(d, "test/qa-signoff.md", r)
    return _result(r)


def check_reviewed(d: Path) -> GateResult:
    """review/review-report.md has `Verdict: approve`; review/security-review.md has
    `Unresolved High: 0`."""
    r: list[str] = []
    t = _need(d, "review/review-report.md", r)
    if t is not None and (_field(t, "Verdict") or "").lower() != "approve":
        r.append("review-report.md verdict is not approve")
    s = _need(d, "review/security-review.md", r)
    if s is not None and _field(s, "Unresolved High") != "0":
        r.append("security-review.md does not show zero unresolved High findings")
    return _result(r)


def check_released(d: Path) -> GateResult:
    """release/release-notes.md exists and release/go-no-go.md has `Decision: GO`.
    Who wrote the decision (human or release engineer) is not checked here."""
    r: list[str] = []
    _need(d, "release/release-notes.md", r)
    g = _need(d, "release/go-no-go.md", r)
    if g is not None and _field(g, "Decision") != "GO":
        r.append("go-no-go.md does not say GO")
    return _result(r)


def check_retrospected(d: Path) -> GateResult:
    """retro.md exists."""
    r: list[str] = []
    _need(d, "retro.md", r)
    return _result(r)


GATES: dict[str, Callable[[Path], GateResult]] = {
    "discovered": check_discovered,
    "designed": check_designed,
    "planned": check_planned,
    "built": check_built,
    "tested": check_tested,
    "reviewed": check_reviewed,
    "released": check_released,
    "retrospected": check_retrospected,
}
