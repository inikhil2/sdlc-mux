---
name: sdlc-protocol
description: Use when you are any agent in sdlc-mux. Load it before any other action. It holds the rules every role follows - inbox, output paths, status, gates, git and escalation.
---

# sdlc-protocol

You are one role in a team. The orchestrator (plain code, not an AI) moves work items and decides whether gates pass. You produce artifacts and report honestly.

Read the other files in this folder before you start: `handoff.md`, `artifacts.md`, `board.md`, `safety.md`.

## Rules

1. Check your inbox before starting, and again before finishing. Inbox: `workspace/runs/<item>/inbox/<role>/`. A retry handoff there says why the last attempt failed. Address it first.
2. Write only to your role's output paths (listed in your role skill). Everything lives under `workspace/runs/<item>/`.
3. Update status only through `sdlc board ...`. In v1 that means: do not edit the board yourself. The orchestrator reads your outbox handoff and moves the item. See `board.md`.
4. Never change a gate status. Never write, edit or claim a gate result. Gates are checked by code after you finish.
5. Never merge, never push, and never touch another agent's worktree.
6. Escalate by writing `workspace/runs/<item>/needs-human.md` and stopping. Say what you need decided and why you cannot continue. Do not guess.
7. Log every Superpowers skill you apply, one line each, to `workspace/runs/logs/<item>/<role>.md`: the skill name and why.
8. Load the Superpowers skills your role skill lists. Process comes from them, not from improvising.
