# Superpowers

## What you will learn

- What Superpowers is and why sdlc-mux uses it as the management layer.
- How to install it for each runner, and how sdlc uses it.
- Why `sdlc superpowers verify` often says `[UNVERIFIED]`, and what to do.

## What it is

[Superpowers](https://github.com/obra/superpowers) is a library of skills (folders with a `SKILL.md`) that give an AI coding agent process discipline: brainstorm before designing, write a plan before code, test first, debug by root cause, verify before claiming done. The project is by obra and licensed MIT (checked against [superpowers reference](reference/superpowers.md), 2026-11-09). sdlc-mux does not copy or vendor any Superpowers file; it credits and reuses the project through each runner's own plugin route ([ADR 0008](adr/0008-reuse-superpowers-via-runner-plugins.md)).

## Why it is the management layer

sdlc code owns the pipeline (stages, gates, retries). Superpowers owns how each agent works inside its task. Every task prompt tells the agent to load `sdlc-protocol` and its `role-<slug>` skill first, then to follow the Superpowers skills that role lists, and to log each skill it applies with a reason to `workspace/runs/logs/<item>/<role>.md`. The role-to-skill table is in [roles and skills](10-roles-and-skills.md). The twelve skills used are: brainstorming, writing-plans, test-driven-development, subagent-driven-development, executing-plans, using-git-worktrees, systematic-debugging, requesting-code-review, receiving-code-review, verification-before-completion, finishing-a-development-branch, dispatching-parallel-agents (all found in the repo on 2026-11-09). The config pins `v7.0.2`'s `main` commit.

## Install per runner

From the Superpowers README (read 2026-11-09, **not executed**; each runner needs its own install):

| Runner | Route |
|---|---|
| Claude Code | inside Claude Code: `/plugin install superpowers@claude-plugins-official` |
| Codex CLI | inside Codex: run `/plugins`, search `superpowers`, choose Install Plugin |
| Copilot CLI | `copilot plugin marketplace add obra/superpowers-marketplace`, then `copilot plugin install superpowers@superpowers-marketplace` |

`sdlc superpowers install` prints these and runs nothing:

```bash
uv run sdlc superpowers install --runner claude
```
Run: yes, output below

```text
Superpowers is installed through each runner's plugin route. sdlc does not run these:
claude:
  /plugin install superpowers@claude-plugins-official  (inside Claude Code)
```

## Verifying

The README does not say where a plugin install puts its files, so sdlc cannot see them. `verify` therefore looks only in the project skills folders. A skill found there is `[found]`; anything else is `[UNVERIFIED]` with the fix command, never "missing" and never "found". It exits 0 either way.

```bash
uv run sdlc superpowers verify --runner claude --root /tmp/sdlc-proj
```
Run: yes, output below (first rows only; run against a scratch folder)

```text
[UNVERIFIED] claude   brainstorming  cannot check on disk (plugin install); fix: /plugin install superpowers@claude-plugins-official  (inside Claude Code)
[UNVERIFIED] claude   dispatching-parallel-agents  cannot check on disk (plugin install); fix: /plugin install superpowers@claude-plugins-official  (inside Claude Code)
[UNVERIFIED] claude   executing-plans  cannot check on disk (plugin install); fix: /plugin install superpowers@claude-plugins-official  (inside Claude Code)
```

## Troubleshooting

- **Everything says `[UNVERIFIED]`**: expected after a plugin install. Confirm inside the runner that the plugin is listed.
- **Autonomous mode fails the doctor**: in `autonomous` mode a runner counts as verified only when every skill is found on disk. Plugin-only installs cannot be seen, so either stay in `supervised` mode or place the skills in a project skills folder yourself.
- **Wrong marketplace name**: run `/plugin marketplace add obra/superpowers-marketplace` as the alternative Claude Code route.

## Try it

Run the verify command above, then `uv run sdlc doctor` and find the `superpowers for claude not verified ... (warning)` row.

```bash
uv run sdlc doctor
```
Run: yes, output below (the superpowers row only)

```text
[ok]      superpowers for claude not verified (cannot check plugin installs on disk) (warning)
```
