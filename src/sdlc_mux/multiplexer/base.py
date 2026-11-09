"""Multiplexer interface: one terminal session holding a dashboard and one column per section."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Preset = Literal["grid", "sections", "focus"]
PRESETS = ("grid", "sections", "focus")


def pane_title(section: str, role: str, n: int, runner: str, state: str) -> str:
    """Return the pane title `[Section] role#n · runner · state`."""
    return f"[{section}] {role}#{n} · {runner} · {state}"


@dataclass(frozen=True)
class PaneSpec:
    """One pane: its border `title`, border `color`, and the shell `command` it runs."""

    title: str
    color: str
    command: str


@dataclass(frozen=True)
class SectionSpec:
    """One column: a section name and its agent panes, stacked top to bottom."""

    name: str
    color: str
    panes: list[PaneSpec]


@dataclass(frozen=True)
class SessionSpec:
    """The whole room: a full-width dashboard pane above the section columns."""

    dashboard: PaneSpec
    sections: list[SectionSpec]


class Multiplexer(ABC):
    """A terminal multiplexer backend. The session name is fixed per instance."""

    @abstractmethod
    def session_exists(self) -> bool:
        """Return True if the session is running."""

    @abstractmethod
    def create_session(self, spec: SessionSpec, cwd: str) -> None:
        """Create the session with the `sections` layout; raise if it already exists."""

    @abstractmethod
    def layout(self, preset: Preset, focus: str | None = None) -> None:
        """Reflow panes to `preset`; `focus` names the section that gets the whole window."""

    @abstractmethod
    def open_window(self, name: str, command: str, cwd: str) -> None:
        """Open a new window running `command` in the existing session."""

    @abstractmethod
    def kill_session(self) -> None:
        """Stop the session (and every pane in it). State on disk is untouched."""

    @abstractmethod
    def attach(self) -> None:
        """Attach the current terminal to the session; blocks until detached."""
