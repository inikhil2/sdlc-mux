# Superpowers reference

Verified 2026-11-09.

- Repo: https://github.com/obra/superpowers (MIT license)
- Latest release checked: `v7.0.2`, published 2026-11-03T22:17:54Z, https://github.com/obra/superpowers/releases/tag/v7.0.2
- `main` at check time: commit `22f0b463e7a5e579904dd6211a520321035526f7` (2026-11-03T22:17:07Z)
- Suggested `pinned_ref` for `sdlc.yaml`: `v7.0.2`. The tag-to-commit link was not separately confirmed; release `target_commitish` was `main`.
- Skill list source: GitHub contents API for `skills/` on the repo, and the README "Skills Library" section, both read 2026-11-09. Both agree on the 12 names below.

## Skill names used by Prompt.md section 8.1

| Name | Result | Source |
|---|---|---|
| brainstorming | found | https://github.com/obra/superpowers/tree/main/skills/brainstorming |
| writing-plans | found | .../skills/writing-plans |
| test-driven-development | found | .../skills/test-driven-development |
| subagent-driven-development | found | .../skills/subagent-driven-development |
| executing-plans | found | .../skills/executing-plans |
| using-git-worktrees | found | .../skills/using-git-worktrees |
| systematic-debugging | found | .../skills/systematic-debugging |
| requesting-code-review | found | .../skills/requesting-code-review |
| receiving-code-review | found | .../skills/receiving-code-review |
| verification-before-completion | found | .../skills/verification-before-completion |
| finishing-a-development-branch | found | .../skills/finishing-a-development-branch |
| dispatching-parallel-agents | found | .../skills/dispatching-parallel-agents |

Name mapping needed: none. All 12 match exactly.

Other skills in the repo, not used by the role catalogue: `using-superpowers`, `writing-skills`, `diagnosing-superpowers`.

## Install routes (from the README, 2026-11-09)

| Runner | Route | Status |
|---|---|---|
| Claude Code | `/plugin install superpowers@claude-plugins-official`, or `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace` | VERIFIED (README text, not executed) |
| Codex CLI | In the CLI run `/plugins`, search `superpowers`, choose Install Plugin | VERIFIED (README text, not executed) |
| Copilot CLI | `copilot plugin marketplace add obra/superpowers-marketplace` then `copilot plugin install superpowers@superpowers-marketplace` | VERIFIED (README text, not executed) |

The README says each harness needs its own install.

## Where installed skills land, for `sdlc superpowers verify`

UNVERIFIED for all three runners. The README does not say which directory a plugin install writes to, so `verify` cannot assume one. T7 must either find the plugin install locations (for example `claude plugin list`, `~/.claude/plugins/`) or have `verify` report "cannot check, install route is plugin-based".
