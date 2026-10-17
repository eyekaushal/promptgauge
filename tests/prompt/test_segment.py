import pytest
from pydantic import ValidationError

from promptgauge.prompt.segment import Segment


def test_block_segment_round_trips_text_length() -> None:
    seg = Segment(level="block", index=0, start=4, end=9, text="hello", tokens=1)
    assert (seg.parent_index, seg.end - seg.start) == (None, len(seg.text))


def test_line_segment_carries_parent_index() -> None:
    seg = Segment(level="line", index=2, parent_index=1, start=0, end=2, text="hi", tokens=1)
    assert seg.parent_index == 1


@pytest.mark.parametrize(
    "fields",
    [
        {"level": "block", "index": 0, "start": 0, "end": 4, "text": "hi", "tokens": 1},
        {"level": "block", "index": 0, "start": 0, "end": 2, "text": "", "tokens": 1},
        {"level": "block", "index": 0, "parent_index": 0, "start": 0, "end": 2, "text": "hi"},
        {"level": "line", "index": 0, "start": 0, "end": 2, "text": "hi", "tokens": 1},
        {"level": "word", "index": 0, "start": 0, "end": 2, "text": "hi", "tokens": 1},
        {"level": "block", "index": -1, "start": 0, "end": 2, "text": "hi", "tokens": 1},
        {"level": "block", "index": 0, "start": 0, "end": 2, "text": "hi", "tokens": -1},
        {"level": "block", "index": 0, "start": 0, "end": 2, "text": "hi", "tokens": 1, "x": 1},
    ],
)
def test_invalid_segments_are_rejected(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Segment(**fields)  # type: ignore[arg-type]


def test_segment_is_frozen() -> None:
    seg = Segment(level="block", index=0, start=0, end=2, text="hi", tokens=1)
    with pytest.raises(ValidationError):
        seg.text = "ho"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("text", "fenced"),
    [
        ("```json\n{}\n```", True),
        ("~~~\ncode\n~~~", True),
        ("  ```\nx\n```", True),
        ("Use this:\n```\nx\n```", False),
        ("- item", False),
    ],
)
def test_is_fenced_code(text: str, fenced: bool) -> None:
    seg = Segment(level="block", index=0, start=0, end=len(text), text=text, tokens=1)
    assert seg.is_fenced_code() is fenced
