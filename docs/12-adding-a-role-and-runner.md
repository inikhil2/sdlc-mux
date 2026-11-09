# Adding a role and a runner

## What you will learn

- Every place to touch to add a role, with a Technical Writer as the example.
- Every place to touch to add a runner.
- Which tests catch a missed step.

This page is a guide read from the code. The Technical Writer was **not** built; no code for it exists, so nothing below was run as an example. The checks at the end were run against the existing twelve roles.

## Add a role (example: technical-writer)

A role is not only a YAML line. The role name appears in code, because gates and prompts need to know what the role produces.

1. **Register the name.** Add `"technical-writer"` to `ROLES` in `src/sdlc_mux/config.py`. Without it, `sdlc.yaml` is rejected with `unknown role 'technical-writer'; known roles: ...`.
2. **Choose its Superpowers.** Add an entry to `ROLE_SKILLS` in `src/sdlc_mux/superpowers.py`, for example `("brainstorming", "verification-before-completion")`. Only the twelve verified Superpowers names are allowed; a test checks this.
3. **Declare its outputs.** Add the `(role, stage)` entry to `OUTPUTS` in `src/sdlc_mux/bootstrap.py` (what the prompt tells the agent to write). The offline runner needs the same entry in `src/sdlc_mux/runners/mock.py` plus a template in `src/sdlc_mux/templates/`, otherwise `--runner mock` cannot play the role.
4. **Write its skill.** Create `skills/roles/technical-writer/SKILL.md` with the ten required sections in order (see [roles and skills](10-roles-and-skills.md)), named `role-technical-writer`, with a description that starts "Use when you are the technical writer agent in sdlc-mux". Its Definition of done must match what a gate checks.
5. **Gate it, or say it is not gated.** If its output matters for passing a stage, extend the validator for that stage in `src/sdlc_mux/gates.py` (with a passing and a failing fixture test). If not, list the output under "Also produced (no gate checks these)" in the skill. A test fails if a skill names a gate-checked output that no gate checks.
6. **Put it in the team.** In `sdlc.yaml`, add `{role: technical-writer, runner: claude}` under a section, and add the role to a stage's `roles:` list in `pipeline`. A new stage name also needs `STAGES` in `config.py` and `STAGE_STATES` in `orchestrator.py` (and a board state, which is a bigger change).
7. **Sync and check.** `sdlc skills sync`, then `sdlc doctor`.

```bash
uv run sdlc doctor --config sdlc.yaml
```
Run: yes, output below (current twelve-role config; first rows)

```text
[ok]      python 3.12
[ok]      uv
[ok]      tmux
[ok]      runner claude (claude)
```

What a mistake looks like. A copy of `sdlc.yaml` with `product-owner` misspelled `product-owner2`:

```bash
uv run sdlc doctor --config bad.yaml
```
Run: yes, output below (bad.yaml is that edited copy; the fix text is trimmed)

```text
[MISSING] config bad.yaml
          fix: sections.0.agents.0.role: unknown role 'product-owner2'; known roles: product-owner, business-analyst, ux-designer, ...
```

## Add a runner

1. Create `src/sdlc_mux/runners/<name>.py`: a subclass of `Runner` with `name`, `binary`, `config_dir`, `project_skills`, `user_skills`, `_flags(profile, headless)` and `build_command(...)`. Copy `claude.py` as the shape. Any flag that disables sandboxing or approvals belongs only in the `unsafe` profile, which the base class refuses without `--i-understand-the-risks`.
2. Register it in `RUNNERS` (`runners/__init__.py`) and `RUNNER_BINARIES` (`config.py`).
3. Add a fix command to `FIXES` in `doctor.py`.
4. If it reads a new project skills folder, add it to `TARGETS` in `skills_sync.py`.
5. Add its argv to the snapshot file `tests/fixtures/runner_argv.json` and check the flags against its real `--help`. Flags you cannot check must be marked `UNVERIFIED` in [runners reference](reference/runners.md), as Codex and Copilot are today.

## Try it

Run the tests that guard these steps:

```bash
uv run pytest tests/test_skills.py -q
```
Run: yes, output below

```text
...............................................                          [100%]
47 passed in 0.16s
```
