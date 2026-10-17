"""Judge: fixed system prompt per scorer, temperature 0, through the cache, one retry, judge_failed
on malformed JSON. PRD F3.5.
"""

from importlib.resources import files
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from promptgauge.cache.call_cache import CallCache
from promptgauge.core.logger import Logger
from promptgauge.scorers.scorer import NOT_JSON, parse_json

T = TypeVar("T", bound=BaseModel)

# Judge answers are short JSON objects (PRD §14).
MAX_TOKENS = 512


class Judge:
    """One judge per experiment: every scorer that needs a model opinion asks through here.

    The scorer's system prompt is the full text of a file in `scorers/prompts/`, so editing a
    prompt changes the cache key. The retry uses repeat index 1 so it cannot hit the cached
    malformed answer from attempt 0.
    """

    def __init__(self, cache: CallCache, model: str, experiment_id: int, logger: Logger) -> None:
        self._cache = cache
        self._model = model
        self._experiment_id = experiment_id
        self._log = logger

    @property
    def model(self) -> str:
        """The judge model id."""
        return self._model

    @staticmethod
    def prompt(name: str) -> str:
        """The system prompt text for a scorer, read from `scorers/prompts/<name>.md`."""
        return (files("promptgauge.scorers") / "prompts" / f"{name}.md").read_text("utf-8")

    async def ask(self, system: str, user: str, answer_type: type[T]) -> T | None:
        """Ask once, retry once on a malformed answer, then give up with None.

        Provider errors propagate; the runner reports those as a failed case.
        """
        for attempt in range(2):
            completion = await self._cache.complete(
                system=system,
                user=user,
                model=self._model,
                temperature=0.0,
                max_tokens=MAX_TOKENS,
                repeat_index=attempt,
                experiment_id=self._experiment_id,
            )
            answer = self._parse(completion.text, answer_type)
            if answer is not None:
                return answer
            self._log.warning("judge answer malformed", model=self._model, attempt=attempt + 1)
        return None

    @staticmethod
    def _parse(text: str, answer_type: type[T]) -> T | None:
        data = parse_json(text)
        if data is NOT_JSON:
            return None
        try:
            return answer_type.model_validate(data)
        except ValidationError:
            return None
