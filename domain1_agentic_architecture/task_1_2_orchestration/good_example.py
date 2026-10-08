"""Task 1.2 — Build a Hub-and-Spoke Research Coordinator (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-2-orchestration-patterns

All communication flows through the coordinator. Subagents start with isolated context:
no coordinator history, no other subagent's output, no shared memory - only what the
coordinator writes into their prompt. Every routed message is logged (observability).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

TOPIC = "renewable energy technologies"
GOAL = f"Produce a structured report covering the full breadth of {TOPIC}"
REQUIRED_SUBTOPICS = {"solar", "wind", "geothermal", "tidal", "biomass", "nuclear fusion"}  # Step 6

# ---- Step 1: the coordinator is the orchestrating hub ------------------------------------------

COORDINATOR_SYSTEM = (
    "You are the coordinator of a research system. You own decomposition, subagent selection and "
    "aggregation. Subagents never talk to each other; everything routes through you."
)

SUBAGENT_SYSTEMS = {  # Step 3: two subagents with their own roles
    "web_search": "You are a web search subagent. Return findings from public web sources, each with its source URL.",
    "document_analysis": "You are a document analysis subagent. Return findings from the internal document library, each citing document and page.",
}

SUBTOPICS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["subtopics"],
                    "properties": {"subtopics": {"type": "array", "items": {"type": "string"}}}}
FINDINGS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"],
                   "properties": {"findings": {"type": "array", "items": {
                       "type": "object", "additionalProperties": False, "required": ["claim", "source"],
                       "properties": {"claim": {"type": "string"}, "source": {"type": "string"}}}}}}

WELL_COVERED_MIN = 3  # sourced findings needed for "well-covered"; 1-2 = partial; 0 = missing


@dataclass
class Report:
    topic: str
    subtopics: list[str]
    findings: dict[str, list[dict]]
    coverage: dict[str, str]
    iterations: int
    routing_log: list[dict] = field(default_factory=list)  # every hub <-> spoke message


class Coordinator:
    def __init__(self, client, max_iterations: int = 3):
        self.client = client
        self.max_iterations = max_iterations  # safety net; the threshold is the real exit
        self.routing_log: list[dict] = []
        self.subagent_systems = dict(SUBAGENT_SYSTEMS)

    # Step 2: decomposition covering the full breadth
    def decompose(self, topic: str) -> list[str]:
        prompt = (f"[DECOMPOSE]\nResearch goal: {GOAL}\nSplit '{topic}' into at least five distinct subtopics "
                  "that together cover its full breadth. Don't merge distinct areas; list every major category.")
        return ask_json(self.client, prompt, SUBTOPICS_SCHEMA, system=COORDINATOR_SYSTEM)["subtopics"]

    # Step 3: every subagent prompt carries subtopic + goal + relevant earlier results
    @staticmethod
    def build_subagent_prompt(subtopic: str, prior_results: list[dict], follow_up: str | None = None) -> str:
        prompt = (f"Research goal: {GOAL}\n"
                  f"Your assigned subtopic: {subtopic}\n"
                  f"Relevant results already gathered by other agents: {json.dumps(prior_results) if prior_results else 'none'}\n"
                  "Return findings as JSON, each with a claim and a source.")
        if follow_up:
            prompt += f"\nTargeted follow-up: {follow_up}"
        return prompt

    def delegate(self, role: str, subtopic: str, prior_results: list[dict], follow_up: str | None = None) -> list[dict]:
        prompt = self.build_subagent_prompt(subtopic, prior_results, follow_up)
        self.routing_log.append({"to": role, "subtopic": subtopic, "follow_up": bool(follow_up), "prompt": prompt})
        findings = ask_json(self.client, prompt, FINDINGS_SCHEMA, system=self.subagent_systems[role])["findings"]
        for f in findings:
            f["retrieved_by"] = role
        self.routing_log.append({"from": role, "subtopic": subtopic, "n_findings": len(findings)})
        return findings

    # Step 4: aggregate and label coverage
    @staticmethod
    def assess_coverage(findings: dict[str, list[dict]]) -> dict[str, str]:
        labels = {}
        for subtopic, fs in findings.items():
            n = sum(1 for f in fs if f.get("source"))
            labels[subtopic] = "well-covered" if n >= WELL_COVERED_MIN else "partial" if n else "missing"
        return labels

    def run(self, topic: str = TOPIC, threshold: float = 1.0) -> Report:
        subtopics = self.decompose(topic)
        findings: dict[str, list[dict]] = {}
        for s in subtopics:
            web = self.delegate("web_search", s, prior_results=[])
            docs = self.delegate("document_analysis", s, prior_results=web)  # coordinator passes web results on
            findings[s] = web + docs
        coverage = self.assess_coverage(findings)

        # Step 5: re-delegate only the gaps until the threshold is met (or the safety cap)
        iterations = 0
        while sum(v == "well-covered" for v in coverage.values()) / len(coverage) < threshold:
            if iterations == self.max_iterations:
                break
            iterations += 1
            for s, label in coverage.items():
                if label == "well-covered":
                    continue
                role = self.relevant_subagent(findings[s])
                gap = f"'{s}' is {label} ({len(findings[s])} sourced findings); find more sourced evidence."
                findings[s] += self.delegate(role, s, prior_results=findings[s], follow_up=gap)
            coverage = self.assess_coverage(findings)
        return Report(topic, subtopics, findings, coverage, iterations, self.routing_log)

    @staticmethod
    def relevant_subagent(fs: list[dict]) -> str:
        web = sum(f["retrieved_by"] == "web_search" for f in fs)
        return "web_search" if web <= len(fs) - web else "document_analysis"


def trace_coverage_failure(report: Report, required: set[str] = REQUIRED_SUBTOPICS) -> str:
    """Trace a gap to its origin: was the category ever assigned?"""
    assigned = {s.lower() for s in report.subtopics}
    never_assigned = sorted(required - assigned)
    if never_assigned:
        return f"coordinator decomposition: never assigned {never_assigned}"
    weak = sorted(s for s, v in report.coverage.items() if v != "well-covered")
    return f"subagent coverage: assigned but weak {weak}" if weak else "no gap"


PRACTICE = {
    "question": "A renewable-energy report covers only solar and wind although every subagent did solid "
                "work on its assignment. Most likely root cause?",
    "options": {"A": "Document analysis subagent lacked sources for the other categories",
                "B": "Synthesis subagent didn't notice the gaps",
                "C": "Web search queries were too narrow",
                "D": "The coordinator decomposed the topic into only solar and wind"},
    "answer": "D",
    "why": "Subagents can only research what they're assigned; the gap originates in decomposition.",
}


# ---- mock model ------------------------------------------------------------------------------

def _sourced(subtopic: str, role: str, n: int, start: int = 1) -> dict:
    src = "https://example.org/{}/{}" if role == "web_search" else "Energy Library: {} report p.{}"
    return {"findings": [{"claim": f"{subtopic} finding {i}", "source": src.format(subtopic.replace(' ', '-'), i)}
                         for i in range(start, start + n)]}


INITIAL_YIELD = {  # (web, docs) sourced findings on the first pass
    "solar": (2, 1), "wind": (2, 1), "geothermal": (2, 1), "biomass": (2, 1),
    "tidal": (0, 0),            # missing
    "nuclear fusion": (1, 1),   # partial
}


def mock_model(kwargs: dict):
    prompt, system = last_user_text(kwargs), kwargs.get("system", "")
    if prompt.startswith("[DECOMPOSE]"):
        if "two most important" in prompt:  # the narrow decomposition from the anti-pattern
            return json_message({"subtopics": ["solar", "wind"]})
        return json_message({"subtopics": sorted(REQUIRED_SUBTOPICS)})
    role = "web_search" if system == SUBAGENT_SYSTEMS["web_search"] else "document_analysis"
    if "Your assigned subtopic: " not in prompt:  # no explicit context: the subagent can only guess
        return json_message({"findings": [{"claim": "Unclear what to research - no subtopic or goal given", "source": ""}]})
    subtopic = prompt.split("Your assigned subtopic: ")[1].split("\n")[0]
    if "Targeted follow-up" in prompt:
        return json_message(_sourced(subtopic, role, 2, start=10 + len(prompt) % 7))
    web_n, doc_n = INITIAL_YIELD.get(subtopic, (2, 1))
    return json_message(_sourced(subtopic, role, web_n if role == "web_search" else doc_n))


def main():
    print(mode_banner())
    report = Coordinator(get_client(mock_model)).run()
    print(f"decomposition ({len(report.subtopics)}): {report.subtopics}")
    print(f"refinement iterations: {report.iterations}")
    for s, label in report.coverage.items():
        print(f"  {s:15s} {label:13s} {len(report.findings[s])} findings")
    print(f"routed messages logged by the hub: {len(report.routing_log)}")
    print(f"trace: {trace_coverage_failure(report)}")


if __name__ == "__main__":
    main()
