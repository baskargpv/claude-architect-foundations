"""Task 5.3 — Error Propagation in Multi-Agent Systems (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-3-error-propagation

Structured error context = failure type + attempted action + partial results + alternatives.
It gives the coordinator a middle ground between "bare exception" (-> kill the pipeline) and
"empty success" (-> silent gap). Recover transient failures locally before propagating.
"""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel

# ---- Step 1: the structured error schema --------------------------------------------------------

class SubagentResult(BaseModel):
    status: Literal["success", "partial_failure", "failure"]
    failureType: Literal["transient", "validation", "business", "permission"] | None = None
    attemptedAction: str | None = None
    partialResults: list[str] = []
    alternativeApproaches: list[str] = []
    shouldRetry: bool = False
    results: list[str] = []


# ---- Step 2: a search subagent that tells access failure apart from a valid empty result ------------

class Source:
    def __init__(self, name: str, results: list[str] | None, fails_times: int = 0):
        self.name, self.results, self.fails_left = name, results, fails_times

    def query(self, q: str) -> list[str]:
        if self.fails_left != 0:
            self.fails_left -= 1
            raise TimeoutError(f"{self.name} timed out after 30s")
        return self.results or []


# ---- Step 3: local retry with exponential backoff (1s, 2s, 4s - scaled), keeping partial results -----

def search_with_recovery(sources: list[Source], query: str, attempts: int = 3, base_delay: float = 0.001) -> SubagentResult:
    gathered, failed = [], []
    for src in sources:
        for attempt in range(attempts):
            try:
                gathered += [f"{src.name}: {r}" for r in src.query(query)]
                break
            except TimeoutError:
                if attempt == attempts - 1:
                    failed.append(src.name)
                else:
                    time.sleep(base_delay * 2 ** attempt)
    if not failed:
        return SubagentResult(status="success", results=gathered)  # may be empty - and that's a valid answer
    return SubagentResult(status="partial_failure", failureType="transient", partialResults=gathered,
                          attemptedAction=f"query {query!r} against {[s.name for s in sources]}; {failed} timed out after {attempts} attempts",
                          alternativeApproaches=[f"retry {failed[0]} later", "use cached results", "try a broader query"],
                          shouldRetry=True)


# ---- Step 4: the coordinator handles each outcome without suppressing anything ------------------------

def coordinate(results: dict[str, SubagentResult]) -> dict:
    coverage, actions = {}, []
    for topic, r in results.items():
        if r.status == "success":
            coverage[topic] = ("well-supported", "") if r.results else ("unavailable", "searched successfully - no sources exist")
        elif r.partialResults:
            coverage[topic] = ("limited", r.attemptedAction)
            actions.append(f"{topic}: proceed with {len(r.partialResults)} partial results; next try: {r.alternativeApproaches[0]}")
        else:
            coverage[topic] = ("unavailable", r.attemptedAction)
            actions.append(f"{topic}: try alternative - {r.alternativeApproaches[0]}")
    return {"coverage": coverage, "actions": actions}


# ---- Step 5: coverage section in the synthesis output -----------------------------------------------

def coverage_section(coverage: dict) -> str:
    lines = ["## Coverage"]
    for topic, (level, reason) in coverage.items():
        lines.append(f"- {topic}: {level}" + (f" ({reason})" if reason else ""))
    return "\n".join(lines)


def demo_results() -> dict[str, SubagentResult]:
    return {
        "solar": search_with_recovery([Source("news", ["solar output up 12%"]), Source("journals", ["perovskite record"])], "solar"),
        "geothermal": search_with_recovery([Source("news", ["Iceland plant expands"]), Source("journals", None, fails_times=-1)], "geothermal"),
        "fusion": search_with_recovery([Source("journals", ["tokamak record"], fails_times=2)], "fusion"),  # recovers locally
        "space solar": search_with_recovery([Source("patents", [])], "space solar"),  # valid empty
    }


PRACTICE = {
    "question": "A web search subagent times out mid-research. What best enables intelligent coordinator recovery?",
    "options": {"A": "Return an empty result marked successful", "B": "Terminate the whole workflow",
                "C": "Structured error context: failure type, query, partial results, alternatives",
                "D": "Retry with backoff, then return a generic 'search unavailable'"},
    "answer": "C",
    "why": "The coordinator can assess the damage, retry, try an alternative, or proceed with partial results.",
}


def main():
    results = demo_results()
    for topic, r in results.items():
        print(f"{topic:12s} -> {r.status:16s} shouldRetry={r.shouldRetry} partial={r.partialResults}")
    plan = coordinate(results)
    print("\n".join(plan["actions"]))
    print(coverage_section(plan["coverage"]))


if __name__ == "__main__":
    main()
