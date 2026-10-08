from common.mcp_util import tool_defs
from common.mock import MockClient
from domain2_tool_design_mcp.task_2_1_tool_interface_design import anti_pattern as anti
from domain2_tool_design_mcp.task_2_1_tool_interface_design import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_mcp_server_exposes_both_tools_with_given_descriptions():
    tools = tool_defs(good.build_server(good.VAGUE))
    assert {t["name"]: t["description"] for t in tools} == good.VAGUE


def test_step2_vague_descriptions_misroute():
    r = good.evaluate(client(), tool_defs(good.build_server(good.VAGUE)))
    assert len(good.QUERIES) == 10 and r["accuracy"] < 0.5


def test_step3_clear_descriptions_have_all_five_elements():
    for d in good.CLEAR.values():
        assert "Input:" in d and "Examples:" in d and ("Does not" in d or "Returns nothing" in d)
        assert "instead" in d  # explicit boundary vs the other tool


def test_step4_clear_descriptions_route_correctly():
    assert good.evaluate(client(), tool_defs(good.build_server(good.CLEAR)))["accuracy"] == 1.0


def test_step5_detects_keyword_instruction_in_system_prompt():
    assert good.find_keyword_conflicts("Be polite. Always check customer details before proceeding.") == [
        "Always check customer details before proceeding."]
    assert good.find_keyword_conflicts("Be polite and concise.") == []


def test_trap1_few_shot_only_partly_fixes_and_costs_tokens():
    r = anti.trap1_few_shot(client())
    assert 0.4 < r["accuracy"] < 1.0 and r["extra_prompt_chars"] > 0


def test_trap2_classifier_misses_unanticipated_phrasing():
    r = anti.trap2_routing_classifier()
    assert r["accuracy"] < 1.0 and any("1Z" in q for q in r["misses"])


def test_trap3_consolidation_keeps_the_confusion():
    r = anti.trap3_consolidate_first(client())
    assert r["tools_after_merge"] == 1 and r["accuracy"] < 0.5


def test_trap4_system_prompt_overrides_good_descriptions():
    assert anti.trap4_ignore_system_prompt(client())["accuracy"] < 1.0


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "accuracy 100%" in capsys.readouterr().out
