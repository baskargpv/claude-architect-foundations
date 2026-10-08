"""Task 4.3 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-3-structured-output

Trap 1  believing tool_use with a schema prevents all extraction errors
Trap 2  confusing tool_choice "auto" with "any"
Trap 3  making every schema field required
"""

from __future__ import annotations

import copy

from pydantic import BaseModel

from common.client import get_client
from domain4_prompt_engineering.task_4_3_structured_output.good_example import EXTRACT_INVOICE, extract_all, mock_model


class InvoiceShape(BaseModel):
    vendor: str
    invoice_number: str
    total: float
    due_date: str | None
    line_items: list[float] = []


def trap1_schema_is_not_correctness() -> dict:
    """All three pass the schema; all three are wrong."""
    sum_mismatch = InvoiceShape(vendor="Acme", invoice_number="INV-1", total=500.0, due_date=None, line_items=[200.0, 250.0])
    misplaced = InvoiceShape(vendor="2026-11-01", invoice_number="INV-2", total=90.0, due_date="Acme Ltd")  # fields swapped
    fabricated = InvoiceShape(vendor="Echo plc", invoice_number="INV-5", total=75.5, due_date="2026-12-31")  # not in source
    return {"schema_valid": 3, "semantically_wrong": [
        f"line items sum {sum(sum_mismatch.line_items)} != total {sum_mismatch.total}",
        f"vendor holds a date: {misplaced.vendor!r}", f"due_date {fabricated.due_date} appears nowhere in the document"]}


def trap2_auto_for_structured_output(client) -> list[str]:
    return [d for d, v in extract_all(client, tool_choice=None).items() if v is None]  # auto may answer in prose


def trap3_all_required(client) -> dict:
    strict = copy.deepcopy(EXTRACT_INVOICE)
    for f in ("due_date", "po_number", "tax"):
        strict["input_schema"]["properties"][f] = {"type": "number" if f == "tax" else "string"}  # no null allowed
    out = extract_all(client, {"type": "any"}, tools=[strict])
    return {"d4_due_date": out["d4"]["due_date"], "d4_po_number": out["d4"]["po_number"]}  # invented


def main():
    print(f"trap 1 schema != correct : {trap1_schema_is_not_correctness()}")
    print(f"trap 2 auto              : no structured output for {trap2_auto_for_structured_output(get_client(mock_model))}")
    print(f"trap 3 all required      : {trap3_all_required(get_client(mock_model))}  <- fabricated for a doc that has neither")


if __name__ == "__main__":
    main()
