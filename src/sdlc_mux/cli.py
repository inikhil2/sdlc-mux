"""The `sdlc` command-line entry point."""

import getpass
import os
import re
import shlex
import time
from pathlib import Path
from typing import Annotated, cast

import typer

from sdlc_mux import dashboard, superpowers
from sdlc_mux.agent_loop import item_dir, log_event, work_once
from sdlc_mux.config import Config, ConfigError, load_config
from sdlc_mux.doctor import run_checks
from sdlc_mux.gates import GATES
from sdlc_mux.multiplexer import PaneSpec, SectionSpec, SessionSpec, TmuxMultiplexer, pane_title
from sdlc_mux.multiplexer.base import PRESETS, Preset
from sdlc_mux.multiplexer.tmux import TmuxError
from sdlc_mux.orchestrator import _runner_for, init_item, run_item
from sdlc_mux.runners import RUNNERS
from sdlc_mux.runners.base import Bundle, RiskRefusal
from sdlc_mux.skills_sync import sync_skills

app = typer.Typer(
    help="Run an SDLC pipeline with a team of AI agents in tmux.", no_args_is_help=True
)
skills_app = typer.Typer(help="Manage the sdlc skills.", no_args_is_help=True)
superpowers_app = typer.Typer(help="Install and verify Superpowers.", no_args_is_help=True)
app.add_typer(skills_app, name="skills")
app.add_typer(superpowers_app, name="superpowers")


@app.callback()
def main() -> None:
    """sdlc-mux command group."""


@app.command()
def learn() -> None:
    """Print a guided tour, built from docs/00-start-here.md and docs/01-concepts.md."""
    parts = [DOCS / "00-start-here.md", DOCS / "01-concepts.md"]
    if not all(p.is_file() for p in parts):
        typer.echo(
            "The tour is built from docs/00-start-here.md and docs/01-concepts.md, which are not "
            "part of this install. Read them in the repository: "
            "https://github.com/inikhil2/sdlc-mux/tree/main/docs",
            err=True,
        )
        raise typer.Exit(1)
    for n, p in enumerate(parts, 1):
        text = re.sub(
            r"```mermaid.*?```",
            "(diagram: open the file to see it)",
            p.read_text(),
            flags=re.DOTALL,
        )
        typer.echo(f"=== Part {n} of {len(parts)}: docs/{p.name} ===\n\n{text.strip()}\n")


@app.command()
def doctor(
    config: Annotated[Path, typer.Option("--config", help="Path to sdlc.yaml.")] = Path(
        "sdlc.yaml"
    ),
) -> None:
    """Check prerequisites; print the fix command for each missing item; exit 1 if any missing."""
    failed = False
    for item, ok, detail in run_checks(config):
        typer.echo(f"[ok]      {item}" if ok else f"[MISSING] {item}\n          fix: {detail}")
        failed |= not ok
    raise typer.Exit(1 if failed else 0)


ConfigOpt = Annotated[Path, typer.Option("--config", help="Path to sdlc.yaml.")]
WorkspaceOpt = Annotated[Path, typer.Option("--workspace", help="Workspace folder.")]
SESSION = "sdlc"
DOCS = Path(__file__).resolve().parents[2] / "docs"  # present in a checkout, not in a wheel


def _mux() -> TmuxMultiplexer:
    """The tmux backend; SDLC_TMUX_SOCKET picks a dedicated server (tests), else the default."""
    return TmuxMultiplexer(SESSION, os.environ.get("SDLC_TMUX_SOCKET"))


def _load(config: Path) -> Config:
    try:
        return load_config(config)
    except ConfigError as e:
        typer.echo("\n".join(e.errors), err=True)
        raise typer.Exit(2) from e


def _pane_cmd(*args: str) -> str:
    """Shell command for `sdlc <args>`; SDLC_PANE_CMD overrides the `sdlc` program (tests)."""
    return shlex.join([*shlex.split(os.environ.get("SDLC_PANE_CMD", "sdlc")), *args])


