import anthropic

from common.mock import MockClient
from domain4_prompt_engineering.task_4_3_structured_output import anti_pattern as anti
from domain4_prompt_engineering.task_4_3_structured_output import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_schema_design():
    props = good.EXTRACT_INVOICE["input_schema"]["properties"]
    nullable = [k for k, v in props.items() if "anyOf" in v]
    assert len(nullable) == 4 and {"unclear", "other"} <= set(props["category"]["enum"])


def test_step2_auto_can_return_text():
    assert [d for d, v in good.extract_all(client()).items() if v is None] == ["d4"]


def test_step3_any_always_returns_a_tool_call():
    c = client()
    out = good.extract_all(c, {"type": "any"})
    assert all(v is not None for v in out.values())
    assert all(call["tool_choice"] == {"type": "any"} for call in c.calls)  # set per request


def test_step4_named_tool_runs_even_if_another_fits():
    r = good.create(client(), good.DOCS[0], [good.EXTRACT_RECEIPT, good.EXTRACT_INVOICE], {"type": "tool", "name": "extract_receipt"})
    assert r.content[0].name == "extract_receipt"


def test_step5_missing_fields_are_null_not_invented():
    out = good.extract_all(client(), {"type": "any"})
    assert out["d4"]["due_date"] is None and out["d4"]["po_number"] is None and out["d4"]["tax"] is None
    assert out["d3"]["category"] == "other" and out["d3"]["category_detail"] == "map licence"
    assert out["d4"]["category"] == "unclear"


class Rejected(anthropic.BadRequestError):
    def __init__(self):
        Exception.__init__(self, "tool_choice any/tool not supported")


def test_falls_back_when_forced_tool_choice_is_rejected():
    def rejecting(kwargs):
        if "tool_choice" in kwargs:
            raise Rejected()
        return good.mock_model(kwargs)
    out = good.extract_all(MockClient(rejecting), {"type": "any"})
    assert all(v is not None for v in out.values())


def test_trap1_schema_valid_but_wrong():
    assert anti.trap1_schema_is_not_correctness()["schema_valid"] == 3


def test_trap2_auto_gives_no_guarantee():
    assert anti.trap2_auto_for_structured_output(client()) == ["d4"]


def test_trap3_required_fields_cause_fabrication():
    r = anti.trap3_all_required(client())
    assert r["d4_due_date"] and r["d4_po_number"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "fabricated" in capsys.readouterr().out
