"""Task 1.7 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-7-session-state-resumption

Trap 1  full re-exploration when only 3 files changed       -> correct, but wasteful
Trap 2  --resume after files were modified                  -> stale tool results skew the advice
        (the "naive fix" - resume + re-read - doesn't remove the stale results either)
Trap 3  confusing fork_session with --resume                 -> alternatives pile into one history
Trap 4  fork_session to handle stale context                 -> the fork inherits the same stale history
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from common.client import get_client, mode_banner
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent
from domain1_agentic_architecture.task_1_7_session_resumption.good_example import (
    QUESTION,
    READ_TOOL,
    SessionStore,
    analyse_codebase,
    apply_fixes,
    make_reader,
    make_workspace,
    mock_model,
    resume,
    stale_symptoms,
)


def setup(tmp: Path, client=None):
    ws, store = make_workspace(tmp / "ws"), SessionStore(tmp / "sessions")
    analyse_codebase(client or get_client(mock_model), ws, store)
    apply_fixes(ws)
    return ws, store


def trap1_full_reexploration(client, ws: Path) -> dict:
    reads: list = []
    result = run_agent(client, f"Re-analyse the entire codebase from scratch. {QUESTION}",
                       tools=READ_TOOL, execute=make_reader(ws, reads))
    return {"answer": result.final_text, "reads": reads}


def trap2_resume_after_modification(client, store: SessionStore, ws: Path) -> dict:
    return resume(client, store, "auth-review", ws)


def trap2b_resume_and_reread(client, store: SessionStore, ws: Path) -> dict:
    return resume(client, store, "auth-review", ws, f"re-read auth.ts, session.ts, middleware.ts first. {QUESTION}")


def trap3_resume_instead_of_fork(client, store: SessionStore, ws: Path) -> dict:
    """Wants to compare two approaches from one baseline - but resumes twice."""
    resume(client, store, "auth-review", ws, "Approach A: fix everything in one big PR.")
    resume(client, store, "auth-review", ws, "Approach B: one PR per file.")
    history = store.load("auth-review").messages
    return {"approach_b_history_contains_a": any("Approach A" in str(m["content"]) for m in history)}


def trap4_fork_to_fix_staleness(client, store: SessionStore, ws: Path) -> dict:
    store.fork("auth-review", "auth-review-fork")
    out = resume(client, store, "auth-review-fork", ws)
    return {**out, "fork_holds_old_reads": "password === stored" in str(store.load("auth-review-fork").messages)}


def main():
    print(mode_banner())
    with tempfile.TemporaryDirectory() as tmp:
        ws, store = setup(Path(tmp))
        r = trap1_full_reexploration(get_client(mock_model), ws)
        print(f"trap 1 full re-exploration : read {len(r['reads'])} files for 3 changes")
        r = trap2_resume_after_modification(get_client(mock_model), store, ws)
        print(f"trap 2 resume after change : stale recommendations for {stale_symptoms(r['answer'], ws)}")
    with tempfile.TemporaryDirectory() as tmp:
        ws, store = setup(Path(tmp))
        r = trap2b_resume_and_reread(get_client(mock_model), store, ws)
        print(f"trap 2b resume + re-read   : re-read {r['reads']}, still stale for {stale_symptoms(r['answer'], ws)}")
    with tempfile.TemporaryDirectory() as tmp:
        ws, store = setup(Path(tmp))
        print(f"trap 3 resume vs fork      : {trap3_resume_instead_of_fork(get_client(mock_model), store, ws)}")
    with tempfile.TemporaryDirectory() as tmp:
        ws, store = setup(Path(tmp))
        r = trap4_fork_to_fix_staleness(get_client(mock_model), store, ws)
        print(f"trap 4 fork for staleness  : fork holds old reads={r['fork_holds_old_reads']}, stale for {stale_symptoms(r['answer'], ws)}")


if __name__ == "__main__":
    main()
