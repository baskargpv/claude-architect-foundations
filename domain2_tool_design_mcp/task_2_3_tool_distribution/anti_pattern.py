"""Task 2.3 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-3-tool-distribution-choice

Trap 1  routing all simple verifications through the coordinator
Trap 2  tool_choice "auto" when structured output is required
Trap 3  giving one agent 18 tools
Trap 4  a generic fetch_url where a constrained load_document would do
"""

from __future__ import annotations

from common import config
from common.client import get_client, mode_banner
from common.mock import message, text, tool_use
from domain2_tool_design_mcp.task_2_3_tool_distribution.good_example import AGENT_TOOLS, audit_toolsets, schema


def trap1_route_everything_via_coordinator(verifications: int = 20, simple_share: float = 0.85) -> dict:
    hops_via_coordinator = 4  # synthesis -> coordinator -> doc agent -> coordinator -> synthesis
    simple = round(verifications * simple_share)
    return {"round_trips_all_via_coordinator": verifications * hops_via_coordinator,
            "round_trips_with_scoped_verify_fact": (verifications - simple) * hops_via_coordinator}


def auto_mock(kwargs):
    if (kwargs.get("tool_choice") or {}).get("type") in ("any", "tool"):
        return message(tool_use("extract_metadata", {"url": "doc"}))
    return message(text("The document looks like a Q3 report from October."))  # auto: free to answer in prose


def trap2_auto_when_structure_required(client) -> dict:
    r = client.messages.create(model=config.model(), max_tokens=1024, tools=[schema("extract_metadata")],
                               messages=[{"role": "user", "content": "Extract the metadata."}])  # tool_choice auto
    return {"got_tool_call": any(b.type == "tool_use" for b in r.content), "got": r.content[0].type}


def trap3_one_agent_18_tools() -> list[str]:
    everything = [t for tools in AGENT_TOOLS.values() for t in tools] + ["send_email", "run_sql", "delete_file", "deploy",
                                                                         "post_slack", "create_ticket"]
    return audit_toolsets({"do_everything_agent": everything[:18]})


def fetch_url(url: str) -> dict:
    return {"url": url, "status": 200, "text": "<whatever the URL returns>"}  # no constraints at all


def trap4_generic_fetch_url() -> dict:
    return fetch_url("http://169.254.169.254/latest/meta-data/iam/credentials")  # cloud metadata: misuse succeeds


def main():
    print(mode_banner())
    print(f"trap 1 via coordinator : {trap1_route_everything_via_coordinator()}")
    print(f"trap 2 tool_choice auto: {trap2_auto_when_structure_required(get_client(auto_mock))}")
    print(f"trap 3 18 tools        : {trap3_one_agent_18_tools()}")
    print(f"trap 4 fetch_url       : status {trap4_generic_fetch_url()['status']} on the cloud metadata endpoint")


if __name__ == "__main__":
    main()
