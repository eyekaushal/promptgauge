from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "prompts"
FIXTURE_NAMES = ["headings_and_bullets", "paragraphs", "mixed", "single_block", "fenced_code"]


def read_fixture(name: str) -> str:
    return (FIXTURES / f"{name}.md").read_text()


@pytest.fixture(params=FIXTURE_NAMES)
def fixture_text(request: pytest.FixtureRequest) -> str:
    return read_fixture(request.param)
