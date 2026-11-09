import pytest

from sdlc_mux.handoffs import Handoff, HandoffError, parse_handoff, write_handoff

VALID = """---
from: backend-engineer
to: sdet
item: i1
task: T1
stage: build
status: done
produced: [build/T1-report.md]
needs: [write tests]
---
Notes here.
"""


def test_parse_valid() -> None:
    h = parse_handoff(VALID)
    assert h.from_ == "backend-engineer" and h.status == "done"
    assert h.produced == ["build/T1-report.md"] and h.body == "Notes here.\n"


def test_roundtrip() -> None:
    h = Handoff(
        from_="a", to="b", item="i", task="t", stage="test", status="blocked",
        produced=[], needs=["x"], body="hi\n",
    )  # fmt: skip
    assert parse_handoff(write_handoff(h)) == h


@pytest.mark.parametrize(
    ("text", "msg"),
    [
        (VALID.replace("status: done", "status: finished"), "status"),
        (VALID.replace("task: T1\n", ""), "task"),
        (VALID.replace("stage: build", "stage: party"), "unknown stage"),
        (VALID.replace("needs: [write tests]\n", ""), "needs"),
        (VALID.replace("item: i1", "item: i1\nextra: 1"), "extra"),
        (VALID.replace("from: backend-engineer\n", ""), "from"),
        ("no frontmatter", "frontmatter"),
        ("---\n- a\n---\n", "mapping"),
    ],
)
def test_parse_invalid(text: str, msg: str) -> None:
    with pytest.raises(HandoffError, match=msg):
        parse_handoff(text)
