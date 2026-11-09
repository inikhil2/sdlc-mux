"""Terminal multiplexer backends: tmux (built) and Zellij (planned)."""

from sdlc_mux.multiplexer.base import Multiplexer, PaneSpec, SectionSpec, SessionSpec, pane_title
from sdlc_mux.multiplexer.tmux import TmuxMultiplexer
from sdlc_mux.multiplexer.zellij import ZellijMultiplexer

__all__ = [
    "Multiplexer",
    "PaneSpec",
    "SectionSpec",
    "SessionSpec",
    "TmuxMultiplexer",
    "ZellijMultiplexer",
    "pane_title",
]
