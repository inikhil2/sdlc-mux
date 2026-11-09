import pytest

from sdlc_mux.board import STATES, Board, BoardError


@pytest.fixture
def board() -> Board:
    b = Board(":memory:")
    b.add_item("i1", "Item")
    return b


def test_seventeen_states_in_order() -> None:
    assert len(STATES) == 17 and STATES[0] == "idea" and STATES[-1] == "done"


def test_walks_every_state(board: Board) -> None:
    for s in STATES[1:]:
        board.transition("i1", s)
    assert board.state("i1") == "done"
    assert board.list_items() == [("i1", "Item", "done")]


def test_skip_ahead_rejected(board: Board) -> None:
    with pytest.raises(BoardError, match="only discovering"):
        board.transition("i1", "built")
    assert board.state("i1") == "idea"


def test_backwards_rejected(board: Board) -> None:
    board.transition("i1", "discovering")
    with pytest.raises(BoardError, match="illegal transition"):
        board.transition("i1", "idea")


def test_same_state_and_past_done_rejected(board: Board) -> None:
    with pytest.raises(BoardError):
        board.transition("i1", "idea")


def test_unknown_state_rejected(board: Board) -> None:
    with pytest.raises(BoardError, match="unknown state"):
        board.transition("i1", "shipped")


def test_unknown_and_duplicate_item(board: Board) -> None:
    with pytest.raises(BoardError, match="unknown item"):
        board.state("nope")
    with pytest.raises(BoardError, match="already exists"):
        board.add_item("i1", "again")


def test_needs_human_blocks_until_cleared(board: Board) -> None:
    board.set_needs_human("i1", True)
    assert board.needs_human("i1")
    with pytest.raises(BoardError, match="needs a human"):
        board.transition("i1", "discovering")
    board.set_needs_human("i1", False)
    board.transition("i1", "discovering")
