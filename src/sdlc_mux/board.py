"""SQLite board: the source of truth for work items and their pipeline state."""

import sqlite3
from pathlib import Path

STATES = (
    "idea",
    "discovering",
    "discovered",
    "designing",
    "designed",
    "planning",
    "planned",
    "building",
    "built",
    "testing",
    "tested",
    "reviewing",
    "reviewed",
    "releasing",
    "released",
    "retrospected",
    "done",
)


class BoardError(Exception):
    """Raised for unknown items, unknown states, or illegal transitions."""


class Board:
    """A work-item board stored in one SQLite file (or ':memory:')."""

    def __init__(self, path: Path | str) -> None:
        """Open (and create if needed) the board database at `path`."""
        self._db = sqlite3.connect(str(path))
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS items ("
            "id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL, "
            "needs_human INTEGER NOT NULL DEFAULT 0)"
        )
        self._db.commit()

    def add_item(self, item_id: str, title: str) -> None:
        """Create an item in state 'idea'; raises BoardError if the id already exists."""
        try:
            self._db.execute(
                "INSERT INTO items (id, title, state) VALUES (?, ?, 'idea')", (item_id, title)
            )
        except sqlite3.IntegrityError:
            raise BoardError(f"item '{item_id}' already exists") from None
        self._db.commit()

    def _row(self, item_id: str) -> tuple[str, int]:
        row = self._db.execute(
            "SELECT state, needs_human FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise BoardError(f"unknown item '{item_id}'")
        return str(row[0]), int(row[1])

    def state(self, item_id: str) -> str:
        """Return the item's current state; raises BoardError for an unknown item."""
        return self._row(item_id)[0]

    def needs_human(self, item_id: str) -> bool:
        """Return True if the item is flagged as needing a human."""
        return bool(self._row(item_id)[1])

    def set_needs_human(self, item_id: str, flag: bool) -> None:
        """Set or clear the needs-human flag; transitions are refused while it is set."""
        self._row(item_id)
        self._db.execute("UPDATE items SET needs_human = ? WHERE id = ?", (int(flag), item_id))
        self._db.commit()

    def transition(self, item_id: str, to: str) -> None:
        """Move the item to `to`, which must be the very next state.

        Raises BoardError for an unknown state, a skip-ahead, a backwards move, or a move
        on an item flagged needs-human.
        """
        if to not in STATES:
            raise BoardError(f"unknown state '{to}'; known states: {', '.join(STATES)}")
        current, flagged = self._row(item_id)
        if flagged:
            raise BoardError(f"item '{item_id}' needs a human; clear the flag before moving it")
        nxt = STATES.index(current) + 1
        if nxt >= len(STATES) or STATES[nxt] != to:
            allowed = STATES[nxt] if nxt < len(STATES) else "nothing (already done)"
            raise BoardError(f"illegal transition {current} -> {to}; only {allowed} is allowed")
        self._db.execute("UPDATE items SET state = ? WHERE id = ?", (to, item_id))
        self._db.commit()

    def list_items(self) -> list[tuple[str, str, str]]:
        """Return (id, title, state) for every item, ordered by id."""
        rows = self._db.execute("SELECT id, title, state FROM items ORDER BY id").fetchall()
        return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]

    def close(self) -> None:
        """Close the database connection."""
        self._db.close()
