"""Task 1.7 — pick resume / fork / fresh start from what's still TRUE.

    --resume <name>   prior context still valid (no files changed)   -> append to the same session
    fork_session      divergent exploration from a valid baseline    -> branch; original untouched
    fresh + summary   files changed, or context degraded             -> new session, conclusions only,
                                                                        changed files named for TARGETED re-reads

Resuming restores EVERY prior tool result, including reads of files that have since
changed. That stale data sits beside anything new and contradicts it.

`--resume` / `fork_session` are Claude Code / Agent SDK session features. Here a session
is a saved Messages-API history, so the demo runs anywhere. The decision logic is the same.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field

from common.client import get_client, mode_banner
from common.mock import last_tool_results, message, prompt_text, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

STALE_MARKER = "pw == stored"  # appears only in the pre-fix auth.py
OLD_AUTH = "def check(pw, stored):\n    return pw == stored  # timing-unsafe\n"
NEW_AUTH = "import hmac\n\ndef check(pw, stored):\n    return hmac.compare_digest(pw, stored)\n"
DB = "def find(conn, uid):\n    return conn.execute('SELECT * FROM t WHERE id=?', (uid,))\n"
UTILS = "def slug(s):\n    return s.lower().replace(' ', '-')\n"


def sha(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class Session:
    name: str
    messages: list
    file_hashes: dict  # path -> hash at the time the session read it
    conclusions: list  # (path, conclusion) - distilled findings, not raw tool output
    parent: str | None = None


def previous_session() -> Session:
    """Yesterday's review session: it read auth.py (old version) and reached conclusions."""
    return Session(
        name="auth-review",
        messages=[
            {"role": "user", "content": "Review auth.py, db.py and utils.py for security issues."},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "read_file", "input": {"path": "auth.py"}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": OLD_AUTH}]},
            {"role": "assistant", "content": "auth.py compares passwords with == (timing attack); no login rate limiting. db.py and utils.py are fine."},
        ],
        file_hashes={"auth.py": sha(OLD_AUTH), "db.py": sha(DB), "utils.py": sha(UTILS)},
        conclusions=[
            ("auth.py", "password check uses == (timing-unsafe) -> use hmac.compare_digest"),
            ("auth.py", "no login rate limiting"),
            ("db.py", "queries are parameterised - OK"),
            ("utils.py", "no security-relevant code"),
        ],
    )


def changed_files(session: Session, workspace: dict[str, str]) -> list[str]:
    return sorted(p for p, h in session.file_hashes.items() if sha(workspace.get(p, "")) != h)


def choose_strategy(session: Session, workspace: dict[str, str], intent: str = "continue") -> str:
    if changed_files(session, workspace):
        return "fresh"  # stale tool results in history; a fork would inherit them too
    if intent == "explore_alternatives":
        return "fork"  # shared, still-valid baseline; branch without touching the original
    return "resume"  # context still valid; cheapest option


def fork(session: Session, new_name: str) -> Session:
    branch = copy.deepcopy(session)
    branch.name, branch.parent = new_name, session.name
    return branch


def build_fresh_prompt(session: Session, workspace: dict[str, str], question: str) -> str:
    changed = changed_files(session, workspace)
    still_true = [f"- {p}: {c}" for p, c in session.conclusions if p not in changed]
    to_recheck = [f"- {p}: {c}" for p, c in session.conclusions if p in changed]
    return (
        "Context from a previous session (conclusions only - no raw tool output):\n"
        + "\n".join(still_true)
        + "\n\nConclusions about files that CHANGED since then (re-verify, do not trust):\n"
        + "\n".join(to_recheck)
        + f"\n\nFiles changed since last session: {', '.join(changed)}\n"
        "Re-read ONLY those files; everything else above is still accurate.\n\n"
        f"Task: {question}"
    )


READ_TOOL = [{"name": "read_file", "description": "Read a file from the workspace.",
              "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]


def make_reader(workspace: dict[str, str], log: list):
    def execute(name: str, tool_input: dict) -> dict:
        log.append(tool_input["path"])
        return {"path": tool_input["path"], "content": workspace[tool_input["path"]]}
    return execute


def continue_work(client, session: Session, workspace: dict[str, str], question: str, intent: str = "continue") -> dict:
    strategy = choose_strategy(session, workspace, intent)
    reads: list = []
    execute = make_reader(workspace, reads)
    if strategy == "fresh":
        result = run_agent(client, build_fresh_prompt(session, workspace, question), tools=READ_TOOL, execute=execute)
        active = Session(f"{session.name}-fresh", result.messages, {p: sha(c) for p, c in workspace.items()}, [])
    else:
        active = fork(session, f"{session.name}-alt") if strategy == "fork" else session
        result = run_agent(client, question, tools=READ_TOOL, execute=execute, history=active.messages)
        active.messages[:] = result.messages  # resume appends; a fork appends to its own copy
    return {"strategy": strategy, "answer": result.final_text, "reads": reads, "session": active}


QUESTION = "What security fixes are still needed?"


def workspace_after_fix() -> dict[str, str]:
    return {"auth.py": NEW_AUTH, "db.py": DB, "utils.py": UTILS}  # someone applied the compare_digest fix


# ---- mock model --------------------------------------------------------------------------

def mock_model(kwargs: dict):
    """Reasons from whatever auth.py content appears ANYWHERE in the request."""
    seen = prompt_text(kwargs)
    if not last_tool_results(kwargs):
        if "Files changed since last session:" in seen:
            changed = seen.split("Files changed since last session: ")[1].split("\n")[0].split(", ")
            return message(*[tool_use("read_file", {"path": p}) for p in changed])
        if "Re-explore the whole codebase" in seen:
            return message(*[tool_use("read_file", {"path": p}) for p in ("auth.py", "db.py", "utils.py")])
        if "re-read auth.py" in seen:
            return message(tool_use("read_file", {"path": "auth.py"}))
    stale = STALE_MARKER in seen
    if stale:  # the old tool result is still in history, so it leaks into the answer
        return message(text("1) Replace == with hmac.compare_digest in auth.py. 2) Add login rate limiting."))
    return message(text("auth.py already uses hmac.compare_digest. Remaining: add login rate limiting."))


def main():
    print(mode_banner())
    session, ws = previous_session(), workspace_after_fix()
    print(f"changed since last session: {changed_files(session, ws)}")
    out = continue_work(get_client(mock_model), session, ws, QUESTION)
    print(f"strategy={out['strategy']} reads={out['reads']}\nanswer: {out['answer']}")

    unchanged = {"auth.py": OLD_AUTH, "db.py": DB, "utils.py": UTILS}
    print(f"\nno files changed, continue -> {choose_strategy(previous_session(), unchanged)}")
    print(f"no files changed, compare two refactors -> {choose_strategy(previous_session(), unchanged, 'explore_alternatives')}")
    original = previous_session()
    out = continue_work(get_client(mock_model), original, unchanged, "Sketch an alternative fix using bcrypt.", "explore_alternatives")
    print(f"fork: original still has {len(original.messages)} messages; branch '{out['session'].name}' has {len(out['session'].messages)}")


if __name__ == "__main__":
    main()
