"""Judge wiring for scorer tests: FakeProvider → CallCache → Judge, in-memory SQLite."""

from collections.abc import Callable

import pytest

from promptgauge.cache.call_cache import CallCache
from promptgauge.core.logger import Logger
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.database import Database
from promptgauge.provider.fake_provider import FakeProvider
from promptgauge.scorers.judge import Judge

JUDGE_MODEL = "claude-haiku-4-5"


class SequenceProvider(FakeProvider):
    """Returns the next scripted answer on every call, whatever the input."""

    def __init__(self, answers: list[str]) -> None:
        super().__init__()
        self._answers = list(answers)

    async def complete(self, system, user, model, temperature, max_tokens):
        self._outputs[user] = self._answers.pop(0)
        return await super().complete(system, user, model, temperature, max_tokens)


@pytest.fixture
def make_judge(db: Database, experiment_id: int) -> Callable[[FakeProvider], Judge]:
    def build(provider: FakeProvider) -> Judge:
        cache = CallCache(provider, CallRepository(db), Logger("test"))
        return Judge(cache, JUDGE_MODEL, experiment_id, Logger("test"))

    return build
