import pytest

from common.mock import MockClient, message, text
from domain1_agentic_architecture.task_1_1_agentic_loop import anti_pattern as anti
from domain1_agentic_architecture.task_1_1_agentic_loop import good_example as good


def test_good_loop_runs_tools_then_finishes_on_end_turn():
    client = MockClient(good.mock_model)
    result = good.run_agent(client, good.QUESTION)
    assert result.stop_reason == "end_turn"
    assert result.iterations == 2
    assert [c[2]["order_id"] for c in result.tool_calls] == ["A-100", "B-200"]
    assert "A-100 is shipped" in result.final_text and "B-200 is processing" in result.final_text


def test_good_loop_appends_assistant_turn_then_one_tool_result_turn():
    client = MockClient(good.mock_model)
    result = good.run_agent(client, good.QUESTION)
    roles = [m["role"] for m in result.messages]
    assert roles == ["user", "assistant", "user", "assistant"]
    tool_results = result.messages[2]["content"]
    # Each result carries the matching tool_use_id
    assert [r["tool_use_id"] for r in tool_results] == [c[0] for c in result.tool_calls]


def test_good_loop_never_sets_tool_choice():
    client = MockClient(good.mock_model)
    good.run_agent(client, good.QUESTION)
    assert all("tool_choice" not in call for call in client.calls)


def test_good_loop_cap_is_a_safety_net_that_raises():
    always_tools = MockClient(lambda kw: good.mock_model({**kw, "tool_choice": {"type": "any"}}))
    with pytest.raises(good.IterationCapReached):
        good.run_agent(always_tools, good.QUESTION, max_iterations=3)


def test_good_loop_surfaces_unexpected_stop_reasons():
    client = MockClient([message(text("partial"), stop_reason="max_tokens")])
    result = good.run_agent(client, good.QUESTION)
    assert result.stop_reason == "max_tokens"


def test_anti_content0_check_exits_before_running_tools():
    result = anti.run_agent_text_check(MockClient(good.mock_model), good.QUESTION)
    assert result.tool_calls == []
    assert result.final_text == "Let me check both orders."
    assert result.stop_reason == "tool_use"  # Claude was NOT done


def test_anti_forced_tool_choice_never_reaches_end_turn():
    client = MockClient(good.mock_model)
    result = anti.run_agent_forced_tool(client, good.QUESTION, max_iterations=5)
    assert result.stop_reason == "cap"
    assert result.final_text == ""
    assert len(result.tool_calls) == 5
    assert all(c["tool_choice"] == {"type": "any"} for c in client.calls)


def test_anti_cap_as_exit_cuts_off_work():
    result = anti.run_agent_cap_only(MockClient(good.mock_model), good.QUESTION, iterations=1)
    assert len(result.tool_calls) == 2  # work was started...
    assert result.stop_reason == "tool_use"  # ...but Claude never got to answer
    assert "shipped" not in result.final_text


def test_demos_run(capsys):
    good.main()
    anti.main()
    out = capsys.readouterr().out
    assert "stop_reason=end_turn" in out
    assert "cut off mid-task" in out
