"""Task 1.6 — match the decomposition pattern to the task.

A. Code review: the plan is knowable before opening any file, so use a FIXED pipeline.
   N per-file local passes (full attention each) + ONE separate cross-file
   integration pass that looks only for what no single-file pass can see.

B. Debugging an intermittent failure: scope is unknown, so use DYNAMIC decomposition.
   Each next step is chosen from what the previous step found.
"""

from __future__ import annotations

import json

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- A. fixed pipeline: multi-pass code review ------------------------------------------

FILES = {
    "api/users.py": 'def get_user(db, uid):\n    row = db.execute("SELECT * FROM users WHERE id=" + uid)\n'
                    '    return {"user_id": row.id, "email": row.email}\n',
    "auth/session.py": 'SECRET_KEY = "hunter2"\n\ndef sign(payload):\n    return hmac(SECRET_KEY, payload)\n',
    "billing/invoice.py": "def total(items):\n    return sum(i.price * i.qty for i in items)  # float money\n",
    "web/client.py": 'def show_user(resp):\n    return f"User {resp["userId"]}"\n',
    "utils/fmt.py": "def pct(x):\n    return f'{x:.1%}'\n",
}

FINDINGS_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["files", "issue", "severity"],
        "properties": {"files": {"type": "array", "items": {"type": "string"}}, "issue": {"type": "string"},
                       "severity": {"type": "string", "enum": ["critical", "major", "minor"]}}}}},
}


def local_review(client, path: str, source: str) -> list[dict]:
    prompt = (f"[LOCAL REVIEW]\nReview ONE file for bugs and security issues. Ignore other files.\n"
              f"--- {path} ---\n{source}")
    return ask_json(client, prompt, FINDINGS_SCHEMA)["findings"]


def integration_review(client, files: dict[str, str], local_findings: list[dict]) -> list[dict]:
    sources = "\n".join(f"--- {p} ---\n{s}" for p, s in files.items())
    prompt = ("[INTEGRATION REVIEW]\nPer-file issues are already reported (below) - do NOT repeat them.\n"
              "Look ONLY for cross-file problems: data contracts between producer and consumer, API "
              "consistency, the same pattern judged differently in different files.\n"
              f"Per-file findings: {json.dumps(local_findings)}\n{sources}")
    return ask_json(client, prompt, FINDINGS_SCHEMA)["findings"]


def review_pipeline(client, files: dict[str, str] = FILES) -> dict:
    """The plan (N local passes + 1 integration pass) is fixed before any file is opened."""
    local = [f for path, src in files.items() for f in local_review(client, path, src)]
    cross = integration_review(client, files, local)
    return {"local": local, "cross_file": cross}


# ---- B. dynamic adaptive decomposition: debugging -----------------------------------------

SYSTEM_DATA = {  # what each investigation step would reveal
    "app logs": "ERROR 14:02 checkout: timeout calling payments-service after 30s (x47, only at peak)",
    "db metrics": "p99 latency 12ms, no lock waits",
    "cdn status": "all edges healthy",
    "payments-service config": "http connection pool size: 2  (default 50)",
    "payments-service deploy history": "pool size changed 50 -> 2 in release 2026.09.30",
}

STEP_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["action", "target", "reason"],
    "properties": {"action": {"type": "string", "enum": ["inspect", "conclude"]},
                   "target": {"type": "string"}, "reason": {"type": "string"}},
}


def investigate(client, symptom: str, max_steps: int = 6) -> dict:
    findings: list[dict] = []
    for _ in range(max_steps):
        prompt = ("[INVESTIGATE]\n"
                  f"Symptom: {symptom}\nAvailable sources: {list(SYSTEM_DATA)}\n"
                  f"Findings so far: {json.dumps(findings)}\n"
                  "Choose the single most informative next source to inspect given what you've found, "
                  "or conclude (put the root cause in `reason`).")
        step = ask_json(client, prompt, STEP_SCHEMA)
        if step["action"] == "conclude":
            return {"steps": [f["source"] for f in findings], "root_cause": step["reason"]}
        findings.append({"source": step["target"], "observation": SYSTEM_DATA.get(step["target"], "no data")})
    return {"steps": [f["source"] for f in findings], "root_cause": None}


