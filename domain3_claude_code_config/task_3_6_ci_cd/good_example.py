"""Task 3.6 — CI/CD Integration (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-6-cicd-integration

`claude -p` (--print) runs once, prints, exits - without it a CI job waits for keyboard input forever.
--output-format json wraps the run in an envelope; --json-schema puts validated data in
`structured_output`. Review in a SEPARATE invocation, and pass prior findings in so only new
issues get reported.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import yaml

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

FINDINGS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"],
                   "properties": {"findings": {"type": "array", "items": {
                       "type": "object", "additionalProperties": False, "required": ["file", "line", "severity", "message"],
                       "properties": {"file": {"type": "string"}, "line": {"type": "integer"},
                                      "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
                                      "message": {"type": "string"}}}}}}

# ---- Steps 1-2: the non-interactive command, the script, and the workflow --------------------------

def ci_command(prompt: str) -> list[str]:
    return ["claude", "-p", prompt, "--output-format", "json", "--json-schema", json.dumps(FINDINGS_SCHEMA)]


CI_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
PREV=$(cat .review/findings.json 2>/dev/null || echo '[]')
claude -p "Review this PR for bugs and security issues. Previously reported (report only new or unaddressed): $PREV" \\
  --output-format json --json-schema "$(cat .review/schema.json)" \\
  | jq '.structured_output.findings' > .review/new_findings.json
"""

WORKFLOW = {
    "name": "claude-review",
    "on": {"pull_request": {"types": ["opened", "synchronize"]}},
    "permissions": {"contents": "read", "pull-requests": "write", "id-token": "write"},
    "jobs": {"review": {"runs-on": "ubuntu-latest", "steps": [
        {"uses": "actions/checkout@v4"},
        {"uses": "anthropics/claude-code-action@v1",
         "with": {"anthropic_api_key": "${{ secrets.ANTHROPIC_API_KEY }}",
                  "prompt": "Review this PR for bugs and security issues; report only new findings.",
                  "claude_args": "--max-turns 5 --output-format json"}}]}},
}


