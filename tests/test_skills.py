"""Skill consistency (role skills vs gates, bootstrap, Superpowers catalogue), sync, verify, doctor."""

import fnmatch
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdlc_mux import gates, superpowers
from sdlc_mux.bootstrap import OUTPUTS
from sdlc_mux.cli import app
from sdlc_mux.config import ROLES
from sdlc_mux.doctor import run_checks
from sdlc_mux.skills_sync import TARGETS, sync_skills

REPO = Path(__file__).parent.parent
ROLE_DIR = REPO / "skills" / "roles"
PROTOCOL = ("SKILL.md", "handoff.md", "artifacts.md", "board.md", "safety.md")
SECTIONS = [
    "Mission", "Load first", "Superpowers flow", "Inputs", "Outputs",
    "Definition of done", "Handoff", "Boundaries", "Escalate when",
]  # fmt: skip
runner = CliRunner()


def section(role: str, name: str) -> str:
    text = (ROLE_DIR / role / "SKILL.md").read_text(encoding="utf-8")
    return re.search(rf"^## {name}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL).group(1)  # type: ignore[union-attr]


def outputs(role: str) -> tuple[list[str], list[str]]:
    """(gate-checked paths, other paths) from a role skill's Outputs section."""
    got: tuple[list[str], list[str]] = ([], [])
    which = 0
    for line in section(role, "Outputs").splitlines():
        if line.startswith("Also produced"):
            which = 1
        m = re.match(r"- `([^`]+\.md)`", line)
        if m:
            got[which].append(m.group(1))
    return got


def flow_skills(role: str) -> list[str]:
    return re.findall(r"^\d+\. ([a-z-]+):", section(role, "Superpowers flow"), re.MULTILINE)


def gate_reasons(tmp_path: Path) -> str:
    """Every 'missing' reason the gates give for an empty item that has a UI."""
    (tmp_path / "ui").write_text("")
    return "\n".join(r for g in gates.GATES.values() for r in g(tmp_path).reasons)


def test_protocol_files_exist() -> None:
    for f in PROTOCOL:
        assert (REPO / "skills" / "sdlc-protocol" / f).read_text(encoding="utf-8").strip()
    rules = (REPO / "skills" / "sdlc-protocol" / "SKILL.md").read_text(encoding="utf-8")
    for needle in ("inbox", "needs-human.md", "sdlc board", "gate status", "Never merge"):
        assert needle in rules


def test_every_role_has_a_skill_in_the_required_shape() -> None:
    assert sorted(d.name for d in ROLE_DIR.iterdir()) == sorted(ROLES)
    for role in ROLES:
        text = (ROLE_DIR / role / "SKILL.md").read_text(encoding="utf-8")
        assert f"\nname: role-{role}\n" in text
        assert re.search(
            r"^description: Use when you are the .+ agent in sdlc-mux", text, re.MULTILINE
        )
        assert re.findall(r"^## (.+)$", text, re.MULTILINE) == SECTIONS


@pytest.mark.parametrize("role", ROLES)
def test_gate_checked_outputs_are_checked_by_gates(role: str, tmp_path: Path) -> None:
    reasons = gate_reasons(tmp_path)
    gated, _ = outputs(role)
    assert gated, f"{role} lists no gate-checked output"
    for path in gated:
        pattern = path.replace("<task>", "*")
        if "*" in pattern:  # a glob: the gate names its folder or its file pattern
            folder, _, name = pattern.rpartition("/")
            ok = f"{folder}/" in reasons or name in reasons
        else:
            ok = pattern in reasons
        assert ok, f"{role} names {path} but no gate in gates.py checks it"


@pytest.mark.parametrize("role", ROLES)
def test_bootstrap_outputs_and_role_skill_agree(role: str) -> None:
    gated, other = outputs(role)
    listed = [p.replace("<task>", "{task}") for p in gated + other]
    boot = [p for (r, _), ps in OUTPUTS.items() if r == role for p in ps]
    for p in boot:  # everything the orchestrator expects is documented in the skill
        assert any(fnmatch.fnmatch(p, g) for g in listed), f"{role}: bootstrap {p} not in skill"
    for g in (p.replace("<task>", "{task}") for p in gated):  # every gated path is expected
        assert any(fnmatch.fnmatch(p, g) for p in boot), f"{role}: skill {g} not in bootstrap"


@pytest.mark.parametrize("role", ROLES)
def test_superpowers_names_match_the_catalogue(role: str) -> None:
    assert flow_skills(role) == list(superpowers.ROLE_SKILLS[role])
    loaded = re.findall(r"^\d+\. Superpowers: (.+)$", section(role, "Load first"), re.MULTILINE)
    assert sorted(loaded) == sorted(set(superpowers.ROLE_SKILLS[role]))


def test_catalogue_names_are_the_twelve_verified_skills() -> None:
    doc = (REPO / "docs" / "reference" / "superpowers.md").read_text(encoding="utf-8")
    verified = set(re.findall(r"^\| ([a-z-]+) \| found \|", doc, re.MULTILINE))
    assert len(verified) == 12 and set(superpowers.SKILLS) <= verified


def test_sync_creates_skills_idempotently_in_a_temp_dir(tmp_path: Path) -> None:
    first = sync_skills(tmp_path)
    (tmp_path / TARGETS[0] / "role-sdet" / "stale.md").write_text("x")
    assert sync_skills(tmp_path) == first
    for t in TARGETS:
        assert (tmp_path / t / "sdlc-protocol" / "board.md").is_file()
        assert not (tmp_path / t / "role-sdet" / "stale.md").exists()
        for role in ROLES:
            assert (tmp_path / t / f"role-{role}" / "SKILL.md").is_file()


def test_sync_cli_writes_only_under_target_root(tmp_path: Path) -> None:
    r = runner.invoke(app, ["skills", "sync", "--target-root", str(tmp_path)])
    assert r.exit_code == 0
    assert (tmp_path / ".agents/skills/role-qa-analyst/SKILL.md").is_file()


def test_install_prints_routes_without_running_anything() -> None:
    r = runner.invoke(app, ["superpowers", "install", "--runner", "copilot"])
    assert r.exit_code == 0
    assert "copilot plugin install superpowers@superpowers-marketplace" in r.output
    assert runner.invoke(app, ["superpowers", "install", "--runner", "nope"]).exit_code == 2


def test_verify_reports_plugin_route_as_unverified_not_found(tmp_path: Path) -> None:
    r = runner.invoke(app, ["superpowers", "verify", "--root", str(tmp_path)])
    assert r.exit_code == 0
    assert "[found]" not in r.output
    assert "cannot check on disk (plugin install)" in r.output
    assert r.output.count("[UNVERIFIED]") == 3 * len(superpowers.SKILLS)
    assert "/plugin install superpowers@claude-plugins-official" in r.output


def test_verify_reports_found_only_with_a_skill_on_disk(tmp_path: Path) -> None:
    skill = tmp_path / ".claude/skills/brainstorming/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: brainstorming\n---\n")
    r = runner.invoke(app, ["superpowers", "verify", "--runner", "claude", "--root", str(tmp_path)])
    assert r.output.count("[found]") == 1 and "brainstorming" in r.output.splitlines()[0]


