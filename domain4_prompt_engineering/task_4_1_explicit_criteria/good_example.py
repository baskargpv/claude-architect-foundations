"""Task 4.1 — System Prompts with Explicit Criteria (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-1-system-prompts

"Be conservative" gives the model no decision boundary. Explicit categories (report X, skip Y),
a concrete trigger for comment findings, and code examples per severity do.
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- the 5 test snippets (with ground truth) ------------------------------------------------------

SNIPPETS = [
    {"id": "s1", "code": "if (items.length = 0) { return empty; }", "truth": "bug"},
    {"id": "s2", "code": "db.query(\"SELECT * FROM users WHERE id=\" + id)", "truth": "security"},
    {"id": "s3", "code": "var total = 0;", "truth": "style"},
    {"id": "s4", "code": "// returns seconds\nfunction elapsed() { return Date.now() - start; }", "truth": "comment_mismatch"},
    {"id": "s5", "code": "// returns milliseconds\nfunction elapsed() { return Date.now() - start; }", "truth": "clean"},
]
REPORTABLE = {"bug", "security", "comment_mismatch"}

# ---- Step 1: baseline (vague) vs Steps 2-3: explicit criteria + severity code examples ------------

VAGUE_PROMPT = "You are a code reviewer. Be conservative and only report high-confidence findings."

EXPLICIT_PROMPT = """You are a code reviewer.
REPORT: bugs and security vulnerabilities.
REPORT a comment only when its claimed behaviour contradicts what the code actually does.
SKIP: style preferences and local patterns (var vs const, naming, formatting).
Severity, by example:
Critical example: db.query("SELECT ... WHERE id=" + id)   // injectable
Critical example: if (x = 0)                                // assignment in condition
Minor example: // returns seconds  ...  return ms;          // misleading comment
"""

FINDINGS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"],
                   "properties": {"findings": {"type": "array", "items": {
                       "type": "object", "additionalProperties": False, "required": ["category", "severity", "confidence"],
                       "properties": {"category": {"type": "string"},
                                      "severity": {"type": "string", "enum": ["critical", "minor"]},
                                      "confidence": {"type": "number"}}}}}}


def review(client, system: str, snippet: dict) -> list[dict]:
    return ask_json(client, f"Review this snippet ({snippet['id']}):\n{snippet['code']}", FINDINGS_SCHEMA, system=system)["findings"]


def evaluate(client, system: str, runs: int = 2) -> dict:
    """Step 4: false-positive rate, per-category stats, and severity consistency across runs."""
    per_run = [{s["id"]: review(client, system, s) for s in SNIPPETS} for _ in range(runs)]
    first = per_run[0]
    flagged = [(s, f) for s in SNIPPETS for f in first[s["id"]]]
    false_pos = [(s, f) for s, f in flagged if s["truth"] not in REPORTABLE]
    by_cat: dict[str, list[bool]] = {}
    for s, f in flagged:
        by_cat.setdefault(f["category"], []).append(s["truth"] not in REPORTABLE)
    sev = lambda run: {k: [f["severity"] for f in v] for k, v in run.items()}
    return {"flagged": len(flagged), "fp_rate": round(len(false_pos) / max(1, len(flagged)), 2),
            "category_fp": {c: round(sum(v) / len(v), 2) for c, v in by_cat.items()},
            "consistent_severity": all(sev(r) == sev(first) for r in per_run)}


# ---- Step 5: disable categories above 25% false positives while their prompts are reworked -----------

def active_categories(category_fp: dict[str, float], limit: float = 0.25) -> dict:
    return {"active": sorted(c for c, fp in category_fp.items() if fp <= limit),
            "disabled_until_refined": sorted(c for c, fp in category_fp.items() if fp > limit)}


PRACTICE = {
    "question": "The review pipeline has a 40% false-positive rate on 'documentation mismatch', and developers now "
                "ignore every category. Most effective fix?",
    "options": {"A": "Temporarily disable that category while refining its prompt with explicit criteria and code examples",
                "B": "Raise temperature and drop findings that appear only once",
                "C": "Add a second pass that discards unverifiable documentation findings",
                "D": "Add 'only report high-confidence documentation issues' to the prompt"},
    "answer": "A",
    "why": "One noisy category destroys trust in all of them; disable it while fixing its criteria. D relies on uncalibrated confidence.",
}


# ---- mock model (SIMULATED: vague prompts over-flag and drift; explicit ones don't) -------------------

_calls = {"n": 0}


def mock_model(kwargs: dict):
    system, prompt = kwargs.get("system", ""), last_user_text(kwargs)
    sid = prompt.split("(")[1].split(")")[0]
    truth = next(s["truth"] for s in SNIPPETS if s["id"] == sid)
    _calls["n"] += 1
    explicit = "REPORT:" in system
    if truth == "clean":  # accurate comment: a vague reviewer still calls it a "documentation issue"
        return json_message({"findings": [] if explicit else [{"category": "comment_mismatch", "severity": "minor", "confidence": 0.85}]})
    if truth == "style" and explicit:
        return json_message({"findings": []})
    category = {"bug": "bug", "security": "security", "style": "style", "comment_mismatch": "comment_mismatch"}[truth]
    if "Critical example:" in system:
        severity = "minor" if truth in ("comment_mismatch", "style") else "critical"
    else:
        severity = ["critical", "minor"][_calls["n"] % 2]  # prose severity -> drifts run to run
    confidence = {"style": 0.9, "bug": 0.6}.get(truth, 0.8)  # self-reported confidence is poorly calibrated
    return json_message({"findings": [{"category": category, "severity": severity, "confidence": confidence}]})


def main():
    print(mode_banner())
    before = evaluate(get_client(mock_model), VAGUE_PROMPT)
    after = evaluate(get_client(mock_model), EXPLICIT_PROMPT)
    print(f"step 1 vague    : {before}")
    print(f"step 4 explicit : {after}")
    print(f"step 5 categories after the vague baseline: {active_categories(before['category_fp'])}")


if __name__ == "__main__":
    main()
