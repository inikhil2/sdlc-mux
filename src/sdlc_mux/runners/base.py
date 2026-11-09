"""Runner interface shared by every agent CLI adapter (Prompt.md section 13)."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Profile = Literal["supervised", "autonomous", "unsafe"]
PROFILES = ("supervised", "autonomous", "unsafe")


class RiskRefusal(Exception):
    """Raised when a profile disables sandboxing or approvals without --i-understand-the-risks."""


@dataclass(frozen=True)
class Bundle:
    """Everything one agent task needs: who, which stage, the brief, and where outputs go."""

    role: str
    stage: str
    item: str
    brief: Path
    outputs_dir: Path
    task: str = "T1"  # build tasks only: names build/<task>-report.md


@dataclass(frozen=True)
class RunnerStatus:
    """`logged_in` is a heuristic (config dir exists); credentials are never read."""

    installed: bool
    version: str | None
    logged_in: bool


@dataclass(frozen=True)
class Result:
    """Outcome of one run: `ok` iff exit code 0; `artifacts` are files under outputs_dir."""

    ok: bool
    exit_code: int
    artifacts: tuple[str, ...]


class Runner(ABC):
    """One agent CLI. Subclasses set the class attributes and implement `_flags`/`build_command`."""

    name: str
    binary: str
    config_dir: str  # under the home directory; only its existence is checked
    project_skills: str
    user_skills: str  # under the home directory

    @abstractmethod
    def _flags(self, profile: Profile, headless: bool) -> list[str]:
        """Flags for an already-validated profile."""

    @abstractmethod
    def build_command(
        self,
        bundle: Bundle,
        prompt: str,
        mode: Profile,
        headless: bool,
        i_understand_the_risks: bool = False,
    ) -> list[str]:
        """Return the argv that runs `prompt` for `bundle` under permission profile `mode`.

        Raises RiskRefusal if the profile disables sandboxing or approvals and
        `i_understand_the_risks` is False. Never executes anything.
        """

    def skills_dir(self, scope: Literal["project", "user"]) -> Path:
        """Directory where this runner reads skills: relative for project, absolute for user."""
        if scope == "project":
            return Path(self.project_skills)
        return Path.home() / self.user_skills

    def permission_flags(
        self, profile: Profile, headless: bool = True, i_understand_the_risks: bool = False
    ) -> list[str]:
        """Flags for `supervised` (runner default), `autonomous` (workspace-limited, no prompts)
        or `unsafe` (disables approvals/sandbox; raises RiskRefusal without the acknowledgement).
        """
        if profile not in PROFILES:
            raise ValueError(f"unknown permission profile '{profile}'")
        if profile == "unsafe" and not i_understand_the_risks:
            raise RiskRefusal(
                f"profile 'unsafe' disables sandboxing or approvals for {self.name}; "
                "pass --i-understand-the-risks to allow it"
            )
        return self._flags(profile, headless)

    def check_installed(self) -> RunnerStatus:
        """Binary on PATH, its `--version` first line, and whether a config dir exists."""
        path = shutil.which(self.binary)
        if path is None:
            return RunnerStatus(False, None, False)
        try:
            out = subprocess.run(
                [path, "--version"], check=False, capture_output=True, text=True, timeout=10
            )
            version = out.stdout.strip().splitlines()[0] if out.stdout.strip() else None
        except (OSError, subprocess.SubprocessError):
            version = None
        return RunnerStatus(True, version, (Path.home() / self.config_dir).exists())

    def parse_result(self, exit_code: int, outputs_dir: Path) -> Result:
        """Exit code plus the sorted relative paths of every file under `outputs_dir`."""
        files = sorted(
            p.relative_to(outputs_dir).as_posix() for p in outputs_dir.rglob("*") if p.is_file()
        )
        return Result(exit_code == 0, exit_code, tuple(files))
