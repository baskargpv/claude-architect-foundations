import pytest

from common.mock import MockClient
from domain1_agentic_architecture.task_1_7_session_resumption import anti_pattern as anti
from domain1_agentic_architecture.task_1_7_session_resumption import good_example as good


@pytest.fixture
def env(tmp_path):
    ws, store = good.make_workspace(tmp_path / "ws"), good.SessionStore(tmp_path / "sessions")
    session = good.analyse_codebase(MockClient(good.mock_model), ws, store)
    return ws, store, session


def client():
    return MockClient(good.mock_model)


# ---- build exercise --------------------------------------------------------------------------

def test_step1_named_session_reads_all_ten_files_and_persists(env):
    ws, store, session = env
    assert len(session.file_hashes) == 10 and len(session.findings) == 6
    assert store.load("auth-review").name == "auth-review"
    with pytest.raises(good.SessionNotFound):  # --resume only resumes sessions that exist
        store.load("never-created")


def test_step2_summary_is_conclusions_only(env):
    _, _, session = env
    summary = good.structured_summary(session)
    assert "auth.ts: issues: timing-unsafe password comparison (high)" in summary
    assert "password === stored" not in summary  # no raw tool output


def test_step3_three_files_changed(env):
    ws, _, session = env
    good.apply_fixes(ws)
    assert good.changed_since(session, ws) == ["auth.ts", "middleware.ts", "session.ts"]


def test_step4_resume_after_change_shows_stale_symptoms(env):
    ws, store, _ = env
    good.apply_fixes(ws)
    out = good.resume(client(), store, "auth-review", ws)
    assert good.stale_symptoms(out["answer"], ws) == ["auth.ts", "middleware.ts", "session.ts"]
    assert len(store.load("auth-review").messages) > 3  # resume appended to the same session


def test_step5_fresh_start_rereads_only_changed_files(env):
    ws, store, session = env
    good.apply_fixes(ws)
    out = good.fresh_start(client(), store, session, ws)
    assert sorted(out["reads"]) == ["auth.ts", "middleware.ts", "session.ts"]
    assert "password === stored" not in out["prompt"]
    assert good.recommended_files(out["answer"]) == {"logger.ts", "payments.ts", "users.ts"}


def test_step6_comparison_favours_fresh_start(env):
    ws, store, session = env
    good.apply_fixes(ws)
    resumed = good.resume(client(), store, "auth-review", ws)
    fresh = good.fresh_start(client(), store, store.load("auth-review"), ws)
    c = good.compare_sessions(resumed, fresh, ws)
    assert c["resumed_stale"] and c["fresh_stale"] == []


def test_resume_is_right_when_nothing_changed(env):
    ws, store, session = env
    assert good.choose_strategy(files_changed=len(good.changed_since(session, ws))) == "resume"
    out = good.resume(client(), store, "auth-review", ws)
    assert good.stale_symptoms(out["answer"], ws) == []


def test_fork_leaves_original_untouched(env):
    ws, store, _ = env
    n = len(store.load("auth-review").messages)
    store.fork("auth-review", "alt")
    good.resume(client(), store, "alt", ws, "Explore a documentation-first strategy.")
    assert len(store.load("auth-review").messages) == n and store.load("alt").parent == "auth-review"


@pytest.mark.parametrize("scenario,kwargs,expected", good.DECISION_MATRIX)
def test_decision_matrix(scenario, kwargs, expected):
    assert good.choose_strategy(**kwargs) == expected


# ---- exam traps ------------------------------------------------------------------------------

def test_trap1_full_reexploration_reads_everything(tmp_path):
    ws, _ = anti.setup(tmp_path, client())
    r = anti.trap1_full_reexploration(client(), ws)
    assert len(r["reads"]) == 10 and good.stale_symptoms(r["answer"], ws) == []


def test_trap2_resume_and_naive_reread_both_stay_stale(tmp_path):
    ws, store = anti.setup(tmp_path, client())
    r = anti.trap2b_resume_and_reread(client(), store, ws)
    assert sorted(r["reads"]) == ["auth.ts", "middleware.ts", "session.ts"]  # new content WAS read...
    assert good.stale_symptoms(r["answer"], ws)  # ...old results still in history


def test_trap3_resume_mixes_alternatives(tmp_path):
    ws, store = anti.setup(tmp_path, client())
    assert anti.trap3_resume_instead_of_fork(client(), store, ws)["approach_b_history_contains_a"]


def test_trap4_fork_inherits_stale_history(tmp_path):
    ws, store = anti.setup(tmp_path, client())
    r = anti.trap4_fork_to_fix_staleness(client(), store, ws)
    assert r["fork_holds_old_reads"] and good.stale_symptoms(r["answer"], ws)


def test_practice_answer():
    assert good.PRACTICE["answer"] == "C"


def test_demos_run(capsys):
    good.main()
    anti.main()
    assert "fork holds old reads=True" in capsys.readouterr().out
