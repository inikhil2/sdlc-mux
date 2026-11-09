"""Handoff messages: Markdown with YAML frontmatter passed between roles."""

from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from sdlc_mux.config import STAGES


class HandoffError(Exception):
    """Raised when a handoff message is malformed."""


class Handoff(BaseModel):
    """A handoff: who it is from/to, which item/task/stage, status, outputs and needs."""

    model_config = ConfigDict(extra="forbid")

    from_: str
    to: str
    item: str
    task: str
    stage: str
    status: Literal["done", "blocked", "question"]
    produced: list[str]
    needs: list[str]
    body: str = ""

    @field_validator("stage")
    @classmethod
    def _known_stage(cls, v: str) -> str:
        if v not in STAGES:
            raise ValueError(f"unknown stage '{v}'; known stages: {', '.join(STAGES)}")
        return v


def write_handoff(h: Handoff) -> str:
    """Render a Handoff as Markdown text that `parse_handoff` reads back unchanged."""
    front = h.model_dump(exclude={"body"})
    front["from"] = front.pop("from_")
    # Put `from` first for readability.
    ordered = {"from": front.pop("from")} | front
    return f"---\n{yaml.safe_dump(ordered, sort_keys=False)}---\n{h.body}"


def parse_handoff(text: str) -> Handoff:
    """Parse handoff Markdown; raises HandoffError on bad frontmatter, a missing field,
    an unknown field, an unknown stage, or a status other than done|blocked|question."""
    parts = text.split("---\n", 2)
    if len(parts) < 3 or parts[0].strip():
        raise HandoffError("handoff must start with a '---' frontmatter block")
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise HandoffError(f"frontmatter is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise HandoffError("frontmatter must be a mapping")
    if "body" in data:
        raise HandoffError("body: not a frontmatter field")
    if "from" in data:
        data["from_"] = data.pop("from")
    try:
        return Handoff(**{**data, "body": parts[2]})
    except ValidationError as e:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']).replace('from_', 'from')}: {err['msg']}"
            for err in e.errors()
        )
        raise HandoffError(problems) from e
