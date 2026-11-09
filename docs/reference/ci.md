# CI

CI is defined in `.github/workflows/ci.yml`. Action versions are major tags, UNVERIFIED.

**What CI runs:** on ubuntu-latest and macos-latest (Python 3.12, tmux installed): `uv sync`, `pytest`, `ruff check`, `ruff format --check`, `mypy --strict` on `config`, `board`, `gates`, and `sdlc doctor --help`. On windows-latest: non-tmux unit tests only. Separate jobs run shellcheck and PSScriptAnalyzer.

**What ran locally (macOS):** pytest, ruff check, ruff format --check, mypy --strict on the three modules.

**What did not run:** the workflow itself (no remote CI run), shellcheck, PSScriptAnalyzer (D6), Windows, and WSL.
