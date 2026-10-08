import asyncio

from common.mock import MockClient
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent
from domain1_agentic_architecture.task_1_5_sdk_hooks import anti_pattern as anti
from domain1_agentic_architecture.task_1_5_sdk_hooks import good_example as good

N = good.mcp_name


# ---- build exercise --------------------------------------------------------------------------

def test_step1_real_mcp_server_exposes_tools_with_mismatched_formats():
    d = good.HookedMCPDispatcher(lambda s: {})  # no hooks: raw MCP output
    names = {t["name"] for t in d.tool_definitions()}
    assert {N("get_customer"), N("lookup_order"), N("check_shipping")} <= names
    raw = [d.execute(N(t), {"customer_id": "C-1"} if t == "get_customer" else {"order_id": "O-1"})
           for t in ("get_customer", "lookup_order", "check_shipping")]
    assert raw[0]["created"] == 1710489600 and raw[1]["placed"].endswith("Z") and raw[2]["shipped_on"] == "04/03/2024"


def test_step2_3_posttooluse_normalises_every_tool_to_one_schema():
    d = good.HookedMCPDispatcher()
    c = d.execute(N("get_customer"), {"customer_id": "C-1"})
    o = d.execute(N("lookup_order"), {"order_id": "O-1"})
    s = d.execute(N("check_shipping"), {"order_id": "O-1"})
    assert c["created"] == "2024-03-15T08:00:00Z" and o["placed"] == "2024-03-15T12:00:00Z"
    assert s["shipped_on"] == "2024-03-04T00:00:00Z"  # 4 March: DD/MM honoured
    assert (c["status"], o["status"], s["status"]) == ("active", "pending", "pending")
    assert c["money"] == {"amount": "1234.50", "currency": "GBP"}
    assert o["money"] == {"amount": "129.99", "currency": "USD"}
    assert s["money"] == {"amount": "12.50", "currency": "EUR"}


def test_step3_agent_queries_all_three_and_sees_normalised_data():
    d = good.HookedMCPDispatcher()
    r = run_agent(MockClient(good.mock_model), "Give me the full status of customer C-1001 and order O-77.",
                  tools=d.tool_definitions(), execute=d.execute)
    assert len(r.tool_calls) == 3 and "04/03/2024" not in r.final_text and "2024-03-04" in r.final_text


def test_step4_refund_threshold_denies_before_handler():
    d = good.HookedMCPDispatcher()
    out = d.execute(N("process_refund"), {"order_id": "O-1", "amount": 750})
    assert out["denied"] and "human" in out["error"]
    assert d.ledger.refunds == [] and ("handler", N("process_refund")) not in d.events
    assert d.execute(N("process_refund"), {"order_id": "O-1", "amount": 120})["status"] == "refunded"


def test_step5_6_aml_gate_uses_state_recorded_by_posttooluse():
    d = good.HookedMCPDispatcher()
    r = run_agent(MockClient(good.mock_model), "Transfer $1000 to ACC-CLEAN-9.", tools=d.tool_definitions(), execute=d.execute)
    assert [c[1] for c in r.tool_calls] == [N("transfer_funds"), N("aml_check"), N("transfer_funds")]
    assert d.ledger.transfers == [("ACC-CLEAN-9", 1000.0)]


def test_failed_aml_never_transfers():
    d = good.HookedMCPDispatcher()
    run_agent(MockClient(good.mock_model), "Transfer $1000 to ACC-FLAGGED-2.", tools=d.tool_definitions(), execute=d.execute)
    assert d.ledger.transfers == []


def test_discount_over_20_percent_waits_for_manager():
    d = good.HookedMCPDispatcher()
    assert d.execute(N("approve_discount"), {"order_id": "O-1", "percent": 30})["denied"]
    assert d.state.approval_queue == [("O-1", 30.0)] and d.ledger.discounts == []
    d.manager_approves("O-1", 30)
    assert d.execute(N("approve_discount"), {"order_id": "O-1", "percent": 30})["status"] == "applied"
    assert d.execute(N("approve_discount"), {"order_id": "O-2", "percent": 15})["status"] == "applied"


def test_hooks_use_agent_sdk_output_shape():
    hooks = good.build_hooks(good.SessionState())
    refund_hook = hooks["PreToolUse"][0][1][0]
    out = asyncio.run(refund_hook({"tool_input": {"amount": 900}}, None, None))
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_posttooluse_block_runs_after_money_moved():
    d = anti.trap1_post_tool_use_block()
    assert d.ledger.refunds == [("O-77", 750.0)]
    assert d.events.index(("handler", N("process_refund"))) < d.events.index(("PostToolUse", N("process_refund")))


def test_trap2_prompt_only_lets_a_flagged_transfer_through():
    assert anti.trap2_prompt_only_compliance()["unscreened_flagged_transfers"] == 1


def test_trap3_model_side_normalisation_is_inconsistent():
    reads = anti.trap3_model_side_normalisation()
    assert len({r["shipped_on"] for r in reads}) > 1 and "processed" in {r["status"] for r in reads}


def test_trap4_pre_hook_cannot_normalise():
    out = anti.trap4_wrong_hook_direction()
    assert out["shipped_on"] == "04/03/2024" and out["status"] == "P"


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "money already moved" in capsys.readouterr().out
