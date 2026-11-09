"""Pipeline driver. The orchestrator alone runs gates and moves the board (ADR 0003).

Plain Python, no LLM decisions. Layout under the workspace root:
board.db, runs/<item>/ (brief.md, artifacts, inbox/, outbox/), runs/logs/<item>/<role>.md.
"""

import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sdlc_mux.agent_loop import item_dir, log_event, run_task, safe_path
from sdlc_mux.board import STATES, Board
from sdlc_mux.config import Config
from sdlc_mux.gates import GATES, GateResult, parse_plan
from sdlc_mux.handoffs import Handoff, write_handoff
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle, Profile, Runner

# stage -> (state while the stage runs, state once its gate passes); the gate has the same name
# as the second state. The retro stage has no working state.
STAGE_STATES: dict[str, tuple[str | None, str]] = {
    "discover": ("discovering", "discovered"),
    "design": ("designing", "designed"),
    "plan": ("planning", "planned"),
    "build": ("building", "built"),
    "test": ("testing", "tested"),
    "review": ("reviewing", "reviewed"),
    "release": ("releasing", "released"),
    "retro": (None, "retrospected"),
}


@dataclass(frozen=True)
class RunResult:
    """Outcome of run_item: final board `state`, whether it `needs_human`, the last gate result
    per stage reached, and the failure `reasons` that stopped the run (empty on success)."""

    item: str
    state: str
    needs_human: bool
    gates: dict[str, GateResult]
    reasons: tuple[str, ...] = ()


def init_item(workspace: Path, item_id: str, brief: Path) -> Path:
    """Copy `brief` to workspace/runs/<item>/brief.md and return that path."""
    dest = item_dir(workspace, item_id) / "brief.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(brief, dest)
    return dest


def _runner_for(config: Config, role: str, override: str | Runner | None) -> Runner:
    if isinstance(override, Runner):
        return override
    if isinstance(override, str):
        return RUNNERS[override]()
    for section in config.sections:
        for agent in section.agents:
            if agent.role == role:
                return RUNNERS[agent.runner]()
    raise ValueError(f"pipeline role '{role}' has no agent in sdlc.yaml sections")


def run_item(
    config: Config,
    item_id: str,
    workspace: Path,
    runner_override: str | Runner | None = None,
    headless: bool = True,
    i_understand_the_risks: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> RunResult:
    """Walk the pipeline for one item whose brief is at workspace/runs/<item>/brief.md.

    Per stage: move the board to the working state, run each role's task, run the stage gate,
    then advance. A failed task or gate is retried up to `limits.max_retries` times with the
    reasons written to each role's inbox; after that the item is flagged needs-human and the
    run stops. A re-run resumes from the board state. `runner_override` (a runner name or
    instance) replaces every agent's configured runner. The profile is `unsafe` only when
    `i_understand_the_risks` is True, else the config mode. Raises ValueError for
    `headless=False` (interactive agents are driven from tmux panes, not from here).
    """
    if not headless:
        raise ValueError("run_item is headless only; interactive agents run in tmux panes")
    profile: Profile = "unsafe" if i_understand_the_risks else config.mode
    brief = item_dir(workspace, item_id) / "brief.md"
    board = Board(safe_path(workspace, "board.db"))
    try:
        if item_id not in {i for i, _, _ in board.list_items()}:
            title = brief.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            board.add_item(item_id, title)
        if board.needs_human(item_id):
            return RunResult(item_id, board.state(item_id), True, {}, ("item needs a human",))
        gates: dict[str, GateResult] = {}
        for entry in config.pipeline:
            reasons = _run_stage(
                config, board, item_id, workspace, entry.stage, entry.roles, gates,
                runner_override, profile, i_understand_the_risks, clock,
            )  # fmt: skip
            if reasons:
                board.set_needs_human(item_id, True)
                log_event(workspace, item_id, "orchestrator", "needs-human", "; ".join(reasons))
                return RunResult(item_id, board.state(item_id), True, gates, tuple(reasons))
        board.transition(item_id, "done")
        log_event(workspace, item_id, "orchestrator", "done")
        return RunResult(item_id, board.state(item_id), False, gates)
    finally:
        board.close()


def _tasks(stage: str, roles: list[str], plan: Path) -> list[tuple[str, str]]:
    """(role, task id) pairs for a stage; build tasks come from plan.md, owned by their owner."""
    if stage != "build":
        return [(r, stage) for r in roles]
    planned = parse_plan(plan.read_text(encoding="utf-8")) if plan.is_file() else {}
    return [(owner, tid) for tid, (owner, _, _) in planned.items() if owner in roles]


def _run_stage(
    config: Config,
    board: Board,
    item: str,
    ws: Path,
    stage: str,
    roles: list[str],
    gates: dict[str, GateResult],
    override: str | Runner | None,
    profile: Profile,
    risks: bool,
    clock: Callable[[], float],
) -> list[str]:
    """Run one stage with retries; return [] on success or the final failure reasons."""
    working, done = STAGE_STATES[stage]
    state = board.state(item)
    if STATES.index(state) >= STATES.index(done):
        return []  # already past this stage (resumed run)
    if working and state != working:
        board.transition(item, working)
    d = item_dir(ws, item)
    reasons: list[str] = []
    for attempt in range(config.limits.max_retries + 1):
        reasons = []
        for role, task in _tasks(stage, roles, d / "plan.md"):
            bundle = Bundle(role, stage, item, d / "brief.md", d, task)
            res = run_task(
                ws, bundle, _runner_for(config, role, override), profile=profile,
                i_understand_the_risks=risks,
                timeout_s=config.limits.max_minutes_per_task * 60, clock=clock,
            )  # fmt: skip
            if not res.ok:
                reasons.append(res.reason)
        gate = GATES[done](d)
        gates[done] = gate
        reasons += list(gate.reasons)
        log_event(ws, item, "orchestrator", f"gate-{done}",
                  f"attempt {attempt + 1}: " + ("passed" if not reasons else "; ".join(reasons)))  # fmt: skip
        if not reasons:
            board.transition(item, done)
            for role in roles:
                safe_path(ws, "runs", item, "inbox", role, f"{stage}.md").unlink(missing_ok=True)
            return []
        for role in roles:
            _send_retry(ws, item, role, stage, reasons)
    return reasons


def _send_retry(ws: Path, item: str, role: str, stage: str, reasons: list[str]) -> None:
    """Write the failure reasons to the role's inbox as a blocked handoff for the stage."""
    h = Handoff(
        from_="orchestrator", to=role, item=item, task=stage, stage=stage, status="blocked",
        produced=[], needs=reasons, body="The stage failed. Fix these and redo your outputs:\n"
        + "\n".join(f"- {r}" for r in reasons) + "\n",
    )  # fmt: skip
    f = safe_path(ws, "runs", item, "inbox", role, f"{stage}.md")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(write_handoff(h), encoding="utf-8")
