"""Task 4.4 — Validation, Retry, and Feedback Loops (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-4-validation-retry-loops

A schema catches syntax; Pydantic validators catch semantics (sums, date order). A retry sends
the original document + the failed extraction + the specific error. Retries fix what's wrong in
the extraction - never what's absent from the source.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date

from pydantic import BaseModel, ValidationError, model_validator

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text

# ---- Step 1: extraction schema with self-checking fields -------------------------------------------

class Invoice(BaseModel):
    vendor: str
    department: str | None  # nullable: may genuinely be absent
    invoice_date: date
    due_date: date
    line_items: list[float]
    stated_total: float
    calculated_total: float  # extracted alongside stated_total -> automatic discrepancy check
    conflict_detected: bool = False  # source contradicts itself
    detected_pattern: str  # which layout produced this extraction (for dismissal analysis)

    # ---- Step 2: semantic validation with specific messages ----
    @model_validator(mode="after")
    def semantics(self):
        if abs(sum(self.line_items) - self.stated_total) > 0.005:
            raise ValueError(f"line items sum to £{sum(self.line_items):.2f} but stated_total is £{self.stated_total:.2f}")
        if self.due_date < self.invoice_date:
            raise ValueError(f"due_date {self.due_date} is before invoice_date {self.invoice_date}")
        return self


SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["vendor", "department", "invoice_date", "due_date", "line_items", "stated_total",
                       "calculated_total", "conflict_detected", "detected_pattern"],
          "properties": {"vendor": {"type": "string"}, "department": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                         "invoice_date": {"type": "string"}, "due_date": {"type": "string"},
                         "line_items": {"type": "array", "items": {"type": "number"}}, "stated_total": {"type": "number"},
                         "calculated_total": {"type": "number"}, "conflict_detected": {"type": "boolean"},
                         "detected_pattern": {"type": "string"}}}

DOCS = {
    "A": "Vendor: Acme. Dept: Facilities. Date 2026-09-01, due 2026-10-01. Lines: 200.00, 250.00, 50.00 (page 2). Total £500.00",
    "B": "Vendor: Brill. Dept: IT. Issued 2026-09-10. Payment due 2026-10-10. Lines: 100.00, 20.00. Total £120.00",
    "C": "Vendor: Corvo. Date 2026-09-03, due 2026-10-03. Lines: 80.00. Total £80.00",
    "D": "Vendor: Dunmore. Date 2026-09-04, due 2026-10-04. Lines: 15.00, 15.00. Total £30.00",
    "E": "Vendor: Ely. Date 2026-09-05, due 2026-10-05. Lines: 999.00. Total £999.00",
}


def extract(client, doc_id: str, feedback: str | None = None) -> dict:
    prompt = f"[EXTRACT {doc_id}]\n{DOCS[doc_id]}"
    if feedback:
        prompt += feedback
    return ask_json(client, prompt, SCHEMA)


def validate(raw: dict) -> tuple[Invoice | None, str | None]:
    try:
        return Invoice(**raw), None
    except ValidationError as e:
        return None, "; ".join(err["msg"].removeprefix("Value error, ") for err in e.errors())


def absent_from_source(raw: dict, doc_id: str) -> list[str]:
    return ["department"] if raw.get("department") is None and "Dept" not in DOCS[doc_id] else []


# ---- Steps 3-4: retry fixable errors with the specific error; route absent info to a human -------------

def process(client, doc_id: str, max_retries: int = 2) -> dict:
    raw = extract(client, doc_id)
    attempts = 1
    invoice, error = validate(raw)
    while error and attempts <= max_retries:
        feedback = (f"\n\nYour previous extraction:\n{json.dumps(raw)}\n"
                    f"Validation error: {error}\nRe-read the document and correct it.")  # doc + failed output + error
        raw = extract(client, doc_id, feedback)
        attempts += 1
        invoice, error = validate(raw)
    missing = absent_from_source(raw, doc_id)
    status = "error" if error else "human_review" if missing else "ok"
    return {"doc": doc_id, "status": status, "attempts": attempts, "error": error, "absent": missing, "raw": raw}


# ---- Step 5: which detected_pattern gets dismissed by reviewers most -----------------------------------

def dismissal_rates(reviews: list[dict]) -> dict[str, float]:
    totals, dismissed = Counter(r["pattern"] for r in reviews), Counter(r["pattern"] for r in reviews if r["dismissed"])
    return {p: round(dismissed[p] / totals[p], 2) for p in totals}


PRACTICE = {
    "question": "Document A's line items sum to £450 but the stated total is £500; Document B's 'department' is missing "
                "from the source entirely. Correct retry strategy?",
    "options": {"A": "Retry both with the errors, re-extracting all fields", "B": "No retries; send both to human review",
                "C": "Retry A with the discrepancy error; flag B for human review",
                "D": "Retry both with the same prompt"},
    "answer": "C",
    "why": "A is a fixable extraction error; B's information is absent, so no retry can create it.",
}


# ---- mock model (first pass misses page-2 lines and mixes up 'Issued'/'due') ---------------------------

def mock_model(kwargs: dict):
    prompt = last_user_text(kwargs)
    doc_id = prompt.split("[EXTRACT ")[1][0]
    text_, has_error = DOCS[doc_id], "Validation error:" in prompt
    lines = [float(x) for x in re.findall(r"\d+\.\d{2}", text_.split("Lines: ")[1].split(" Total")[0])]
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text_)
    if doc_id == "A" and not ("sum to" in prompt and has_error):
        lines = lines[:2]  # missed the item on page 2
    if doc_id == "B" and not ("before invoice_date" in prompt and has_error):
        dates = dates[::-1]  # read 'Issued'/'due' the wrong way round
    dept = re.search(r"Dept: (\w+)", text_)
    total = float(re.search(r"Total £([\d.]+)", text_).group(1))
    return json_message({"vendor": re.search(r"Vendor: (\w+)", text_).group(1), "department": dept.group(1) if dept else None,
                         "invoice_date": dates[0], "due_date": dates[1], "line_items": lines, "stated_total": total,
                         "calculated_total": round(sum(lines), 2), "conflict_detected": False,
                         "detected_pattern": "multi_page_lines" if "page 2" in text_ else "single_block"})


def main():
    print(mode_banner())
    for d in DOCS:
        r = process(get_client(mock_model), d)
        print(f"doc {d}: {r['status']:12s} attempts={r['attempts']} absent={r['absent']} error={r['error']}")
    reviews = [{"pattern": "multi_page_lines", "dismissed": False}, {"pattern": "single_block", "dismissed": True},
               {"pattern": "single_block", "dismissed": True}, {"pattern": "single_block", "dismissed": False}]
    print(f"step 5 dismissal rate by detected_pattern: {dismissal_rates(reviews)}")


if __name__ == "__main__":
    main()
