"""Task 1.3 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-3-subagent-invocation-context

Trap 1  assuming subagents can see the coordinator's history or other subagents' output
Trap 2  blaming the synthesis agent for missing citations (the handoff dropped the metadata)
Trap 3  invoking independent subagents sequentially
Trap 4  confusing fork_session with --resume
"""

from __future__ import annotations

import copy
import threading
import time

from common.client import get_client, mode_banner
from common.mock import MockClient
from domain1_agentic_architecture.task_1_3_subagent_context.good_example import (
    COORDINATOR_OPTIONS,
    COORDINATOR_SYSTEM,
    GOAL,
    Finding,
    Spawner,
    mock_model,
    run_research,
    synthesize,
    verify_attribution,
)


def trap1_assume_inherited_context(client) -> list[Finding]:
    """'Analyse the document we found earlier' - the subagent never saw 'earlier'."""
    spawner = Spawner(client, COORDINATOR_OPTIONS)
    spawner.spawn("document_analysis_agent", "Analyse the document we found earlier and report the key numbers.")
    return spawner.findings


def strip_metadata_prompt(findings: list[Finding], extra_instructions: str = "") -> str:
    claims = "\n".join(f.claim for f in findings)  # WRONG: every source_url / document_name / page dropped
    return f"Goal: {GOAL}\n{extra_instructions}Findings:\n{claims}"


def trap2_blame_synthesis(client) -> dict:
    """Strip metadata at the handoff, then 'fix' it by strengthening the synthesis prompt."""
    findings = run_research(client).findings
    before = synthesize(client, strip_metadata_prompt(findings))
    after = synthesize(client, strip_metadata_prompt(
        findings, "IMPORTANT: cite a source URL and page number for EVERY claim.\n"))
    return {"unattributed_before": verify_attribution(before, findings),
            "unattributed_after_prompt_fix": verify_attribution(after, findings)}


class ConcurrencyTracker:
    def __init__(self):
        self.active = self.peak = 0
        self.lock = threading.Lock()

    def wrap(self, responder):
        def tracked(kwargs):
            with self.lock:
                self.active += 1
                self.peak = max(self.peak, self.active)
            time.sleep(0.02)
            try:
                return responder(kwargs)
            finally:
                with self.lock:
                    self.active -= 1
        return tracked


class SequentialSpawner(Spawner):
    def execute_parallel(self, blocks):  # WRONG: independent work, one at a time
        return [self.spawn(b.input["subagent_type"], b.input["prompt"]) for b in blocks]


def trap3_sequential_invocation(responder=mock_model) -> int:
    """Returns the peak number of subagent calls in flight (1 = fully sequential)."""
    tracker = ConcurrencyTracker()
    client = MockClient(tracker.wrap(responder))
    spawner = SequentialSpawner(client, COORDINATOR_OPTIONS)
    response = mock_model({"system": COORDINATOR_SYSTEM, "messages": [{"role": "user", "content": GOAL}]})
    spawner.execute_parallel([b for b in response.content if b.type == "tool_use"])
    return tracker.peak


def trap4_confuse_fork_with_resume(session: list) -> dict:
    """Wants to compare two approaches from one baseline, but 'resumes' twice instead of forking."""
    baseline_len = len(session)
    session.append({"role": "user", "content": "Approach A: summarise by technology"})  # resume #1 appends...
    session.append({"role": "user", "content": "Approach B: summarise by region"})  # ...resume #2 appends to the SAME history
    fork_a, fork_b = copy.deepcopy(session[:baseline_len]), copy.deepcopy(session[:baseline_len])  # what fork_session gives
    return {"resumed_history_len": len(session), "baseline_len": baseline_len,
            "approach_b_sees_approach_a": any("Approach A" in m["content"] for m in session),
            "forks_independent": fork_a is not fork_b and len(fork_a) == len(fork_b) == baseline_len}


def main():
    print(mode_banner())
    f = trap1_assume_inherited_context(get_client(mock_model))
    print(f"trap 1 inherited context : document agent returned {len(f)} findings  <- it was never told which document")
    r = trap2_blame_synthesis(get_client(mock_model))
    print(f"trap 2 blame synthesis   : unattributed before={len(r['unattributed_before'])}, "
          f"after strengthening the synthesis prompt={len(r['unattributed_after_prompt_fix'])}")
    print(f"trap 3 sequential spawns : peak concurrent subagent calls = {trap3_sequential_invocation()}")
    r = trap4_confuse_fork_with_resume([{"role": "user", "content": "baseline analysis"}])
    print(f"trap 4 fork vs resume    : approach B sees approach A = {r['approach_b_sees_approach_a']}")


if __name__ == "__main__":
    main()
