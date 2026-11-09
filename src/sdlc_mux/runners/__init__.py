"""Runner registry: name -> runner class. Names match RUNNER_BINARIES in config.py."""

from .base import Runner
from .claude import ClaudeRunner
from .codex import CodexRunner
from .copilot import CopilotRunner
from .mock import MockRunner

RUNNERS: dict[str, type[Runner]] = {
    "claude": ClaudeRunner,
    "codex": CodexRunner,
    "copilot": CopilotRunner,
    "mock": MockRunner,
}
