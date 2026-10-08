"""Task 2.3 — Tool Distribution & Tool Choice (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-3-tool-distribution-choice

4-5 tools per agent, scoped to its role. A scoped cross-role tool (verify_fact) removes
coordinator round trips for the simple case. Constrained tools (load_document) replace
generic ones (fetch_url). Forced tool_choice enforces a mandatory first step.
"""

from __future__ import annotations

import re

import anthropic

from common import config
from common.client import get_client, mode_banner
from common.mock import last_tool_results, message, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

# ---- Step 1: three roles, 4-5 role-scoped tools each (+ a coordinator with no domain tools) -----

AGENT_TOOLS = {
    "web_search": ["search_web", "fetch_page", "extract_links", "save_snippet"],
    "document_analysis": ["load_document", "extract_metadata", "extract_data_points", "summarize_content", "verify_claim"],
    "synthesis": ["compile_report", "verify_fact", "format_citation", "assess_coverage"],
    "coordinator": ["Agent", "review_output", "request_revision"],
}


def audit_toolsets(toolsets: dict[str, list[str]], max_tools: int = 5) -> list[str]:
    return [f"{agent} has {len(tools)} tools (max {max_tools})" for agent, tools in toolsets.items() if len(tools) > max_tools]


# ---- Step 2: scoped verify_fact - simple single-source lookups only -----------------------------

FACTS = {"solar efficiency 2025": "24.1%", "offshore wind growth": "18%"}


def verify_fact(claim: str, sources: list[str] | None = None) -> dict:
    if sources and len(sources) > 1 or re.search(r"\b(compare|reconcile|across)\b", claim, re.I):
        return {"is_error": True, "error": "complex verification (multi-source / judgement) - route to the coordinator"}
    key = next((k for k in FACTS if k in claim.lower()), None)
    return {"claim": claim, "verified": key is not None, "value": FACTS.get(key)}


# ---- Step 4: load_document instead of a generic fetch_url ------------------------------------

ALLOWED_DOC = re.compile(r"^https://docs\.example\.com/[\w/-]+\.(pdf|md)$")


def load_document(url: str) -> dict:
    if not ALLOWED_DOC.match(url):
        return {"is_error": True, "error": f"load_document only accepts https://docs.example.com/*.pdf|.md - rejected {url}"}
    return {"url": url, "text": "Q3 report: revenue $4.2M (audited)."}


STUBS = {
    "search_web": lambda **kw: {"results": [{"url": "https://example.org/a", "snippet": "solar efficiency 2025 hit 24.1%"}]},
    "fetch_page": lambda **kw: {"text": "page text"}, "extract_links": lambda **kw: {"links": []},
    "save_snippet": lambda **kw: {"saved": True}, "load_document": lambda **kw: load_document(**kw),
    "extract_metadata": lambda **kw: {"title": "Q3 report", "date": "2026-10-01"},
    "extract_data_points": lambda **kw: {"points": ["revenue $4.2M"]}, "summarize_content": lambda **kw: {"summary": "..."},
    "verify_claim": lambda **kw: {"supported": True}, "compile_report": lambda **kw: {"report": "done"},
    "verify_fact": lambda **kw: verify_fact(**kw), "format_citation": lambda **kw: {"citation": "[1]"},
    "assess_coverage": lambda **kw: {"coverage": "ok"},
}


def schema(name: str) -> dict:
    return {"name": name, "description": f"{name.replace('_', ' ')} (role-scoped tool)",
            "input_schema": {"type": "object", "properties": {"claim": {"type": "string"}, "url": {"type": "string"},
                                                              "query": {"type": "string"}}}}


class ToolGuard:
    """Step 5 check: refuses (and records) any call outside the agent's assigned set."""

    def __init__(self, agent: str):
        self.agent, self.violations = agent, []

    def execute(self, name: str, tool_input: dict) -> dict:
        if name not in AGENT_TOOLS[self.agent]:
            self.violations.append(name)
            return {"is_error": True, "error": f"{name} is not assigned to {self.agent}"}
        return STUBS[name](**tool_input)


# ---- Step 3: forced tool_choice for the mandatory first step, then auto ----------------------