SYMPTOM = "Checkout intermittently fails during peak hours."


# ---- mock model ------------------------------------------------------------------------------

PLANTED = {  # marker in source -> local issue
    'id=" + uid': ("api/users.py", "SQL built by string concatenation (injection)", "critical"),
    'SECRET_KEY = "': ("auth/session.py", "hard-coded signing secret", "critical"),
    "# float money": ("billing/invoice.py", "currency summed as float", "major"),
    'resp["userId"]': ("web/client.py", "no handling for missing key", "minor"),
}
CROSS_FILE = {"files": ["api/users.py", "web/client.py"],
              "issue": "api returns 'user_id' but web client reads 'userId' - KeyError on every render",
              "severity": "critical"}


def _local_issues(prompt: str, only_files: list[str] | None = None) -> list[dict]:
    out = []
    for marker, (path, issue, sev) in PLANTED.items():
        if marker in prompt and (only_files is None or path in only_files):
            out.append({"files": [path], "issue": issue, "severity": sev})
    return out


def _sees_contract_mismatch(prompt: str) -> bool:
    return '"user_id": row.id' in prompt and 'resp["userId"]' in prompt


def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    if prompt.startswith("[LOCAL REVIEW]") or prompt.startswith("[BATCH REVIEW]"):
        # Small scope = full attention. Cross-file issues are visible only if both files are in THIS prompt.
        findings = _local_issues(prompt)
        if prompt.startswith("[BATCH REVIEW]") and _sees_contract_mismatch(prompt):
            findings.append(CROSS_FILE)
        return json_message({"findings": findings})
    if prompt.startswith("[INTEGRATION REVIEW]"):
        return json_message({"findings": [CROSS_FILE] if _sees_contract_mismatch(prompt) else []})
    if prompt.startswith("[SINGLE PASS]"):
        # SIMULATED attention dilution (the documented symptom): thorough on the first files,
        # shallow after that, and the cross-file contract is never connected.
        order = [p for p in FILES if f"--- {p} ---" in prompt]
        return json_message({"findings": _local_issues(prompt, only_files=order[:2])})
    if prompt.startswith("[INVESTIGATE]"):
        if "pool size changed" in prompt:
            return json_message({"action": "conclude", "target": "",
                                 "reason": "Release 2026.09.30 cut the payments-service HTTP pool from 50 to 2; peak traffic exhausts it."})
        if "connection pool size: 2" in prompt:
            return json_message({"action": "inspect", "target": "payments-service deploy history",
                                 "reason": "Pool is far below default - find when it changed."})
        if "timeout calling payments-service" in prompt:
            return json_message({"action": "inspect", "target": "payments-service config",
                                 "reason": "Logs point at payments-service, which wasn't in any initial plan."})
        if "Findings so far: []" in prompt:
            return json_message({"action": "inspect", "target": "app logs", "reason": "Start from the failing path."})
        return json_message({"action": "conclude", "target": "", "reason": "No root cause identified from the inspected sources."})
    raise ValueError(f"unexpected prompt: {prompt[:40]}")


def main():
    print(mode_banner())
    client = get_client(mock_model)
    result = review_pipeline(client)
    print(f"fixed pipeline: {len(FILES)} local passes + 1 integration pass = {len(FILES) + 1} calls")
    for f in result["local"]:
        print(f"  local  [{f['severity']}] {f['files'][0]}: {f['issue']}")
    for f in result["cross_file"]:
        print(f"  CROSS  [{f['severity']}] {' <-> '.join(f['files'])}: {f['issue']}")

    trace = investigate(get_client(mock_model), SYMPTOM)
    print(f"\ndynamic investigation steps: {trace['steps']}")
    print(f"root cause: {trace['root_cause']}")


if __name__ == "__main__":
    main()
