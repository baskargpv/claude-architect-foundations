"""Task 5.6 — Information Provenance & Multi-Source Synthesis (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-6-information-provenance

Every finding carries a claim-source mapping. Synthesis merges mappings instead of paraphrasing
them away. Conflicting values are both kept, with attribution and an explanation - never a winner.
Render by content type: financial -> table, news -> prose, technical -> list.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- Step 1: the claim-source mapping ------------------------------------------------------------

class Finding(BaseModel):
    claim: str
    sourceUrl: str
    documentName: str
    relevantExcerpt: str
    publicationDate: str
    metric: str | None = None  # what is measured (for conflict detection)
    value: str | None = None
    methodology: str | None = None
    contentType: str = "technical"  # financial | news | technical


FINDING_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"], "properties": {"findings": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
                               "required": ["claim", "sourceUrl", "documentName", "relevantExcerpt", "publicationDate",
                                            "metric", "value", "methodology", "contentType"],
                               "properties": {k: {"anyOf": [{"type": "string"}, {"type": "null"}]} for k in
                                              ["claim", "sourceUrl", "documentName", "relevantExcerpt", "publicationDate",
                                               "metric", "value", "methodology", "contentType"]}}}}}


# ---- Step 2: two research subagents output findings in that schema -------------------------------

def research(client, agent: str, topic: str) -> list[Finding]:
    raw = ask_json(client, f"[{agent}] Research: {topic}. Every finding needs all five provenance fields.", FINDING_SCHEMA)
    return [Finding(**f) for f in raw["findings"]]


# ---- Step 4: conflict handling - keep both, explain, never pick ---------------------------------------

def classify_conflict(a: Finding, b: Finding) -> str:
    if a.publicationDate[:4] != b.publicationDate[:4] and a.methodology == b.methodology:
        return "trend over time (different years, same method)"
    if a.methodology != b.methodology:
        return f"methodology difference ({a.methodology} vs {b.methodology})"
    return "unexplained conflict - same date, dataset and method"


def find_conflicts(findings: list[Finding]) -> list[dict]:
    by_metric = defaultdict(list)
    for f in findings:
        if f.metric:
            by_metric[f.metric].append(f)
    return [{"metric": m, "values": [(f.value, f.documentName, f.publicationDate) for f in fs],
             "explanation": classify_conflict(fs[0], fs[1])}
            for m, fs in by_metric.items() if len({f.value for f in fs}) > 1]


# ---- Steps 3 and 5: synthesis that keeps every mapping, rendered by content type ----------------------

def cite(f: Finding) -> str:
    return f"[{f.documentName}, {f.publicationDate}]({f.sourceUrl})"


def synthesise(findings: list[Finding]) -> str:
    conflicts = find_conflicts(findings)
    out = []
    fin = [f for f in findings if f.contentType == "financial"]
    if fin:  # financial -> table
        out += ["| Metric | Value | Source |", "|---|---|---|"] + [f"| {f.metric} | {f.value} | {cite(f)} |" for f in fin]
    news = [f for f in findings if f.contentType == "news"]
    if news:  # news -> prose
        out.append(" ".join(f"{f.claim} {cite(f)}." for f in news))
    tech = [f for f in findings if f.contentType == "technical"]
    if tech:  # technical -> list
        out += [f"- {f.claim} {cite(f)}" for f in tech]
    for c in conflicts:
        vals = "; ".join(f"{v} ({d}, {p})" for v, d, p in c["values"])
        out.append(f"**{c['metric']}:** {vals} - {c['explanation']}.")
    return "\n".join(out)


PRACTICE = {
    "question": "Two credible sources give 12% (2023 data) and 8% (2024 data) market growth; the synthesis agent keeps "
                "the more recent. Correct approach?",
    "options": {"A": "Flag and escalate to a human", "B": "Average them to 10% with a footnote",
                "C": "Always use the most recent source", "D": "Annotate both values with attribution and dates; let the consumer decide"},
    "answer": "D",
    "why": "Never pick a winner; different dates are often a trend, not a contradiction.",
}


# ---- mock research subagents -----------------------------------------------------------------------

SOURCES = {
    "WEB": [{"claim": "EU heat-pump market grew 12%", "sourceUrl": "https://example.org/hp-2023", "documentName": "Heat Pump Review 2023",
             "relevantExcerpt": "installations rose 12% in 2023", "publicationDate": "2024-02-01", "metric": "market growth",
             "value": "12%", "methodology": "installations", "contentType": "financial"},
            {"claim": "A grid operator announced subsidies for home batteries", "sourceUrl": "https://example.net/news/1",
             "documentName": "Energy Daily", "relevantExcerpt": "subsidies announced Tuesday", "publicationDate": "2025-03-04",
             "metric": None, "value": None, "methodology": None, "contentType": "news"}],
    "DOCS": [{"claim": "EU heat-pump market grew 8%", "sourceUrl": "https://example.org/hp-2024", "documentName": "Heat Pump Review 2024",
              "relevantExcerpt": "installations rose 8% in 2024", "publicationDate": "2025-02-01", "metric": "market growth",
              "value": "8%", "methodology": "installations", "contentType": "financial"},
             {"claim": "Inverter heat pumps reach a COP of 4.2 at 7°C", "sourceUrl": "https://example.org/spec", "documentName": "Tech Spec v3",
              "relevantExcerpt": "COP 4.2 (A7/W35)", "publicationDate": "2024-11-10", "metric": None, "value": None,
              "methodology": None, "contentType": "technical"}],
}


def mock_model(kwargs: dict):
    agent = last_user_text(kwargs).split("]")[0].strip("[")
    return json_message({"findings": SOURCES[agent]})


def main():
    print(mode_banner())
    findings = research(get_client(mock_model), "WEB", "heat pumps") + research(get_client(mock_model), "DOCS", "heat pumps")
    print(synthesise(findings))


if __name__ == "__main__":
    main()
