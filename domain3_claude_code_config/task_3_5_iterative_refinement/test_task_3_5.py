import json

from common.mock import MockClient
from domain3_claude_code_config.task_3_5_iterative_refinement import anti_pattern as anti
from domain3_claude_code_config.task_3_5_iterative_refinement import good_example as good


def client():
    return MockClient(good.mock_model)


def distinct(outputs):
    return len({json.dumps(o) for o in outputs})


def test_step1_prose_only_varies_across_runs():
    assert distinct(good.runs(client(), good.TASK)) == 3


def test_step2_examples_make_output_consistent():
    out = good.runs(client(), good.with_examples(good.TASK))
    assert distinct(out) == 1 and out[0][0] == "+1-555-010-4477"
    assert 2 <= len(good.EXAMPLES) <= 3


def test_step3_tdd_feeds_back_failures_until_green():
    history = good.tdd_loop(client())
    assert [len(h["failures"]) for h in history] == [2, 0]
    assert all(f.startswith("Expected") for f in history[0]["failures"])


def test_step4_interview_returns_questions():
    qs = good.interview(client(), "telecom billing phone numbers")
    assert len(qs) == 3 and all(q.endswith("?") for q in qs)


def test_step5_interacting_issues_batched_independent_sequential():
    issues = [{"name": "a", "affects": ["b"]}, {"name": "b", "affects": []}, {"name": "c", "affects": []}]
    assert good.plan_feedback(issues) == [["a", "b"], ["c"]]


def test_trap1_precise_prose_still_inconsistent():
    assert anti.trap1_more_precise_prose(client()) > 1


def test_trap2_and_trap3():
    assert anti.trap2_sequential_for_interacting_issues()["fixes_redone"] > 0
    assert set(anti.trap3_wrong_technique()) == {"interview_when_target_known", "examples_when_target_unknown"}


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "1 distinct output" in capsys.readouterr().out
