from types import SimpleNamespace

import anthropic
import httpx2 as httpx

from assistant.agent import Assistant
from assistant.data import Dataset
from assistant.tools import ToolResult


class Block(SimpleNamespace):
    def model_dump(self, **kwargs):
        return vars(self)


class FakeMessages:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(content=value, stop_reason="tool_use" if any(b.type == "tool_use" for b in value) else "end_turn")


def test_tool_roundtrip_and_error_feedback():
    client = SimpleNamespace(messages=FakeMessages([
        [Block(type="tool_use", id="t1", name="find_nulls", input={}),
         Block(type="tool_use", id="t2", name="delete_everything", input={})],
        [Block(type="text", text="There is one missing value.")],
    ]))
    agent = Assistant(client=client)
    answer, results = agent.ask("Find missing values", Dataset(b"n,label\n1,a\n,b\n"))
    assert answer == "There is one missing value."
    assert results[0].data["total_missing"] == 1 and results[1].error
    messages = client.messages.requests[1]["messages"]
    assert messages[-1]["content"][1]["is_error"]
    assert messages[-1]["content"][0]["tool_use_id"] == "t1"
    assert "label" in client.messages.requests[0]["system"]


def test_api_failure_after_change_preserves_evidence():
    client = SimpleNamespace(messages=FakeMessages([
        [Block(type="tool_use", id="t1", name="remove_duplicates", input={})],
        anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com")),
    ]))
    data = Dataset(b"n\n1\n1\n")
    answer, results = Assistant(client=client).ask("Remove duplicates", data)
    assert "could not complete" in answer and len(results) == 1
    assert len(data.frame) == 1 and data.can_undo


def test_oversized_result_is_not_sent_to_model():
    result = ToolResult("query_sql", {}, {"rows": [["sensitive" * 5000]]})
    assert "sensitive" not in result.for_model()
    assert "result_withheld" in result.for_model()


def test_multistep_tool_budget():
    responses = [[Block(type="tool_use", id=f"t{i}", name="dataset_info", input={}) for i in range(12)],
                 [Block(type="text", text="Finished.")]]
    client = SimpleNamespace(messages=FakeMessages(responses))
    _, results = Assistant(client=client).ask("Inspect", Dataset(b"n\n1\n"))
    assert len(results) == 12
    assert all(result.error for result in results[10:])
