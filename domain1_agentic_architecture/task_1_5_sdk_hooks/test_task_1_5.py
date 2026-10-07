from common.mock import MockClient
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent
from domain1_agentic_architecture.task_1_5_sdk_hooks import anti_pattern as anti
from domain1_agentic_architecture.task_1_5_sdk_hooks import good_example as good


def test_pretooluse_denies_large_refund_before_handler_runs():
    d = good.build()
    out = d.execute("process_refund", {"order_id": "O-3", "amount": 750.0})
    assert out["denied"] and "human approval" in out["error"]
    assert d.backend.ledger.refunds == []
    assert ("handler", "process_refund") not in d.events


def test_refund_under_limit_goes_through():
    d = good.build()
    d.execute("process_refund", {"order_id": "O-1", "amount": 120.0})
    assert d.backend.ledger.refunds == [("O-1", 120.0)]


def test_aml_prerequisite_gate_uses_state_recorded_by_posttooluse():
    d = good.build()
    assert d.execute("transfer_funds", {"account": "ACC-CLEAN", "amount": 1000})["denied"]
    d.execute("aml_check", {"account": "ACC-FLAGGED"})
    assert d.execute("transfer_funds", {"account": "ACC-FLAGGED", "amount": 1000})["denied"]
    d.execute("aml_check", {"account": "ACC-CLEAN"})
    assert d.execute("transfer_funds", {"account": "ACC-CLEAN", "amount": 1000})["status"] == "sent"
    assert d.backend.ledger.transfers == [("ACC-CLEAN", 1000)]


def test_posttooluse_normalises_heterogeneous_formats():
    d = good.build()
    seen = {oid: d.execute("lookup_order", {"order_id": oid}) for oid in good.ORDERS}
    assert seen["O-1"]["placed_date"] == "2024-06-01"  # unix 1717200000
    assert seen["O-2"]["placed_date"] == "2024-06-03"  # DD/MM, not 6 March
    assert seen["O-3"]["placed_date"] == "2024-06-05"
    assert [s["status"] for s in seen.values()] == ["pending", "processing", "shipped"]


def test_hook_callbacks_use_agent_sdk_output_shape():
    import asyncio

    hooks = good.build_hooks(good.SessionState())
    refund_limit = hooks["PreToolUse"][0][1][0]
    out = asyncio.run(refund_limit({"tool_input": {"amount": 900}}, None, None))
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_agent_sees_denial_and_no_money_moves():
    d = good.build()
    result = run_agent(MockClient(good.mock_model), "Refund my order O-3 in full.", tools=good.TOOLS, execute=d.execute)
    assert [c[1] for c in result.tool_calls] == ["lookup_order", "process_refund"]
    assert d.backend.ledger.refunds == []
    assert "approval" in result.final_text


def test_anti_posttooluse_block_is_too_late():
    d = good.build(anti.build_post_blocking_hooks)
    out = d.execute("process_refund", {"order_id": "O-3", "amount": 750.0})
    assert d.backend.ledger.refunds == [("O-3", 750.0)]  # money already moved
    assert "exceeds" in out["hook_feedback"]
    assert d.events.index(("handler", "process_refund")) < d.events.index(("PostToolUse", "process_refund"))


def test_anti_without_normaliser_model_sees_ambiguous_raw_data():
    d = good.build(anti.build_post_blocking_hooks)
    assert d.execute("lookup_order", {"order_id": "O-2"})["placed"] == "03/06/2024"
    assert d.execute("lookup_order", {"order_id": "O-1"})["status"] == "P"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "already moved" in capsys.readouterr().out
