"""CLI and doctor tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdlc_mux.cli import app

runner = CliRunner()
REPO = Path(__file__).parent.parent


def test_help_lists_doctor() -> None:
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "doctor" in r.output


def test_doctor_reports_missing_binary_with_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "bin"
    fake.mkdir()
    for b in ("uv", "tmux"):  # present; claude deliberately absent
        (fake / b).write_text("#!/bin/sh\n")
        (fake / b).chmod(0o755)
    monkeypatch.setenv("PATH", str(fake))
    r = runner.invoke(app, ["doctor", "--config", str(REPO / "sdlc.yaml")])
    assert r.exit_code == 1
    assert "[MISSING] runner claude" in r.output
    assert "fix: brew install --cask claude-code" in r.output
    assert "[ok]      tmux" in r.output


def test_doctor_all_present_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "bin"
    fake.mkdir()
    for b in ("uv", "tmux", "claude"):
        (fake / b).write_text("#!/bin/sh\n")
        (fake / b).chmod(0o755)
    monkeypatch.setenv("PATH", str(fake))
    r = runner.invoke(app, ["doctor", "--config", str(REPO / "sdlc.yaml")])
    assert r.exit_code == 0
