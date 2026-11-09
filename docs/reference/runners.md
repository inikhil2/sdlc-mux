# Runner reference

> **Status update 2026-11-09:** the owner reports Codex and Copilot CLI runs on another system. No command output was captured in this repo, so every UNVERIFIED flag below stays UNVERIFIED until output is recorded here.


Verified 2026-11-09. Every row has a source and a status. `VERIFIED` means confirmed against `--help` output or an official page on that date. `UNVERIFIED` means not confirmed; do not rely on it.

Local Claude Code version: 2.1.319. Full `claude --help` output is saved in [claude-help.txt](claude-help.txt).
Codex CLI and Copilot CLI are not installed on this machine, so neither could be checked against `--help`. Their entries come from web pages only.

## Claude Code (`claude`)

| Item | Value | Status | Source |
|---|---|---|---|
| Interactive with starting prompt | `claude "<prompt>"` | VERIFIED | `claude --help` (`Usage: claude [options] [command] [prompt]`); https://code.claude.com/docs/en/cli-reference (2026-11-09) |
| Headless | `claude -p "<prompt>"` / `--print` | VERIFIED | `claude --help`; https://code.claude.com/docs/en/headless (2026-11-09) |
| Output format (headless only) | `--output-format text\|json\|stream-json` | VERIFIED | `claude --help`; headless docs |
| Permission mode | `--permission-mode acceptEdits\|auto\|bypassPermissions\|manual\|dontAsk\|plan` | VERIFIED | `claude --help` lists these six. The CLI reference also lists `default`, with `manual` as an alias for it (needs v2.1.200+). |
| Skip all permission checks | `--dangerously-skip-permissions` (same as `--permission-mode bypassPermissions`) | VERIFIED | `claude --help`; CLI reference. Needs `--i-understand-the-risks` in sdlc. |
| Pre-approve tools | `--allowedTools "Read,Edit,Bash(git diff *)"` | VERIFIED | `claude --help`; headless docs |
| Deny tools | `--disallowedTools` | VERIFIED | `claude --help` |
| No prompts in unattended `-p` runs | `--permission-prompts none` (v2.1.259+) | VERIFIED | `claude --help`; headless docs |
| `-p` default mode | Starts in Manual mode when nothing sets a mode (v2.1.302+). A call needing approval is denied. | VERIFIED | headless docs |
| Extra dirs | `--add-dir <dirs...>` | VERIFIED | `claude --help` |
| Append instructions | `--append-system-prompt <text>` | VERIFIED | `claude --help` |
| Budget cap (print only) | `--max-budget-usd <amount>` | VERIFIED | `claude --help` |
| Skip auto-discovery (CLAUDE.md, hooks, skills) | `--bare` (uses `ANTHROPIC_API_KEY`, not subscription login) | VERIFIED | `claude --help`; headless docs. sdlc must NOT use it with subscription login. |
| Project skills dir | `.claude/skills/<name>/SKILL.md` | VERIFIED | https://code.claude.com/docs/en/skills (2026-11-09) |
| User skills dir | `~/.claude/skills/<name>/SKILL.md` | VERIFIED | same |
| Instruction file | `CLAUDE.md` | VERIFIED (existence) | skills/headless docs mention it |
| `CLAUDE.md` containing `@AGENTS.md` import | not looked up | UNVERIFIED | Check https://code.claude.com/docs/en/memory before T2/T7. |
| Install: native script, brew cask, npm | `curl -fsSL https://claude.ai/install.sh \| bash`, `brew install --cask claude-code`, `npm install -g @anthropic-ai/claude-code` | UNVERIFIED | Not looked up. `claude install` / `claude update` exist per `--help`. |

## Codex CLI (`codex`) - all rows from web only, binary not installed

