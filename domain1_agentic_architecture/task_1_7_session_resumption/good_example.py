"""Task 1.7 — Implement Session Management Strategies (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-7-session-state-resumption

    --resume <name>        prior context still valid           -> continue the same session (append)
    fork_session           divergent exploration from baseline -> branch; original untouched
    fresh start + summary  files changed / cluttered history   -> new session, conclusions only,
                                                                  changed files named for targeted re-analysis

Claude Code sessions are modelled as named, persisted Messages-API histories (SessionStore),
so the same decisions run offline and live.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from common.client import get_client, mode_banner, parse_json_object
from common.mock import last_tool_results, message, prompt_text, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

HERE = Path(__file__).parent
SAMPLE_CODEBASE = HERE / "sample_codebase"
FIXED_VERSIONS = HERE / "fixed_versions"
CHANGED_FILES = ["auth.ts", "session.ts", "middleware.ts"]  # the lesson's practical example


# ---- sessions --------------------------------------------------------------------------------

@dataclass
class Session:
    name: str
    messages: list
    file_hashes: dict = field(default_factory=dict)  # path -> sha at time of reading
    findings: list = field(default_factory=list)  # per-file conclusions
    parent: str | None = None


class SessionNotFound(KeyError):
    pass


class SessionStore:
    """Named sessions on disk - the analogue of `claude --name <n>` / `claude --resume <n>`."""

    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, s: Session):
        (self.dir / f"{s.name}.json").write_text(json.dumps(asdict(s), indent=1))

    def load(self, name: str) -> Session:
        path = self.dir / f"{name}.json"
        if not path.exists():  # current docs: --resume only resumes sessions that already exist
            raise SessionNotFound(name)
        return Session(**json.loads(path.read_text()))

    def fork(self, name: str, new_name: str) -> Session:
        branch = copy.deepcopy(self.load(name))
        branch.name, branch.parent = new_name, name
        self.save(branch)
        return branch


def jsonable(messages: list) -> list:
    out = []
    for m in messages:
        content = m["content"]
        if isinstance(content, list):
            content = [b.model_dump(exclude_none=True) if hasattr(b, "model_dump") else b for b in content]
        out.append({"role": m["role"], "content": content})
    return out


def sha(text_: str) -> str:
    return hashlib.sha256(text_.encode()).hexdigest()[:12]


def workspace_hashes(workspace: Path) -> dict:
    return {p.name: sha(p.read_text()) for p in sorted(workspace.glob("*.ts"))}


READ_TOOL = [{"name": "read_file", "description": "Read a source file from the workspace.",
              "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]


def make_reader(workspace: Path, log: list):
    def execute(name: str, tool_input: dict) -> dict:
        log.append(tool_input["path"])
        return {"path": tool_input["path"], "content": (workspace / tool_input["path"]).read_text()}
    return execute


# ---- Step 1: a named session that analyses the 10-file codebase ------------------------------

def analyse_codebase(client, workspace: Path, store: SessionStore, name: str = "auth-review") -> Session:
    files = sorted(p.name for p in workspace.glob("*.ts"))
    reads: list = []
    prompt = (f"[ANALYSE] Read and review every file: {', '.join(files)}. Return JSON "
              '{"findings": [{"file", "issues": [{"issue", "severity"}], "recommendations": []}]}.')
    result = run_agent(client, prompt, tools=READ_TOOL, execute=make_reader(workspace, reads))
    session = Session(name, jsonable(result.messages), workspace_hashes(workspace),
                      parse_json_object(result.final_text)["findings"])
    store.save(session)
    return session


# ---- Step 2: structured summary - conclusions only, never raw tool output --------------------

def structured_summary(session: Session) -> str:
    lines = []
    for f in session.findings:
        issues = "; ".join(f"{i['issue']} ({i['severity']})" for i in f["issues"]) or "no issues"
        recs = "; ".join(f["recommendations"]) or "none"
        lines.append(f"- {f['file']}: issues: {issues}. recommendations: {recs}")
    return "Prior findings (conclusions only):\n" + "\n".join(lines)


# ---- Step 3: modify three files ----------------------------------------------------------------

def make_workspace(target: Path) -> Path:
    shutil.copytree(SAMPLE_CODEBASE, target)
    return target


def apply_fixes(workspace: Path, files: list[str] = CHANGED_FILES):
    for f in files:
        shutil.copy(FIXED_VERSIONS / f, workspace / f)


def changed_since(session: Session, workspace: Path) -> list[str]:
    now = workspace_hashes(workspace)
    return sorted(f for f, h in session.file_hashes.items() if now.get(f) != h)


# ---- Step 4: resume (the stale path) ------------------------------------------------------------

QUESTION = "What should we fix next? List every remaining fix."


def resume(client, store: SessionStore, name: str, workspace: Path, question: str = QUESTION) -> dict:
    session = store.load(name)
    reads: list = []
    result = run_agent(client, question, tools=READ_TOOL, execute=make_reader(workspace, reads), history=session.messages)
    session.messages = jsonable(result.messages)  # resume APPENDS to the same session
    store.save(session)
    return {"answer": result.final_text, "reads": reads, "session": session}


# ---- Step 5: fresh start with the summary + targeted re-analysis --------------------------------

def fresh_start(client, store: SessionStore, prior: Session, workspace: Path, question: str = QUESTION) -> dict:
    changed = changed_since(prior, workspace)
    prompt = (f"{structured_summary(prior)}\n\n"
              f"Files changed since the last session: {', '.join(changed)}\n"
              "Re-analyse ONLY those files (their earlier findings may be outdated); the summary covers the rest.\n\n"
              f"{question}")
    reads: list = []
    result = run_agent(client, prompt, tools=READ_TOOL, execute=make_reader(workspace, reads))
    session = Session(f"{prior.name}-fresh", jsonable(result.messages), workspace_hashes(workspace), prior.findings)
    store.save(session)
    return {"answer": result.final_text, "reads": reads, "session": session, "prompt": prompt}


# ---- Step 6: compare the two ------------------------------------------------------------------

def recommended_files(answer: str) -> set[str]:
    return set(re.findall(r"(\w+\.ts):", answer))


def stale_symptoms(answer: str, workspace: Path) -> list[str]:
    """Recommendations for issues the CURRENT code no longer has."""
    return sorted(f for f in recommended_files(answer)
                  if not any(re.search(rule[0], (workspace / f).read_text()) for rule in RULES.get(f, [])))


def compare_sessions(resumed: dict, fresh: dict, workspace: Path) -> dict:
    return {"resumed_stale": stale_symptoms(resumed["answer"], workspace),
            "fresh_stale": stale_symptoms(fresh["answer"], workspace),
            "fresh_reads": fresh["reads"]}


# ---- the decision matrix ------------------------------------------------------------------------

def choose_strategy(files_changed: int = 0, intent: str = "continue", history_cluttered: bool = False,
                    dependencies_updated: bool = False) -> str:
    if files_changed or dependencies_updated or history_cluttered:
        return "fresh_start_with_summary"  # stale or degraded context; a fork would inherit it
    if intent in ("compare_approaches", "independent_strategies"):
        return "fork_session"
    return "resume"


DECISION_MATRIX = [  # (scenario, kwargs, expected) - the lesson's six rows
    ("continuing yesterday's work, no files changed", {}, "resume"),
    ("comparing two refactoring approaches", {"intent": "compare_approaches"}, "fork_session"),
    ("resuming after modifying 3 of 50 files", {"files_changed": 3}, "fresh_start_with_summary"),
    ("long session with cluttered history", {"history_cluttered": True}, "fresh_start_with_summary"),
    ("testing strategy vs documentation strategy", {"intent": "independent_strategies"}, "fork_session"),
    ("resuming after dependency updates", {"dependencies_updated": True}, "fresh_start_with_summary"),
]

PRACTICE = {
    "question": "After modifying 3 of 50 files, a resumed session recommends changes already made and cites code "
                "that no longer exists. Most appropriate approach?",
    "options": {"A": "Resume and ask the agent to re-read the 3 files",
                "B": "New session, no context, re-analyse all 50 files",
                "C": "Fresh session with an injected summary, naming the 3 changed files for targeted re-analysis",
                "D": "fork_session to handle the changes on a separate branch"},
    "answer": "C",
    "why": "A keeps stale results in history, B wastes effort on 47 unchanged files, D inherits the stale context.",
}


# ---- mock model: a rule-based reviewer that reasons from whatever code is in its context --------

RULES = {  # file -> [(regex on code, issue, severity, recommendation)]
    "auth.ts": [(r"password === stored", "timing-unsafe password comparison", "high", "use crypto.timingSafeEqual")],
    "session.ts": [(r"reused for the whole login lifetime", "session token never rotated", "medium", "rotate the session token")],
    "middleware.ts": [(r'app\.post\("/login", handleLogin\)', "no rate limiting on /login", "medium", "add a rate limiter to /login")],
    "users.ts": [(r"req\.body\.email\)", "email saved without validation", "medium", "validate the email format")],
    "payments.ts": [(r"parseFloat\(i\.price\)", "money summed as floats", "high", "use integer cents")],
    "logger.ts": [(r'console\.log\("login", user\)', "logs the whole user object (PII)", "medium", "log the user id only")],
}


def review_code(code: str) -> list[dict]:
    findings = []
    for f, rules in RULES.items():
        for pattern, issue, sev, rec in rules:
            if re.search(pattern, code):
                findings.append({"file": f, "issues": [{"issue": issue, "severity": sev}], "recommendations": [rec]})
    return findings


def code_in_context(kwargs: dict) -> str:
    """Every file body that reached the model via a tool_result, decoded from its JSON envelope."""
    bodies = []
    for m in kwargs["messages"]:
        if isinstance(m["content"], list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    bodies.append(json.loads(b["content"]).get("content", ""))
    return "\n".join(bodies)


def mock_model(kwargs: dict):
    first = kwargs["messages"][0]["content"]
    latest = kwargs["messages"][-1]["content"]
    latest = latest if isinstance(latest, str) else ""
    if not last_tool_results(kwargs):
        if first.startswith("[ANALYSE]") and len(kwargs["messages"]) == 1:
            files = first.split("every file: ")[1].split(". Return")[0].split(", ")
            return message(text("Reading every file."), *[tool_use("read_file", {"path": f}) for f in files])
        targets = []
        if "Files changed since the last session:" in latest:
            targets = latest.split("Files changed since the last session: ")[1].split("\n")[0].split(", ")
        elif "re-analyse the entire codebase" in latest.lower():
            targets = sorted(p.name for p in SAMPLE_CODEBASE.glob("*.ts"))
        elif m := re.search(r"re-read ([\w., ]+?) first", latest):
            targets = [t.strip() for t in m.group(1).split(",")]
        if targets:
            return message(*[tool_use("read_file", {"path": t}) for t in targets])
    if first.startswith("[ANALYSE]") and len(kwargs["messages"]) == 3:
        return message(text(json.dumps({"findings": review_code(code_in_context(kwargs))})))
    # Answering: every code version visible ANYWHERE in the request influences the answer.
    seen = review_code(code_in_context(kwargs))
    remaining = {f["file"] for f in seen}
    summary_issues = {line.split(":")[0].strip("- ") for line in prompt_text(kwargs).splitlines()
                      if line.startswith("- ") and "no issues" not in line and ".ts:" in line}
    changed = set(re.findall(r"Files changed since the last session: ([\w., ]+)", prompt_text(kwargs))[0].split(", ")) \
        if "Files changed since the last session:" in prompt_text(kwargs) else set()
    recs = {f["file"]: f["recommendations"][0] for f in seen}
    for f in summary_issues - changed - remaining:  # unchanged files: trust the summary's conclusions
        recs[f] = next(r[3] for r in RULES[f])
    return message(text("Remaining fixes: " + "; ".join(f"{f}: {r}" for f, r in sorted(recs.items()))))


def main():
    import tempfile

    print(mode_banner())
    for scenario, kwargs, _ in DECISION_MATRIX:
        print(f"  {scenario:45s} -> {choose_strategy(**kwargs)}")
    with tempfile.TemporaryDirectory() as tmp:
        ws, store = make_workspace(Path(tmp) / "ws"), SessionStore(Path(tmp) / "sessions")
        session = analyse_codebase(get_client(mock_model), ws, store)  # Step 1
        print(f"step 1 named session '{session.name}': {len(session.findings)} files with findings")
        print(structured_summary(session))  # Step 2
        apply_fixes(ws)  # Step 3
        print(f"step 3 changed: {changed_since(session, ws)} -> {choose_strategy(files_changed=len(changed_since(session, ws)))}")
        resumed = resume(get_client(mock_model), store, "auth-review", ws)  # Step 4
        fresh = fresh_start(get_client(mock_model), store, store.load("auth-review"), ws)  # Step 5
        print(f"step 4 resumed: {resumed['answer']}")
        print(f"step 5 fresh  : {fresh['answer']}")
        print(f"step 6 compare: {compare_sessions(resumed, fresh, ws)}")


if __name__ == "__main__":
    main()
