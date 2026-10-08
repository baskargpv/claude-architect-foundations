import pytest

from common.mock import MockClient
from domain5_context_reliability.task_5_2_escalation import anti_pattern as anti
from domain5_context_reliability.task_5_2_escalation import good_example as good


def test_steps1_2_prompt_has_triggers_anti_patterns_and_examples():
    p = good.SYSTEM_PROMPT
    assert "explicitly asks for a human" in p and "SILENT" in p and "genuine attempt" in p
    assert "Never escalate because the customer sounds upset" in p and p.count("Example:") == 3


def test_step3_ambiguous_match_never_resolves_to_a_record():
    r = good.match_customer("John Smith")
    assert r["customer"] is None and "3 accounts" in r["ask"]
    assert good.match_customer("John Smith", "jsmith@example.net")["customer"]["id"] == "C-2"


@pytest.mark.parametrize("scenario,action", [("frustrated_simple", "resolve"), ("calm_policy_gap", "escalate"),
                                             ("explicit_human", "escalate"), ("ambiguous_match", "ask_identifier")])
def test_step4_scenarios(scenario, action):
    msg, ctx = good.SCENARIOS[scenario]
    assert good.decide(MockClient(good.mock_model), msg, ctx)["action"] == action


def test_step5_explicit_request_escalates_in_first_response_with_no_lookups():
    c = MockClient(good.mock_model)
    r = good.decide(c, *good.SCENARIOS["explicit_human"])
    assert r["action"] == "escalate" and len(c.calls) == 1 and "tools" not in c.calls[0]


def test_trap1_sentiment_escalates_simple_case():
    assert anti.trap1_sentiment()["frustrated_simple"] == "escalate"


def test_trap2_confidence_is_backwards():
    assert anti.trap2_confidence_router() == {"frustrated_simple": "escalate", "calm_policy_gap": "resolve"}


def test_trap3_investigating_delays_explicit_request():
    assert anti.trap3_investigate_first()["first_response_escalates"] is False


def test_trap4_recency_heuristic_picks_a_record():
    assert anti.trap4_pick_most_recent()["picked"] == "C-2"


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "ask_identifier" in capsys.readouterr().out
