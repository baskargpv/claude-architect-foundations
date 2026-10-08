from common.mock import MockClient
from domain1_agentic_architecture.task_1_6_task_decomposition.good_example import single_pass_review
from domain4_prompt_engineering.task_4_6_multi_pass_review import anti_pattern as anti
from domain4_prompt_engineering.task_4_6_multi_pass_review import good_example as good


def review_client():
    return MockClient(good.review_mock)


def test_step1_single_pass_shows_dilution():
    assert anti.trap2_single_pass(review_client())["artefacts"] > 0


def test_steps2_3_multi_pass_finds_local_and_cross_file_issues():
    findings = good.review_with_confidence(review_client())
    assert sum(f["kind"] == "api_contract" for f in findings) == 1
    assert all(0 <= f["confidence"] <= 1 for f in findings)


def test_step5_calibration_picks_threshold_from_verified_labels():
    labelled = [(0.92, True), (0.92, True), (0.85, False), (0.82, True), (0.72, True), (0.72, False)]
    assert good.calibrate(labelled) == 0.92


def test_verification_runs_in_a_separate_instance():
    verifier = MockClient(good.verify_mock)
    good.pipeline(review_client(), verifier)
    assert all(len(c["messages"]) == 1 and "[VERIFY]" in c["messages"][0]["content"] for c in verifier.calls)


def test_step4_calibrated_routing_keeps_false_positives_away_from_developers():
    r = good.pipeline(review_client(), MockClient(good.verify_mock))
    assert r["false_positives_to_developers"] == 0 and r["to_developers"] > 0 and r["to_humans"] > 0


def test_trap1_self_review_approves():
    assert anti.trap1_same_session_self_review()["issues_found"] == 0


def test_trap3_bigger_context_same_dilution():
    assert anti.trap3_bigger_context(review_client())["artefacts"] == anti.trap2_single_pass(review_client())["artefacts"]


def test_trap4_raw_confidence_sends_false_positives_to_developers():
    assert anti.trap4_raw_confidence_routing(review_client())["false_positives_to_developers"] == 2


def test_practice_answer():
    assert good.PRACTICE["answer"] == "B"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "calibrated threshold" in capsys.readouterr().out
