# Handoff format

A handoff is a Markdown file with YAML frontmatter. It tells the next role what you made and what it must do.

```markdown
---
from: backend-engineer
to: code-reviewer
item: expense-splitter
task: T1
stage: build
status: done
produced:
  - build/T1-report.md
needs:
  - Review branch feat/expense-splitter-T1
---
Free-text notes. Keep them short.
```

## Fields

| Field | Meaning |
|---|---|
| `from` | Your role name. |
| `to` | The receiving role, or `orchestrator`. |
| `item` | Work item id. |
| `task` | Task id from `plan.md`, or the stage name when there is no task. |
| `stage` | One of `discover`, `design`, `plan`, `build`, `test`, `review`, `release`, `retro`. |
| `status` | `done`, `blocked` or `question`. |
| `produced` | Paths you made, relative to `workspace/runs/<item>/`. |
| `needs` | What the receiver must do. One short line each. |

## Where handoffs go

- When your run ends, the agent loop writes `outbox/<role>/<stage>-<task>.md` for the orchestrator. You do not write that file.
- To give a peer specific instructions, write a handoff to `inbox/<to>/<stage>-<task>-<from>.md` in this format.
- Use `status: blocked` when you cannot finish, and `status: question` when you need an answer. Pair either with `needs-human.md` when a human must decide.
