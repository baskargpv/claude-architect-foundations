from common.mock import MockClient
from domain4_prompt_engineering.task_4_2_few_shot import anti_pattern as anti
from domain4_prompt_engineering.task_4_2_few_shot import good_example as good


def client():
    return MockClient(good.mock_model)


def test_steps1_2_baseline_fails_on_narrative_documents():
    r = good.run(client(), good.INSTRUCTIONS)
    assert len(good.DOCS) == 10
    assert r["empty_by_structure"]["table"] == 0 and r["empty_by_structure"]["narrative"] >= 8


def test_step3_three_examples_each_with_reasoning():
    assert good.FEW_SHOT.count("Example (") == 3 and good.FEW_SHOT.count("Reasoning:") == 3


def test_step4_few_shot_cuts_empty_fields():
    before = good.run(client(), good.INSTRUCTIONS)
    after = good.run(client(), good.INSTRUCTIONS + good.FEW_SHOT)
    assert after["empty_fields"] == 1 < before["empty_fields"]
    assert after["results"]["n2"] == {"author": "Garcia", "year": 2018, "sample_size": 1200}


def test_step5_remaining_gap_is_absent_information():
    after = good.run(client(), good.INSTRUCTIONS + good.FEW_SHOT)
    assert good.remaining_issues(after)[0].startswith("n4: value genuinely absent")


def test_trap1_more_instructions_do_not_fix_it():
    assert anti.trap1_more_instructions(client())["empty_by_structure"]["narrative"] >= 8


def test_trap2_examples_without_reasoning_do_not_generalise():
    assert anti.trap2_examples_without_reasoning(client())["empty_by_structure"]["narrative"] >= 8


def test_trap3_confidence_filter_misses_root_cause():
    assert anti.trap3_confidence_threshold()["root_cause_addressed"] is False


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "few-shot" in capsys.readouterr().out
