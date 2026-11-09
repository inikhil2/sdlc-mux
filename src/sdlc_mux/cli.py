"""The `sdlc` command-line entry point."""

from pathlib import Path
from typing import Annotated

import typer

from sdlc_mux.doctor import run_checks

app = typer.Typer(
    help="Run an SDLC pipeline with a team of AI agents in tmux.", no_args_is_help=True
)


@app.callback()
def main() -> None:
    """sdlc-mux command group."""


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
