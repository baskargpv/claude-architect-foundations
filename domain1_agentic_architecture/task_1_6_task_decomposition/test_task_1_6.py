from common.mock import MockClient
from domain1_agentic_architecture.task_1_6_task_decomposition import anti_pattern as anti
from domain1_agentic_architecture.task_1_6_task_decomposition import good_example as good


def _cross(findings):
    return [f for f in findings if len(f["files"]) > 1]


def test_fixed_pipeline_is_n_local_passes_plus_one_integration_pass():
    client = MockClient(good.mock_model)
    good.review_pipeline(client)
    prompts = [c["messages"][0]["content"] for c in client.calls]
    assert sum(p.startswith("[LOCAL REVIEW]") for p in prompts) == len(good.FILES)
    assert sum(p.startswith("[INTEGRATION REVIEW]") for p in prompts) == 1
    assert prompts[-1].startswith("[INTEGRATION REVIEW]")  # runs once, after all local passes


def test_each_local_pass_sees_exactly_one_file():
    client = MockClient(good.mock_model)
    good.review_pipeline(client)
    for call in client.calls[:-1]:
        assert call["messages"][0]["content"].count("--- ") == 1


def test_pipeline_finds_every_local_issue_and_the_cross_file_contract_bug():
    result = good.review_pipeline(MockClient(good.mock_model))
    assert len(result["local"]) == len(good.PLANTED)
    assert result["cross_file"] == [good.CROSS_FILE]


def test_dynamic_investigation_follows_unplanned_lead_to_root_cause():
    trace = good.investigate(MockClient(good.mock_model), good.SYMPTOM)
    assert trace["steps"] == ["app logs", "payments-service config", "payments-service deploy history"]
    assert "50 to 2" in trace["root_cause"]


def test_anti_single_pass_misses_later_files_and_cross_file_bug():
    findings = anti.single_pass_review(MockClient(good.mock_model))
    assert len(findings) < len(good.PLANTED)
    assert not _cross(findings)


def test_anti_batching_without_integration_misses_cross_batch_bug():
    findings = anti.batched_review(MockClient(good.mock_model))
    assert len(findings) == len(good.PLANTED)  # within-batch dilution solved...
    assert not _cross(findings)  # ...cross-batch issue still invisible


def test_batching_would_catch_it_only_if_both_files_shared_a_batch():
    reordered = {p: good.FILES[p] for p in ["api/users.py", "web/client.py", "auth/session.py", "billing/invoice.py", "utils/fmt.py"]}
    assert _cross(anti.batched_review(MockClient(good.mock_model), reordered))  # luck, not architecture


def test_anti_fixed_pipeline_never_reaches_root_cause():
    inv = anti.fixed_pipeline_investigation()
    assert "payments-service config" not in inv["steps"]
    assert inv["root_cause"] is None


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "CROSS" in capsys.readouterr().out
