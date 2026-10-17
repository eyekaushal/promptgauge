import pytest

from promptgauge.ablate.ablation_planner import AblationPlanner
from promptgauge.prompt.prompt_segmenter import PromptSegmenter
from tests.prompt.conftest import read_fixture

MULTI = read_fixture("headings_and_bullets")  # 4 blocks; only the bullet block has >1 line
SINGLE = read_fixture("single_block")  # 1 block, 3 sentences


def planner(cases: int = 10, repeats: int = 3) -> AblationPlanner:
    return AblationPlanner(PromptSegmenter(), cases, repeats)


def test_stage_one_is_baseline_plus_one_variant_per_block() -> None:
    plan = planner().stage_one(MULTI)
    assert plan.stage == 1 and plan.baseline
    assert [s.level for s in plan.segments] == ["block"] * 4
    assert (plan.variants, plan.calls) == (5, 150)


def test_single_block_prompt_is_ablated_at_line_level_directly() -> None:
    plan = planner().stage_one(SINGLE)
    assert [s.level for s in plan.segments] == ["line"] * 3
    assert [s.text for s in plan.segments] == [
        "Only one block, three sentences.",
        "No headings at all.",
        "Still ablated line by line.",
    ]
    assert (plan.variants, plan.calls) == (4, 120)


def test_stage_two_runs_lines_of_multi_line_red_blocks_only() -> None:
    p = planner()
    blocks = p.stage_one(MULTI).segments
    role, _, _, rules = blocks
    plan = p.stage_two([role, rules])
    assert plan.stage == 2 and not plan.baseline
    # '# Role' is a single-line block: nothing to split, so it contributes no lines (F6.6).
    assert [s.text for s in plan.segments] == ["- Answer briefly.", "- Never guess."]
    assert all(s.parent_index == rules.index for s in plan.segments)
    assert (plan.variants, plan.calls) == (2, 60)


def test_stage_two_with_no_red_blocks_is_empty() -> None:
    plan = planner().stage_two([])
    assert plan.segments == [] and plan.calls == 0


def test_stage_two_after_a_single_block_stage_one_is_empty() -> None:
    p = planner()
    red_lines = p.stage_one(SINGLE).segments
    assert p.stage_two(red_lines).segments == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("headings_and_bullets", 2),
        ("mixed", 4),  # '- one','- two' + 'Para one.','Para two?'
        ("paragraphs", 3),
        ("fenced_code", 0),  # every block there is a single line
        ("single_block", 0),  # stage one already ran the lines
    ],
)
def test_stage_two_candidates(name: str, expected: int) -> None:
    assert planner().stage_two_candidates(read_fixture(name)) == expected


@pytest.mark.parametrize(("cases", "repeats"), [(0, 3), (10, 0)])
def test_rejects_empty_runs(cases: int, repeats: int) -> None:
    with pytest.raises(ValueError):
        AblationPlanner(PromptSegmenter(), cases, repeats)
