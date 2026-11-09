"""Copilot CLI adapter. Binary not installed here, so every flag is UNVERIFIED."""

from .base import Bundle, Profile, Runner


class CopilotRunner(Runner):
    """Headless `copilot -p "<prompt>"`, interactive `copilot -i "<prompt>"`."""

    name = "copilot"
    binary = "copilot"
    config_dir = ".copilot"
    project_skills = ".agents/skills"
    user_skills = ".copilot/skills"

    def _flags(self, profile: Profile, headless: bool) -> list[str]:
        if profile == "supervised":
            return []
        if profile == "unsafe":
            return ["--allow-all-tools"]  # UNVERIFIED: see docs/reference/runners.md
        # Copilot has no sandbox; autonomous pre-approves file writes only, not all tools.
        return ["--allow-tool=write"]  # UNVERIFIED: see docs/reference/runners.md

    def build_command(
        self,
        bundle: Bundle,
        prompt: str,
        mode: Profile,
        headless: bool,
        i_understand_the_risks: bool = False,
    ) -> list[str]:
        """argv for Copilot CLI; see `Runner.build_command`."""
        flags = self.permission_flags(mode, headless, i_understand_the_risks)
        # UNVERIFIED: see docs/reference/runners.md (-p headless, -i interactive)
        return ["copilot", *flags, "-p" if headless else "-i", prompt]