def first_turn_tool_choice(client, messages, tools, system) -> tuple:
    """Exam answer: tool_choice {"type": "tool", "name": "extract_metadata"} on the first request only.
    Current docs: claude-sonnet-5-5 rejects forced tool_choice with a 400, so fall back to
    auto + an explicit instruction, and check the first call."""
    try:
        r = client.messages.create(model=config.model(), max_tokens=4096, tools=tools, system=system, messages=messages,
                                   tool_choice={"type": "tool", "name": "extract_metadata"})
        return r, "forced"
    except anthropic.BadRequestError:
        r = client.messages.create(model=config.model(), max_tokens=4096, tools=tools, messages=messages,
                                   system=system + " Your FIRST call must be extract_metadata.")
        return r, "auto+instruction"


def run_document_agent(client, url: str) -> dict:
    guard, tools = ToolGuard("document_analysis"), [schema(t) for t in AGENT_TOOLS["document_analysis"]]
    system = SYSTEMS["document_analysis"]
    messages = [{"role": "user", "content": f"Analyse {url}"}]
    first, mode = first_turn_tool_choice(client, messages, tools, system)
    calls = [b.name for b in first.content if b.type == "tool_use"]
    messages += [{"role": "assistant", "content": first.content},
                 {"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": str(guard.execute(b.name, b.input))}
                                              for b in first.content if b.type == "tool_use"]}]
    rest = run_agent(client, "Continue.", tools=tools, execute=guard.execute, system=system, history=messages)  # auto from here
    return {"first_call": calls[0] if calls else None, "mode": mode, "calls": calls + [c[1] for c in rest.tool_calls],
            "violations": guard.violations}


SYSTEMS = {"web_search": "You are the web search agent.", "document_analysis": "You are the document analysis agent.",
           "synthesis": "You are the synthesis agent."}


def run_agent_guarded(client, agent: str, task: str) -> dict:
    guard = ToolGuard(agent)
    r = run_agent(client, task, tools=[schema(t) for t in AGENT_TOOLS[agent]], execute=guard.execute, system=SYSTEMS[agent])
    return {"agent": agent, "calls": [c[1] for c in r.tool_calls], "violations": guard.violations}


def end_to_end(client) -> list[dict]:
    return [run_agent_guarded(client, "web_search", "Find solar efficiency data"),
            run_document_agent(client, "https://docs.example.com/q3-report.pdf"),
            run_agent_guarded(client, "synthesis", "Write the report; check 'solar efficiency 2025 was 24.1%'")]


PRACTICE = {
    "question": "A synthesis agent sends simple fact checks (85% of cases) through the coordinator: 2-3 round trips, "
                "~40% added latency. Most effective fix?",
    "options": {"A": "A scoped local verify_fact tool for simple lookups", "B": "Remove verification",
                "C": "Coordinator-level caching", "D": "More coordinator parallelism"},
    "answer": "A",
    "why": "The common simple case is handled locally; complex verification still goes through the coordinator.",
}


# ---- mock model ------------------------------------------------------------------------------

SCRIPTS = {  # agent -> tool calls it makes in order
    "You are the web search agent.": [("search_web", {"query": "solar efficiency"}), ("save_snippet", {"query": "24.1%"})],
    "You are the document analysis agent.": [("extract_metadata", {"url": "doc"}), ("extract_data_points", {"url": "doc"})],
    "You are the synthesis agent.": [("verify_fact", {"claim": "solar efficiency 2025 was 24.1%"}), ("compile_report", {})],
}


def mock_model(kwargs: dict):
    system = kwargs.get("system", "").split(" Your FIRST")[0]
    choice = kwargs.get("tool_choice") or {}
    if choice.get("type") == "tool":
        return message(tool_use(choice["name"], {"url": "doc"}))
    done = sum(1 for m in kwargs["messages"] if m["role"] == "assistant")
    script = SCRIPTS[system]
    if done < len(script):
        name, args = script[done]
        return message(tool_use(name, args))
    return message(text("Finished."))


def main():
    print(mode_banner())
    print(f"step 1 toolset audit: {audit_toolsets(AGENT_TOOLS) or 'all agents within 4-5 tools'}")
    print(f"step 2 verify_fact simple : {verify_fact('solar efficiency 2025 was 24.1%')}")
    print(f"       verify_fact complex: {verify_fact('reconcile figures across reports', ['a', 'b'])['error']}")
    print(f"step 4 load_document: {load_document('http://169.254.169.254/latest/meta-data')['error']}")
    for r in end_to_end(get_client(mock_model)):
        print(f"step 5 {r.get('agent', 'document_analysis'):18s} calls={r['calls']} violations={r['violations']}")


if __name__ == "__main__":
    main()
