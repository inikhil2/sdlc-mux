from pathlib import Path

import pytest

import sdlc_mux
from sdlc_mux import gates

TEMPLATES = Path(sdlc_mux.__file__).parent / "templates"
# Every artifact named in the role catalogue (Prompt.md 8.1) plus retro.md (retrospected gate).
ARTIFACTS = [
    "vision", "story", "business-rules", "process-flow", "data-dictionary", "user-flows",
    "screen-specs", "accessibility-checklist", "design-doc", "adr", "plan", "test-plan",
    "test-report", "qa-signoff", "review-report", "security-review", "release-plan",
    "release-notes", "go-no-go", "build-report", "handoff", "retro",
]  # fmt: skip


@pytest.mark.parametrize("name", ARTIFACTS)
def test_template_exists(name: str) -> None:
    assert (TEMPLATES / f"{name}.md").read_text(encoding="utf-8").strip()


def test_plan_template_follows_documented_format() -> None:
    tasks = gates.parse_plan((TEMPLATES / "plan.md").read_text(encoding="utf-8"))
    assert set(tasks) == {"T1", "T2"} and tasks["T2"][1] == ["T1"]


def test_design_doc_template_has_required_sections() -> None:
    text = (TEMPLATES / "design-doc.md").read_text(encoding="utf-8")
    assert all(f"## {s}" in text for s in gates.DESIGN_SECTIONS)


def test_handoff_template_has_every_field() -> None:
    text = (TEMPLATES / "handoff.md").read_text(encoding="utf-8")
    keys = ("from", "to", "item", "task", "stage", "status", "produced", "needs")
    assert all(f"{k}:" in text for k in keys)
