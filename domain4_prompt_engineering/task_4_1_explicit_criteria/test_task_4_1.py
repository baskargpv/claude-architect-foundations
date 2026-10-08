from common.mock import MockClient
from domain4_prompt_engineering.task_4_1_explicit_criteria import anti_pattern as anti
from domain4_prompt_engineering.task_4_1_explicit_criteria import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_vague_baseline_over_flags_and_drifts():
    r = good.evaluate(client(), good.VAGUE_PROMPT)
    assert r["fp_rate"] >= 0.4 and not r["consistent_severity"]


def test_steps2_3_explicit_prompt_has_categories_trigger_and_examples():
    p = good.EXPLICIT_PROMPT
    assert "REPORT:" in p and "SKIP:" in p and "contradicts" in p and p.count("example:") >= 3


def test_step4_explicit_criteria_remove_false_positives_and_stabilise_severity():
    r = good.evaluate(client(), good.EXPLICIT_PROMPT)
    assert r["fp_rate"] == 0 and r["flagged"] == 3 and r["consistent_severity"]


def test_step5_disable_categories_over_25_percent():
    assert good.active_categories({"bug": 0.0, "comment_mismatch": 0.5, "style": 1.0}) == {
        "active": ["bug"], "disabled_until_refined": ["comment_mismatch", "style"]}


def test_trap1_vague_wording_does_not_help():
    assert anti.trap1_vague_instructions(client())["fp_rate"] >= 0.4


def test_trap2_confidence_filter_keeps_fps_and_drops_a_real_bug():
    r = anti.trap2_confidence_threshold(client())
    assert r["kept_false_positives"] >= 1 and r["dropped_real_bug"]


def test_trap3_one_noisy_category_kills_trust_in_all():
    assert anti.trap3_keep_noisy_category({"security": 0.0, "docs": 0.4})["developers_read_findings"] is False


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "disabled_until_refined" in capsys.readouterr().out