def write_ci_files(repo: Path) -> dict[str, Path]:
    (repo / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (repo / ".review").mkdir(exist_ok=True)
    paths = {"script": repo / "ci_review.sh", "workflow": repo / ".github/workflows/claude-review.yml",
             "schema": repo / ".review/schema.json", "claude_md": repo / "CLAUDE.md"}
    paths["script"].write_text(CI_SCRIPT)
    paths["workflow"].write_text(yaml.safe_dump(WORKFLOW, sort_keys=False))
    paths["schema"].write_text(json.dumps(FINDINGS_SCHEMA))
    paths["claude_md"].write_text(CI_CLAUDE_MD)  # Step 4
    return paths


def validate_workflow(text_: str) -> list[str]:
    wf, problems = yaml.safe_load(text_), []
    steps = wf["jobs"]["review"]["steps"]
    uses = [s.get("uses", "") for s in steps]
    if not any(u.startswith("actions/checkout") for u in uses):
        problems.append("missing actions/checkout - the repo isn't on disk")
    action = next((s for s in steps if s.get("uses", "").startswith("anthropics/claude-code-action")), None)
    if action is None:
        problems.append("missing anthropics/claude-code-action")
    elif "secrets." not in action["with"].get("anthropic_api_key", ""):
        problems.append("API key must come from a repository secret")
    if wf.get("permissions", {}).get("id-token") != "write":
        problems.append("id-token: write is needed for the action's GitHub App auth")
    return problems


# ---- Step 4: CLAUDE.md is read in CI exactly as in interactive mode ------------------------------------

CI_CLAUDE_MD = """# CI review standards
- Critical: security holes, data loss. Major: wrong behaviour. Minor: style (don't report).
- Tests live next to sources as *.test.ts; fixtures in tests/fixtures/.
"""

# ---- Steps 2-3: run in print mode, extract structured_output, post inline comments ----------------------

def run_print_mode(client, prompt: str) -> dict:
    """What `claude -p ... --output-format json --json-schema ...` prints: an envelope, data in structured_output.
    Emulated on the Messages API so the demo needs no CLI install."""
    data = ask_json(client, prompt, FINDINGS_SCHEMA)
    return {"type": "result", "result": f"{len(data['findings'])} findings", "session_id": str(uuid.uuid4()),
            "total_cost_usd": 0.0, "structured_output": data}


def post_inline_comments(envelope: dict) -> list[str]:
    return [f"{f['file']}:{f['line']} [{f['severity']}] {f['message']}" for f in envelope["structured_output"]["findings"]]


# ---- Step 5: generation and review are independent invocations ------------------------------------------

def generate(client, task: str) -> str:
    return ask_json(client, f"[GENERATE] {task}", {"type": "object", "additionalProperties": False,
                                                    "required": ["code"], "properties": {"code": {"type": "string"}}})["code"]


def review(client, code: str, prior: list[dict] | None = None) -> dict:
    prior_txt = json.dumps(prior or [])
    return run_print_mode(client, f"[REVIEW] Previously reported (report only new or unaddressed): {prior_txt}\n"
                                  f"--- auth.ts ---\n{code}")


# ---- Step 6: incremental review - store findings, pass them in, report only what's new --------------------

def incremental_runs(client, code_versions: list[str], store: Path) -> list[list[str]]:
    reported = []
    for code in code_versions:
        prior = json.loads(store.read_text()) if store.exists() else []
        env = review(client, code, prior)
        reported.append(post_inline_comments(env))
        store.write_text(json.dumps(prior + env["structured_output"]["findings"]))
    return reported


def choose_api(blocking: bool) -> str:
    return "synchronous (real-time) API" if blocking else "Message Batches API (50% cheaper, up to 24h, no SLA)"


PRACTICE = {
    "question": "A CI script runs `claude` with a prompt; the job hangs and the logs show it waiting for interactive input. Fix?",
    "options": {"A": "Set CLAUDE_HEADLESS=true", "B": "Add --batch", "C": "Redirect stdin from /dev/null", "D": "Add -p"},
    "answer": "D",
    "why": "-p / --print is the actual non-interactive mode; the other three don't exist or don't change the mode.",
}


# ---- mock model ------------------------------------------------------------------------------------------

ISSUES = {"eval(": ("critical", "eval() on request input"), "password ==": ("major", "timing-unsafe password comparison")}


def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    if prompt.startswith("[GENERATE]"):
        return json_message({"code": "function login(req) {\n  const cfg = eval(req.body.cfg);\n  return password == cfg.pw;\n}"})
    if "[REVIEW]" in prompt:
        prior = json.loads(prompt.split("unaddressed): ")[1].split("\n")[0])
        code = prompt.split("--- auth.ts ---\n", 1)[1]
        findings = []
        for line_no, line in enumerate(code.splitlines(), 1):
            for marker, (sev, msg) in ISSUES.items():
                if marker in line and not any(p["message"] == msg for p in prior):
                    findings.append({"file": "auth.ts", "line": line_no, "severity": sev, "message": msg})
        return json_message({"findings": findings})
    raise ValueError(prompt[:40])


def main():
    import tempfile

    print(mode_banner())
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        paths = write_ci_files(repo)
        print(f"step 1 command: {' '.join(ci_command('Review this PR')[:5])} ...")
        print(f"step 1 workflow problems: {validate_workflow(paths['workflow'].read_text()) or 'none'}")
        client = get_client(mock_model)
        code = generate(client, "Write a login handler")  # session A
        env = review(client, code)  # session B, independent
        print(f"step 2-3 envelope keys: {sorted(env)}; comments: {post_inline_comments(env)}")
        v2 = code + "\n// added a feature, issues unchanged"
        v3 = v2.replace("eval(req.body.cfg)", "JSON.parse(req.body.cfg)") + "\nif (password == x) {}"
        runs = incremental_runs(client, [code, v2, v3], repo / ".review/findings.json")
        print(f"step 6 comments per push: {[len(r) for r in runs]}  <- dismissed issues aren't re-flagged")
    print(f"pre-merge check -> {choose_api(True)}; nightly audit -> {choose_api(False)}")


if __name__ == "__main__":
    main()
