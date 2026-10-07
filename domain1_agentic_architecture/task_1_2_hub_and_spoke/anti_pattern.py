"""Task 1.2 — the coordinator the exam wants you to reject.

- "Divide into EXACTLY N subtopics": forces merging/dropping categories.
- No separate validation pass, so missing categories are never noticed.
- Bare subagent prompts ("Research: music"): the subagent never sees the goal,
  the format or prior findings, because it assumes context it doesn't have.
- Re-runs EVERY subtopic each round and stops after a fixed number of rounds.
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from domain1_agentic_architecture.task_1_2_hub_and_spoke.good_example import (
    FINDINGS_SCHEMA,
    GOAL,
    SUBTOPICS_SCHEMA,
    ResearchRun,
    coverage_map,
    mock_model,
)


def research(client, goal: str = GOAL, rounds: int = 2) -> ResearchRun:
    prompt = f"[PHASE 1: DECOMPOSE]\nResearch goal: {goal}\nDivide this into exactly 3 subtopics."
    subtopics = ask_json(client, prompt, SUBTOPICS_SCHEMA)["subtopics"]
    # (no Phase 2 validation pass)

    findings: dict[str, list[dict]] = {t: [] for t in subtopics}
    run = ResearchRun(subtopics, findings, {})
    for round_no in range(1, rounds + 1):  # fixed rounds = the exit condition
        run.rounds = round_no
        for subtopic in subtopics:  # everything, every round
            prompt = f"Research: {subtopic}"  # no goal, no format, no prior findings
            run.prompts.append(prompt)
            run.delegations.append((round_no, subtopic))
            findings[subtopic] += ask_json(client, prompt, FINDINGS_SCHEMA)["findings"]
    run.coverage = coverage_map(findings)
    return run


def main():
    print(mode_banner())
    run = research(get_client(mock_model))
    print(f"subtopics ({len(run.subtopics)}): {run.subtopics}  <- 'film and writing' merged, games never found")
    for round_no in range(1, run.rounds + 1):
        print(f"round {round_no} delegated: {[t for r, t in run.delegations if r == round_no]}  <- everything again")
    print(f"sample subagent prompt: {run.prompts[0]!r}  <- no goal, no format")
    print(f"coverage: {run.coverage}")


if __name__ == "__main__":
    main()
