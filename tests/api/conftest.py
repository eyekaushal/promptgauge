"""API fixtures: an in-memory database seeded with one eval and one ablation, and an httpx client
whose Host header is the local server's."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from promptgauge.api.app import App
from promptgauge.config.pricing import Pricing
from promptgauge.core.logger import Logger
from promptgauge.db.call_repository import CallRepository
from promptgauge.db.case_repository import CaseRepository
from promptgauge.db.database import Database
from promptgauge.db.experiment_repository import ExperimentRepository
from promptgauge.db.result_repository import ResultRepository
from promptgauge.db.segment_repository import SegmentRepository
from promptgauge.db.verdict_repository import VerdictRepository

DATASET = "d" * 8
PROMPT = "# Role\n\nBe brief.\nBe kind.\n"
PORT = 7331
BASE_URL = f"http://127.0.0.1:{PORT}"


def _experiment(db: Database, kind: str, name: str) -> int:
    return ExperimentRepository(db).create(
        kind=kind,
        name=name,
        prompt_hash="p" * 8,
        prompt_text=PROMPT,
        dataset_hash=DATASET,
        model="claude-sonnet-4-5",
        judge="claude-haiku-4-5",
        config_json=json.dumps({"delta": 0.05, "repeats": 2}),
    )


def _results(db: Database, experiment_id: int, case_ids: list[int], scores: list[float]) -> None:
    rows = []
    for case_id, score in zip(case_ids, scores, strict=True):
        for repeat in (0, 1):
            call_hash = f"h{experiment_id}-{case_id}-{repeat}"
            CallRepository(db).insert(
                hash=call_hash,
                model="claude-sonnet-4-5",
                system_hash="s",
                input_hash="i",
                temperature=0.7,
                repeat_index=repeat,
                output=f"out {case_id}/{repeat}",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.001,
                cached=repeat == 1,
                experiment_id=experiment_id,
            )
            rows.append(
                {
                    "case_id": case_id,
                    "repeat_index": repeat,
                    "variant_id": None,
                    "scorer": "contains",
                    "score": score,
                    "reason": None,
                    "call_hash": call_hash,
                }
            )
            rows.append(
                {
                    "case_id": case_id,
                    "repeat_index": repeat,
                    "variant_id": None,
                    "scorer": "rubric:helpful",
                    "score": None if repeat == 1 else score / 2,
                    "reason": "judge",
                    "call_hash": call_hash,
                }
            )
    ResultRepository(db).insert_many(experiment_id, rows)


@pytest.fixture
def seeded(db: Database) -> dict[str, int]:
    """Two cases; eval #1 (scores 1.0, 0.5), eval #2 (0.5, 0.5), ablation #3 with segments."""
    case_ids = CaseRepository(db).upsert_many(
        DATASET,
        [
            {"index": 0, "input": "hello", "expected": "hi", "tags": ["greet"]},
            {"index": 1, "input": "bye", "expected": None, "context": "ctx"},
        ],
    )
    eval_a = _experiment(db, "eval", "first")
    _results(db, eval_a, case_ids, [1.0, 0.5])
    ExperimentRepository(db).finish(eval_a, "done")
    eval_b = _experiment(db, "eval", "second")
    _results(db, eval_b, case_ids, [0.5, 0.5])
    ExperimentRepository(db).finish(eval_b, "partial")

    ablation = _experiment(db, "ablation", "cut")
    _results(db, ablation, case_ids, [1.0, 1.0])
    segments = SegmentRepository(db)
    block = segments.insert(
        ablation,
        parent_segment_id=None,
        level="block",
        index=0,
        start_offset=0,
        end_offset=6,
        text="# Role",
        tokens=2,
    )
    body = segments.insert(
        ablation,
        parent_segment_id=None,
        level="block",
        index=1,
        start_offset=8,
        end_offset=25,
        text="Be brief.\nBe kind.",
        tokens=6,
    )
    line = segments.insert(
        ablation,
        parent_segment_id=body,
        level="line",
        index=0,
        start_offset=8,
        end_offset=17,
        text="Be brief.",
        tokens=3,
    )
    unmeasured = segments.insert(
        ablation,
        parent_segment_id=body,
        level="line",
        index=1,
        start_offset=18,
        end_offset=25,
        text="Be kind.",
        tokens=3,
    )
    verdicts = VerdictRepository(db)
    verdicts.upsert(
        ablation,
        block,
        mean_delta=0.0,
        ci_low=-0.02,
        ci_high=0.02,
        n_cases=2,
        verdict="grey",
        stage=1,
    )
    verdicts.upsert(
        ablation,
        body,
        mean_delta=-0.3,
        ci_low=-0.4,
        ci_high=-0.2,
        n_cases=2,
        verdict="red",
        stage=1,
    )
    # Stored as grey on purpose: the API must repaint from the interval (ci_low > delta → green).
    verdicts.upsert(
        ablation, line, mean_delta=0.2, ci_low=0.1, ci_high=0.3, n_cases=2, verdict="grey", stage=2
    )
    ExperimentRepository(db).save_ablation(
        ablation,
        baseline_score=1.0,
        cut_score=0.98,
        cut_ci_low=0.9,
        cut_ci_high=1.0,
        cut_prompt="Be brief.\nBe kind.\n",
        tokens_before=8,
        tokens_after=6,
        confirmed=True,
    )
    ExperimentRepository(db).finish(ablation, "done")
    return {
        "eval_a": eval_a,
        "eval_b": eval_b,
        "ablation": ablation,
        "block": block,
        "body": body,
        "line": line,
        "unmeasured": unmeasured,
        "case_0": case_ids[0],
        "case_1": case_ids[1],
    }


@pytest.fixture
def key_state() -> dict[str, bool]:
    """Mutable switch for whether the API key counts as present."""
    return {"present": False}


@pytest.fixture
def app_factory(db: Database, key_state: dict[str, bool], tmp_path: Path):
    """Builds an App over the test database; `static_dir` defaults to an empty directory."""

    def make(config=None, static_dir: Path | None = None) -> App:
        return App(
            db,
            config,
            lambda: key_state["present"],
            Logger("test-api"),
            Pricing({"claude-sonnet-4-5": (3.0, 15.0), "m": (1.0, 5.0)}),
            port=PORT,
            static_dir=static_dir or tmp_path / "static",
        )

    return make


@pytest.fixture
def client(app_factory) -> Iterator[TestClient]:
    """httpx client with the local Host header; server exceptions become 500 responses."""
    with TestClient(app_factory().build(), base_url=BASE_URL, raise_server_exceptions=False) as c:
        yield c
