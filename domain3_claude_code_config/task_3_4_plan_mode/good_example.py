"""Task 3.4 — Plan Mode vs Direct Execution (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-4-plan-mode-execution

"The decision is not about difficulty but about ambiguity." Plan mode reads and proposes,
writing nothing until the plan is approved; direct execution suits a known fix.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from common import config
from common.client import get_client, mode_banner, response_text
from common.mock import message, text

# ---- Step 5: the decision framework ---------------------------------------------------------------

PLAN_CRITERIA = {  # criterion -> example
    "large_scale_restructure": "split a monolith into microservices",
    "multiple_valid_approaches": "pick a caching strategy",
    "architectural_decision": "define service boundaries / API contracts",
    "multi_file_change": "migrate a logging library across 30 files",
    "needs_exploration": "change an unfamiliar legacy module",
}
DIRECT_CRITERIA = {
    "single_file_clear_cause": "null pointer with a clear stack trace",
    "approach_known": "add a validation conditional",
    "limited_scope": "update a config value",
}


@dataclass
class Task:
    name: str
    traits: set = field(default_factory=set)


def choose_mode(task: Task) -> str:
    if task.traits & set(PLAN_CRITERIA):
        return "plan, then direct execution" if "multi_file_change" in task.traits and len(task.traits) == 1 else "plan"
    return "direct"


def entered_plan_mode(cli_args: list[str], prompt: str) -> bool:
    """Plan mode is a mode switch - writing 'in plan mode' in the prompt body does nothing."""
    return ("--permission-mode" in cli_args and cli_args[cli_args.index("--permission-mode") + 1] == "plan") \
        or prompt.startswith("/plan")


# ---- Steps 1 and 3: plan mode reads and proposes; nothing is written until approval -----------------

class PlanModeSession:
    READ_ONLY = {"Read", "Grep", "Glob"}

    def __init__(self, files: dict[str, str]):
        self.files, self.approved, self.writes = files, False, []

    def use_tool(self, tool: str, path: str, content: str | None = None):
        if tool in self.READ_ONLY:
            return self.files.get(path)
        if not self.approved:
            return {"blocked": f"{tool} {path}: plan mode writes nothing until the plan is approved"}
        self.files[path] = content
        self.writes.append(path)
        return {"ok": True}


def plan_then_execute(files: dict[str, str], old: str, new: str) -> dict:
    """Hybrid: plan (find every importer, map the API change), then apply it file by file."""
    session = PlanModeSession(files)
    plan = [p for p in files if old in (session.use_tool("Read", p) or "")]
    blocked = session.use_tool("Edit", plan[0], "x") if plan else None
    session.approved = True  # the developer approves the plan
    for p in plan:
        session.use_tool("Edit", p, files[p].replace(old, new))
    return {"plan": plan, "write_before_approval": blocked, "written": session.writes}


# ---- Step 4: Explore subagent - discovery in isolation, summary back -------------------------------

def explore(client, question: str, main_history: list) -> list:
    sub = [{"role": "user", "content": f"[EXPLORE] {question}"}]  # isolated context
    findings = response_text(client.messages.create(model=config.model(), max_tokens=4096, messages=sub))
    summary = findings.splitlines()[-1]
    return main_history + [{"role": "user", "content": f"Explore summary: {summary}"}]


PRACTICE = {
    "question": "(1) Restructure a monolith into microservices, (2) fix a null pointer in one function with a clear "
                "stack trace, (3) migrate a logging library across 30 files. Which mode for each?",
    "options": {"A": "Plan mode for (1) and (3), direct execution for (2)", "B": "Plan mode for all three",
                "C": "Direct execution for all three with detailed instructions", "D": "Plan mode only for (1)"},
    "answer": "A",
    "why": "Ambiguity, not difficulty: (2) has a known cause and fix; (1) and (3) need a strategy first.",
}


def mock_model(kwargs: dict):
    listing = "\n".join(f"src/module_{i}.ts imports logger v1 (line {i * 3})" for i in range(30))
    return message(text(f"{listing}\nSUMMARY: 30 files import logger v1; all use log.info/log.error only."))


def main():
    print(mode_banner())
    tasks = [Task("restructure monolith into microservices", {"large_scale_restructure", "architectural_decision"}),
             Task("null pointer, clear stack trace", {"single_file_clear_cause"}),
             Task("migrate logging library across 30 files", {"multi_file_change"})]
    for t in tasks:
        print(f"{t.name:42s} -> {choose_mode(t)}")
    print(f"'in plan mode' written in the prompt -> plan mode? {entered_plan_mode([], 'Please work in plan mode')}")
    print(f"--permission-mode plan               -> plan mode? {entered_plan_mode(['--permission-mode', 'plan'], 'go')}")
    files = {f"src/m{i}.ts": "import log from 'logger-v1'" for i in range(3)} | {"src/other.ts": "x"}
    r = plan_then_execute(files, "logger-v1", "logger-v2")
    print(f"hybrid: plan={r['plan']} write before approval -> {r['write_before_approval']} written={r['written']}")
    history = explore(get_client(mock_model), "Which files use logger v1?", [])
    print(f"Explore: main conversation got {len(history[-1]['content'])} chars: {history[-1]['content']!r}")


if __name__ == "__main__":
    main()
