"""Task 4.2 — Few-Shot Prompting (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-2-few-shot-prompting

When detailed instructions still give inconsistent output, show 2-4 targeted examples -
each with its REASONING - covering the cases that actually fail.
"""

from __future__ import annotations

import re

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- 10 test documents in three structures ---------------------------------------------------------

DOCS = [
    {"id": "t1", "kind": "table", "text": "| author | year | n |\n| Lee | 2021 | 120 |"},
    {"id": "t2", "kind": "table", "text": "| author | year | n |\n| Okafor | 2019 | 64 |"},
    {"id": "t3", "kind": "table", "text": "| author | year | n |\n| Silva | 2023 | 300 |"},
    {"id": "n1", "kind": "narrative", "text": "In 2020, Patel recruited 85 volunteers for the trial."},
    {"id": "n2", "kind": "narrative", "text": "Garcia's 2018 survey reached 1,200 households."},
    {"id": "n3", "kind": "narrative", "text": "The 2022 study by Kim followed 40 patients."},
    {"id": "n4", "kind": "narrative", "text": "Nakamura (2017) described the method; no sample size is reported."},
    {"id": "m1", "kind": "mixed", "text": "Author: Haddad. Conducted 2021 with n = 75 participants."},
    {"id": "m2", "kind": "mixed", "text": "Author: Novak. Fieldwork in 2016; sample: 210."},
    {"id": "m3", "kind": "mixed", "text": "Author: Mensah. 2024. Cohort of 33."},
]
FIELDS = ("author", "year", "sample_size")

# ---- Step 1: detailed instructions, no examples -------------------------------------------------------

INSTRUCTIONS = ("Extract author (surname), year (4 digits) and sample_size (integer) from the study description. "
                "Look carefully in tables and prose. Use null only if the value is truly absent.")

# ---- Step 3: three examples (table, narrative, mixed), each WITH reasoning --------------------------------

FEW_SHOT = """
Example (table): "| author | year | n |\\n| Ito | 2015 | 50 |"
Output: {"author": "Ito", "year": 2015, "sample_size": 50}
Reasoning: the column headers name each field directly; 'n' is the sample size.

Example (narrative): "In 2019, Brown enrolled 90 adults."
Output: {"author": "Brown", "year": 2019, "sample_size": 90}
Reasoning: in prose the sample size is the count attached to a recruitment verb (enrolled, recruited, followed,
reached) - not a table cell. The year is the 4-digit number tied to when the study ran.

Example (mixed, missing value): "Author: Reyes. 2014. Method paper."
Output: {"author": "Reyes", "year": 2014, "sample_size": null}
Reasoning: no participant count appears anywhere, so sample_size is null rather than a guess.
"""

SCHEMA = {"type": "object", "additionalProperties": False, "required": list(FIELDS),
          "properties": {"author": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                         "year": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                         "sample_size": {"anyOf": [{"type": "integer"}, {"type": "null"}]}}}


def extract(client, doc: dict, system: str) -> dict:
    return ask_json(client, f"Document {doc['id']}:\n{doc['text']}", SCHEMA, system=system)


def run(client, system: str) -> dict:
    """Steps 2 and 4: empty-field rate, broken down by document structure."""
    results = {d["id"]: extract(client, d, system) for d in DOCS}
    empty_by_kind: dict[str, int] = {}
    for d in DOCS:
        empties = sum(results[d["id"]][f] is None for f in FIELDS)
        empty_by_kind[d["kind"]] = empty_by_kind.get(d["kind"], 0) + empties
    total = sum(empty_by_kind.values())
    return {"empty_fields": total, "empty_rate": round(total / (len(DOCS) * len(FIELDS)), 2),
            "empty_by_structure": empty_by_kind, "results": results}


# ---- Step 5: which problems few-shot fixed, and which need another tool ---------------------------------

def remaining_issues(after: dict) -> list[str]:
    left = [doc for doc, r in after["results"].items() if any(r[f] is None for f in FIELDS)]
    return [f"{d}: value genuinely absent from the source -> keep the nullable schema field (4.3), don't retry (4.4)"
            for d in left]


PRACTICE = {
    "question": "Extraction reads values from tables but returns empty fields for the same data in narrative "
                "paragraphs; detailed instructions are already in place. What first?",
    "options": {"A": "Convert narrative text to tables first", "B": "Use a larger context window",
                "C": "Add few-shot examples covering tables and narrative", "D": "Retry when fields are empty"},
    "answer": "C",
    "why": "The data is present in an unexpected format; examples with reasoning show how to read it.",
}


# ---- mock model (SIMULATED: without a narrative example, prose values are missed) -------------------------

def _parse(text: str, kind: str, reads_prose: bool) -> dict:
    author = re.search(r"\| ([A-Z][a-z]+) \||Author: ([A-Z][a-z]+)|by ([A-Z][a-z]+)|([A-Z][a-z]+)(?: \(| recruited|'s)", text)
    year = re.search(r"\b(19|20)\d{2}\b", text)
    size = re.search(r"\| (\d+) \||n = (\d+)|sample: (\d+)|Cohort of (\d+)|(\d[\d,]*) (?:volunteers|households|patients)", text)
    out = {"author": next(g for g in author.groups() if g) if author else None,
           "year": int(year.group(0)) if year else None,
           "sample_size": int(next(g for g in size.groups() if g).replace(",", "")) if size else None}
    if kind == "narrative" and not reads_prose:  # info is there, in an unexpected format
        out["author"], out["sample_size"] = None, None
    return out


def mock_model(kwargs: dict):
    prompt, system = last_user_text(kwargs), kwargs.get("system", "")
    doc = next(d for d in DOCS if f"Document {d['id']}:" in prompt)
    reads_prose = "Example (narrative)" in system and "Reasoning:" in system
    return json_message(_parse(doc["text"], doc["kind"], reads_prose))


def main():
    print(mode_banner())
    before = run(get_client(mock_model), INSTRUCTIONS)
    after = run(get_client(mock_model), INSTRUCTIONS + FEW_SHOT)
    print(f"step 2 no examples : empty {before['empty_rate']:.0%} {before['empty_by_structure']}")
    print(f"step 4 few-shot    : empty {after['empty_rate']:.0%} {after['empty_by_structure']}")
    print(f"step 5 still empty : {remaining_issues(after)}")


if __name__ == "__main__":
    main()
