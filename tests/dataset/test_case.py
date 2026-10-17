import pytest
from pydantic import ValidationError

from promptgauge.dataset.case import Case


def test_minimal_case_has_defaults() -> None:
    case = Case(index=0, input="hi")
    assert (case.expected, case.context, case.tags) == (None, None, [])


def test_blank_expected_and_context_become_none() -> None:
    case = Case(index=0, input="hi", expected="", context="")
    assert (case.expected, case.context) == (None, None)


def test_full_case_round_trips_to_row() -> None:
    case = Case(index=2, input="q", expected="a", context="c", tags=["x", "y"])
    assert case.to_row() == {
        "index": 2,
        "input": "q",
        "expected": "a",
        "context": "c",
        "tags": ["x", "y"],
    }


@pytest.mark.parametrize(
    "fields",
    [
        {"index": 0},
        {"index": 0, "input": ""},
        {"index": 0, "input": 3},
        {"index": -1, "input": "hi"},
        {"index": 0, "input": "hi", "tags": "late"},
        {"index": 0, "input": "hi", "tags": [1]},
        {"index": 0, "input": "hi", "expected": 5},
        {"index": 0, "input": "hi", "extra": True},
    ],
)
def test_invalid_rows_are_rejected(fields: dict) -> None:
    with pytest.raises(ValidationError):
        Case(**fields)
