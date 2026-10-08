import json

from common.mock import MockClient
from domain3_claude_code_config.task_3_6_ci_cd import anti_pattern as anti
from domain3_claude_code_config.task_3_6_ci_cd import good_example as good


def client():
    return MockClient(good.mock_model)


def test_step1_command_is_print_mode_with_json_schema():
    argv = good.ci_command("Review")
    assert argv[:2] == ["claude", "-p"] and "--output-format" in argv and "--json-schema" in argv
    assert json.loads(argv[argv.index("--json-schema") + 1]) == good.FINDINGS_SCHEMA


def test_step1_generated_files(tmp_path):
    paths = good.write_ci_files(tmp_path)
    assert "claude -p" in paths["script"].read_text() and "jq '.structured_output" in paths["script"].read_text()
    assert good.validate_workflow(paths["workflow"].read_text()) == []
    assert "Critical:" in paths["claude_md"].read_text()


def test_workflow_validation_catches_mistakes():
    bad = good.yaml.safe_dump({"jobs": {"review": {"steps": [
        {"uses": "anthropics/claude-code-action@v1", "with": {"anthropic_api_key": "sk-literal"}}]}}})
    problems = good.validate_workflow(bad)
    assert len(problems) == 3


def test_steps2_3_envelope_and_inline_comments():
    env = good.review(client(), good.generate(client(), "login handler"))
    assert {"result", "session_id", "structured_output"} <= env.keys()
    assert good.post_inline_comments(env) == ["auth.ts:2 [critical] eval() on request input",
                                              "auth.ts:3 [major] timing-unsafe password comparison"]


def test_step5_review_is_an_independent_invocation():
    c = client()
    good.review(c, good.generate(c, "login handler"))
    review_call = c.calls[-1]
    assert len(review_call["messages"]) == 1 and "[GENERATE]" not in review_call["messages"][0]["content"]


def test_step6_only_new_findings_are_reported(tmp_path):
    code = good.generate(client(), "x")
    v2 = code + "\n// unrelated change"
    runs = good.incremental_runs(client(), [code, v2], tmp_path / "findings.json")
    assert [len(r) for r in runs] == [2, 0]


def test_batch_vs_realtime():
    assert good.choose_api(blocking=True).startswith("synchronous")
    assert "Batches" in good.choose_api(blocking=False)


def test_trap1_only_p_stops_the_hang():
    r = anti.trap1_ci_hang_fixes()
    assert r["-p"] == "finishes" and all(v == "hangs" for k, v in r.items() if k != "-p")


def test_trap2_independent_review_finds_what_self_review_approves():
    r = anti.trap2_same_session_self_review(client())
    assert "Looks good" in r["same_session"] and r["independent_review_findings"] == 2


def test_trap3_batch_has_no_sla():
    assert anti.trap3_batch_for_pre_merge()["latency_sla"] is None


def test_trap4_without_prior_findings_every_push_repeats_comments():
    assert anti.trap4_no_prior_findings(client()) == [2, 2, 2]


def test_practice_answer():
    assert good.PRACTICE["answer"] == "D"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "comments per push" in capsys.readouterr().out
