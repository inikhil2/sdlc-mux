# Superpowers reference

> **Status update 2026-11-09:** verified on this machine: Claude plugin `superpowers@claude-plugins-official` version 7.0.0, enabled, user scope (`claude plugin list`). Codex and Copilot routes are still UNVERIFIED here.


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

UNVERIFIED for all three runners. The README does not say which directory a plugin install writes to, so `verify` does not assume one. Resolved in T7 (2026-11-09): `verify` checks only the project skills folders a runner reads (`.claude/skills`, `.agents/skills`, and for Copilot also `.github/skills`). A skill found there is reported `[found]` with its path. Anything else is reported `[UNVERIFIED] cannot check on disk (plugin install)` with the plugin command, never as found and never as proven missing. `verify` exits 0 either way.

## Mapping changes from Prompt.md (2026-11-09)

- Skills sync targets: Prompt.md section 4 lists `~/.codex/skills` and `.github/skills`. Replaced by `.claude/skills` (Claude Code) and `.agents/skills` (Codex and Copilot), per [ADR 0009](../adr/0009-reuse-agents-skills-dir.md). The user-scope Codex folder is `~/.agents/skills` per [runners.md](runners.md); `sdlc skills sync` does not write to any home folder.
- Superpowers install: Prompt.md section 9 falls back to cloning into `vendor/superpowers/` and copying skills. Not built. All three runners have a plugin route ([ADR 0008](../adr/0008-reuse-superpowers-via-runner-plugins.md)), and `sdlc superpowers install` prints that route without running it.
- Catalogue: the engineers also run `verification-before-completion` (the section 8.2 example does), which section 8.1 omits.
- Doctor: in autonomous mode a runner counts as verified only if every referenced skill is found on disk. A plugin-only install cannot be seen, so autonomous mode fails for it until the skills are also placed in a project skills folder.
