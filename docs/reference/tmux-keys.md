# tmux keys in the sdlc room

The tmux prefix is `Ctrl-b` unless you changed it. Press the prefix, release, then the key.

| Keys | What it does |
|---|---|
| prefix, then an arrow key | Move to the pane above, below, left or right |
| prefix, then `z` | Zoom the current pane to the whole window; press again to restore |
| prefix, then `[` | Scroll back through the pane's output (`q` to leave; arrows or PageUp/PageDown to move) |
| prefix, then `d` | Detach and leave everything running; `sdlc attach` returns |

Related commands: `sdlc layout --preset grid|sections|focus <section>` reflows panes; `sdlc down` stops the session and keeps all state on disk.