@app.command()
def up(
    config: ConfigOpt = Path("sdlc.yaml"),
    workspace: WorkspaceOpt = Path("workspace"),
    detach: Annotated[bool, typer.Option("--detach", help="Do not attach.")] = False,
) -> None:
    """Create the tmux session `sdlc` (window `room`) and attach; if it exists, just reattach."""
    cfg, mux = _load(config), _mux()
    if mux.session_exists():
        typer.echo(f"session '{SESSION}' already exists; reattaching")
    else:
        ws, cf = str(workspace.resolve()), str(config.resolve())
        dash = PaneSpec("[Dashboard]", "white", _pane_cmd("dashboard", "--workspace", ws))
        sections = [
            SectionSpec(s.name, s.color, [
                PaneSpec(pane_title(s.name, a.role, n, a.runner, "idle"), s.color,
                         _pane_cmd("agent-loop", "--role", a.role, "--instance", str(n),
                                   "--config", cf, "--workspace", ws))
                for a in s.agents for n in range(1, a.instances + 1)
            ]) for s in cfg.sections
        ]  # fmt: skip
        workspace.mkdir(parents=True, exist_ok=True)
        mux.create_session(SessionSpec(dash, sections), str(workspace.resolve()))
        typer.echo(f"session '{SESSION}' created")
    if not detach:
        mux.attach()


@app.command()
def attach() -> None:
    """Attach this terminal to the running session."""
    mux = _mux()
    if not mux.session_exists():
        typer.echo(f"no session '{SESSION}'; run `sdlc up`", err=True)
        raise typer.Exit(1)
    mux.attach()


@app.command()
def down() -> None:
    """Kill the session; the workspace (board, runs, logs) stays on disk."""
    _mux().kill_session()
    typer.echo(f"session '{SESSION}' stopped; state kept on disk")


