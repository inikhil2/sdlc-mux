"""tmux backend (ADR 0001). One window `room`; all pane work is by pane id.

Every pane carries user options `@section` (empty for the dashboard), `@order` (creation order)
and `@color`. Presets other than `sections`/`grid` park the hidden panes in a window `parked`
so their processes keep running.
"""

import os
import subprocess

from sdlc_mux.multiplexer.base import Multiplexer, Preset, SessionSpec

WINDOW = "room"
PARKED = "parked"
BORDER_FORMAT = "#[fg=#{@color},bold] #{pane_title} "


class TmuxError(Exception):
    """Raised when a tmux command fails; the message is tmux's own."""


def _csum(layout: str) -> str:
    c = 0
    for ch in layout:
        c = (c >> 1) + ((c & 1) << 15)
        c = (c + ord(ch)) & 0xFFFF
    return f"{c:04x}"


def _split(total: int, n: int) -> list[int]:
    """Divide `total` cells into n near-equal sizes (the first ones take the remainder)."""
    return [total // n + (i < total % n) for i in range(n)]


def _leaf(pid: str, w: int, h: int, x: int, y: int) -> str:
    return f"{w}x{h},{x},{y},{pid.lstrip('%')}"


def sections_layout(w: int, h: int, dashboard: str, columns: list[list[str]]) -> str:
    """Return a tmux layout string (with checksum) for a w x h window.

    Top band: `dashboard` pane, ~30% of the height, full width. Below: one column per list in
    `columns`, each stacking its pane ids (like '%3') top to bottom. A 1-cell border separates
    siblings.
    """
    if not columns:
        return _csum(body := _leaf(dashboard, w, h, 0, 0)) + "," + body
    dh = max(1, round(h * 0.3))
    rest = h - dh - 1
    cols, x = [], 0
    for cw, ids in zip(_split(w - (len(columns) - 1), len(columns)), columns, strict=True):
        hs, y, kids = _split(rest - (len(ids) - 1), len(ids)), dh + 1, []
        for pid, ph in zip(ids, hs, strict=True):
            kids.append(_leaf(pid, cw, ph, x, y))
            y += ph + 1
        cols.append(kids[0] if len(ids) == 1 else f"{cw}x{rest},{x},{dh + 1}[{','.join(kids)}]")
        x += cw + 1
    row = cols[0] if len(cols) == 1 else f"{w}x{rest},0,{dh + 1}{{{','.join(cols)}}}"
    body = f"{w}x{h},0,0[{_leaf(dashboard, w, dh, 0, 0)},{row}]"
    return f"{_csum(body)},{body}"


class TmuxMultiplexer(Multiplexer):
    """tmux session `session`; `socket` (tmux -L) selects a dedicated server, else the default."""

    def __init__(self, session: str = "sdlc", socket: str | None = None) -> None:
        """Bind to session `session` on server `socket` (None: the user's default server)."""
        self.session = session
        self.socket = socket

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        cmd = ["tmux", *(["-L", self.socket] if self.socket else []), *args]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if check and p.returncode:
            raise TmuxError(f"tmux {' '.join(args)}: {p.stderr.strip()}")
        return p

    def _out(self, *args: str) -> list[str]:
        return self._run(*args).stdout.splitlines()

    @property
    def _room(self) -> str:
        return f"{self.session}:{WINDOW}"

    def session_exists(self) -> bool:
        """Return True if the session is running on this tmux server."""
        return self._run("has-session", "-t", f"={self.session}", check=False).returncode == 0

    def create_session(self, spec: SessionSpec, cwd: str) -> None:
        """Create session with window `room`: dashboard on top, one column per section.

        Pane titles, per-section border colours and the border format are set; raises TmuxError
        if the session already exists or tmux fails.
        """
        panes = [(spec.dashboard, "")] + [(p, s.name) for s in spec.sections for p in s.panes]
        # A big detached window leaves room for every split; attaching resizes it.
        ids = [self._out("new-session", "-d", "-s", self.session, "-n", WINDOW, "-c", cwd,
                         "-x", "300", "-y", "200", "-P", "-F", "#{pane_id}",
                         spec.dashboard.command)[0]]  # fmt: skip
        for pane, _ in panes[1:]:
            ids += self._out("split-window", "-d", "-v", "-l", "3", "-t", ids[0], "-c", cwd,
                             "-P", "-F", "#{pane_id}", pane.command)  # fmt: skip
        for i, (pid, (pane, section)) in enumerate(zip(ids, panes, strict=True)):
            self._run("select-pane", "-t", pid, "-T", pane.title)
            for k, v in (("@section", section), ("@order", f"{i:03d}"), ("@color", pane.color)):
                self._run("set-option", "-p", "-t", pid, k, v)
        self._reorder()
        self._run("set-option", "-w", "-t", self._room, "pane-border-status", "top")
        self._run("set-option", "-w", "-t", self._room, "pane-border-format", BORDER_FORMAT)
        self.layout("sections")

    def _panes(self, window: str) -> list[tuple[str, str]]:
        """(pane id, section) for the panes of `window`, in window order."""
        rows = self._out("list-panes", "-t", window, "-F", "#{pane_id}\t#{@section}")
        return [(a, b) for a, _, b in (r.partition("\t") for r in rows)]

    def _has_parked(self) -> bool:
        return f"{self.session}:{PARKED}" in {
            f"{self.session}:{n}" for n in self._out("list-windows", "-t", self.session, "-F",
                                                     "#{window_name}")}  # fmt: skip

    def _restore(self) -> None:
        """Bring parked panes back into `room`, in creation order."""
        if self._has_parked():
            for pid, _ in self._panes(f"{self.session}:{PARKED}"):
                last = self._panes(self._room)[-1][0]
                self._run("join-pane", "-d", "-v", "-l", "3", "-s", pid, "-t", last)
                self._run("select-layout", "-t", self._room, "tiled")
        self._reorder()

    def _reorder(self) -> None:
        """Swap panes of `room` into creation order (splits and joins insert out of order)."""
        order = {p: self._out("show-options", "-pqv", "-t", p, "@order")[0]
                 for p, _ in self._panes(self._room)}  # fmt: skip
        for k, want in enumerate(sorted(order, key=lambda p: order[p])):
            cur = self._panes(self._room)[k][0]
            if cur != want:
                self._run("swap-pane", "-d", "-s", want, "-t", cur)

    def layout(self, preset: Preset, focus: str | None = None) -> None:
        """Reflow to `preset`: sections (dashboard band + columns), grid (tiled), or focus
        (only section `focus` stays in the window, stacked over the full window; the other
        panes are parked and come back with the next preset). Raises ValueError for an unknown
        or missing focus section.
        """
        self._restore()
        panes = self._panes(self._room)
        if preset == "focus":
            if focus not in {s for _, s in panes if s}:
                names = ", ".join(sorted({s for _, s in panes if s}))
                raise ValueError(f"focus needs a section name; known sections: {names}")
            for pid, section in panes:
                if section != focus:
                    self._park(pid)
            self._run("select-layout", "-t", self._room, "even-vertical")
        elif preset == "grid":
            self._run("select-layout", "-t", self._room, "tiled")
        else:
            w, h = self._out("display-message", "-p", "-t", self._room,
                             "#{window_width} #{window_height}")[0].split()  # fmt: skip
            cols: dict[str, list[str]] = {}
            for pid, section in panes[1:]:
                cols.setdefault(section, []).append(pid)
            self._run("select-layout", "-t", self._room,
                      sections_layout(int(w), int(h), panes[0][0], list(cols.values())))  # fmt: skip

    def _park(self, pid: str) -> None:
        if self._has_parked():
            last = self._panes(f"{self.session}:{PARKED}")[-1][0]
            self._run("join-pane", "-d", "-v", "-l", "3", "-s", pid, "-t", last)
            self._run("select-layout", "-t", f"{self.session}:{PARKED}", "tiled")
        else:
            self._run("break-pane", "-d", "-s", pid, "-n", PARKED)

    def open_window(self, name: str, command: str, cwd: str) -> None:
        """Open window `name` running `command` in `cwd`; raises TmuxError if no session."""
        self._run("new-window", "-t", f"{self.session}:", "-n", name, "-c", cwd, command)

    def kill_session(self) -> None:
        """Kill the session if it exists; no-op otherwise."""
        self._run("kill-session", "-t", f"={self.session}", check=False)

    def attach(self) -> None:
        """Attach (or, inside tmux, switch the client) to the session; blocks until detached."""
        verb = "switch-client" if os.environ.get("TMUX") and not self.socket else "attach-session"
        cmd = [
            "tmux",
            *(["-L", self.socket] if self.socket else []),
            verb,
            "-t",
            f"={self.session}",
        ]
        if subprocess.run(cmd, check=False).returncode:  # inherits the terminal
            raise TmuxError(f"tmux {verb} failed")
