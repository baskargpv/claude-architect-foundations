from common.mock import MockClient
from domain1_agentic_architecture.task_1_7_session_state import anti_pattern as anti
from domain1_agentic_architecture.task_1_7_session_state import good_example as good

UNCHANGED = {"auth.py": good.OLD_AUTH, "db.py": good.DB, "utils.py": good.UTILS}


def test_strategy_matrix():
    s = good.previous_session()
    assert good.choose_strategy(s, UNCHANGED) == "resume"
    assert good.choose_strategy(s, UNCHANGED, "explore_alternatives") == "fork"
    assert good.choose_strategy(s, good.workspace_after_fix()) == "fresh"
    # files changed: fresh even when the intent is to explore alternatives (a fork would inherit stale reads)
    assert good.choose_strategy(s, good.workspace_after_fix(), "explore_alternatives") == "fresh"


def test_fresh_prompt_has_conclusions_and_changed_files_but_no_raw_tool_output():
    prompt = good.build_fresh_prompt(good.previous_session(), good.workspace_after_fix(), good.QUESTION)
    assert good.OLD_AUTH not in prompt and "pw == stored" not in prompt
    assert "Files changed since last session: auth.py" in prompt
    assert "db.py: queries are parameterised - OK" in prompt


def test_fresh_start_rereads_only_changed_files_and_answers_correctly():
    client = MockClient(good.mock_model)
    out = good.continue_work(client, good.previous_session(), good.workspace_after_fix(), good.QUESTION)
    assert out["strategy"] == "fresh"
    assert out["reads"] == ["auth.py"]
    assert "already uses hmac.compare_digest" in out["answer"]
    assert not any("pw == stored" in str(m["content"]) for call in client.calls for m in call["messages"])


def test_fork_branches_and_leaves_original_untouched():
    original = good.previous_session()
    n = len(original.messages)
    out = good.continue_work(MockClient(good.mock_model), original, UNCHANGED, "alt fix?", "explore_alternatives")
    assert out["strategy"] == "fork"
    assert len(original.messages) == n
    assert len(out["session"].messages) > n and out["session"].parent == "auth-review"


def test_resume_appends_to_same_session():
    s = good.previous_session()
    n = len(s.messages)
    out = good.continue_work(MockClient(good.mock_model), s, UNCHANGED, good.QUESTION)
    assert out["strategy"] == "resume" and out["session"] is s and len(s.messages) > n


def test_anti_resume_after_change_recommends_applied_fix():
    r = anti.resume_anyway(MockClient(good.mock_model), good.previous_session(), good.workspace_after_fix())
    assert "Replace == with hmac.compare_digest" in r["answer"]


def test_anti_reread_does_not_remove_stale_result():
    r = anti.resume_and_reread(MockClient(good.mock_model), good.previous_session(), good.workspace_after_fix())
    assert r["reads"] == ["auth.py"]  # the new content WAS read...
    assert anti.holds_stale_read(r["messages"])  # ...but the old read is still in history
    assert "Replace == with hmac.compare_digest" in r["answer"]


def test_anti_fork_inherits_stale_history():
    assert anti.holds_stale_read(anti.fork_to_fix_staleness(good.previous_session()).messages)


def test_anti_full_reexploration_wastes_reads():
    r = anti.fresh_full_reexploration(MockClient(good.mock_model), good.workspace_after_fix())
    assert r["reads"] == ["auth.py", "db.py", "utils.py"]


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "strategy=fresh reads=['auth.py']" in capsys.readouterr().out
