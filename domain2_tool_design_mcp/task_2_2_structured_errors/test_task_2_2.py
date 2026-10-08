import pytest

from common.mcp_util import call
from domain2_tool_design_mcp.task_2_2_structured_errors import anti_pattern as anti
from domain2_tool_design_mcp.task_2_2_structured_errors import good_example as good


@pytest.mark.parametrize("args,category,retryable", [
    ({"email": "jane@example.com", "failure_mode": "transient"}, "transient", True),
    ({"email": "Bad Email"}, "validation", False),
    ({"email": "jane@example.com", "failure_mode": "business"}, "business", False),
    ({"email": "jane@example.com", "failure_mode": "permission"}, "permission", False),
])
def test_steps2_3_each_category_is_an_execution_error_with_metadata(args, category, retryable):
    r = call(good.build_server(), "lookup_customer", args)
    assert r.is_error
    assert r.structured_content == {"errorCategory": category, "isRetryable": retryable,
                                    "description": r.content[0].text}


def test_step4_empty_result_is_not_an_error():
    r = call(good.build_server(), "lookup_customer", {"email": "nobody@example.com"})
    assert r.is_error is False and r.structured_content == {"resultCount": 0, "results": []}


@pytest.mark.parametrize("email,mode,outcome,actions", [
    ("jane@example.com", "none", "found", []),
    ("nobody@example.com", "none", "no such customer", []),
    ("jane@example.com", "transient", "found", ["transient", "transient"]),
    (" Jane@Example.com", "none", "found", ["validation"]),
    ("jane@example.com", "business", "escalated", ["business"]),
    ("jane@example.com", "permission", "found", ["permission"]),
])
def test_step5_recovery_branches_on_category(email, mode, outcome, actions):
    r = good.lookup_with_recovery(good.build_server(), email, mode)
    assert r["outcome"] == outcome and r["actions"] == actions


def test_trap1_retrying_empty_result_wastes_calls_and_escalates():
    r = anti.trap1_retry_empty_result()
    assert r["calls"] == 4 and "escalated" in r["outcome"]


def test_trap2_generic_errors_force_blind_retries():
    assert all("still failing" in v for v in anti.trap2_generic_errors().values())


def test_trap3_business_errors_fail_every_time():
    assert anti.trap3_business_as_retryable()["all_failed"]


def test_trap4_resending_malformed_call_repeats_the_error():
    assert anti.trap4_validation_marked_retryable()["results"] == ["validation"] * 3


def test_trap5_abandons_a_fixable_task():
    assert anti.trap5_false_means_abandon()["outcome"] == "abandoned"
    assert good.lookup_with_recovery(good.build_server(), " Jane@Example.com")["outcome"] == "found"


def test_trap6_suppressed_timeout_looks_like_missing_customer():
    assert anti.trap6_silent_suppression()["coordinator_concludes"] == "customer does not exist"


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "escalated" in capsys.readouterr().out
