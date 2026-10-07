from common.mock import MockClient
from domain1_agentic_architecture.task_1_4_prerequisite_gates import anti_pattern as anti
from domain1_agentic_architecture.task_1_4_prerequisite_gates import good_example as good


def _request(cid):
    return f"I'm customer {cid}. My order arrived damaged, please refund $40."


def test_gate_blocks_refund_before_verification_then_allows_it():
    result, state = good.handle(MockClient(good.mock_model), _request("C-42"))
    assert [c[1] for c in result.tool_calls] == ["process_refund", "get_customer", "process_refund"]
    assert state.blocked == [("process_refund", "C-42")]
    assert state.refunds == [{"refund_id": "R-001", "customer_id": "C-42", "amount": 40.0}]


def test_gate_never_refunds_unverified_customer_and_escalates_with_full_handoff():
    result, state = good.handle(MockClient(good.mock_model), _request("C-99"))
    assert state.refunds == []
    assert len(state.handoffs) == 1
    handoff = state.handoffs[0]
    assert handoff.refund_amount == 40.0 and "unverified" in handoff.root_cause


def test_gate_is_independent_of_the_model():
    desk = good.SupportDesk()
    out = desk.execute("process_refund", {"customer_id": "C-42", "amount": 10, "reason": "x"})
    assert out["blocked"] and desk.state.refunds == []


def test_handoff_rejects_placeholders_with_field_specific_errors():
    out = good.SupportDesk().execute("escalate_to_human", anti.PLACEHOLDER_HANDOFF)
    assert out["is_error"]
    assert {f["field"] for f in out["fields"]} == {"conversation_summary", "root_cause", "recommended_action"}


def test_handoff_can_cover_multiple_bundled_concerns():
    payload = good.HandoffPayload(
        customer_id="C-42",
        conversation_summary="(1) return of damaged kettle; (2) duplicate charge on 3 Oct; (3) email address change",
        root_cause="(1) courier damage; (2) payment retry bug; (3) customer moved provider",
        refund_amount=40.0,
        recommended_action="(1) approve return; (2) reverse duplicate charge; (3) update email after ID check",
    )
    assert payload.conversation_summary.count("(") == 3


def test_anti_prompt_only_refunds_unverified_customer():
    result, state = good.handle(MockClient(good.mock_model), _request("C-99"), anti.PromptOnlySupportDesk())
    assert [c[1] for c in result.tool_calls] == ["process_refund"]
    assert state.refunds and state.refunds[0]["customer_id"] == "C-99"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "money moved" in capsys.readouterr().out
