"""Codex CLI adapter. Binary not installed here, so every flag is UNVERIFIED."""

from .base import Bundle, Profile, Runner


class CodexRunner(Runner):
    """Headless `codex exec "<prompt>"`, interactive `codex "<prompt>"`."""

    name = "codex"
    binary = "codex"
    config_dir = ".codex"
    project_skills = ".agents/skills"
    user_skills = ".agents/skills"

    def _flags(self, profile: Profile, headless: bool) -> list[str]:
        if profile == "supervised":
            return []
        if profile == "unsafe":
            return [
                "--dangerously-bypass-approvals-and-sandbox"
            ]  # UNVERIFIED: see docs/reference/runners.md
        return ["--sandbox", "workspace-write"]  # UNVERIFIED: see docs/reference/runners.md

    def build_command(
        self,
        bundle: Bundle,
        prompt: str,
        mode: Profile,
        headless: bool,
        i_understand_the_risks: bool = False,
    ) -> list[str]:
        """argv for Codex CLI; see `Runner.build_command`."""
        flags = self.permission_flags(mode, headless, i_understand_the_risks)
        # UNVERIFIED: see docs/reference/runners.md (`exec` subcommand)
        return ["codex", "exec", *flags, prompt] if headless else ["codex", *flags, prompt]
