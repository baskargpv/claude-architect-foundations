from common.mock import MockClient
from domain1_agentic_architecture.task_1_2_hub_and_spoke import anti_pattern as anti
from domain1_agentic_architecture.task_1_2_hub_and_spoke import good_example as good


def _good_run():
    return good.research(MockClient(good.mock_model))


def test_phase2_validation_adds_missing_category():
    run = _good_run()
    assert "games and interactive media" in run.subtopics
    assert len(run.subtopics) == 5  # breadth discovered, not capped at 4


def test_every_subagent_prompt_restates_goal_subtopic_format_and_prior():
    run = _good_run()
    for prompt in run.prompts:
        assert f"Research goal: {good.GOAL}" in prompt
        assert "Your subtopic: " in prompt
        assert "Output format: " in prompt
        assert "Prior findings" in prompt


def test_only_gaps_are_redelegated():
    run = _good_run()
    round1 = [t for r, t in run.delegations if r == 1]
    round2 = [t for r, t in run.delegations if r == 2]
    assert round1 == run.subtopics
    assert round2 == ["music"]  # the one thin result


def test_redelegation_carries_prior_findings():
    run = _good_run()
    music_retry = [p for p in run.prompts if "Your subtopic: music" in p][1]
    assert "AI affects music" in music_retry


def test_exit_on_coverage_not_cap():
    run = good.research(MockClient(good.mock_model), max_rounds=4)
    assert run.rounds == 2
    assert all(run.coverage.values())


def test_non_empty_is_not_substantive():
    assert not good.coverage_map({"t": [{"claim": "x", "evidence": "it does"}] * 3})["t"]


def test_subagent_calls_are_isolated_single_message_requests():
    client = MockClient(good.mock_model)
    good.research(client)
    assert all(len(call["messages"]) == 1 for call in client.calls)


def test_anti_exactly_n_merges_and_misses_categories():
    run = anti.research(MockClient(good.mock_model))
    assert run.subtopics == ["music", "visual art", "film and writing"]
    assert not any("games" in t for t in run.subtopics)


def test_anti_bare_prompts_and_full_redelegation():
    run = anti.research(MockClient(good.mock_model))
    assert all(good.GOAL not in p and "Output format" not in p for p in run.prompts)
    assert [t for r, t in run.delegations if r == 2] == run.subtopics
    assert not any(run.coverage.values())


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "round 2 delegated: ['music']" in capsys.readouterr().out
