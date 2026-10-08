"""Task 3.5 — Iterative Refinement Techniques (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/3-claude-code-config/3-5-iterative-refinement

Known target, inconsistent interpretation -> 2-3 concrete input/output examples.
Complex transformation with edge cases     -> tests first; feed back "Expected X, got Y".
Unfamiliar domain                          -> interview pattern (Claude asks first).
Interacting issues -> one batched message; independent issues -> sequential.
"""

from __future__ import annotations

import json
import re

from common import config
from common.client import get_client, mode_banner, response_text
from common.mock import message, text

TASK = "Normalise these phone numbers."
INPUTS = ["(555) 010-4477", "555.010.9921", "+1 555 010 3300"]
EXAMPLES = [("(555) 010-1234", "+1-555-010-1234"), ("555.010.5678", "+1-555-010-5678")]


def transform(client, prompt: str, inputs: list[str]) -> list[str]:
    reply = response_text(client.messages.create(model=config.model(), max_tokens=1024, messages=[
        {"role": "user", "content": f"{prompt}\nReturn a JSON list.\nInputs: {json.dumps(inputs)}"}]))
    return json.loads(reply[reply.index("["): reply.rindex("]") + 1])


def runs(client, prompt: str, n: int = 3) -> list[list[str]]:
    return [transform(client, prompt, INPUTS) for _ in range(n)]


def with_examples(prompt: str) -> str:
    return prompt + "\nExamples:\n" + "\n".join(f"{i} -> {o}" for i, o in EXAMPLES)


# ---- Step 3: test-driven iteration --------------------------------------------------------------

TESTS = [("(555) 010-4477", "+1-555-010-4477"), ("", ""), ("555-0100", "INVALID"), ("+44 20 7946 0958", "+44-20-7946-0958")]


def tdd_loop(client, max_rounds: int = 3) -> list[dict]:
    prompt, history = with_examples(TASK), []
    for _ in range(max_rounds):
        got = transform(client, prompt, [i for i, _ in TESTS])
        failures = [f"Expected {want!r}, got {g!r} for input {i!r}" for (i, want), g in zip(TESTS, got) if g != want]
        history.append({"failures": failures})
        if not failures:
            break
        prompt = with_examples(TASK) + "\nTest failures to fix:\n" + "\n".join(failures)  # failures, not prose
    return history


# ---- Step 4: interview pattern ---------------------------------------------------------------------

def interview(client, task: str) -> list[str]:
    reply = response_text(client.messages.create(model=config.model(), max_tokens=1024, messages=[
        {"role": "user", "content": f"Before implementing, ask me the questions you need answered.\nTask: {task}"}]))
    return [line.strip("- ") for line in reply.splitlines() if line.strip().endswith("?")]


# ---- Step 5: batch interacting issues, send independent ones one by one -----------------------------

def plan_feedback(issues: list[dict]) -> list[list[str]]:
    """issues: [{"name", "affects": [other issue names]}] -> list of messages (each a list of issue names)."""
    interacting = {i["name"] for i in issues if i["affects"]} | {a for i in issues for a in i["affects"]}
    batch = [i["name"] for i in issues if i["name"] in interacting]
    singles = [[i["name"]] for i in issues if i["name"] not in interacting]
    return ([batch] if batch else []) + singles


PRACTICE = {
    "question": "A transformation described in prose comes out differently each time. What should the developer try first?",
    "options": {"A": "2-3 concrete input/output examples", "B": "A test suite, iterating on failures",
                "C": "The interview pattern", "D": "Rewrite the prose with more precise terminology"},
    "answer": "A",
    "why": "Inconsistent interpretation of a known target -> examples first, not better prose.",
}


# ---- mock model (SIMULATED interpretation drift for prose-only prompts) -------------------------------

_run = {"n": 0}
PROSE_STYLES = [lambda d: f"+1-{d[:3]}-{d[3:6]}-{d[6:]}", lambda d: f"({d[:3]}) {d[3:6]}-{d[6:]}", lambda d: d]


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _canonical(s: str, fixed: str) -> str:
    d = _digits(s)
    if not s:
        return ""
    if s.startswith("+44") and "Expected '+44" in fixed:  # fixed only once the test failure is fed back
        return "+44-20-" + d[4:8] + "-" + d[8:]
    if len(d) == 7 and "Expected 'INVALID'" in fixed:
        return "INVALID"
    d = d[-10:]
    return f"+1-{d[:3]}-{d[3:6]}-{d[6:]}"


def mock_model(kwargs: dict):
    prompt = kwargs["messages"][0]["content"]
    if prompt.startswith("Before implementing"):
        return message(text("- Which country should numbers without a country code default to?\n"
                            "- Should invalid numbers be dropped, kept, or flagged?\n- Is E.164 the target format?"))
    inputs = json.loads(prompt.split("Inputs: ")[1])
    if "Examples:" in prompt:
        return message(text(json.dumps([_canonical(s, prompt) for s in inputs])))
    style = PROSE_STYLES[_run["n"] % 3]  # prose only: each run picks a different reasonable reading
    _run["n"] += 1
    return message(text(json.dumps([style(_digits(s)[-10:]) for s in inputs])))


def main():
    print(mode_banner())
    prose = runs(get_client(mock_model), TASK)
    print(f"step 1 prose x3     : {len({json.dumps(r) for r in prose})} different outputs: {[r[0] for r in prose]}")
    ex = runs(get_client(mock_model), with_examples(TASK))
    print(f"step 2 examples x3  : {len({json.dumps(r) for r in ex})} distinct output(s): {ex[0]}")
    print(f"step 3 TDD rounds   : {[len(h['failures']) for h in tdd_loop(get_client(mock_model))]} failures per round")
    print(f"step 4 interview    : {interview(get_client(mock_model), 'Normalise phone numbers for a telecom billing system')}")
    issues = [{"name": "error response shape", "affects": ["client SDK types"]}, {"name": "client SDK types", "affects": []},
              {"name": "logging format", "affects": ["error response shape"]}, {"name": "indentation", "affects": []}]
    print(f"step 5 feedback plan: {plan_feedback(issues)}")


if __name__ == "__main__":
    main()
