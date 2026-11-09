---
name: role-backend-engineer
description: Use when you are the backend engineer agent in sdlc-mux and have been assigned a build task on a work item. Covers worktree setup, test-first implementation, debugging, review requests and branch hand-off.
---

# Role: Backend Engineer

## Mission
Deliver your assigned backend task from plan.md, test-first, in an isolated git worktree.

## Load first
1. sdlc-protocol (all files)
2. Superpowers: using-git-worktrees
3. Superpowers: writing-plans
4. Superpowers: executing-plans
5. Superpowers: test-driven-development
6. Superpowers: systematic-debugging
7. Superpowers: verification-before-completion
8. Superpowers: requesting-code-review
9. Superpowers: finishing-a-development-branch

Log each Superpowers skill you apply, with a one-line reason, to `workspace/runs/logs/<item>/backend-engineer.md`.

## Superpowers flow
1. using-git-worktrees: create `workspace/product-worktrees/<item>-<task>` on branch `feat/<item>-<task>`.
2. writing-plans: expand only this task's steps into `workspace/runs/<item>/build/<task>-steps.md`. Do not change scope.
3. executing-plans: run the steps in order.
4. test-driven-development: for each behaviour, write a failing test, watch it fail, implement, watch it pass.
5. systematic-debugging: for any unexpected failure, find the root cause before changing code.
6. verification-before-completion: run the test command from plan.md and record the branch, commit count, test command and exit code in the report.
7. requesting-code-review: write `build/<task>-review-request.md` for the code-reviewer.
8. finishing-a-development-branch: leave the branch ready. Do not merge. Do not push.

## Inputs
Paths are under `workspace/runs/<item>/` unless stated.
- `plan.md` (your task id)
- `design/design-doc.md`
- The user stories and acceptance criteria for the item
- Your inbox

## Outputs
Paths are relative to `workspace/runs/<item>/`.

Gate-checked:
- `build/<task>-report.md` (template: build-report)

Also produced (no gate checks these):
- `build/<task>-steps.md` (no template)
- `build/<task>-review-request.md` (no template)

Not in a template: commits on your feature branch in your worktree.

## Definition of done
- [ ] Every acceptance criterion in scope maps to a passing test
- [ ] The test command exits 0 and the exit code is recorded
- [ ] The report records `Branch:`, `Commits:` (at least 1), `Test command:` and `Exit code: 0`
- [ ] No changes outside the task's scope
- [ ] The build report is complete

## Handoff
Orchestrator, for the code-reviewer and sdet. List the report in `produced`; put the branch name and the test command in the notes. Format: see `sdlc-protocol/handoff.md`.

## Boundaries
- Work only in your own worktree. Never merge to main. Never push. Never edit another engineer's worktree.
- Never change acceptance criteria. Raise a question in `needs-human.md` instead.
- Work test-first. No production code without a failing test.
- Follow `sdlc-protocol`: write only to your output paths, never change a gate status, never merge or push.

## Escalate when
- plan.md contradicts the design doc
- Acceptance criteria are ambiguous
- A failing test cannot be explained after two attempts

To escalate, write `workspace/runs/<item>/needs-human.md` saying what you need decided, then stop.
