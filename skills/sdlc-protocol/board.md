# Board

The board is a SQLite database. It is the source of truth for each item's state (`idea` through `done`). `BOARD.md` is a read-only mirror made from it.

## Who changes it

Only the orchestrator moves an item, and only after the gate for the stage passes. The rule for agents is: change status only through `sdlc board ...`, never by editing the database or `BOARD.md`.

## Commands

The planned commands are `sdlc board list`, `sdlc board show <item>` and `sdlc board update`. They are **not built in v1**. Until they are, you do not touch the board at all:

- Report your result with your outbox handoff (`status: done`, `blocked` or `question`). The orchestrator reads it.
- To see what is going on, read your inbox and the item folder.
- If you need the item stopped for a human, write `needs-human.md` (see `SKILL.md`).

Never try to work around the missing commands by writing to `workspace/board.db` or `BOARD.md`.
