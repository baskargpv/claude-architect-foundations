from domain4_prompt_engineering.task_4_5_batch_processing import anti_pattern as anti
from domain4_prompt_engineering.task_4_5_batch_processing import good_example as good


def test_step1_blocking_is_synchronous():
    assert good.classify(True).startswith("synchronous") and good.classify(False).startswith("batch")


def test_step2_twenty_requests_with_unique_custom_ids():
    reqs = good.build_requests(good.DOCS)
    assert len(reqs) == 20 and len({r["custom_id"] for r in reqs}) == 20
    assert {"model", "max_tokens", "messages"} <= reqs[0]["params"].keys()


def test_step3_only_failures_resubmitted_with_changes_and_all_succeed():
    r = good.process_all(good.batch_client(), good.DOCS)
    assert sorted(r["first_pass_failed"]) == ["doc-07", "doc-13", "doc-18"]  # expired counts as failed
    assert r["resubmitted"] == 3 and r["succeeded"] == 20


def test_retry_requests_modify_params():
    original = {r["custom_id"]: r for r in good.build_requests(good.DOCS)}
    retry = good.retry_requests(["doc-07"], original)
    assert retry[0]["params"]["max_tokens"] == 2048


def test_step4_cadence_must_be_shorter_than_buffer():
    assert not good.cadence_ok(6, 30) and good.cadence_ok(4, 30)
    assert good.recommended_cadence(30) == 4


def test_step5_sample_tuning_math():
    assert good.expected_retries(1000, 0.9) == 100 and good.expected_retries(1000, 0.6) == 400


def test_trap1_blocking_workflows_would_wait():
    assert "pre-merge security check" in anti.trap1_everything_to_batch()["blocking_workflows_now_waiting_up_to_24h"]


def test_trap2_typical_timing_hides_worst_case_breach():
    r = anti.trap2_design_for_typical_time()
    assert r["looks_fine_typically"] and not r["meets_sla_in_worst_case"]


def test_trap3_batch_item_stops_at_tool_use():
    assert anti.trap3_multi_turn_tools_in_batch()["stop_reason"] == "tool_use"


def test_practice_answer():
    assert good.PRACTICE["answer"] == "A"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "recommended every 4h" in capsys.readouterr().out
