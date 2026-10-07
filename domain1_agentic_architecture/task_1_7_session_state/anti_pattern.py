"""Task 1.7 — four wrong ways to continue after files changed.

1. --resume anyway: the old auth.py read is still in history, so Claude recommends
   a fix that has already been applied.
2. The "naive fix": resume and ask it to re-read auth.py. The NEW content arrives, but
   the OLD tool result is still sitting in history and still steers the answer.
3. fork_session to escape stale context: the fork copies the same stale history.
4. Fresh start that re-explores the whole codebase: correct answer, wasted reads.
"""

from __future__ import annotations

from common.client import get_client, mode_banner
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent
from domain1_agentic_architecture.task_1_7_session_state.good_example import (
    QUESTION,
    READ_TOOL,
    STALE_MARKER,
    fork,
    make_reader,
    mock_model,
    previous_session,
    workspace_after_fix,
)


def resume_anyway(client, session, workspace, question=QUESTION) -> dict:
    reads: list = []
    result = run_agent(client, question, tools=READ_TOOL, execute=make_reader(workspace, reads), history=session.messages)
    return {"answer": result.final_text, "reads": reads, "messages": result.messages}


def resume_and_reread(client, session, workspace, question=QUESTION) -> dict:
    return resume_anyway(client, session, workspace, f"auth.py was modified - re-read auth.py first. {question}")


def fork_to_fix_staleness(session):
    return fork(session, f"{session.name}-fork")


def fresh_full_reexploration(client, workspace, question=QUESTION) -> dict:
    reads: list = []
    result = run_agent(client, f"Re-explore the whole codebase from scratch. {question}",
                       tools=READ_TOOL, execute=make_reader(workspace, reads))
    return {"answer": result.final_text, "reads": reads}


def holds_stale_read(messages) -> bool:
    return any(STALE_MARKER in str(m["content"]) for m in messages)


def main():
    print(mode_banner())
    ws = workspace_after_fix()
    r = resume_anyway(get_client(mock_model), previous_session(), ws)
    print(f"1) resume after change: {r['answer']}  <- recommends a fix already applied")
    r = resume_and_reread(get_client(mock_model), previous_session(), ws)
    print(f"2) resume + re-read: reads={r['reads']}, stale read still in history={holds_stale_read(r['messages'])}\n   answer: {r['answer']}")
    f = fork_to_fix_staleness(previous_session())
    print(f"3) fork: stale read copied into fork={holds_stale_read(f.messages)}")
    r = fresh_full_reexploration(get_client(mock_model), ws)
    print(f"4) full re-exploration: reads={r['reads']}  <- only auth.py changed")


if __name__ == "__main__":
    main()
