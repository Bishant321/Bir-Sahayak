import json

from assistant.config import ROOT
from experiments.evaluate import business, equal_rows


def test_all_business_reference_answers():
    result = business(live=False)
    assert result["total"] == 30
    assert result["passed"] == 30


def test_routing_fixture_size_and_numeric_comparison():
    prompts = json.loads((ROOT / "experiments/tool_prompts.json").read_text())
    assert len(prompts) == 40
    assert equal_rows([[1.00000001, None, "North"]], [[1, None, "North"]])
    assert not equal_rows([["1"]], [[1]])
    assert not equal_rows([[1, 2]], [[1]])
