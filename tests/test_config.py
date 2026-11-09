"""Config validation: one test per error case in Prompt.md section 7."""

from pathlib import Path

import pytest
import yaml

from sdlc_mux.config import ROLES, ConfigError, load_config

REPO = Path(__file__).parent.parent


def write(tmp_path: Path, **overrides: object) -> Path:
    """Write the repo sdlc.yaml with top-level keys overridden; return its path."""
    data = yaml.safe_load((REPO / "sdlc.yaml").read_text()) | overrides
    p = tmp_path / "sdlc.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def section(*roles: str, runner: str = "mock") -> list[dict[str, object]]:
    """Build a one-section sections list."""
    return [
        {"name": "S", "color": "blue", "agents": [{"role": r, "runner": runner} for r in roles]}
    ]


def test_default_yaml_validates(tmp_path: Path) -> None:
    skills = tmp_path / "skills"
    for r in ROLES:
        (skills / r).mkdir(parents=True)
        (skills / r / "SKILL.md").write_text("x")
    cfg = load_config(REPO / "sdlc.yaml", skills_dir=skills, check_binaries=True, which=lambda b: b)
    assert cfg.defaults.max_panes == 14
    assert cfg.runners_used() == ["claude"]


def test_unknown_role(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="unknown role 'wizard'"):
        load_config(write(tmp_path, sections=section("wizard")))


def test_unknown_stage(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="unknown stage 'deploy'"):
        load_config(write(tmp_path, pipeline=[{"stage": "deploy", "roles": ["sdet"]}]))


def test_missing_role_skill(tmp_path: Path) -> None:
    skills = tmp_path / "skills"
    skills.mkdir()
    with pytest.raises(ConfigError, match="role 'sdet' has no skill"):
        load_config(write(tmp_path, sections=section("sdet")), skills_dir=skills)


def test_runner_binary_not_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir: no binaries at all
    p = write(tmp_path, sections=section("sdet", runner="codex"))
    with pytest.raises(ConfigError, match="binary 'codex' is not on PATH"):
        load_config(p, check_binaries=True)


def test_runner_binary_found_on_fake_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "codex").write_text("#!/bin/sh\n")
    (fake / "codex").chmod(0o755)
    monkeypatch.setenv("PATH", str(fake))
    load_config(write(tmp_path, sections=section("sdet", runner="codex")), check_binaries=True)


def test_duplicate_role_in_section(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="duplicate role 'sdet' in section 'S'"):
        load_config(write(tmp_path, sections=section("sdet", "sdet")))


def test_same_role_in_two_sections_is_allowed(tmp_path: Path) -> None:
    two = section("sdet") + section("sdet")
    load_config(write(tmp_path, sections=two))


def test_unknown_runner(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="unknown runner 'gpt'"):
        load_config(write(tmp_path, sections=section("sdet", runner="gpt")))
