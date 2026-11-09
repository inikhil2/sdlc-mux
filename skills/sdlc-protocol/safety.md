# Safety

## Files
- Write only inside `workspace/runs/<item>/` and, for code roles, inside your own git worktree.
- Do not read or write anything in the home folder, other projects, or system folders.
- Do not delete files you did not create.

## Git
- Work on your own branch in your own worktree.
- Never merge. Never push. Never force anything. Never rewrite history.
- Never touch another agent's worktree or branch.

## Network
- Do not call the network unless your task says to and the human approved it. Installing packages needs approval.

## Secrets
- Never read, print, copy or write API keys, tokens, passwords or login files.
- If you find a secret in the code, do not repeat it. Note the file and line in your report and escalate with `needs-human.md`.

## Commands
- Prefer read-only commands. Ask before anything destructive.
- If a command needs more permission than you have, stop and escalate. Do not look for a way around the limit.
