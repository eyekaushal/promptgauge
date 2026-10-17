"""Completion: text, input_tokens, output_tokens, cost_usd."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Completion:
    """What one model call produced. `cached` and `call_hash` are filled in by CallCache."""

    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cached: bool = False
    call_hash: str = ""
