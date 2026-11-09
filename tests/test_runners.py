import json
import os
from pathlib import Path

import pytest

from sdlc_mux import gates
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle, RiskRefusal
from sdlc_mux.runners.mock import MockRunner

FIXTURE = Path(__file__).parent / "fixtures" / "runner_argv.json"
BRIEF = """# Expense splitter

- **Goal**: help a group of friends see who owes whom.
- **Users**: group organiser, group member.
- **In scope**: create a group; add expenses; show balances.
- **Constraints**: Python 3.12, FastAPI, SQLite.

1. Given a group with two members, when Ana pays 10 for both, then Bo owes Ana 5.
2. Given an empty group, when I add a member, then the group has one member.
3. Given balances, when I ask for settle-up, then I see the fewest transfers.
"""
CASES = [(r, m, h) for r in ("claude", "codex", "copilot") for m in ("supervised", "autonomous")
         for h in (True, False)]  # fmt: skip


def bundle(tmp_path: Path, role: str = "product-owner", stage: str = "discover") -> Bundle:
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")
    return Bundle(role, stage, "item-1", brief, tmp_path / "out")


@pytest.mark.parametrize(("runner", "mode", "headless"), CASES)
def test_argv_snapshot(tmp_path: Path, runner: str, mode: str, headless: bool) -> None:
    key = f"{runner}/{mode}/{'headless' if headless else 'interactive'}"
    argv = RUNNERS[runner]().build_command(bundle(tmp_path), "do the task", mode, headless)  # type: ignore[arg-type]
    assert argv == json.loads(FIXTURE.read_text())[key]


def test_runner_flag_changes_command(tmp_path: Path) -> None:
    b = bundle(tmp_path)
    heads = {n: RUNNERS[n]().build_command(b, "p", "supervised", True)[0] for n in RUNNERS}
    assert [heads[n] for n in ("claude", "codex", "copilot")] == ["claude", "codex", "copilot"]
    assert len(set(heads.values())) == len(RUNNERS)


def test_never_bare() -> None:
    for mode in ("supervised", "autonomous", "unsafe"):
        assert "--bare" not in RUNNERS["claude"]().permission_flags(mode, True, True)  # type: ignore[arg-type]


@pytest.mark.parametrize("runner", ["claude", "codex", "copilot"])
def test_unsafe_refused_without_flag(tmp_path: Path, runner: str) -> None:
    r = RUNNERS[runner]()
    with pytest.raises(RiskRefusal, match="--i-understand-the-risks"):
        r.build_command(bundle(tmp_path), "p", "unsafe", True)
    assert r.build_command(bundle(tmp_path), "p", "unsafe", True, i_understand_the_risks=True)


def test_unknown_profile() -> None:
    with pytest.raises(ValueError):
        RUNNERS["claude"]().permission_flags("yolo")  # type: ignore[arg-type]


def test_skills_dirs() -> None:
    assert RUNNERS["claude"]().skills_dir("project") == Path(".claude/skills")
    assert RUNNERS["codex"]().skills_dir("user") == Path.home() / ".agents/skills"


def test_check_installed_missing_and_fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    assert not RUNNERS["claude"]().check_installed().installed
    fake = tmp_path / "claude"
    fake.write_text("#!/bin/sh\necho 'fake 1.0'\n")
    fake.chmod(0o755)
    st = RUNNERS["claude"]().check_installed()
    assert st.installed and st.version == "fake 1.0"


def test_parse_result(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.md").write_text("x")
    res = RUNNERS["mock"]().parse_result(0, tmp_path)
    assert res.ok and res.artifacts == ("a/x.md",)
    assert not RUNNERS["mock"]().parse_result(2, tmp_path).ok


def snapshot(d: Path) -> dict[str, bytes]:
    return {
        p.relative_to(d).as_posix(): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()
    }


DISCOVER = ["product-owner", "business-analyst", "ux-designer"]


def run_discover(tmp_path: Path, out: str) -> Path:
    d = tmp_path / out
    for role in DISCOVER:
        b = bundle(tmp_path, role)
        MockRunner().run(Bundle(b.role, b.stage, b.item, b.brief, d))
    return d


def test_mock_deterministic(tmp_path: Path) -> None:
    one, two = run_discover(tmp_path, "a"), run_discover(tmp_path, "b")
    assert snapshot(one) and snapshot(one) == snapshot(two)


def test_mock_uses_brief_and_passes_discovered_gate(tmp_path: Path) -> None:
    d = run_discover(tmp_path, "a")
    assert "help a group of friends" in (d / "vision.md").read_text()
    assert "Bo owes Ana 5" in (d / "stories/S1.md").read_text()
    (d / "ui").touch()  # item has a UI, so screen-specs.md is required too
    assert gates.check_discovered(d).passed, gates.check_discovered(d).reasons
    assert not list(d.rglob("*{{*"))
    assert all("{{" not in t.decode() for t in snapshot(d).values())


def test_mock_all_stages_pass_their_gates(tmp_path: Path) -> None:
    """Every gate except `built` and `retrospected` roles' extras is satisfiable by the mock."""
    d = tmp_path / "all"
    roles = {
        "discover": DISCOVER, "design": ["solution-architect"], "plan": ["scrum-master", "sdet"],
        "build": ["backend-engineer"], "test": ["sdet", "qa-analyst"],
        "review": ["code-reviewer", "security-engineer"], "release": ["release-engineer"],
        "retro": ["scrum-master"],
    }  # fmt: skip
    for stage, rs in roles.items():
        for role in rs:
            b = bundle(tmp_path, role, stage)
            for t in ("T1", "T2"):
                MockRunner().run(Bundle(role, stage, b.item, b.brief, d, t))
    for name, check in gates.GATES.items():
        res = check(d)
        assert res.passed, (name, res.reasons)


def test_mock_command_is_offline_module(tmp_path: Path) -> None:
    argv = MockRunner().build_command(bundle(tmp_path), "ignored", "supervised", True)
    assert argv[1:3] == ["-m", "sdlc_mux.runners.mock"] and os.path.isabs(argv[0])
