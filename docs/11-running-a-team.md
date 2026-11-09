# Running a team

## What you will learn

- How to open the room (`up`), start a work item (`run`), watch the panes, step in (`chat`), record a human decision (`approve`), and stop (`down`).
- What each pane shows.

Commands that attach your terminal to tmux, or that start a real model session, were **not run** by the build; the layout was exercised on a private tmux server with `sdlc up --detach` and its output is pasted. The build's panes ran `sleep` instead of the agent loop (the `SDLC_PANE_CMD` override, which the test suite also uses), so what an agent pane prints while a real item runs was not observed.

## up

`sdlc up` opens a tmux session named `sdlc` with one window, `room`: a dashboard pane on top, then one labelled column per section, one pane per agent. If the session exists, it reattaches.

```bash
uv run sdlc up
```
Run: no, it attaches your terminal to tmux and would use your default tmux server.

With `--detach` it creates the session without attaching. Run against a private tmux server (`SDLC_TMUX_SOCKET=sdlc-test`, so your own tmux is untouched):

```bash
SDLC_TMUX_SOCKET=sdlc-test SDLC_PANE_CMD="sh -c 'sleep 300' sdlc" uv run sdlc up --detach --workspace /tmp/sdlc-ws
```
Run: yes, output below

```text
session 'sdlc' created
```

Run it again and it is idempotent:

```text
session 'sdlc' already exists; reattaching
```

(That second line is from running the same command twice, run: yes.) The panes, from `tmux -L sdlc-test list-panes -t sdlc:room -F '#{pane_index} #{pane_title}'`:

```bash
tmux -L sdlc-test list-panes -t sdlc:room -F '#{pane_index} #{pane_title}'
```
Run: yes, output below

```text
0 [Dashboard]
1 [Discovery] product-owner#1 · claude · idle
2 [Discovery] business-analyst#1 · claude · idle
3 [Discovery] ux-designer#1 · claude · idle
4 [Architecture & Delivery] solution-architect#1 · claude · idle
5 [Architecture & Delivery] scrum-master#1 · claude · idle
6 [Engineering] backend-engineer#1 · claude · idle
7 [Engineering] backend-engineer#2 · claude · idle
8 [Engineering] frontend-engineer#1 · claude · idle
9 [Quality] sdet#1 · claude · idle
10 [Quality] qa-analyst#1 · claude · idle
11 [Governance] code-reviewer#1 · claude · idle
12 [Governance] security-engineer#1 · claude · idle
13 [Operations] release-engineer#1 · claude · idle
```

That is 14 panes: 13 agents plus the dashboard. Keys to move around: see [tmux keys](reference/tmux-keys.md).

## run

`sdlc run <brief>` creates a work item (id = brief file name) and walks it through all stages. The agent panes poll their inboxes; the dashboard shows the board. With the offline runner:

```bash
uv run sdlc run examples/expense-splitter.md --runner mock --workspace /tmp/sdlc-demo
```
Run: yes, output below (see [start here](00-start-here.md); last line shown)

```text
expense-splitter: done
```

What each stage shows (the path is under `runs/<item>/`, the check is the gate): discover writes `vision.md`, stories, business rules (gate `discovered`); design writes `design/design-doc.md` plus an ADR (`designed`); plan writes `plan.md` and `test/test-plan.md` (`planned`); build writes `build/<task>-report.md` (`built`); test writes `test/test-report.md` and `test/qa-signoff.md` (`tested`); review writes the review and security reports (`reviewed`); release writes release notes and `go-no-go.md` (`released`); retro writes `retro.md` (`retrospected`). The pane titles end in a state word; `idle` is what the build observed.

## Watching the dashboard

```bash
uv run sdlc dashboard --once --workspace /tmp/sdlc-demo
```
Run: yes, output below (the Feed table shows the last 20 events and is trimmed here)

```text
      Board      
┏━━━━━━━┳━━━━━━━┓
┃ stage ┃ items ┃
┡━━━━━━━╇━━━━━━━┩
│ done  │ 1     │
└───────┴───────┘
                     Items                     
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ item             ┃ title            ┃ state ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ expense-splitter │ Expense splitter │ done  │
└──────────────────┴──────────────────┴───────┘
```

## Reflowing the layout

```bash
SDLC_TMUX_SOCKET=sdlc-test uv run sdlc layout --preset focus Engineering
```
Run: yes, no output, exit code 0. Afterwards the three Engineering panes filled the whole window (each 300 columns wide).

`--preset sections` restores the columns (run: yes, exit 0, no output). `--preset grid` also exists. An unknown preset is refused:

```bash
uv run sdlc layout --preset diagonal
```
Run: yes, output below

```text
unknown preset 'diagonal'; use one of: grid, sections, focus
```

## chat

`sdlc chat <role>` opens an interactive session with that role's runner in a new window of the same tmux session, so you can step in.

```bash
uv run sdlc chat backend-engineer
```
Run: no, it starts a real Claude Code session.

## approve

`sdlc approve <item> <gate>` records a logged human override. For the release gate it also writes `release/go-no-go.md` with `Decision: GO`; no other gate is passed by it.

```bash
uv run sdlc approve expense-splitter release --workspace /tmp/sdlc-demo
```
Run: yes, output below

```text
recorded: nikhil approved gate 'released' for expense-splitter
```

```bash
uv run sdlc approve expense-splitter nope --workspace /tmp/sdlc-demo
```
Run: yes, output below (exit code 2)

```text
unknown gate 'nope'; known gates: discovered, designed, planned, built, tested, reviewed, released, retrospected
```

## down

```bash
SDLC_TMUX_SOCKET=sdlc-test uv run sdlc down
```
Run: yes, output below

```text
session 'sdlc' stopped; state kept on disk
```

After `down`, `sdlc attach` says there is nothing to attach to (exit 1):

```text
no session 'sdlc'; run `sdlc up`
```

(Run: yes, `uv run sdlc attach` with the test socket.) Workspace state stays on disk, so `sdlc up` later picks the board up again.

## Try it

Do the offline `run` and `dashboard` commands above in a scratch folder, then try `up --detach` on a private tmux server as shown. Without the override variables, `sdlc up` uses your default tmux server and real `sdlc` agent panes, and you attach with it.
