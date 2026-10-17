"""CallCache: SHA-256 of (model, system prompt text, user input, temperature, repeat index); hit
costs $0; every call becomes a call row. PRD F2.4, F2.6.
"""

import asyncio
import hashlib
import json
from dataclasses import replace

from promptgauge.core.logger import Logger
from promptgauge.db.call_repository import CallRepository
from promptgauge.provider.completion import Completion
from promptgauge.provider.provider import Provider


class CallCache:
    """Every model call goes through here: look up, call if needed, always write a call row.

    Also owns the concurrency limit (PRD F2.5): at most `concurrency` provider calls are in
    flight; cache hits never wait for a slot.
    """

    def __init__(
        self, provider: Provider, calls: CallRepository, logger: Logger, concurrency: int = 8
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        self._provider = provider
        self._calls = calls
        self._log = logger
        self._semaphore = asyncio.Semaphore(concurrency)

    @staticmethod
    def key(system: str, user: str, model: str, temperature: float, repeat_index: int) -> str:
        """The cache key. The full system text is hashed, so a prompt variant is a new key."""
        payload = {
            "model": model,
            "system": system,
            "user": user,
            "temperature": temperature,
            "repeat_index": repeat_index,
        }
        return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    async def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float,
        max_tokens: int,
        repeat_index: int,
        experiment_id: int,
    ) -> Completion:
        """Return the completion for this key, from the table if seen before, else the provider.

        A hit is recorded as its own row with `cached = 1` and `cost_usd = 0`; a miss is recorded
        with the real tokens and cost. Provider errors propagate unrecorded.
        """
        call_hash = self.key(system, user, model, temperature, repeat_index)
        original = self._calls.find_original(call_hash)
        if original is not None:
            completion = Completion(
                text=original["output"],
                input_tokens=original["input_tokens"],
                output_tokens=original["output_tokens"],
                cost_usd=0.0,
                cached=True,
                call_hash=call_hash,
            )
        else:
            async with self._semaphore:
                fresh = await self._provider.complete(system, user, model, temperature, max_tokens)
            completion = replace(fresh, cached=False, call_hash=call_hash)

        self._calls.insert(
            hash=call_hash,
            model=model,
            system_hash=_sha256(system),
            input_hash=_sha256(user),
            temperature=temperature,
            repeat_index=repeat_index,
            output=completion.text,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            cost_usd=completion.cost_usd,
            cached=completion.cached,
            experiment_id=experiment_id,
        )
        self._log.debug(
            "call", model=model, cached=completion.cached, cost_usd=f"{completion.cost_usd:.6f}"
        )
        return completion


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
