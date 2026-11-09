from pathlib import Path

import pytest

from sdlc_mux import gates

STORY = "\n".join(f"- Given a{i}\n- When b{i}\n- Then c{i}" for i in range(3))
DESIGN = "\n".join(f"## {s}\ntext" for s in gates.DESIGN_SECTIONS)
PLAN = "## Tasks\n- T1 | owner: backend-engineer | deps: - | test: tests/a.py\n- T2 | owner: sdet | deps: T1 | test: tests/b.py\n"
BUILD = "- Branch: feat/t1\n- Commits: 2\n- Test command: pytest\n- Exit code: 0\n"


def put(d: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    return d


PASS: dict[str, dict[str, str]] = {
    "discovered": {"vision.md": "v", "business-rules.md": "b", "stories/s1.md": STORY},
    "designed": {"design/design-doc.md": DESIGN, "design/adr/0001.md": "adr"},
    "planned": {"plan.md": PLAN, "test/test-plan.md": "tp"},
    "built": {"plan.md": PLAN, "build/T1-report.md": BUILD, "build/T2-report.md": BUILD},
    "tested": {
        "test/test-report.md": "- Passed: 12\n- Failed: 0\n- Open P1 bugs: 0\n",
        "test/qa-signoff.md": "ok",
    },
    "reviewed": {
        "review/review-report.md": "- Verdict: approve\n",
        "review/security-review.md": "- Unresolved High: 0\n",
    },
    "released": {"release/release-notes.md": "n", "release/go-no-go.md": "- Decision: GO\n"},
    "retrospected": {"retro.md": "r"},
}

# Each fail fixture is a near-miss of the pass fixture, plus the expected reason fragment.
FAIL: dict[str, tuple[dict[str, str], str]] = {
    "discovered": (
        {**PASS["discovered"], "stories/s1.md": "- Given a\n- When b\n- Then c\n"},
        "Given/When/Then",
    ),
    "designed": (
        {**PASS["designed"], "design/design-doc.md": "## Context\nx"},
        "lacks section 'Options'",
    ),
    "planned": (
        {
            **PASS["planned"],
            "plan.md": "- T1 | owner: a | deps: T2 | test: x\n- T2 | owner: a | deps: T1 | test: x\n",
        },
        "cycle",
    ),
    "built": (
        {**PASS["built"], "build/T2-report.md": BUILD.replace("Exit code: 0", "Exit code: 1")},
        "did not exit 0",
    ),
    "tested": (
        {**PASS["tested"], "test/test-report.md": "- Passed: 12\n- Open P1 bugs: 2\n"},
        "P1",
    ),
    "reviewed": (
        {**PASS["reviewed"], "review/security-review.md": "- Unresolved High: 1\n"},
        "High",
    ),
    "released": ({**PASS["released"], "release/go-no-go.md": "- Decision: NO-GO\n"}, "GO"),
    "retrospected": ({}, "retro.md is missing"),
}


@pytest.mark.parametrize("name", list(gates.GATES))
def test_gate_passes(name: str, tmp_path: Path) -> None:
    res = gates.GATES[name](put(tmp_path, PASS[name]))
    assert res.passed and res.reasons == ()


@pytest.mark.parametrize("name", list(gates.GATES))
def test_gate_fails(name: str, tmp_path: Path) -> None:
    files, reason = FAIL[name]
    res = gates.GATES[name](put(tmp_path, files))
    assert not res.passed and any(reason in r for r in res.reasons)


@pytest.mark.parametrize("name", list(gates.GATES))
def test_gate_fails_on_empty_dir(name: str, tmp_path: Path) -> None:
    assert not gates.GATES[name](tmp_path).passed


def test_gate_names_match_board_states() -> None:
    from sdlc_mux.board import STATES

    assert set(gates.GATES) <= set(STATES)


def test_discovered_requires_screen_specs_for_ui(tmp_path: Path) -> None:
    put(tmp_path, {**PASS["discovered"], "ui": ""})
    assert "screen-specs.md is missing" in gates.check_discovered(tmp_path).reasons
    put(tmp_path, {"screen-specs.md": "s"})
    assert gates.check_discovered(tmp_path).passed


def test_designed_needs_adr(tmp_path: Path) -> None:
    put(tmp_path, {"design/design-doc.md": DESIGN})
    assert "design/adr/ has no ADR" in gates.check_designed(tmp_path).reasons


def test_planned_duplicate_ids_and_missing_test(tmp_path: Path) -> None:
    put(
        tmp_path,
        {
            "plan.md": "- T1 | owner: a | deps: - | test: x\n- T1 | owner: a | deps: - |\n",
            "test/test-plan.md": "t",
        },
    )
    reasons = gates.check_planned(tmp_path).reasons
    assert "duplicate task id 'T1'" in reasons


def test_planned_missing_test_reference(tmp_path: Path) -> None:
    put(tmp_path, {"plan.md": "- T1 | owner: a | deps: -\n", "test/test-plan.md": "t"})
    assert "task T1 has no test reference" in gates.check_planned(tmp_path).reasons


def test_built_missing_report_for_planned_task(tmp_path: Path) -> None:
    put(tmp_path, {"plan.md": PLAN, "build/T1-report.md": BUILD})
    assert "task T2 has no build report" in gates.check_built(tmp_path).reasons
