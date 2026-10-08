import anthropic

from common.mock import MockClient
from domain2_tool_design_mcp.task_2_3_tool_distribution import anti_pattern as anti
from domain2_tool_design_mcp.task_2_3_tool_distribution import good_example as good


def test_step1_every_role_has_4_to_5_tools():
    assert good.audit_toolsets(good.AGENT_TOOLS) == []
    assert all(4 <= len(t) <= 5 for a, t in good.AGENT_TOOLS.items() if a != "coordinator")
    assert "verify_fact" in good.AGENT_TOOLS["synthesis"]


def test_step2_verify_fact_handles_simple_and_rejects_complex():
    assert good.verify_fact("solar efficiency 2025 was 24.1%")["verified"]
    assert good.verify_fact("compare the two figures")["is_error"]
    assert good.verify_fact("offshore wind growth", sources=["a", "b"])["is_error"]


def test_step3_extract_metadata_forced_first_then_auto():
    client = MockClient(good.mock_model)
    r = good.run_document_agent(client, "https://docs.example.com/q3.pdf")
    assert r["first_call"] == "extract_metadata" and r["mode"] == "forced"
    assert client.calls[0]["tool_choice"] == {"type": "tool", "name": "extract_metadata"}
    assert all("tool_choice" not in c for c in client.calls[1:])  # back to auto


class ForcedToolChoiceRejected(anthropic.BadRequestError):
    """What claude-sonnet-5-5 returns for forced tool_choice (a 400), without needing an HTTP response."""

    def __init__(self):
        Exception.__init__(self, "tool_choice: type 'tool' and 'any' are not supported for this model.")


def test_step3_falls_back_when_api_rejects_forced_tool_choice():
    def rejecting(kwargs):
        if "tool_choice" in kwargs:
            raise ForcedToolChoiceRejected()
        return good.mock_model(kwargs)
    r = good.run_document_agent(MockClient(rejecting), "https://docs.example.com/q3.pdf")
    assert r["mode"] == "auto+instruction" and r["first_call"] == "extract_metadata"


def test_step4_load_document_validates_urls():
    assert good.load_document("https://docs.example.com/reports/q3.pdf")["text"]
    assert good.load_document("http://169.254.169.254/latest/meta-data")["is_error"]
    assert good.load_document("https://evil.example.net/x.pdf")["is_error"]


def test_step5_no_agent_calls_outside_its_set():
    results = good.end_to_end(MockClient(good.mock_model))
    assert all(r["violations"] == [] for r in results)
    guard = good.ToolGuard("synthesis")
    assert guard.execute("search_web", {})["is_error"] and guard.violations == ["search_web"]


def test_trap1_coordinator_routing_multiplies_round_trips():
    r = anti.trap1_route_everything_via_coordinator()
    assert r["round_trips_all_via_coordinator"] > 5 * r["round_trips_with_scoped_verify_fact"]


def test_trap2_auto_may_return_text_instead_of_structure():
    assert anti.trap2_auto_when_structure_required(MockClient(anti.auto_mock))["got_tool_call"] is False


def test_trap3_18_tools_flagged():
    assert anti.trap3_one_agent_18_tools() == ["do_everything_agent has 18 tools (max 5)"]


def test_trap4_fetch_url_allows_misuse():
    assert anti.trap4_generic_fetch_url()["status"] == 200


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "violations=[]" in capsys.readouterr().out
