import logging

from common.mock import MockClient, message, text
from domain1_agentic_architecture.task_1_1_agentic_loop import anti_pattern as anti
from domain1_agentic_architecture.task_1_1_agentic_loop import good_example as good


def _run():
    client = MockClient(good.mock_model)
    return client, good.run_agent(client, good.QUESTION)


# ---- build exercise --------------------------------------------------------------------------

def test_step1_two_tools_with_valid_schemas():
    assert {t["name"] for t in good.TOOLS} == {"calculator", "web_search"}
    assert all(t["description"] and t["input_schema"]["type"] == "object" for t in good.TOOLS)


def test_calculator_is_safe():
    assert good.calculate("330 * 3.28084") == 330 * 3.28084
    assert good.execute_tool("calculator", {"expression": "__import__('os')"})["is_error"]


def test_step5_sequential_tools_then_end_turn():
    _, r = _run()
    assert r.complete and r.stop_reason == "end_turn"
    assert [c[1] for c in r.tool_calls] == ["web_search", "calculator"]  # second depends on the first
    assert r.iterations == 3 and "1082.68 feet" in r.final_text


def test_step3_history_format():
    _, r = _run()
    assert [m["role"] for m in r.messages] == ["user", "assistant", "user", "assistant", "user", "assistant"]
    first_results = r.messages[2]["content"]
    assert first_results[0]["type"] == "tool_result" and first_results[0]["tool_use_id"] == r.tool_calls[0][0]


def test_every_request_resends_full_history_and_leaves_tool_choice_unset():
    client, _ = _run()
    assert [len(c["messages"]) for c in client.calls] == [1, 3, 5]
    assert all("tool_choice" not in c for c in client.calls)


def test_step6_safety_cap_logs_warning_and_flags(caplog):
    forced = MockClient(lambda kw: good.mock_model({**kw, "tool_choice": {"type": "any"}}))
    with caplog.at_level(logging.WARNING):
        r = good.run_agent(forced, good.QUESTION, max_iterations=4)
    assert r.hit_safety_cap and not r.complete
    assert "MAX_ITERATIONS" in caplog.text
    assert good.MAX_ITERATIONS == 20


def test_current_docs_stop_reasons_are_not_treated_as_done():
    for reason in good.INCOMPLETE_STOP_REASONS:
        r = good.run_agent(MockClient([message(text("partial"), stop_reason=reason)]), good.QUESTION)
        assert r.stop_reason == reason and not r.complete


def test_pause_turn_resends_and_continues():
    script = [message(text("working"), stop_reason="pause_turn"), message(text("done"))]
    r = good.run_agent(MockClient(script), good.QUESTION)
    assert r.complete and r.iterations == 2


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_content_type_check_quits_early():
    r = anti.trap1_content_type_check(MockClient(good.mock_model))
    assert r.tool_calls == [] and r.final_text == "Let me look that up." and r.stop_reason == "tool_use"


def test_trap2_cap_as_exit_cuts_off_work():
    r = anti.trap2_cap_as_primary_stop(MockClient(good.mock_model), cap=2)
    assert len(r.tool_calls) == 2 and r.stop_reason == "tool_use" and "feet" not in r.final_text


def test_trap3_phrase_parsing_wastes_iterations():
    client = MockClient(good.mock_model)
    r = anti.trap3_parse_completion_phrase(client, safety_cap=6)
    assert r.stop_reason == "cap" and len(client.calls) == 6  # the job needed 3


def test_trap4_tool_choice_any_never_finishes():
    client = MockClient(good.mock_model)
    r = anti.trap4_force_tool_choice_any(client, safety_cap=5)
    assert r.stop_reason == "cap" and r.final_text == "" and len(r.tool_calls) == 5


def test_practice_answer_is_stop_reason():
    assert good.PRACTICE["answer"] == "B"


def test_demos_run(capsys):
    good.main()
    anti.main()
    out = capsys.readouterr().out
    assert "stop_reason=end_turn" in out and "trap 4" in out
