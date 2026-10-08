import pytest

from common.mock import MockClient
from domain5_context_reliability.task_5_4_context_degradation import anti_pattern as anti
from domain5_context_reliability.task_5_4_context_degradation import good_example as good


def client():
    return MockClient(good.mock_model)


@pytest.fixture
def run(tmp_path):
    return good.explore(client(), tmp_path)


def test_step1_subagents_return_structured_summaries_only():
    out = good.run_subagent(client(), good.TASKS["refund_flow"])
    assert out["findings"] and "read file" not in str(out)


def test_step2_scratchpad_holds_specifics(run):
    assert "OrderRepository.findById (src/repos/order.ts, cached)" in run["scratchpad"]


def test_step3_phase2_prompt_is_seeded_with_phase1_summary(run):
    assert run["phase2_prompt"].startswith("# Key findings") and "[PHASE 2]" in run["phase2_prompt"]


def test_step4_manifest_fields_and_resume(run):
    m = run["manifest"]
    assert set(m) == {"sessionId", "phase", "exploredPaths", "keyFindings", "nextSteps"}
    assert m["exploredPaths"] == list(good.TASKS) and m["nextSteps"] == []


def test_step5_specific_names_persist_only_with_scratchpad(run):
    assert "src/repos/order.ts" in good.answer_later_question(client(), run["scratchpad"])
    assert "typical repository pattern" in good.answer_later_question(client(), "(verbose history)")


def test_trap1_bigger_window_still_degrades():
    assert "typical" in anti.trap1_bigger_window(client())


def test_trap2_inline_exploration_floods_main_context(run):
    assert anti.trap2_inline_exploration(client())["main_context_chars"] > 10 * len(run["scratchpad"])


def test_trap3_and_trap4():
    assert anti.trap3_restart_without_saving()["findings_lost"] == 1
    assert anti.trap4_compact_only_at_limit()["turns_spent_degraded_before_compacting"] > 0


def test_practice_answer():
    assert good.PRACTICE["answer"] == "B"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "Key findings" in capsys.readouterr().out
