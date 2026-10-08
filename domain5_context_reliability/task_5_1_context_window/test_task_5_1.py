from common.mock import MockClient
from domain5_context_reliability.task_5_1_context_window import anti_pattern as anti
from domain5_context_reliability.task_5_1_context_window import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_facts_extracted():
    facts = good.extract_case_facts(good.ORDER_LOOKUP, 247.83)
    assert facts == {"customerId": "C-5512", "orderId": "8891", "orderDate": "2026-03-03", "refundAmount": 247.83,
                     "status": "delivered", "itemDescription": "Espresso machine, model EX-200"}


def test_step2_facts_block_in_every_prompt():
    c = client()
    good.run_conversation(c)
    agent_calls = [k for k in c.calls if "system" in k]
    assert len(agent_calls) == 6 and all("247.83" in k["system"] for k in agent_calls)


def test_step3_trim_before_history():
    assert len(good.ORDER_LOOKUP) > 40 and list(good.trim(good.ORDER_LOOKUP)) == list(good.KEEP)


def test_step4_specifics_survive_summarisation():
    assert "$247.83" in good.run_conversation(client())[-1] and "#8891" in good.run_conversation(client())[-1]


def test_step5_key_findings_first_with_headers():
    out = good.aggregate({"A": "a", "B": "b"}, ["k1"])
    assert out.startswith("## Key Findings Summary") and "## A" in out and "## B" in out


def test_trap1_summary_destroys_specifics():
    assert "recent refund request" in anti.trap1_summarisation_only(client())


def test_trap2_instruction_does_not_fix_position():
    r = anti.trap2_attention_instruction()
    assert r["instruction_added"] and not r["key_finding_used"]


def test_trap3_untrimmed_costs_more():
    r = anti.trap3_untrimmed_results()
    assert r["chars_over_conversation_untrimmed"] > 5 * r["trimmed"]


def test_trap4_truncation_breaks_history():
    assert anti.trap4_truncate_history()["orphaned_tool_results"] == ["t1"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "B"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "Key Findings Summary" in capsys.readouterr().out
