"""Pydantic schema and validation for sdlc.yaml."""

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

ROLES = (
    "product-owner",
    "business-analyst",
    "ux-designer",
    "solution-architect",
    "scrum-master",
    "backend-engineer",
    "frontend-engineer",
    "sdet",
    "qa-analyst",
    "code-reviewer",
    "security-engineer",
    "release-engineer",
)
STAGES = ("discover", "design", "plan", "build", "test", "review", "release", "retro")
# Runner name -> binary it needs on PATH (None: needs no binary).
RUNNER_BINARIES: dict[str, str | None] = {
    "claude": "claude",
    "codex": "codex",
    "copilot": "copilot",
    "mock": None,
}


class ConfigError(Exception):
    """Raised when sdlc.yaml is unreadable or invalid; `errors` lists every problem found."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


class Agent(BaseModel):
    """One role bound to a runner, with a number of running instances."""

    role: str
    runner: str
    instances: int = Field(default=1, ge=1)

    @field_validator("role")
    @classmethod
    def _known_role(cls, v: str) -> str:
        if v not in ROLES:
            raise ValueError(f"unknown role '{v}'; known roles: {', '.join(ROLES)}")
        return v

    @field_validator("runner")
    @classmethod
    def _known_runner(cls, v: str) -> str:
        if v not in RUNNER_BINARIES:
            raise ValueError(f"unknown runner '{v}'; known runners: {', '.join(RUNNER_BINARIES)}")
        return v


class Section(BaseModel):
    """A labelled group of agents shown together on screen."""

    name: str
    color: str
    agents: list[Agent]

    @model_validator(mode="after")
    def _no_duplicate_roles(self) -> "Section":
        seen: set[str] = set()
        for a in self.agents:
            if a.role in seen:
                raise ValueError(
                    f"duplicate role '{a.role}' in section '{self.name}'; use 'instances' instead"
                )
            seen.add(a.role)
        return self


class Stage(BaseModel):
    """One pipeline stage and the roles that work in it."""

    stage: str
    roles: list[str]

    @field_validator("stage")
    @classmethod
    def _known_stage(cls, v: str) -> str:
        if v not in STAGES:
            raise ValueError(f"unknown stage '{v}'; known stages: {', '.join(STAGES)}")
        return v

    @field_validator("roles")
    @classmethod
    def _known_roles(cls, v: list[str]) -> list[str]:
        for r in v:
            if r not in ROLES:
                raise ValueError(f"unknown role '{r}' in pipeline; known roles: {', '.join(ROLES)}")
        return v


class Superpowers(BaseModel):
    """Where Superpowers comes from and which version is pinned."""

    repo: str
    pinned_ref: str


class Defaults(BaseModel):
    """Phase 0 answers: the environment this team was configured for."""

    os: str = "macos"
    demo_runner: str = "mock"
    max_panes: int = Field(default=14, ge=1)


class Limits(BaseModel):
    """Per-task time and retry limits enforced by the orchestrator."""

    max_minutes_per_task: int = Field(default=30, ge=1)
    max_retries: int = Field(default=2, ge=0)


class Release(BaseModel):
    """Release gate behaviour."""

    auto_go_when_gates_green: bool = False


class Config(BaseModel):
    """The whole sdlc.yaml document."""

    version: Literal[1]
    mode: Literal["supervised", "autonomous"] = "supervised"
    defaults: Defaults = Defaults()
    superpowers: Superpowers
    sections: list[Section]
    pipeline: list[Stage]
    limits: Limits = Limits()
    release: Release = Release()

    def runners_used(self) -> list[str]:
        """Return the sorted distinct runner names used by any agent."""
        return sorted({a.runner for s in self.sections for a in s.agents})

    def roles_used(self) -> list[str]:
        """Return the sorted distinct role names used by any agent."""
        return sorted({a.role for s in self.sections for a in s.agents})


def missing_binaries(cfg: Config, which: Callable[[str], str | None] = shutil.which) -> list[str]:
    """Return one error message per runner in use whose binary is not on PATH."""
    errors = []
    for runner in cfg.runners_used():
        binary = RUNNER_BINARIES[runner]
        if binary and not which(binary):
            errors.append(
                f"runner '{runner}' is used in sdlc.yaml but binary '{binary}' is not on PATH; "
                f"install it, or change those agents to another runner (e.g. 'mock')"
            )
    return errors


def missing_skills(cfg: Config, skills_dir: Path) -> list[str]:
    """Return one error message per used role lacking <skills_dir>/<role>/SKILL.md."""
    return [
        f"role '{r}' has no skill: expected {skills_dir / r / 'SKILL.md'}"
        for r in cfg.roles_used()
        if not (skills_dir / r / "SKILL.md").is_file()
    ]


def load_config(
    path: Path,
    skills_dir: Path | None = None,
    check_binaries: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> Config:
    """Load and validate sdlc.yaml; raise ConfigError listing every problem.

    Schema errors (unknown role/stage/runner, duplicate roles) are always checked.
    Role skills are checked when `skills_dir` is given; runner binaries when `check_binaries`.
    """
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError([f"cannot read {path}: {e}"]) from e
    try:
        cfg = Config.model_validate(data)
    except ValidationError as e:
        raise ConfigError(
            [
                f"{'.'.join(str(p) for p in x['loc'])}: {x['msg'].removeprefix('Value error, ')}"
                for x in e.errors()
            ]
        ) from e
    errors = missing_skills(cfg, skills_dir) if skills_dir else []
    if check_binaries:
        errors += missing_binaries(cfg, which)
    if errors:
        raise ConfigError(errors)
    return cfg