| Item | Value | Status | Source |
|---|---|---|---|
| Interactive with starting prompt | `codex "<prompt>"` (optional PROMPT argument starts the TUI) | VERIFIED (docs only) | https://learn.chatgpt.com/docs/developer-commands?surface=cli (redirect from developers.openai.com/codex/cli/reference), 2026-11-09 |
| Headless | `codex exec "<prompt>"` (short form `codex e`; `-` reads prompt from stdin; `--json` for JSON events) | VERIFIED (docs only) | same |
| Sandbox | `--sandbox, -s read-only\|workspace-write\|danger-full-access` | VERIFIED (docs only) | same |
| Approvals | `--ask-for-approval, -a on-request\|never` (the interactive CLI rejects it when `--approve-for-me` is used) | VERIFIED (docs only) | same. The page was truncated at 100000 chars, so other values may exist. |
| Auto-review mode | `--approve-for-me` / `--not-so-yolo` (on-request approvals, workspace-write sandbox) | VERIFIED (docs only) | same |
| Bypass everything | `--dangerously-bypass-approvals-and-sandbox` / `--yolo`. Needs `--i-understand-the-risks` in sdlc. | VERIFIED (docs only) | same |
| `--full-auto` | not listed on the page | UNVERIFIED | Do not use. |
| Project skills dir | `.agents/skills/` (scanned from cwd up to repo root) | VERIFIED (docs only) | https://learn.chatgpt.com/docs/build-skills (redirect from developers.openai.com/codex/skills), 2026-11-09 |
| User skills dir | `$HOME/.agents/skills/` (and `/etc/codex/skills` for admins) | VERIFIED (docs only) | same |
| `~/.codex/skills/` | Prompt.md section 4 says this. The docs do not list it. | UNVERIFIED, likely wrong | Use `~/.agents/skills/`. |
| `AGENTS.md` loading | not confirmed on the pages read | UNVERIFIED | |
| Install: `brew install codex`, `npm install -g @openai/codex` | not looked up | UNVERIFIED | |
| Login detection without reading credentials | not looked up | UNVERIFIED | |

## Copilot CLI (`copilot`) - all rows from web only, binary not installed

| Item | Value | Status | Source |
|---|---|---|---|
| Interactive with starting prompt | `copilot -i "<prompt>"` / `--interactive=PROMPT` ("Start an interactive session and automatically execute this prompt.") | VERIFIED (docs only) | https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference (2026-11-09) |
| Headless | `copilot -p "<prompt>"` / `--prompt=PROMPT`; `-s` prints only the response | VERIFIED (docs only) | same; https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-getting-started |
| Allow specific tools | `--allow-tool=TOOL ...` | VERIFIED (docs only) | command reference |
| Allow all tools | `--allow-all-tools` (no safety review or prompts; deny rules still apply) | VERIFIED (docs only) | same. Needs `--i-understand-the-risks` in sdlc. |
| Allow all | `--allow-all` (= `--allow-all-tools --allow-all-paths --allow-all-urls`) | VERIFIED (docs only) | same. Needs `--i-understand-the-risks`. |
| `--yolo` | Documented only as a slash-command alias (`/yolo` = `/allow-all`), not as a CLI flag | UNVERIFIED as flag | same |
| Extra dirs | `--add-dir=PATH` (loads skills from `.github/`, `.agents/`, `.claude/` there) | VERIFIED (docs only) | same |
| Project skills dirs | `.github/skills`, `.claude/skills`, `.agents/skills` | VERIFIED (docs only) | https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills (2026-11-09) |
| User skills dirs | `~/.copilot/skills`, `~/.agents/skills` | VERIFIED (docs only) | same |
| `AGENTS.md` | Supported (`--no-custom-instructions` disables loading from "`AGENTS.md` and related files") | VERIFIED (docs only) | command reference |
| Install | `npm install -g @github/copilot` (Node 22+), `winget install GitHub.Copilot`, `brew install --cask copilot-cli` | VERIFIED (docs only) | https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-getting-started. Prompt.md says `brew install copilot-cli`; the docs say `--cask`. |
| Login detection without reading credentials | not looked up | UNVERIFIED | |

## Differences from Prompt.md section 4

- Codex user skills dir is `~/.agents/skills`, not `~/.codex/skills`.
- Copilot also reads `.agents/skills` and `.claude/skills`, and `~/.agents/skills`. One shared `.agents/skills/` covers Codex and Copilot; Claude Code needs `.claude/skills/`.
- Copilot brew install is `--cask`.
- `claude --help` offers `manual`, not `default`, for `--permission-mode`.
