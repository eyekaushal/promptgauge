from pathlib import Path

import pytest

from promptgauge.core.errors import DatasetError
from promptgauge.dataset.dataset_loader import DatasetLoader

ROWS = (
    '{"input": "Order 4471 is late", "expected": "refund", "tags": ["late"]}\n'
    '{"input": "When does it arrive?", "expected": "", "context": "ETA 20 min"}\n'
    "\n"
    '{"input": "Hello"}\n'
)


@pytest.fixture
def dataset_file(tmp_path: Path) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text(ROWS, encoding="utf-8")
    return path


def test_load_parses_every_non_empty_line_in_order(dataset_file: Path) -> None:
    dataset = DatasetLoader().load(dataset_file)
    assert dataset.path == dataset_file
    assert [c.index for c in dataset.cases] == [0, 1, 2]
    assert [c.input for c in dataset.cases] == [
        "Order 4471 is late",
        "When does it arrive?",
        "Hello",
    ]
    assert dataset.cases[0].tags == ["late"]
    assert dataset.cases[1].expected is None
    assert dataset.cases[1].context == "ETA 20 min"


def test_load_accepts_a_string_path(dataset_file: Path) -> None:
    assert len(DatasetLoader().load(str(dataset_file)).cases) == 3


def test_hash_is_sha256_and_stable_across_loads(dataset_file: Path) -> None:
    first = DatasetLoader().load(dataset_file).hash
    second = DatasetLoader().load(dataset_file).hash
    assert first == second
    assert len(first) == 64 and int(first, 16) >= 0


def test_hash_ignores_whitespace_key_order_and_blank_lines(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text('{"input": "hi", "tags": ["t"]}\n{"input": "yo"}\n')
    b.write_text('\n\n{ "tags":["t"] , "input":"hi" }\n\n{"input":"yo"}')
    assert DatasetLoader().load(a).hash == DatasetLoader().load(b).hash


def test_hash_changes_when_content_changes(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text('{"input": "hi"}\n')
    b.write_text('{"input": "hi", "expected": "x"}\n')
    assert DatasetLoader().load(a).hash != DatasetLoader().load(b).hash


def test_hash_changes_when_order_changes(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text('{"input": "one"}\n{"input": "two"}\n')
    b.write_text('{"input": "two"}\n{"input": "one"}\n')
    assert DatasetLoader().load(a).hash != DatasetLoader().load(b).hash


def test_hash_matches_example_dataset_on_repeat_runs() -> None:
    example = Path(__file__).parents[2] / "examples" / "support-bot" / "cases.jsonl"
    loader = DatasetLoader()
    assert loader.load(example).hash == loader.load(example).hash


def test_missing_file() -> None:
    with pytest.raises(DatasetError, match="dataset file not found"):
        DatasetLoader().load("/nowhere/cases.jsonl")


def test_empty_dataset_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text("\n\n")
    with pytest.raises(DatasetError, match="no cases"):
        DatasetLoader().load(path)


@pytest.mark.parametrize(
    ("bad_line", "message"),
    [
        ("{not json", "not valid JSON"),
        ('["input", "hi"]', "must be a JSON object"),
        ('"hi"', "must be a JSON object"),
        ('{"expected": "x"}', "input: Field required"),
        ('{"input": ""}', "input: String should have at least 1 character"),
        ('{"input": 3}', "input: Input should be a valid string"),
        ('{"input": "hi", "tags": "late"}', "tags: Input should be a valid list"),
        ('{"input": "hi", "tags": [1]}', "tags.0: Input should be a valid string"),
        ('{"input": "hi", "note": 1}', "note: Extra inputs are not permitted"),
        ('{"input": "hi", "index": 4}', "'index' is assigned by position"),
    ],
)
def test_bad_line_reports_its_line_number(tmp_path: Path, bad_line: str, message: str) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text('{"input": "ok"}\n\n' + bad_line + '\n{"input": "also ok"}\n')
    with pytest.raises(DatasetError) as info:
        DatasetLoader().load(path)
    text = str(info.value)
    assert text.startswith(f"{path}:3: ")
    assert message in text


def test_non_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_bytes(b'{"input": "\xff"}\n')
    with pytest.raises(DatasetError, match="not UTF-8"):
        DatasetLoader().load(path)


def test_cases_feed_the_case_repository(dataset_file: Path, db) -> None:
    from promptgauge.db.case_repository import CaseRepository

    dataset = DatasetLoader().load(dataset_file)
    ids = CaseRepository(db).upsert_many(dataset.hash, [c.to_row() for c in dataset.cases])
    assert len(ids) == 3
    stored = CaseRepository(db).list_by_dataset(dataset.hash)
    assert [row["input"] for row in stored] == [c.input for c in dataset.cases]
    assert stored[0]["tags"] == ["late"]
