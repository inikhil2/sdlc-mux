"""Zellij backend: planned, not built in v1 (ADR 0007)."""

from sdlc_mux.multiplexer.base import Multiplexer, Preset, SessionSpec

PLANNED = "Zellij backend is planned, not built in v1; see docs/adr/0007-zellij-planned-only.md"


class ZellijMultiplexer(Multiplexer):
    """Placeholder that keeps the interface honest: every method raises NotImplementedError."""

    def session_exists(self) -> bool:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)

    def create_session(self, spec: SessionSpec, cwd: str) -> None:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)

    def layout(self, preset: Preset, focus: str | None = None) -> None:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)

    def open_window(self, name: str, command: str, cwd: str) -> None:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)

    def kill_session(self) -> None:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)

    def attach(self) -> None:
        """Always raises NotImplementedError."""
        raise NotImplementedError(PLANNED)
