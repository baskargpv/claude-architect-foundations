from domain5_context_reliability.task_5_3_error_propagation import anti_pattern as anti
from domain5_context_reliability.task_5_3_error_propagation import good_example as good


def test_step1_schema_has_the_four_elements():
    fields = good.SubagentResult.model_fields
    assert {"failureType", "attemptedAction", "partialResults", "alternativeApproaches", "shouldRetry"} <= fields.keys()


def test_step2_access_failure_vs_valid_empty():
    empty = good.search_with_recovery([good.Source("patents", [])], "q")
    failed = good.search_with_recovery([good.Source("journals", None, fails_times=-1)], "q")
    assert empty.status == "success" and empty.results == [] and not empty.shouldRetry
    assert failed.status == "partial_failure" and failed.shouldRetry and failed.failureType == "transient"


def test_step3_transient_failure_recovered_locally():
    r = good.search_with_recovery([good.Source("journals", ["x"], fails_times=2)], "q")
    assert r.status == "success" and r.results == ["journals: x"]


def test_step3_partial_results_kept_on_failure():
    r = good.search_with_recovery([good.Source("news", ["a"]), good.Source("journals", None, fails_times=-1)], "q")
    assert r.partialResults == ["news: a"] and "journals" in r.attemptedAction and r.alternativeApproaches


def test_steps4_5_coordinator_and_coverage_section():
    plan = good.coordinate(good.demo_results())
    assert plan["coverage"]["solar"][0] == "well-supported"
    assert plan["coverage"]["geothermal"][0] == "limited"
    assert plan["coverage"]["space solar"] == ("unavailable", "searched successfully - no sources exist")
    section = good.coverage_section(plan["coverage"])
    assert section.startswith("## Coverage") and "geothermal: limited (" in section


def test_trap1_timeout_hidden_as_success():
    assert anti.trap1_silent_suppression()["results"] == []


def test_trap2_termination_discards_completed_work():
    assert anti.trap2_terminate_pipeline()["results_kept"] == {}


def test_trap3_generic_status_has_no_context():
    assert set(anti.trap3_generic_status()) == {"status", "message"}


def test_trap4_retrying_empty_is_pointless():
    assert anti.trap4_retry_valid_empty()["all_empty"]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "## Coverage" in capsys.readouterr().out
