from common.mock import MockClient
from domain3_claude_code_config.task_3_4_plan_mode import anti_pattern as anti
from domain3_claude_code_config.task_3_4_plan_mode import good_example as good


def test_step5_framework_has_4_plan_and_3_direct_criteria_with_examples():
    assert len(good.PLAN_CRITERIA) >= 4 and len(good.DIRECT_CRITERIA) >= 3
    assert all(good.PLAN_CRITERIA.values()) and all(good.DIRECT_CRITERIA.values())


def test_modes_for_the_practice_tasks():
    assert good.choose_mode(good.Task("monolith", {"large_scale_restructure", "architectural_decision"})) == "plan"
    assert good.choose_mode(good.Task("npe", {"single_file_clear_cause"})) == "direct"
    assert good.choose_mode(good.Task("logging", {"multi_file_change"})) == "plan, then direct execution"


def test_plan_mode_is_a_switch_not_prose():
    assert not good.entered_plan_mode([], "please work in plan mode")
    assert good.entered_plan_mode(["--permission-mode", "plan"], "go")
    assert good.entered_plan_mode([], "/plan restructure auth")


def test_steps1_3_no_writes_before_approval_then_file_by_file():
    files = {"a.ts": "logger-v1", "b.ts": "logger-v1", "c.ts": "other"}
    r = good.plan_then_execute(files, "logger-v1", "logger-v2")
    assert r["plan"] == ["a.ts", "b.ts"] and "blocked" in r["write_before_approval"]
    assert r["written"] == ["a.ts", "b.ts"] and files["a.ts"] == "logger-v2"


def test_step4_explore_returns_only_a_summary():
    history = good.explore(MockClient(good.mock_model), "which files use logger v1?", [])
    assert history[-1]["content"].startswith("Explore summary: SUMMARY:") and len(history[-1]["content"]) < 120


def test_traps():
    assert anti.trap1_direct_for_architecture()["edits_to_unwind"] > 0
    assert anti.trap2_plan_for_clear_bug()["overhead_steps"] == 3
    assert anti.trap3_plan_or_direct_only()["plan_only_files_changed"] == 0
    assert anti.trap4_switch_late()["complexity_stated_upfront"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "plan, then direct execution" in capsys.readouterr().out
