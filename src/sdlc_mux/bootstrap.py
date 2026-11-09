"""Per-task prompt builder. Pure text: it never touches gates or the board (ADR 0003)."""

from pathlib import Path

from sdlc_mux.handoffs import Handoff

# (role, stage) -> artifact paths relative to the item directory; `{task}` is the build task id.
OUTPUTS: dict[tuple[str, str], tuple[str, ...]] = {
    ("product-owner", "discover"): ("vision.md", "stories/S1.md"),
    ("business-analyst", "discover"): (
        "business-rules.md",
        "process-flow.md",
        "data-dictionary.md",
    ),
    ("ux-designer", "discover"): ("user-flows.md", "screen-specs.md", "accessibility-checklist.md"),
    ("solution-architect", "design"): ("design/design-doc.md", "design/adr/0001-architecture.md"),
    ("scrum-master", "plan"): ("plan.md",),
    ("sdet", "plan"): ("test/test-plan.md",),
    ("backend-engineer", "build"): ("build/{task}-report.md",),
    ("frontend-engineer", "build"): ("build/{task}-report.md",),
    ("sdet", "test"): ("test/test-report.md",),
    ("qa-analyst", "test"): ("test/qa-signoff.md",),
    ("code-reviewer", "review"): ("review/review-report.md",),
    ("security-engineer", "review"): ("review/security-review.md",),
    ("release-engineer", "release"): (
        "release/release-plan.md",
        "release/release-notes.md",
        "release/go-no-go.md",
    ),
    ("scrum-master", "retro"): ("retro.md",),
}


def expected_outputs(role: str, stage: str, task: str) -> list[str]:
    """Return the artifact paths (relative to the item directory) `role` must produce in `stage`.

    `{task}` is filled with `task`. A (role, stage) pair with no entry yields an empty list.
    """
    return [p.format(task=task) for p in OUTPUTS.get((role, stage), ())]


def build_prompt(
    role: str,
    stage: str,
    task: str,
    item: str,
    brief: Path,
    item_dir: Path,
    log: Path,
    inbox: list[Handoff],
) -> str:
    """Return the prompt for one task.

    It tells the agent to load `sdlc-protocol` and `role-<role>` first, to log each Superpowers
    skill it applies to `log`, which files to produce under `item_dir`, and that the orchestrator
    alone decides gate status. Inbox handoffs (for example retry reasons) are appended verbatim.
    """
    outputs = "\n".join(f"- {item_dir / p}" for p in expected_outputs(role, stage, task))
    lines = [
        f"You are the {role} agent in sdlc-mux. Stage: {stage}. Task: {task}. Work item: {item}.",
        "",
        (
            "1. Before any other action, load the skills `sdlc-protocol` and "
            f"`role-{role}`, then follow the Superpowers skills that role skill lists."
        ),
        f"2. Read the product brief at {brief}.",
        (
            f"3. Each time you apply a Superpowers skill, append one line to {log} naming the "
            "skill and why you applied it."
        ),
        "4. Produce these outputs, and write only inside the item directory:",
        outputs or "- (none listed for this role and stage)",
        (
            "5. Gate status is decided by the orchestrator, not by you. Never edit, claim or "
            "record a gate result, and never change board state."
        ),
    ]
    if inbox:
        lines += ["", "Handoffs in your inbox (address these first):"]
        lines += [f"--- from {h.from_}, status {h.status}\n{h.body.strip()}" for h in inbox]
    return "\n".join(lines) + "\n"
