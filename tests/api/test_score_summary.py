import pytest

from promptgauge.api.score_summary import ScoreSummary


def _row(case_id, repeat, scorer, score, variant_id=None):
    return {
        "case_id": case_id,
        "repeat_index": repeat,
        "variant_id": variant_id,
        "scorer": scorer,
        "score": score,
    }


def test_empty_rows_give_none_everywhere() -> None:
    summary = ScoreSummary([])
    assert summary.score is None
    assert summary.scorer_means() == {}
    assert summary.per_case() == {}


def test_run_score_is_the_mean_of_its_present_scorer_values() -> None:
    rows = [
        _row(1, 0, "contains", 1.0),
        _row(1, 0, "rubric:x", 0.5),
        _row(1, 1, "contains", 0.0),
        _row(1, 1, "rubric:x", None),
        _row(2, 0, "contains", 1.0),
        _row(2, 0, "rubric:x", 1.0),
    ]
    summary = ScoreSummary(rows)
    assert summary.scorer_keys == ["contains", "rubric:x"]
    assert summary.score == pytest.approx((0.75 + 0.0 + 1.0) / 3)
    assert summary.scorer_means() == {"contains": pytest.approx(2 / 3), "rubric:x": 0.75}
    per_case = summary.per_case()
    assert per_case[1] == {
        "score": pytest.approx(0.375),
        "scorer_means": {"contains": 0.5, "rubric:x": 0.5},
        "repeats": 2,
    }
    assert per_case[2]["repeats"] == 1


def test_variant_rows_are_ignored() -> None:
    rows = [_row(1, 0, "contains", 1.0), _row(1, 0, "contains", 0.0, variant_id=7)]
    assert ScoreSummary(rows).score == 1.0


def test_a_run_with_only_failed_judges_counts_as_unscored() -> None:
    rows = [_row(1, 0, "rubric:x", None), _row(1, 1, "rubric:x", 1.0)]
    assert ScoreSummary(rows).score == 1.0
    assert ScoreSummary(rows).per_case()[1]["repeats"] == 2
