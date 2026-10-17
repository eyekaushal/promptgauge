import pytest
from pydantic import ValidationError

from promptgauge.scorers.score_result import ScoreResult


def test_none_score_is_allowed_for_judge_failures() -> None:
    assert ScoreResult(score=None, reason="judge_failed").score is None


@pytest.mark.parametrize("score", [-0.1, 1.1, 2])
def test_score_outside_unit_interval_is_rejected(score: float) -> None:
    with pytest.raises(ValidationError):
        ScoreResult(score=score)
