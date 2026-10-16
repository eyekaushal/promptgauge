import pytest

from promptgauge.config.scorer_spec import ScorerSpec


@pytest.mark.parametrize(
    ("entry", "name", "arg", "key"),
    [
        ("contains", "contains", None, "contains"),
        ("exact", "exact", None, "exact"),
        ("grounded", "grounded", None, "grounded"),
        ({"rubric": "helpful"}, "rubric", "helpful", "rubric:helpful"),
        ({"json_schema": "schema.json"}, "json_schema", "schema.json", "json_schema:schema.json"),
    ],
)
def test_parse_valid(entry: object, name: str, arg: str | None, key: str) -> None:
    spec = ScorerSpec.parse(entry)
    assert (spec.name, spec.arg, spec.key) == (name, arg, key)


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("bleu", "name"),
        ({"contains": "x"}, "takes no argument"),
        ({"rubric": None}, "needs a value"),
        ({"rubric": "a", "exact": None}, "one-key mapping"),
        (42, "one-key mapping"),
        ([], "one-key mapping"),
    ],
)
def test_parse_invalid(entry: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ScorerSpec.parse(entry)
