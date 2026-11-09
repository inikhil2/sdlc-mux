"""The loop one agent pane runs: read inbox, build prompt, invoke runner, log, write outbox.

It never decides gate status and never moves the board; the orchestrator owns both (ADR 0003).
All writes go under the workspace root.
"""

import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sdlc_mux.bootstrap import build_prompt
from sdlc_mux.handoffs import Handoff, HandoffError, parse_handoff, write_handoff
from sdlc_mux.runners.base import Bundle, Profile, Runner


@dataclass(frozen=True)
class TaskResult:
    """Outcome of one agent task: `ok` iff the runner exited 0 within the time limit."""

    ok: bool
    exit_code: int
    seconds: float
    reason: str = ""


def safe_path(workspace: Path, *parts: str) -> Path:
    """Return workspace/<parts> resolved; raise ValueError if it would leave the workspace."""
    root = workspace.resolve()
    p = root.joinpath(*parts).resolve()
    if not p.is_relative_to(root):
        raise ValueError(f"path {'/'.join(parts)!r} escapes the workspace {root}")
    return p


def item_dir(workspace: Path, item: str) -> Path:
    """Directory holding the item's brief and artifacts: workspace/runs/<item>."""
    return safe_path(workspace, "runs", item)


def log_event(workspace: Path, item: str, role: str, event: str, detail: str = "") -> None:
    """Append one line `<utc time> | <role> | <event> | <detail>` to runs/logs/<item>/<role>.md."""
    f = safe_path(workspace, "runs", "logs", item, f"{role}.md")
    f.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts} | {role} | {event} | {' '.join(detail.split())}\n")


def read_inbox(workspace: Path, item: str, role: str, stage: str) -> list[Handoff]:
    """Return the handoffs in the role's inbox for `stage`, oldest file name first.

    Raises HandoffError if an inbox file is malformed.
    """
    box = safe_path(workspace, "runs", item, "inbox", role)
    found = [parse_handoff(f.read_text(encoding="utf-8")) for f in sorted(box.glob("*.md"))]
    return [h for h in found if h.stage == stage]


def run_task(
    workspace: Path,
    bundle: Bundle,
    runner: Runner,
    *,
    profile: Profile = "supervised",
    headless: bool = True,
    i_understand_the_risks: bool = False,
    timeout_s: float = 1800,
    clock: Callable[[], float] = time.monotonic,
) -> TaskResult:
    """Run one task end to end and write an outbox handoff to the orchestrator.

    Reads the inbox, builds the prompt, runs the runner's command with cwd=workspace and a
    `timeout_s` limit (elapsed time is also measured with `clock`), logs each event, and writes
    runs/<item>/outbox/<role>/<stage>-<task>.md. A non-zero exit or a time overrun is a failed
    result. Raises RiskRefusal if the profile needs the acknowledgement and it was not given.
    """
    b = bundle
    log = safe_path(workspace, "runs", "logs", b.item, f"{b.role}.md")
    inbox = read_inbox(workspace, b.item, b.role, b.stage)
    log_event(workspace, b.item, b.role, "task-start", f"{b.stage}/{b.task}, {len(inbox)} inbox")
    prompt = build_prompt(b.role, b.stage, b.task, b.item, b.brief, b.outputs_dir, log, inbox)
    argv = runner.build_command(b, prompt, profile, headless, i_understand_the_risks)
    log_event(workspace, b.item, b.role, "runner-start", f"{runner.name} {profile}")
    start = clock()
    try:
        proc = subprocess.run(
            argv, cwd=workspace, capture_output=True, text=True, timeout=timeout_s, check=False
        )
        code, tail = proc.returncode, (proc.stderr or proc.stdout)[-200:]
    except subprocess.TimeoutExpired:
        code, tail = -1, "killed at the time limit"
    seconds = clock() - start
    reason, timed_out = "", seconds > timeout_s
    if timed_out:
        reason = f"{b.role} exceeded the time limit ({seconds:.0f}s > {timeout_s:.0f}s)"
    elif code != 0:
        reason = f"{b.role} runner exited with code {code}: {tail}"
    log_event(workspace, b.item, b.role, "timeout" if timed_out else "runner-exit",
              reason or f"exit {code} in {seconds:.0f}s")  # fmt: skip
    result = TaskResult(not reason, code, seconds, reason)
    produced = [p.relative_to(b.outputs_dir).as_posix() for p in sorted(b.outputs_dir.rglob("*"))
                if p.is_file() and "inbox" not in p.parts and "outbox" not in p.parts]  # fmt: skip
    out = Handoff(
        from_=b.role, to="orchestrator", item=b.item, task=b.task, stage=b.stage,
        status="done" if result.ok else "blocked", produced=produced,
        needs=[] if result.ok else [reason], body=reason or "completed\n",
    )  # fmt: skip
    f = safe_path(workspace, "runs", b.item, "outbox", b.role, f"{b.stage}-{b.task}.md")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(write_handoff(out), encoding="utf-8")
    log_event(workspace, b.item, b.role, "outbox-written", f.name)
    return result


def work_once(workspace: Path, role: str, runner: Runner, profile: Profile = "supervised") -> int:
    """Run every inbox task of `role` not yet answered by a newer outbox handoff; return how many.

    A malformed inbox file is logged and skipped. Never touches the board or gates.
    """
    ran = 0
    for f in sorted(safe_path(workspace, "runs").glob(f"*/inbox/{role}/*.md")):
        item = f.relative_to(safe_path(workspace, "runs")).parts[0]
        try:
            h = parse_handoff(f.read_text(encoding="utf-8"))
        except HandoffError as e:
            log_event(workspace, item, role, "bad-inbox", f"{f.name}: {e}")
            continue
        out = safe_path(workspace, "runs", item, "outbox", role, f"{h.stage}-{h.task}.md")
        if out.exists() and out.stat().st_mtime >= f.stat().st_mtime:
            continue  # already answered
        d = item_dir(workspace, item)
        run_task(workspace, Bundle(role, h.stage, item, d / "brief.md", d, h.task), runner,
                 profile=profile)  # fmt: skip
        ran += 1
    return ran
