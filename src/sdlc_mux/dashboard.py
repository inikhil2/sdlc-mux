"""The dashboard pane: board counts per stage, a table of items, and the last 20 events."""

import time
from pathlib import Path

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.table import Table

from sdlc_mux.board import STATES, Board

FEED_LINES = 20


def feed(workspace: Path, limit: int = FEED_LINES) -> list[str]:
    """Return the last `limit` log lines across runs/logs/<item>/<role>.md, oldest first.

    Each line reads `<utc time> | <role> | <event> | <detail>`; the item id is prefixed.
    """
    rows = [
        (line.split(" | ", 1)[0], f"{f.parent.name} | {line}")
        for f in (workspace / "runs" / "logs").glob("*/*.md")
        for line in f.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [text for _, text in sorted(rows, key=lambda r: r[0])[-limit:]]


def render(workspace: Path) -> RenderableType:
    """Build the dashboard from board.db and the logs under `workspace` (empty if neither)."""
    db = workspace / "board.db"
    items = []
    if db.is_file():
        board = Board(db)
        items = board.list_items()
        board.close()
    counts = Table("stage", "items", title="Board")
    for state in STATES:
        n = sum(1 for _, _, s in items if s == state)
        if n:
            counts.add_row(state, str(n))
    table = Table("item", "title", "state", title="Items")
    for item, title, state in items:
        table.add_row(item, title, state)
    events = Table("event", title=f"Feed (last {FEED_LINES})", show_header=False)
    for line in feed(workspace):
        events.add_row(line)
    return Group(counts, table, events)


def run(workspace: Path, once: bool = False, interval: float = 2.0) -> None:
    """Print the dashboard once, or keep it live (refresh every `interval` s) until Ctrl-C."""
    console = Console()
    if once:
        console.print(render(workspace))
        return
    with Live(render(workspace), console=console, screen=True) as live:
        while True:
            time.sleep(interval)
            live.update(render(workspace))
