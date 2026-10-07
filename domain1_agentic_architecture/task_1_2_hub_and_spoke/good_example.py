"""Task 1.2 — hub-and-spoke coordinator done right.

- Phase 1: breadth-first decomposition, "at least N, don't stop at N".
- Phase 2: a SEPARATE validation pass, "is anything major missing?".
- Every subagent call restates subtopic + research goal + output format + prior findings.
  Subagents share nothing; each call is a fresh, single-message request.
- Coverage map scores substantive evidence (not just non-empty); only gaps are re-delegated.
- Exit = coverage threshold met. max_rounds is the safety net.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

GOAL = "Assess the impact of generative AI on the creative industries"

SUBTOPICS_SCHEMA = {
    "type": "object",
    "properties": {"subtopics": {"type": "array", "items": {"type": "string"}}},
    "required": ["subtopics"],
    "additionalProperties": False,
}
MISSING_SCHEMA = {
    "type": "object",
    "properties": {"missing": {"type": "array", "items": {"type": "string"}}},
    "required": ["missing"],
    "additionalProperties": False,
}
FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"claim": {"type": "string"}, "evidence": {"type": "string"}},
                "required": ["claim", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}
OUTPUT_FORMAT = (
    'JSON {"findings": [{"claim": str, "evidence": str}]}. At least 2 findings; '
    "evidence must be a concrete fact, figure or named example, not a restatement of the claim."
)
MIN_SUBSTANTIVE = 2
MIN_EVIDENCE_CHARS = 20


def decompose(client, goal: str, at_least: int = 4) -> list[str]:
    """Phase 1 - discover breadth; the number is a floor, not a target."""
    prompt = (
        f"[PHASE 1: DECOMPOSE]\nResearch goal: {goal}\n"
        f"List the distinct subtopics this research must cover. Give at least {at_least}; "
        f"do not stop at {at_least} if more genuinely exist, and do not merge distinct areas to hit a number."
    )
    return ask_json(client, prompt, SUBTOPICS_SCHEMA)["subtopics"]


def validate_breadth(client, goal: str, subtopics: list[str]) -> list[str]:
    """Phase 2 - a dedicated second look beats self-critique during generation."""
    prompt = (
        f"[PHASE 2: VALIDATE]\nResearch goal: {goal}\nProposed subtopics: {json.dumps(subtopics)}\n"
        "Is anything major missing? Return only subtopics that are absent (empty list if none)."
    )
    return ask_json(client, prompt, MISSING_SCHEMA)["missing"]


def build_subagent_prompt(goal: str, subtopic: str, prior_findings: list[dict]) -> str:
    """Isolation principle: nothing is assumed carried over - restate everything, every call."""
    prior = json.dumps(prior_findings) if prior_findings else "none"
    return (
        "[SUBAGENT]\n"
        f"Research goal: {goal}\n"
        f"Your subtopic: {subtopic}\n"
        f"Prior findings on this subtopic (build on these, fill the gaps, do not repeat): {prior}\n"
        f"Output format: {OUTPUT_FORMAT}"
    )


def is_substantive(finding: dict) -> bool:
    return len(finding.get("evidence", "").strip()) >= MIN_EVIDENCE_CHARS


def coverage_map(findings: dict[str, list[dict]]) -> dict[str, bool]:
    return {t: sum(is_substantive(f) for f in fs) >= MIN_SUBSTANTIVE for t, fs in findings.items()}


@dataclass
class ResearchRun:
    subtopics: list[str]
    findings: dict[str, list[dict]]
    coverage: dict[str, bool]
    delegations: list[tuple[int, str]] = field(default_factory=list)  # (round, subtopic)
    prompts: list[str] = field(default_factory=list)
    rounds: int = 0


def research(client, goal: str = GOAL, threshold: float = 1.0, max_rounds: int = 4) -> ResearchRun:
    subtopics = decompose(client, goal)
    subtopics += [m for m in validate_breadth(client, goal, subtopics) if m not in subtopics]

    findings: dict[str, list[dict]] = {t: [] for t in subtopics}
    run = ResearchRun(subtopics, findings, {})
    to_delegate = list(subtopics)

    for round_no in range(1, max_rounds + 1):  # max_rounds = safety net only
        run.rounds = round_no
        for subtopic in to_delegate:
            prompt = build_subagent_prompt(goal, subtopic, findings[subtopic])
            run.prompts.append(prompt)
            run.delegations.append((round_no, subtopic))
            findings[subtopic] += ask_json(client, prompt, FINDINGS_SCHEMA)["findings"]

        run.coverage = coverage_map(findings)
        covered = sum(run.coverage.values()) / len(run.coverage)
        if covered >= threshold:  # the real exit condition
            break
        to_delegate = [t for t, ok in run.coverage.items() if not ok]  # re-delegate ONLY the gaps
    return run


# ---- mock model ------------------------------------------------------------------------

def _evidence(subtopic: str, n: int) -> str:
    return f"Named example #{n} with a 2025 figure for {subtopic} from an industry survey"


def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    if prompt.startswith("[PHASE 1"):
        if "exactly" in prompt:  # rigid count -> categories get merged to hit the number
            return json_message({"subtopics": ["music", "visual art", "film and writing"]})
        return json_message({"subtopics": ["music", "visual art", "film", "writing"]})
    if prompt.startswith("[PHASE 2"):
        return json_message({"missing": ["games and interactive media"]})
    if prompt.startswith("[SUBAGENT]"):
        subtopic = prompt.split("Your subtopic: ")[1].split("\n")[0]
        has_prior = "do not repeat): none" not in prompt
        if subtopic == "music" and not has_prior:
            # First pass on music comes back thin: non-empty, but not substantive.
            return json_message({"findings": [{"claim": "AI affects music", "evidence": "it does"}]})
        start = 3 if has_prior else 1
        return json_message({"findings": [{"claim": f"{subtopic} claim {i}", "evidence": _evidence(subtopic, i)} for i in (start, start + 1)]})
    # Bare prompt with no goal / format (the anti-pattern): the subagent can only guess.
    return json_message({"findings": [{"claim": "Generic remark", "evidence": ""}]})


def main():
    print(mode_banner())
    run = research(get_client(mock_model))
    print(f"subtopics ({len(run.subtopics)}): {run.subtopics}")
    for round_no in range(1, run.rounds + 1):
        print(f"round {round_no} delegated: {[t for r, t in run.delegations if r == round_no]}")
    print(f"coverage: {run.coverage}")


if __name__ == "__main__":
    main()
