import pytest

from common.mock import MockClient
from domain1_agentic_architecture.task_1_6_task_decomposition import anti_pattern as anti
from domain1_agentic_architecture.task_1_6_task_decomposition import good_example as good

FILES = good.load_repo()


def _multi():
    client = MockClient(good.mock_model)
    return client, good.multi_pass_review(client, FILES)


# ---- build exercise --------------------------------------------------------------------------

def test_step1_loads_at_least_ten_files(tmp_path):
    assert len(FILES) == 12
    (tmp_path / "a.js").write_text("x")
    with pytest.raises(ValueError):
        good.load_repo(tmp_path)


def test_step2_single_pass_shows_depth_dropoff():
    single = good.single_pass_review(MockClient(good.mock_model), FILES)
    later = {i["file"] for i in single["issues"]} & {"10_profile.js", "11_reports.js", "12_admin.js"}
    assert later == set()


def test_step3_one_pass_per_file_with_structured_output():
    client, multi = _multi()
    local_calls = [c for c in client.calls if c["messages"][0]["content"].startswith("[LOCAL REVIEW]")]
    assert len(local_calls) == len(FILES)
    assert all(c["messages"][0]["content"].count("\n--- ") == 1 for c in local_calls)
    s = multi["per_file"][0]
    assert {"bug_count", "issues", "exports", "uses"} <= s.keys() and all("line" in i for i in s["issues"])


def test_step3_last_file_gets_same_depth_as_first():
    _, multi = _multi()
    files_with_issues = {i["file"] for i in multi["issues"]}
    assert {"03_search.js", "11_reports.js", "05_cart.js", "12_admin.js"} <= files_with_issues


def test_step4_integration_pass_finds_cross_file_issues():
    client, multi = _multi()
    kinds = {c["kind"] for c in multi["cross_file"]}
    assert kinds == {"api_contract", "inconsistent_pattern"}
    contract = next(c for c in multi["cross_file"] if c["kind"] == "api_contract")
    assert contract["files"] == ["01_users.js", "10_profile.js"]
    assert client.calls[-1]["messages"][0]["content"].startswith("[INTEGRATION REVIEW]")  # runs once, last


def test_step5_comparison():
    single = good.single_pass_review(MockClient(good.mock_model), FILES)
    _, multi = _multi()
    c = good.compare(single, multi, FILES)
    assert c["multi_total"] > c["single_total"] and c["multi_missed_files"] == []
    assert c["cross_file_found_by"] == "integration pass"


def test_step6_identical_code_inconsistently_judged_only_in_single_pass():
    single = good.single_pass_review(MockClient(good.mock_model), FILES)
    _, multi = _multi()
    foreach = next(a for a in good.dilution_artefacts(single, FILES) if a["kind"] == "inefficient_foreach")
    assert foreach == {"kind": "inefficient_foreach", "flagged_in": ["03_search.js"], "approved_in": ["11_reports.js"]}
    assert good.dilution_artefacts(multi, FILES) == []


def test_pattern_choice_follows_task_characteristics():
    assert good.choose_pattern(steps_known_upfront=True) == "fixed_pipeline"
    assert good.choose_pattern(steps_known_upfront=False) == "dynamic_decomposition"


def test_adaptive_plan_reprioritises_untested_dependency():
    plan = good.adaptive_test_plan(FILES)
    order = plan["order"]
    assert order.index("04_db.js") < order.index("06_orders.js") < order.index("09_invoice.js")
    assert any("depends on untested" in line for line in plan["log"])


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_sophistication_picks_wrong_pattern_for_code_review():
    assert anti.trap1_pattern_by_sophistication("code review") != good.choose_pattern(True)


@pytest.mark.parametrize("trap", [anti.trap2_bigger_model, anti.trap3_better_prompt])
def test_trap2_3_single_pass_variants_still_diluted(trap):
    r = trap(MockClient(good.mock_model), FILES)
    _, multi = _multi()
    assert len(r["issues"]) < len(multi["issues"]) and good.dilution_artefacts(r, FILES)


def test_trap4_fixed_plan_builds_tests_on_untested_dependencies():
    r = anti.trap4_fixed_pipeline_for_exploration(FILES)
    assert ("09_invoice.js", "06_orders.js") in r["tests_built_on_untested_dependencies"]


def test_trap5_batching_finds_local_issues_but_misses_cross_batch_contract():
    r = anti.trap5_batching_without_integration(MockClient(good.mock_model), FILES)
    _, multi = _multi()
    assert len(r["issues"]) == len(multi["issues"]) and r["cross_file"] == []


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "contract bug missed" in capsys.readouterr().out