def _config(tmp_path: Path, mode: str) -> Path:
    text = (
        (REPO / "sdlc.yaml")
        .read_text(encoding="utf-8")
        .replace("mode: supervised", f"mode: {mode}")
    )
    f = tmp_path / "sdlc.yaml"
    f.write_text(text, encoding="utf-8")
    return f


def _which(name: str) -> str:
    return f"/fake/{name}"


def test_doctor_autonomous_fails_when_superpowers_not_verified(tmp_path: Path) -> None:
    rows = run_checks(_config(tmp_path, "autonomous"), _which, tmp_path)
    bad = [r for r in rows if not r[1]]
    assert len(bad) == 1 and "superpowers for claude not verified" in bad[0][0]
    assert "/plugin install" in bad[0][2]


def test_doctor_supervised_only_warns(tmp_path: Path) -> None:
    rows = run_checks(_config(tmp_path, "supervised"), _which, tmp_path)
    assert all(ok for _, ok, _ in rows)
    assert any("superpowers for claude" in i and "(warning)" in i for i, _, _ in rows)
    skills = [(i, d) for i, _, d in rows if i.startswith("sdlc skills missing")]
    assert skills and skills[0][1] == "sdlc skills sync"


def test_doctor_skills_warning_clears_after_sync(tmp_path: Path) -> None:
    sync_skills(tmp_path)
    rows = run_checks(_config(tmp_path, "supervised"), _which, tmp_path)
    assert not any(i.startswith("sdlc skills missing") for i, _, _ in rows)
