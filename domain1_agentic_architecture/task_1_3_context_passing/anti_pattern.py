"""Task 1.3 — how attribution dies before synthesis ever sees it.

1. Subagents defined in `agents`, but 'Agent'/'Task' missing from allowed_tools:
   the coordinator cannot spawn any of them.
2. Over-broad subagent tools: the web agent can read files, the doc agent can browse.
3. THE exam target: the coordinator flattens findings to claim text
   ("\n".join(f.claim ...), the Python twin of .map(f => f.claim).join(...)) and every
   source_url / document_name / page_number is silently dropped. The synthesis prompt
   is blameless; it never received the metadata.
"""

from __future__ import annotations

from common.client import get_client, mode_banner
from domain1_agentic_architecture.task_1_3_context_passing.good_example import (
    GOAL,
    Finding,
    can_spawn_subagents,
    gather_findings,
    mock_model,
    synthesize,
    tool_scope_violations,
)

BROKEN_OPTIONS = {
    "allowed_tools": ["WebSearch", "Read", "Grep"],  # no 'Agent' -> no subagents, whatever `agents` says
    "agents": {
        "web_search_agent": {"description": "...", "prompt": "...", "tools": ["WebSearch", "Read", "Grep"]},
        "document_analysis_agent": {"description": "...", "prompt": "...", "tools": ["Read", "Grep", "WebSearch"]},
    },
}


def build_synthesis_prompt(goal: str, findings: list[Finding]) -> str:
    claims = "\n".join(f.claim for f in findings)  # WRONG: strips every metadata field
    return (
        f"[SYNTHESIS]\nGoal: {goal}\n"
        "Write a short report. Cite every claim with its source.\n"  # asking nicely can't restore data
        f"Findings:\n{claims}"
    )


def run(client, goal: str = GOAL) -> tuple[str, str]:
    findings = gather_findings(client, goal)
    prompt = build_synthesis_prompt(goal, findings)
    return prompt, synthesize(client, prompt)


def main():
    print(mode_banner())
    print(f"coordinator can spawn subagents: {can_spawn_subagents(BROKEN_OPTIONS)}  <- agents defined, never granted")
    print(f"tool scope violations: {tool_scope_violations(BROKEN_OPTIONS['agents'])}")
    _, report = run(get_client(mock_model))
    print(report)
    print("^ every claim unsourced - diagnose by checking what reached the synthesis prompt FIRST")


if __name__ == "__main__":
    main()
