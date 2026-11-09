"""Multiplexer, dashboard and T6 CLI tests. tmux tests use a dedicated server (-L sdlc-test)."""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdlc_mux.board import Board
from sdlc_mux.cli import app
from sdlc_mux.config import load_config
from sdlc_mux.gates import GATES
from sdlc_mux.handoffs import Handoff, write_handoff
from sdlc_mux.multiplexer import ZellijMultiplexer

ROOT = Path(__file__).parent.parent
SOCKET = "sdlc-test"
cli = CliRunner()
CFG = load_config(ROOT / "sdlc.yaml")


def tmux(*args: str) -> list[str]:
    p = subprocess.run(["tmux", "-L", SOCKET, *args], capture_output=True, text=True, check=False)
    return p.stdout.splitlines()


@pytest.fixture
def room(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A workspace path with the sdlc CLI pointed at the dedicated tmux server; panes just sleep."""
    if not shutil.which("tmux"):
        pytest.skip("tmux is not installed")
    monkeypatch.setenv("SDLC_TMUX_SOCKET", SOCKET)
    monkeypatch.setenv("SDLC_PANE_CMD", "sh -c 'sleep 300' sdlc")
    tmux("kill-server")
    yield tmp_path / "ws"
    tmux("kill-server")


def up(ws: Path) -> str:
    r = cli.invoke(
        app, ["up", "--detach", "--config", str(ROOT / "sdlc.yaml"), "--workspace", str(ws)]
    )
    assert r.exit_code == 0, r.output
    return r.output


def panes(fmt: str) -> list[str]:
    return tmux("list-panes", "-t", "sdlc:room", "-F", fmt)


def test_up_creates_one_room_window_with_all_panes(room: Path) -> None:
    up(room)
    assert tmux("list-sessions", "-F", "#{session_name}") == ["sdlc"]
    assert tmux("list-windows", "-t", "sdlc", "-F", "#{window_name}") == ["room"]
    instances = sum(a.instances for s in CFG.sections for a in s.agents)
    assert instances == 13
    titles = panes("#{pane_title}")
    assert len(titles) == 1 + instances == 14


def test_titles_and_column_order_follow_sdlc_yaml(room: Path) -> None:
    up(room)
    want = [
        f"[{s.name}] {a.role}#{n} · {a.runner} · idle"
        for s in CFG.sections
        for a in s.agents
        for n in range(1, a.instances + 1)
    ]
    assert panes("#{pane_title}")[1:] == want
    # Dashboard spans the full width on top; columns run left to right in section order.
    rows = [r.split() for r in panes("#{pane_left} #{pane_top} #{pane_width} #{window_width}")]
    assert rows[0][0] == "0" and rows[0][2] == rows[0][3]
    lefts = [int(r[0]) for r in rows[1:]]
    assert lefts == sorted(lefts)
    assert panes("#{@color}")[1:4] == ["blue"] * 3
    assert tmux("show-options", "-wv", "-t", "sdlc:room", "pane-border-status") == ["top"]
    height = int(tmux("display", "-p", "-t", "sdlc:room", "#{window_height}")[0])
    assert abs(int(rows[0][1] == "1" and panes("#{pane_height}")[0]) - 0.3 * height) < 3


def test_up_is_idempotent(room: Path) -> None:
    up(room)
    ids = panes("#{pane_id}")
    out = up(room)
    assert "already exists" in out
    assert tmux("list-sessions", "-F", "#{session_name}") == ["sdlc"]
    assert panes("#{pane_id}") == ids


def test_down_kills_session_and_keeps_state(room: Path) -> None:
    up(room)
    room.joinpath("board.db").write_text("state")
    assert cli.invoke(app, ["down"]).exit_code == 0
    assert tmux("list-sessions") == []
    assert (room / "board.db").read_text() == "state"


def test_focus_gives_section_the_full_window_and_sections_restores(room: Path) -> None:
    up(room)
    r = cli.invoke(app, ["layout", "--preset", "focus", "Engineering"])
    assert r.exit_code == 0, r.output
    assert panes("#{pane_title}") == [
        "[Engineering] backend-engineer#1 · claude · idle",
        "[Engineering] backend-engineer#2 · claude · idle",
        "[Engineering] frontend-engineer#1 · claude · idle",
    ]
    assert {r for r in panes("#{pane_width}=#{window_width}")} == {"300=300"}
    assert sum(int(h) for h in panes("#{pane_height}")) >= 190  # three stacked panes fill 200 rows
    assert cli.invoke(app, ["layout", "--preset", "grid"]).exit_code == 0
    assert len(panes("#{pane_id}")) == 14
    assert cli.invoke(app, ["layout", "--preset", "sections"]).exit_code == 0
    assert panes("#{pane_title}")[0] == "[Dashboard]" and len(panes("#{pane_id}")) == 14
    assert cli.invoke(app, ["layout", "--preset", "focus", "Nope"]).exit_code == 1


def test_chat_opens_a_window_in_the_session(room: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    up(room)
    cfg = room.parent / "chat.yaml"  # mock runner: its interactive command is harmless
    cfg.write_text((ROOT / "sdlc.yaml").read_text().replace("runner: claude", "runner: mock"))
    r = cli.invoke(app, ["chat", "sdet", "--config", str(cfg), "--workspace", str(room)])
    assert r.exit_code == 0, r.output
    assert "chat-sdet" in tmux("list-windows", "-t", "sdlc", "-F", "#{window_name}")


def test_approve_records_override_and_only_release_writes_go(tmp_path: Path) -> None:
    item = tmp_path / "runs" / "x"
    item.mkdir(parents=True)
    log = tmp_path / "runs" / "logs" / "x" / "orchestrator.md"

    def approve(gate: str) -> int:
        return cli.invoke(app, ["approve", "x", gate, "--workspace", str(tmp_path)]).exit_code

    assert approve("reviewed") == 0
    assert "human-override | gate=reviewed approver=" in log.read_text()
    assert not (item / "release" / "go-no-go.md").exists()
    assert not GATES["reviewed"](item).passed  # the override does not pass the gate
    assert approve("release") == 0
    assert "Decision: GO" in (item / "release" / "go-no-go.md").read_text()
    assert "gate=released" in log.read_text()
    assert not GATES["released"](item).passed  # release-notes.md still missing
    assert approve("bogus") == 2


def test_run_with_mock_reaches_done_and_dashboard_shows_it(tmp_path: Path) -> None:
    r = cli.invoke(app, ["run", str(ROOT / "examples" / "expense-splitter.md"), "--runner", "mock",
                         "--config", str(ROOT / "sdlc.yaml"), "--workspace", str(tmp_path)])  # fmt: skip
    assert r.exit_code == 0, r.output
    assert "expense-splitter: done" in r.output
    d = cli.invoke(app, ["dashboard", "--once", "--workspace", str(tmp_path)])
    assert "expense-splitter" in d.output and "done" in d.output
    assert cli.invoke(app, ["run", "x.md", "--runner", "nope"]).exit_code == 2


def test_dashboard_feed_keeps_last_20(tmp_path: Path) -> None:
    from sdlc_mux.dashboard import feed

    log = tmp_path / "runs" / "logs" / "i" / "r.md"
    log.parent.mkdir(parents=True)
    log.write_text("".join(f"2026-01-01T00:00:{n:02d}+00:00 | r | e | {n}\n" for n in range(30)))
    got = feed(tmp_path)
    assert len(got) == 20 and got[0].endswith("| 10") and got[-1].endswith("| 29")
    Board(tmp_path / "board.db").close()


def test_agent_loop_runs_inbox_task_then_stops(tmp_path: Path) -> None:
    inbox = tmp_path / "runs" / "i" / "inbox" / "product-owner"
    inbox.mkdir(parents=True)
    (tmp_path / "runs" / "i" / "brief.md").write_text("# Brief\n")
    h = Handoff(from_="orchestrator", to="product-owner", item="i", task="discover",
                stage="discover", status="blocked", produced=[], needs=["x"], body="b\n")  # fmt: skip
    (inbox / "discover.md").write_text(write_handoff(h))
    args = ["agent-loop", "--role", "product-owner", "--instance", "1", "--runner", "mock",
            "--max-iterations", "2", "--interval", "0", "--config", str(ROOT / "sdlc.yaml"),
            "--workspace", str(tmp_path)]  # fmt: skip
    r = cli.invoke(app, args)
    assert r.exit_code == 0, r.output
    assert "ran 1 task(s)" in r.output and "ran 1 task(s)" not in r.output.split("ran 1", 1)[1]
    assert (tmp_path / "runs" / "i" / "outbox" / "product-owner" / "discover-discover.md").is_file()


def test_zellij_is_planned_only() -> None:
    msg = "Zellij backend is planned, not built in v1; see docs/adr/0007-zellij-planned-only.md"
    z = ZellijMultiplexer()
    for call in (z.session_exists, z.kill_session, z.attach):
        with pytest.raises(NotImplementedError, match=msg.replace(".", r"\.")):
            call()
