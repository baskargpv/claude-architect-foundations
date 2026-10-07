"""Task 1.3 — context passing that keeps attribution alive.

- The coordinator must hold the Agent tool (exam: "Task") in allowed_tools to spawn
  ANY subagent. Defining subagents in `agents` grants nothing on its own.
- Each subagent gets only the tools its job needs (web: WebSearch; docs: Read/Grep).
- Findings are structured: content (claim) + metadata whose shape depends on retrieved_by.
- Independent subagents run in parallel; the coordinator waits for both.
- The FULL structured array goes to synthesis (json.dumps), never just claim text.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from pydantic import BaseModel, model_validator

from common.client import ask_json, get_client, mode_banner, response_text
from common import config
from common.mock import json_message, last_user_text, message, text

# ---- configuration (shape mirrors claude-agent-sdk ClaudeAgentOptions / AgentDefinition) ----

SUBAGENTS = {
    "web_search_agent": {
        "description": "Finds and quotes public web sources. Returns claims with source_url.",
        "prompt": "You research the public web. Every claim must carry its source_url.",
        "tools": ["WebSearch"],  # no file access
    },
    "document_analysis_agent": {
        "description": "Extracts claims from internal documents. Returns document_name and page_number.",
        "prompt": "You analyse internal documents. Every claim must carry document_name and page_number.",
        "tools": ["Read", "Grep"],  # no web access
    },
}

COORDINATOR_OPTIONS = {
    "allowed_tools": ["Agent"],  # the deliberate, separate grant to spawn subagents ("Task" in exam guide v1.0)
    "agents": SUBAGENTS,
}

SPAWN_TOOL_NAMES = {"Agent", "Task"}  # current name, exam-guide name


def can_spawn_subagents(options: dict) -> bool:
    """Subagent definitions do not imply permission to invoke them."""
    return bool(SPAWN_TOOL_NAMES & set(options.get("allowed_tools", [])))


def tool_scope_violations(agents: dict) -> list[str]:
    problems = []
    if {"Read", "Grep", "Write"} & set(agents["web_search_agent"]["tools"]):
        problems.append("web_search_agent has file access")
    if {"WebSearch", "WebFetch"} & set(agents["document_analysis_agent"]["tools"]):
        problems.append("document_analysis_agent has web access")
    return problems


# ---- the Finding schema --------------------------------------------------------------------

class Finding(BaseModel):
    claim: str  # content
    retrieved_by: Literal["web_search_agent", "document_analysis_agent"]
    confidence: Literal["high", "medium", "low"]
    source_url: str | None = None  # metadata: web only
    document_name: str | None = None  # metadata: documents only
    page_number: int | None = None  # metadata: documents only

    @model_validator(mode="after")
    def metadata_matches_retriever(self):
        if self.retrieved_by == "web_search_agent" and not self.source_url:
            raise ValueError("web finding without source_url")
        if self.retrieved_by == "document_analysis_agent" and not (self.document_name and self.page_number):
            raise ValueError("document finding without document_name/page_number")
        return self


# ---- source material (stands in for what WebSearch / Read would return) --------------------

WEB_SOURCES = [
    {"url": "https://example.org/creative-ai-survey-2025",
     "text": "A 2025 survey of 2,000 illustrators found 41% now use generative tools weekly."},
    {"url": "https://example.net/music-licensing-report",
     "text": "Music licensing disputes involving AI-generated tracks tripled between 2023 and 2025."},
]
DOCUMENTS = [
    {"name": "Studio Annual Report 2025.pdf", "pages": {
        4: "Storyboarding time fell 30% after the studio adopted AI-assisted previsualisation.",
        9: "Freelance concept-art spend dropped from $1.2M to $0.7M year over year."}},
]

CONFIDENCE = {"type": "string", "enum": ["high", "medium", "low"]}
WEB_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"], "properties": {"findings": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
                               "required": ["claim", "source_url", "confidence"],
                               "properties": {"claim": {"type": "string"}, "source_url": {"type": "string"}, "confidence": CONFIDENCE}}}}}
DOC_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"], "properties": {"findings": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
                               "required": ["claim", "document_name", "page_number", "confidence"],
                               "properties": {"claim": {"type": "string"}, "document_name": {"type": "string"},
                                              "page_number": {"type": "integer"}, "confidence": CONFIDENCE}}}}}


def run_web_agent(client, goal: str) -> list[Finding]:
    sources = "\n".join(f"- url: {s['url']}\n  text: {s['text']}" for s in WEB_SOURCES)
    prompt = f"[WEB AGENT]\n{SUBAGENTS['web_search_agent']['prompt']}\nGoal: {goal}\nSearch results:\n{sources}\nExtract findings."
    raw = ask_json(client, prompt, WEB_SCHEMA)["findings"]
    return [Finding(retrieved_by="web_search_agent", **f) for f in raw]


def run_document_agent(client, goal: str) -> list[Finding]:
    pages = "\n".join(f"- document: {d['name']} | page {p}: {t}" for d in DOCUMENTS for p, t in d["pages"].items())
    prompt = f"[DOC AGENT]\n{SUBAGENTS['document_analysis_agent']['prompt']}\nGoal: {goal}\nDocument pages:\n{pages}\nExtract findings."
    raw = ask_json(client, prompt, DOC_SCHEMA)["findings"]
    return [Finding(retrieved_by="document_analysis_agent", **f) for f in raw]


def gather_findings(client, goal: str) -> list[Finding]:
    """Independent subagents, no shared state: run in parallel, wait for both."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        web = pool.submit(run_web_agent, client, goal)
        docs = pool.submit(run_document_agent, client, goal)
        return web.result() + docs.result()


