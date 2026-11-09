"""Claude Code adapter. All flags VERIFIED against docs/reference/claude-help.txt.

Never uses --bare: it ignores subscription login.
"""

from .base import Bundle, Profile, Runner


class ClaudeRunner(Runner):
    """Headless `claude -p "<prompt>"`, interactive `claude "<prompt>"`."""

    name = "claude"
    binary = "claude"
    config_dir = ".claude"
    project_skills = ".claude/skills"
    user_skills = ".claude/skills"

    def _flags(self, profile: Profile, headless: bool) -> list[str]:
        if profile == "supervised":
            return []
        if profile == "unsafe":
            return ["--dangerously-skip-permissions"]
        # autonomous: accept edits in the workspace; with -p, anything else that would prompt
        # is denied automatically (--permission-prompts is print-only).
        flags = ["--permission-mode", "acceptEdits"]
        return flags + ["--permission-prompts", "none"] if headless else flags

    def build_command(
        self,
        bundle: Bundle,
        prompt: str,
        mode: Profile,
        headless: bool,
        i_understand_the_risks: bool = False,
    ) -> list[str]:
        """argv for Claude Code; see `Runner.build_command`."""
        flags = self.permission_flags(mode, headless, i_understand_the_risks)
        return ["claude", *flags, "-p", prompt] if headless else ["claude", *flags, prompt]