@app.command()
def layout(
    preset: Annotated[str, typer.Option("--preset", help="grid | sections | focus")],
    section: Annotated[str | None, typer.Argument(help="Section for --preset focus.")] = None,
) -> None:
    """Reflow the panes: grid, sections (default columns), or focus <section> (whole window)."""
    if preset not in PRESETS:
        typer.echo(f"unknown preset '{preset}'; use one of: {', '.join(PRESETS)}", err=True)
        raise typer.Exit(2)
    try:
        _mux().layout(cast(Preset, preset), section)
    except (ValueError, TmuxError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e


@app.command()
def chat(
    role: str,
    config: ConfigOpt = Path("sdlc.yaml"),
    workspace: WorkspaceOpt = Path("workspace"),
) -> None:
    """Open an interactive session with <role> in a new window of the sdlc tmux session."""
    cfg, mux = _load(config), _mux()
    if not mux.session_exists():
        typer.echo(f"no session '{SESSION}'; run `sdlc up`", err=True)
        raise typer.Exit(1)
    ws = workspace.resolve()
    prompt = f"You are the {role} of this team. Greet the human and wait for instructions."
    bundle = Bundle(role, "discover", "chat", ws / "brief.md", ws)
    try:
        argv = _runner_for(cfg, role, None).build_command(bundle, prompt, cfg.mode, False)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    mux.open_window(f"chat-{role}", shlex.join(argv), str(ws))


@app.command()
def approve(
    item: str,
    gate: str,
    workspace: WorkspaceOpt = Path("workspace"),
) -> None:
    """Record a human override for <gate> of <item> in runs/logs/<item>/orchestrator.md.

    For the release gate it also writes release/go-no-go.md with `Decision: GO`. No other gate
    is passed: gates keep checking the artifacts.
    """
    gate = {"release": "released"}.get(gate, gate)
    if gate not in GATES:
        typer.echo(f"unknown gate '{gate}'; known gates: {', '.join(GATES)}", err=True)
        raise typer.Exit(2)
    d = item_dir(workspace, item)
    if not d.is_dir():
        typer.echo(f"unknown item '{item}': no {d}", err=True)
        raise typer.Exit(2)
    who = getpass.getuser()
    if gate == "released":
        (d / "release").mkdir(exist_ok=True)
        (d / "release" / "go-no-go.md").write_text(
            f"# Go / no-go: {item}\n\n- Decision: GO\n- Decided by: {who} via sdlc approve\n"
            "- Reason: human override\n", encoding="utf-8")  # fmt: skip
    log_event(workspace, item, "orchestrator", "human-override", f"gate={gate} approver={who}")
    typer.echo(f"recorded: {who} approved gate '{gate}' for {item}")


@app.command()
def run(
    brief: Path,
    runner: Annotated[str | None, typer.Option("--runner", help="Override every runner.")] = None,
    headless: Annotated[bool, typer.Option("--headless/--no-headless")] = True,
    i_understand_the_risks: Annotated[bool, typer.Option("--i-understand-the-risks")] = False,
    config: ConfigOpt = Path("sdlc.yaml"),
    workspace: WorkspaceOpt = Path("workspace"),
) -> None:
    """Create a work item from <brief> (item id = file name) and run it through the pipeline."""
    cfg = _load(config)
    if runner is not None and runner not in RUNNERS:
        typer.echo(f"unknown runner '{runner}'; known: {', '.join(RUNNERS)}", err=True)
        raise typer.Exit(2)
    item = brief.stem
    init_item(workspace, item, brief)
    try:
        res = run_item(cfg, item, workspace, runner, headless, i_understand_the_risks)
    except (RiskRefusal, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(2) from e
    for stage, g in res.gates.items():
        typer.echo(f"gate {stage}: {'passed' if g.passed else 'FAILED'}")
    typer.echo(f"{item}: {res.state}" + (" (needs a human)" if res.needs_human else ""))
    for reason in res.reasons:
        typer.echo(f"  - {reason}", err=True)
    raise typer.Exit(1 if res.needs_human else 0)


@app.command("dashboard")
def dashboard_cmd(
    workspace: WorkspaceOpt = Path("workspace"),
    once: Annotated[bool, typer.Option("--once", help="Print once and exit.")] = False,
) -> None:
    """Show the live dashboard: board counts, items, and the last 20 events."""
    dashboard.run(workspace, once)


@app.command("agent-loop")
def agent_loop_cmd(
    role: Annotated[str, typer.Option("--role")],
    instance: Annotated[int, typer.Option("--instance")] = 1,
    config: ConfigOpt = Path("sdlc.yaml"),
    workspace: WorkspaceOpt = Path("workspace"),
    runner: Annotated[str | None, typer.Option("--runner", help="Override the runner.")] = None,
    max_iterations: Annotated[int, typer.Option(help="Stop after N polls; 0 = forever.")] = 0,
    interval: Annotated[float, typer.Option(help="Seconds between polls.")] = 2.0,
) -> None:
    """Poll the inbox of <role> and run each task that arrives, until stopped."""
    cfg = _load(config)
    try:
        the_runner = _runner_for(cfg, role, runner)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(2) from e
    typer.echo(f"{role}#{instance} ({the_runner.name}) waiting for work in {workspace}")
    n = 0
    while max_iterations == 0 or n < max_iterations:
        ran = work_once(workspace, role, the_runner, cfg.mode)
        if ran:
            typer.echo(f"{role}#{instance}: ran {ran} task(s)")
        n += 1
        if max_iterations == 0 or n < max_iterations:
            time.sleep(interval)


@skills_app.command("sync")
def skills_sync(
    target_root: Annotated[Path, typer.Option(help="Project root to copy into.")] = Path("."),
) -> None:
    """Copy sdlc-protocol and the role skills into <target-root>/.claude/skills and .agents/skills."""
    for d in sync_skills(target_root):
        typer.echo(f"synced {d}")


RunnerOpt = Annotated[str, typer.Option("--runner", help="claude | codex | copilot | all")]


def _runners(runner: str) -> list[str]:
    try:
        return superpowers.pick_runners(runner)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(2) from e


@superpowers_app.command("install")
def superpowers_install(runner: RunnerOpt = "all") -> None:
    """Print the verified plugin route for <runner>. Nothing is executed."""
    typer.echo(superpowers.install_text(_runners(runner)))


@superpowers_app.command("verify")
def superpowers_verify(
    runner: RunnerOpt = "all",
    root: Annotated[Path, typer.Option(help="Project root to check.")] = Path("."),
) -> None:
    """Report, per runner, each Superpowers skill the roles use: found, or UNVERIFIED plus the fix.

    Exits 0 even when skills are not found; non-zero only for a bad option.
    """
    typer.echo(superpowers.report(superpowers.verify(root, _runners(runner))))


if __name__ == "__main__":
    app()