def build_synthesis_prompt(goal: str, findings: list[Finding]) -> str:
    all_findings = json.dumps([f.model_dump(exclude_none=True) for f in findings], indent=2)
    return (
        f"[SYNTHESIS]\nGoal: {goal}\n"
        "Write a short report. Cite every claim: (source_url) for web findings, (document_name p.N) for documents.\n"
        f"Findings (full structured records):\n{all_findings}"
    )


def synthesize(client, prompt: str) -> str:
    response = client.messages.create(model=config.model(), max_tokens=config.MAX_TOKENS,
                                      messages=[{"role": "user", "content": prompt}])
    return response_text(response)


GOAL = "How is generative AI changing creative production costs and practices?"


def run(client, goal: str = GOAL, options: dict = COORDINATOR_OPTIONS) -> tuple[str, str]:
    if not can_spawn_subagents(options):
        raise PermissionError("coordinator cannot spawn subagents: 'Agent' (exam: 'Task') missing from allowed_tools")
    findings = gather_findings(client, goal)
    prompt = build_synthesis_prompt(goal, findings)
    return prompt, synthesize(client, prompt)


# ---- mock model ------------------------------------------------------------------------------

def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    if prompt.startswith("[WEB AGENT]"):
        return json_message({"findings": [
            {"claim": "41% of illustrators use generative tools weekly", "source_url": WEB_SOURCES[0]["url"], "confidence": "high"},
            {"claim": "AI music licensing disputes tripled 2023-2025", "source_url": WEB_SOURCES[1]["url"], "confidence": "medium"}]})
    if prompt.startswith("[DOC AGENT]"):
        return json_message({"findings": [
            {"claim": "Storyboarding time fell 30%", "document_name": DOCUMENTS[0]["name"], "page_number": 4, "confidence": "high"},
            {"claim": "Concept-art spend fell from $1.2M to $0.7M", "document_name": DOCUMENTS[0]["name"], "page_number": 9, "confidence": "high"}]})
    # Synthesis: it can only cite what actually reached it.
    lines = []
    try:
        records = json.loads(prompt.split("(full structured records):\n", 1)[1])
    except (IndexError, ValueError):
        records = None
    if records:
        for r in records:
            cite = r.get("source_url") or f"{r.get('document_name')} p.{r.get('page_number')}"
            lines.append(f"- {r['claim']} ({cite})")
    else:
        lines = [f"- {line.strip()}" for line in prompt.split("Findings:\n", 1)[-1].splitlines() if line.strip()]
    return message(text("Report:\n" + "\n".join(lines)))


def main():
    print(mode_banner())
    print(f"coordinator can spawn subagents: {can_spawn_subagents(COORDINATOR_OPTIONS)}")
    print(f"tool scope violations: {tool_scope_violations(SUBAGENTS) or 'none'}")
    _, report = run(get_client(mock_model))
    print(report)


if __name__ == "__main__":
    main()
