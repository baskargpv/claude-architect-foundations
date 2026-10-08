"""Task 1.3 — Implement Context Passing with Structured Metadata (lesson Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-3-subagent-invocation-context

The coordinator is a tool-using agent whose spawn tool is `Agent` (exam guide: `Task`).
Options and AgentDefinitions are shaped like claude-agent-sdk's ClaudeAgentOptions /
AgentDefinition but run on the Messages API so everything works offline.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, model_validator

from common import config
from common.client import get_client, mode_banner, parse_json_object, response_text
from common.mock import last_tool_results, message, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

SPAWN_TOOL_NAMES = {"Agent", "Task"}  # current name, exam-guide name (Task is still an alias)


# ---- Step 2: two subagents, each with description + system prompt + restricted tools ----------

@dataclass
class AgentDefinition:
    description: str  # the coordinator uses this to decide when to invoke it
    prompt: str  # the subagent's system prompt
    tools: list[str]  # scoped to the role


@dataclass
class AgentOptions:
    allowed_tools: list[str]
    agents: dict[str, AgentDefinition]
    unattended: bool = True  # CI / batch run: nobody is there to approve a permission prompt


SUBAGENTS = {
    "web_search_agent": AgentDefinition(
        description="Searches the public web. Returns findings with source_url and document_name (page title).",
        prompt="You are a web research subagent. Use web_search, then return JSON "
               '{"findings": [{"claim", "source_url", "document_name", "confidence"}]}. Never drop a source.',
        tools=["web_search"],  # search only - no file access
    ),
    "document_analysis_agent": AgentDefinition(
        description="Reads internal documents. Returns findings with document_name and page_number.",
        prompt="You are a document analysis subagent. Use read_document, then return JSON "
               '{"findings": [{"claim", "document_name", "page_number", "confidence"}]}. Never drop a page reference.',
        tools=["read_document"],  # file reading only - no web access
    ),
}

# Step 1: Agent in allowed_tools alongside the coordinator's own tools; subagents under `agents`
COORDINATOR_OPTIONS = AgentOptions(allowed_tools=["Agent"], agents=SUBAGENTS)


def spawn_decision(options: AgentOptions) -> str:
    """Exam answer: no Agent/Task in allowed_tools -> cannot spawn.
    Current docs: allowed_tools is an auto-approve list; without it the spawn goes to the
    permission check, which denies it in an unattended run (same outcome there)."""
    if SPAWN_TOOL_NAMES & set(options.allowed_tools):
        return "allow"
    return "deny" if options.unattended else "ask"


def scope_violations(agents: dict[str, AgentDefinition]) -> list[str]:
    problems = []
    if set(agents["web_search_agent"].tools) - {"web_search"}:
        problems.append("web_search_agent can do more than search")
    if set(agents["document_analysis_agent"].tools) - {"read_document"}:
        problems.append("document_analysis_agent can do more than read documents")
    return problems


# ---- the subagents' own tools (stubs) ---------------------------------------------------------

WEB_INDEX = [
    {"url": "https://example.org/solar-efficiency-2025", "title": "Global Solar Industry Report 2025",
     "snippet": "Commercial monocrystalline panels reached 24.1% average efficiency in 2025."},
    {"url": "https://example.net/wind-capacity", "title": "Wind Market Outlook",
     "snippet": "Offshore wind capacity grew 18% year over year."},
]
DOCUMENTS = {"Grid Integration Study.pdf": {
    12: "Battery storage cut curtailment of solar output by 31% in the pilot region.",
    27: "Grid upgrade costs averaged $1.4M per 100 MW of new renewable capacity."}}

SUBAGENT_TOOL_DEFS = {
    "web_search": {"name": "web_search", "description": "Search the web; returns url, title, snippet.",
                   "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    "read_document": {"name": "read_document", "description": "Read an internal document; returns text by page number.",
                      "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
}


def run_subagent_tool(name: str, tool_input: dict) -> dict:
    if name == "web_search":
        return {"results": WEB_INDEX}
    if name == "read_document":
        return {"name": tool_input["name"], "pages": DOCUMENTS.get(tool_input["name"], {})}
    return {"is_error": True, "error": f"tool {name} not available to this subagent"}


# ---- Step 3: structured findings - content separated from metadata ----------------------------

class Finding(BaseModel):
    claim: str  # content
    source_url: str | None = None  # metadata (web)
    document_name: str | None = None  # metadata (web title, or internal document)
    page_number: int | None = None  # metadata (documents)
    confidence: Literal["high", "medium", "low"]
    retrieved_by: Literal["web_search_agent", "document_analysis_agent"]

    @model_validator(mode="after")
    def metadata_matches_retriever(self):
        if self.retrieved_by == "web_search_agent" and not self.source_url:
            raise ValueError("web finding without source_url")
        if self.retrieved_by == "document_analysis_agent" and not (self.document_name and self.page_number):
            raise ValueError("document finding without document_name/page_number")
        return self

    def citation(self) -> str:
        return self.source_url if self.source_url else f"{self.document_name} p.{self.page_number}"


# ---- the coordinator ---------------------------------------------------------------------------

AGENT_TOOL = {
    "name": "Agent",
    "description": "Spawn a subagent. It sees ONLY the prompt you write - include the goal, its subtopic and "
                   "any context it needs. Emit several Agent calls in one response to run independent work in parallel.",
    "input_schema": {"type": "object", "required": ["subagent_type", "prompt"],
                     "properties": {"subagent_type": {"type": "string", "enum": list(SUBAGENTS)},
                                    "prompt": {"type": "string"}}},
}

COORDINATOR_SYSTEM = ("You coordinate research. Available subagents: "
                      + "; ".join(f"{n}: {d.description}" for n, d in SUBAGENTS.items())
                      + ". Spawn independent research in parallel. State goals and quality criteria, not step-by-step procedures.")

GOAL = "How are solar generation and grid integration evolving? Every claim must be attributable."


@dataclass
class Spawner:
    client: object
    options: AgentOptions
    spawn_log: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def spawn(self, subagent_type: str, prompt: str) -> dict:
        if spawn_decision(self.options) != "allow":
            return {"is_error": True, "error": "Agent tool not permitted for this coordinator"}
        definition = self.options.agents[subagent_type]
        self.spawn_log.append({"subagent": subagent_type, "prompt": prompt})
        tools = [SUBAGENT_TOOL_DEFS[t] for t in definition.tools]
        result = run_agent(self.client, prompt, tools=tools, execute=run_subagent_tool, system=definition.prompt)
        raw = parse_json_object(result.final_text)["findings"]
        found = [Finding(retrieved_by=subagent_type, **f) for f in raw]
        self.findings += found
        return {"findings": [f.model_dump(exclude_none=True) for f in found]}

    def execute_parallel(self, blocks: list) -> list[dict]:
        """Step 6: every Agent call from ONE coordinator response runs concurrently."""
        with ThreadPoolExecutor(max_workers=max(1, len(blocks))) as pool:
            futures = [pool.submit(self.spawn, b.input["subagent_type"], b.input["prompt"]) for b in blocks]
            return [f.result() for f in futures]


def run_research(client, options: AgentOptions = COORDINATOR_OPTIONS, goal: str = GOAL) -> Spawner:
    spawner = Spawner(client, options)
    messages: list = [{"role": "user", "content": goal}]
    for _ in range(5):
        response = client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS, system=COORDINATOR_SYSTEM,
                                          tools=[AGENT_TOOL], messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        blocks = [b for b in response.content if b.type == "tool_use" and b.name in SPAWN_TOOL_NAMES]
        outputs = spawner.execute_parallel(blocks)  # waits for all before continuing
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(o), "is_error": bool(o.get("is_error"))}
            for b, o in zip(blocks, outputs)]})
    return spawner


# ---- Steps 4-5: full structured hand-off to synthesis, then verify attribution ----------------

SYNTHESIS_SYSTEM = "You are a synthesis subagent. Write a short report; cite every claim with its source_url, or document_name p.N."


def build_synthesis_prompt(goal: str, findings: list[Finding]) -> str:
    payload = json.dumps({"findings": [f.model_dump(exclude_none=True) for f in findings]}, indent=2)
    return f"Goal: {goal}\nFindings (complete structured records - keep every source):\n{payload}"


def synthesize(client, prompt: str) -> str:
    response = client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS, system=SYNTHESIS_SYSTEM,
                                      messages=[{"role": "user", "content": prompt}])
    return response_text(response)


def verify_attribution(report: str, findings: list[Finding]) -> list[str]:
    """Claims that appear in the report without their citation on the same line."""
    lines = report.splitlines()
    return [f.claim for f in findings
            if not any(f.claim in line and f.citation() in line for line in lines)]


def trace_attribution_gap(synthesis_prompt: str, findings: list[Finding]) -> str:
    """Diagnose from what REACHED synthesis, not from the synthesis wording."""
    missing = [f.citation() for f in findings if f.citation() not in synthesis_prompt
               and str(f.page_number or "") not in synthesis_prompt]
    return "coordinator handoff dropped metadata" if missing else "metadata reached synthesis"


def run(client, options: AgentOptions = COORDINATOR_OPTIONS) -> dict:
    spawner = run_research(client, options)
    prompt = build_synthesis_prompt(GOAL, spawner.findings)
    report = synthesize(client, prompt)
    return {"spawner": spawner, "synthesis_prompt": prompt, "report": report,
            "unattributed": verify_attribution(report, spawner.findings)}


PRACTICE = {
    "question": "A synthesis report has unsourced claims although both research subagents return correct "
                "URLs and page references. Most likely root cause?",
    "options": {"A": "Synthesis agent needs its own web search access",
                "B": "The coordinator passes content without structured metadata",
                "C": "The synthesis prompt lacks citation instructions",
                "D": "The web subagent's output format is unparseable"},
    "answer": "B",
    "why": "The synthesis agent can only cite what it receives; trace the gap to the coordinator's handoff.",
}


# ---- mock model --------------------------------------------------------------------------------

def mock_model(kwargs: dict):
    system = kwargs.get("system", "")
    results = last_tool_results(kwargs)
    if system == COORDINATOR_SYSTEM:
        if results:
            return message(text("Both research subagents have reported back."))
        return message(  # both spawns in ONE response -> parallel
            text("I'll research the web and internal documents in parallel."),
            tool_use("Agent", {"subagent_type": "web_search_agent",
                               "prompt": f"Goal: {GOAL}\nSubtopic: solar efficiency and wind growth. "
                                         "Quality bar: every finding has source_url and page title."}),
            tool_use("Agent", {"subagent_type": "document_analysis_agent",
                               "prompt": f"Goal: {GOAL}\nSubtopic: grid integration. Document: Grid Integration Study.pdf. "
                                         "Quality bar: every finding has document_name and page_number."}),
        )
    if system == SUBAGENTS["web_search_agent"].prompt:
        if not results:
            return message(tool_use("web_search", {"query": "solar panel efficiency 2025"}))
        hits = json.loads(results[-1]["content"])["results"]
        return message(text(json.dumps({"findings": [
            {"claim": h["snippet"], "source_url": h["url"], "document_name": h["title"], "confidence": "high"} for h in hits]})))
    if system == SUBAGENTS["document_analysis_agent"].prompt:
        prompt = kwargs["messages"][0]["content"]
        if not results:
            if "Grid Integration Study.pdf" not in prompt:  # nothing tells it which document
                return message(text(json.dumps({"findings": []})))
            return message(tool_use("read_document", {"name": "Grid Integration Study.pdf"}))
        doc = json.loads(results[-1]["content"])
        return message(text(json.dumps({"findings": [
            {"claim": t, "document_name": doc["name"], "page_number": int(p), "confidence": "high"}
            for p, t in doc["pages"].items()]})))
    if system.startswith("You are a synthesis subagent"):
        prompt = kwargs["messages"][0]["content"]
        try:
            records = json.loads(prompt.split("keep every source):\n", 1)[1])["findings"]
            lines = [f"- {r['claim']} ({r.get('source_url') or str(r.get('document_name')) + ' p.' + str(r.get('page_number'))})"
                     for r in records]
        except (IndexError, ValueError, KeyError):  # only bare claim text arrived
            lines = [f"- {line.strip()}" for line in prompt.split("Findings:\n", 1)[-1].splitlines() if line.strip()]
        return message(text("Report:\n" + "\n".join(lines)))
    raise ValueError(f"unexpected system prompt: {system[:50]}")


def main():
    print(mode_banner())
    print(f"spawn decision: {spawn_decision(COORDINATOR_OPTIONS)}; scope violations: {scope_violations(SUBAGENTS) or 'none'}")
    out = run(get_client(mock_model))
    print(f"subagents spawned: {[s['subagent'] for s in out['spawner'].spawn_log]}")
    print(out["report"])
    print(f"unattributed claims: {out['unattributed'] or 'none'}")


if __name__ == "__main__":
    main()
