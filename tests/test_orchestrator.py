import itertools
import re
import sys
from pathlib import Path

from sdlc_mux import agent_loop, bootstrap
from sdlc_mux.board import Board
from sdlc_mux.config import Config, load_config
from sdlc_mux.gates import GATES
from sdlc_mux.handoffs import Handoff
from sdlc_mux.orchestrator import init_item, run_item
from sdlc_mux.runners.base import Bundle, Profile
from sdlc_mux.runners.mock import OUTPUTS as MOCK_OUTPUTS
from sdlc_mux.runners.mock import MockRunner

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "sdlc_mux"

# Runs the mock, then overwrites the test report with an open P1 bug.
BAD_REPORT = (
    "import sys; from pathlib import Path; from sdlc_mux.runners.mock import main; "
    "main(sys.argv[1:]); out = Path(sys.argv[sys.argv.index('--out') + 1]); "
    "(out / 'test' / 'test-report.md').write_text('- Passed: 3\\n- Open P1 bugs: 2\\n')"
)


class BadTestReportRunner(MockRunner):
    """Fake runner: the sdet's test-stage report always shows open P1 bugs."""

    def build_command(
        self, bundle: Bundle, prompt: str, mode: Profile, headless: bool, risks: bool = False
    ) -> list[str]:
        argv = super().build_command(bundle, prompt, mode, headless, risks)
        if (bundle.role, bundle.stage) == ("sdet", "test"):
            return [sys.executable, "-c", BAD_REPORT, *argv[3:]]
        return argv


def setup(tmp_path: Path, **limits: int) -> tuple[Config, Path]:
    cfg = load_config(ROOT / "sdlc.yaml")
    cfg = cfg.model_copy(update={"limits": cfg.limits.model_copy(update=limits)})
    init_item(tmp_path, "expense", ROOT / "examples" / "expense-splitter.md")
    return cfg, tmp_path


def state(ws: Path) -> str:
    board = Board(ws / "board.db")
    try:
        return board.state("expense")
    finally:
        board.close()


def test_mock_pipeline_reaches_done(tmp_path: Path) -> None:
    cfg, ws = setup(tmp_path)
    res = run_item(cfg, "expense", ws, runner_override="mock")
    assert (res.state, res.needs_human, res.reasons) == ("done", False, ())
    assert set(res.gates) == set(GATES)
    for name, gate in res.gates.items():
        assert gate.passed, (name, gate.reasons)
    d = ws / "runs" / "expense"
    for (role, stage), paths in bootstrap.OUTPUTS.items():
        for p in paths:
            tasks = ("T1", "T2") if stage == "build" else ("",)
            assert any((d / p.format(task=t)).is_file() for t in tasks), (role, p)
    assert (d / "build" / "T1-report.md").is_file() and (d / "build" / "T2-report.md").is_file()
    roles = {r for e in cfg.pipeline for r in e.roles} | {"orchestrator"}
    for role in roles:
        log = ws / "runs" / "logs" / "expense" / f"{role}.md"
        assert log.is_file() and log.stat().st_size > 0, role
    assert (ws / "runs" / "expense" / "outbox" / "product-owner" / "discover-discover.md").is_file()


def test_bootstrap_outputs_match_mock_outputs() -> None:
    mock = {k: {p for p, _, _ in v} for k, v in MOCK_OUTPUTS.items()}
    assert {k: set(v) for k, v in bootstrap.OUTPUTS.items()} == mock


def test_failing_artifact_retries_then_needs_human(tmp_path: Path) -> None:
    cfg, ws = setup(tmp_path, max_retries=1)
    res = run_item(cfg, "expense", ws, runner_override=BadTestReportRunner())
    assert res.needs_human and res.state == "testing"
    assert not res.gates["tested"].passed
    board = Board(ws / "board.db")
    assert board.needs_human("expense")
    board.close()
    for role in ("sdet", "qa-analyst"):
        text = (ws / "runs/expense/inbox" / role / "test.md").read_text()
        assert "status: blocked" in text
        assert "test-report.md does not show zero open P1 bugs" in text
    log = (ws / "runs/logs/expense/orchestrator.md").read_text()
    assert len(re.findall(r"gate-tested \| attempt \d: test-report", log)) == 2  # 1 try + 1 retry
    # A second call stops straight away: the item is flagged.
    again = run_item(cfg, "expense", ws, runner_override=BadTestReportRunner())
    assert again.needs_human and again.reasons == ("item needs a human",)


def test_time_limit_is_a_failure(tmp_path: Path) -> None:
    cfg, ws = setup(tmp_path, max_retries=0, max_minutes_per_task=30)
    ticks = itertools.count()
    res = run_item(cfg, "expense", ws, runner_override="mock", clock=lambda: next(ticks) * 1860.0)
    assert res.needs_human and res.state == "discovering"
    assert "exceeded the time limit" in res.reasons[0]
    assert " | timeout | " in (ws / "runs/logs/expense/product-owner.md").read_text()
    assert (
        "exceeded the time limit"
        in (ws / "runs/expense/outbox/product-owner/discover-discover.md").read_text()
    )


def test_agents_never_touch_gates_or_board() -> None:
    forbidden = re.compile(
        r"sdlc_mux\.(gates|board|orchestrator)|import .*\b(gates|board)\b|\.transition\(|"
        r"set_needs_human|\bGATES\b|check_[a-z]+\(|\bBoard\("
    )
    for mod in ("agent_loop.py", "bootstrap.py"):
        assert not forbidden.findall((SRC / mod).read_text()), mod


def test_prompt_contents(tmp_path: Path) -> None:
    log = tmp_path / "logs" / "x" / "sdet.md"
    retry = Handoff(from_="orchestrator", to="sdet", item="x", task="test", stage="test",
                    status="blocked", produced=[], needs=[], body="fix the P1 bug\n")  # fmt: skip
    prompt = bootstrap.build_prompt(
        "sdet", "test", "test", "x", tmp_path / "b.md", tmp_path, log, [retry]
    )
    assert "load the skills `sdlc-protocol` and `role-sdet`" in prompt
    assert prompt.index("sdlc-protocol") < prompt.index("brief")  # skills come first
    assert f"append one line to {log} naming the skill and why" in prompt
    assert "Superpowers skill" in prompt
    assert str(tmp_path / "test" / "test-report.md") in prompt
    assert "Gate status is decided by the orchestrator, not by you" in prompt
    assert "fix the P1 bug" in prompt


def test_writes_stay_inside_workspace(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="escapes the workspace"):
        agent_loop.log_event(tmp_path, "../../../evil", "po", "x")
    with pytest.raises(ValueError, match="headless only"):
        run_item(load_config(ROOT / "sdlc.yaml"), "expense", tmp_path, headless=False)
