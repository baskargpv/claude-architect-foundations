"""Task 5.4 — Codebase Exploration & Context Degradation (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-4-codebase-exploration

Context degradation: specific early findings get buried under verbose output as a session goes on.
Scratchpad files keep findings outside the context; subagents keep verbose output out of it
entirely; a phase-1 summary seeds phase 2; a state manifest makes crashes recoverable.
"""

from __future__ import annotations

import json
from pathlib import Path

from common import config
from common.client import get_client, mode_banner, parse_json_object, response_text
from common.mock import message, text

TASKS = {  # Step 1: focused exploration questions for subagents
    "tests": "Find the test files and what they cover.",
    "refund_flow": "Trace the refund flow from endpoint to database.",
    "integrations": "List external API integrations and their error handling.",
}


def run_subagent(client, task: str) -> dict:
    """Explores verbosely in its own context; only a structured summary comes back."""
    reply = response_text(client.messages.create(model=config.model(), max_tokens=4096, messages=[
        {"role": "user", "content": f"[EXPLORE] {task}\nReturn JSON {{\"findings\": [...]}} with class names and file paths."}]))
    return parse_json_object(reply)


# ---- Step 2: scratchpad - write findings, read them before each next step ---------------------------

class Scratchpad:
    def __init__(self, path: Path):
        self.path = path
        self.path.write_text("# Key findings\n")

    def add(self, topic: str, findings: list[str]):
        with self.path.open("a") as f:
            f.write(f"\n## {topic}\n" + "\n".join(f"- {x}" for x in findings) + "\n")

    def read(self) -> str:
        return self.path.read_text()


# ---- Step 4: crash-recovery manifest -------------------------------------------------------------

def export_manifest(path: Path, session_id: str, phase: str, explored: list[str], findings: list[str], next_steps: list[str]):
    path.write_text(json.dumps({"sessionId": session_id, "phase": phase, "exploredPaths": explored,
                                "keyFindings": findings, "nextSteps": next_steps}, indent=1))


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


# ---- Steps 1-3: coordinator with delegation, scratchpad and phase-2 summary injection --------------------

def explore(client, workdir: Path) -> dict:
    pad = Scratchpad(workdir / "scratchpad.md")
    explored = []
    for topic, task in TASKS.items():  # phase 1
        findings = run_subagent(client, task)["findings"]
        pad.add(topic, findings)
        explored.append(topic)
        export_manifest(workdir / "manifest.json", "s-1", "phase1", explored, [l for l in pad.read().splitlines() if l.startswith("- ")],
                        [t for t in TASKS if t not in explored])
    phase1_summary = pad.read()
    phase2_prompt = f"{phase1_summary}\n\n[PHASE 2] Using the findings above, propose where to add refund retries."
    return {"scratchpad": phase1_summary, "phase2_prompt": phase2_prompt, "manifest": load_manifest(workdir / "manifest.json")}


def answer_later_question(client, context_extra: str, question: str = "Which class caches findById?") -> str:
    """Step 5: after many steps, is the specific reference still available?"""
    return response_text(client.messages.create(model=config.model(), max_tokens=512, messages=[
        {"role": "user", "content": f"{context_extra}\n\n[QUESTION] {question}"}]))


PRACTICE = {
    "question": "Several modules into an exploration, the agent starts citing 'typical repository patterns' instead of "
                "specific classes. Most effective mitigation?",
    "options": {"A": "A larger context window", "B": "Scratchpad files with key findings, read before later steps",
                "C": "Restart the session fresh", "D": "Pre-load the whole codebase"},
    "answer": "B",
    "why": "Findings kept outside the context can't be buried by later verbose output.",
}


# ---- mock model (SIMULATED degradation: without the scratchpad, specifics are lost) ---------------------

FINDINGS = {
    "tests": ["tests/refund.test.ts covers RefundService.issue happy path only"],
    "refund_flow": ["POST /refunds -> RefundController.create -> RefundService.issue -> OrderRepository.findById (src/repos/order.ts, cached)"],
    "integrations": ["PaymentsClient (src/clients/payments.ts) retries 3x on 5xx; no timeout set"],
}


def mock_model(kwargs: dict):
    prompt = kwargs["messages"][-1]["content"]
    if prompt.startswith("[EXPLORE]"):
        topic = next(t for t, task in TASKS.items() if task in prompt)
        verbose = "\n".join(f"read src/module_{i}.ts: " + "source line " * 12 for i in range(40))  # stays in the subagent
        return message(text(f"{verbose}\n{json.dumps({'findings': FINDINGS[topic]})}"))
    if "[QUESTION]" in prompt:
        if "OrderRepository.findById" in prompt:
            return message(text("OrderRepository (src/repos/order.ts) implements findById with custom caching."))
        return message(text("It follows the typical repository pattern with some caching."))
    return message(text("Add retries in RefundService.issue around PaymentsClient calls."))


def main():
    import tempfile

    print(mode_banner())
    with tempfile.TemporaryDirectory() as tmp:
        out = explore(get_client(mock_model), Path(tmp))
        print(out["scratchpad"])
        print(f"step 3 phase-2 prompt starts with phase-1 findings: {out['phase2_prompt'].startswith('# Key findings')}")
        print(f"step 4 manifest: phase={out['manifest']['phase']} explored={out['manifest']['exploredPaths']} next={out['manifest']['nextSteps']}")
        print(f"step 5 with scratchpad   : {answer_later_question(get_client(mock_model), out['scratchpad'])}")
        print(f"       without scratchpad: {answer_later_question(get_client(mock_model), '(20 turns of verbose output)')}")


if __name__ == "__main__":
    main()
