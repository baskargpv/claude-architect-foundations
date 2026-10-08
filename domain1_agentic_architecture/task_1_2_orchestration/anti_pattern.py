"""Task 1.2 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-2-orchestration-patterns

Trap 1  blaming downstream subagents (e.g. "tune the search queries") when decomposition was too narrow
Trap 2  assuming subagents share memory / inherit the coordinator's history
Trap 3  direct subagent-to-subagent communication "for efficiency"
Trap 4  adding more subagents to fix a decomposition problem
Trap 5  tracing a failure to the wrong place (not to the coordinator's input)
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from domain1_agentic_architecture.task_1_2_orchestration.good_example import (
    COORDINATOR_SYSTEM,
    FINDINGS_SCHEMA,
    GOAL,
    SUBAGENT_SYSTEMS,
    SUBTOPICS_SCHEMA,
    Coordinator,
    Report,
    mock_model,
)


class NarrowCoordinator(Coordinator):
    """Same hub, but it decomposes into the 'two most important' subtopics."""

    def decompose(self, topic: str) -> list[str]:
        prompt = f"[DECOMPOSE]\nResearch goal: {GOAL}\nSplit '{topic}' into the two most important subtopics."
        return ask_json(self.client, prompt, SUBTOPICS_SCHEMA, system=COORDINATOR_SYSTEM)["subtopics"]


def trap1_blame_downstream(client) -> Report:
    """'Fix' the gap by sharpening subagent queries. The subagents still only get solar and wind."""
    class TunedQueries(NarrowCoordinator):
        @staticmethod
        def build_subagent_prompt(subtopic, prior_results, follow_up=None):
            return Coordinator.build_subagent_prompt(subtopic, prior_results, follow_up) + \
                "\nUse precise, expert-level search queries and the most authoritative sources."
    return TunedQueries(client).run()


def trap2_assume_shared_memory(client) -> list[dict]:
    """The coordinator assumes the subagent 'knows' the goal and subtopic from earlier turns."""
    prompt = "Continue researching the subtopic we discussed, for the goal I mentioned earlier."
    return ask_json(client, prompt, FINDINGS_SCHEMA, system=SUBAGENT_SYSTEMS["web_search"])["findings"]


class SubagentFailure(RuntimeError):
    pass


def trap3_direct_subagent_communication(client) -> dict:
    """Web agent hands its output straight to the document agent, skipping the hub.

    The coordinator's routing log never sees the exchange, and when the second hop
    fails there's no central place that catches it.
    """
    hub = Coordinator(client)
    web = ask_json(client, Coordinator.build_subagent_prompt("tidal", []), FINDINGS_SCHEMA, system=SUBAGENT_SYSTEMS["web_search"])

    def document_agent_receives_directly(payload):
        if not payload["findings"]:
            raise SubagentFailure("document agent got an empty hand-off from web agent")
        return payload

    try:
        document_agent_receives_directly(web)
        outcome = "ok"
    except SubagentFailure as e:  # nobody upstream knows this happened
        outcome = f"unhandled by coordinator: {e}"
    return {"outcome": outcome, "coordinator_routing_log": hub.routing_log}


def trap4_add_more_subagents(client) -> Report:
    """Add news + patent subagents. They inherit the same narrow assignments."""
    class MoreSubagents(NarrowCoordinator):
        def __init__(self, client):
            super().__init__(client)
            self.subagent_systems["news"] = SUBAGENT_SYSTEMS["web_search"]
            self.subagent_systems["patents"] = SUBAGENT_SYSTEMS["document_analysis"]

        def run(self, topic="renewable energy technologies", threshold=1.0):
            subtopics = self.decompose(topic)
            findings = {s: [f for role in ("web_search", "document_analysis", "news", "patents")
                            for f in self.delegate(role, s, [])] for s in subtopics}
            return Report(topic, subtopics, findings, self.assess_coverage(findings), 0, self.routing_log)
    return MoreSubagents(client).run()


def trap5_wrong_failure_trace(report: Report) -> str:
    """Blames whichever agent produced the output nearest the symptom."""
    return "synthesis/subagent quality: improve their prompts"  # never looks at what the coordinator assigned


def main():
    print(mode_banner())
    r = trap1_blame_downstream(get_client(mock_model))
    print(f"trap 1 tuned queries     : subtopics={r.subtopics}  <- geothermal/tidal/biomass/fusion still absent")
    f = trap2_assume_shared_memory(get_client(mock_model))
    print(f"trap 2 shared memory     : {f[0]['claim']!r}")
    d = trap3_direct_subagent_communication(get_client(mock_model))
    print(f"trap 3 direct messaging  : {d['outcome']}; hub log entries={len(d['coordinator_routing_log'])}")
    r = trap4_add_more_subagents(get_client(mock_model))
    print(f"trap 4 more subagents    : 4 subagents, subtopics={r.subtopics}")
    print(f"trap 5 wrong trace       : {trap5_wrong_failure_trace(r)!r}")


if __name__ == "__main__":
    main()
