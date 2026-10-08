"""Task 4.3 — Structured Output with Tool Use (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-3-structured-output

tool_use + a JSON schema removes syntax errors. tool_choice: auto (may answer in text),
any (must call some tool), {"type": "tool", "name"} (must call that tool) - per request.
Nullable fields are the main defence against fabrication.
"""

from __future__ import annotations

import re

import anthropic

from common import config
from common.client import get_client, mode_banner
from common.mock import message, text, tool_use

# ---- Step 1: 3 required, 3 nullable, an enum with unclear/other + a detail string ---------------------

NULLABLE = lambda t: {"anyOf": [{"type": t}, {"type": "null"}]}
EXTRACT_INVOICE = {
    "name": "extract_invoice",
    "description": "Record the fields of an invoice. Use null for anything the document doesn't state.",
    "input_schema": {
        "type": "object", "additionalProperties": False,
        "required": ["vendor", "invoice_number", "total", "due_date", "po_number", "tax", "category", "category_detail"],
        "properties": {
            "vendor": {"type": "string"}, "invoice_number": {"type": "string"}, "total": {"type": "number"},  # always present
            "due_date": NULLABLE("string"), "po_number": NULLABLE("string"), "tax": NULLABLE("number"),  # may be absent
            "category": {"type": "string", "enum": ["goods", "services", "unclear", "other"]},
            "category_detail": NULLABLE("string"),  # filled when category is "other"
        },
    },
}
EXTRACT_RECEIPT = {"name": "extract_receipt", "description": "Record a till receipt (store, total).",
                   "input_schema": {"type": "object", "required": ["store", "total"],
                                    "properties": {"store": {"type": "string"}, "total": {"type": "number"}}}}

DOCS = [  # 3 complete, 2 with missing fields
    {"id": "d1", "text": "Invoice INV-101 from Acme Ltd. Goods. Total 1200.00, tax 200.00, due 2026-11-01, PO-77."},
    {"id": "d2", "text": "Invoice INV-102 from Brightworks. Consulting services. Total 900.00, tax 150.00, due 2026-11-15, PO-81."},
    {"id": "d3", "text": "Invoice INV-103 from Carto. Map licence (neither goods nor services). Total 300.00, tax 50.00, due 2026-12-01, PO-90."},
    {"id": "d4", "text": "Invoice INV-104 from Delta Co. Total 450.00."},
    {"id": "d5", "text": "Invoice INV-105 from Echo plc. Total 75.50, tax 12.58."},
]


def create(client, doc: dict, tools: list[dict], tool_choice: dict | None):
    """One request. Current docs: claude-sonnet-5-5 rejects forced tool_choice (any/tool) with a 400 -
    fall back to auto + an explicit instruction (and strict schemas) in that case."""
    kwargs = dict(model=config.model(), max_tokens=2048, tools=tools,
                  messages=[{"role": "user", "content": f"{doc['id']}: {doc['text']}"}])
    if tool_choice:
        try:
            return client.messages.create(**kwargs, tool_choice=tool_choice)
        except anthropic.BadRequestError:
            name = tool_choice.get("name", "one of the tools")
            kwargs["messages"][0]["content"] += f"\nRespond ONLY by calling {name}."
    return client.messages.create(**kwargs)


def tool_input(response) -> dict | None:
    return next((b.input for b in response.content if b.type == "tool_use"), None)


def extract_all(client, tool_choice: dict | None = None, tools: list[dict] = (EXTRACT_INVOICE,)) -> dict:
    return {d["id"]: tool_input(create(client, d, list(tools), tool_choice)) for d in DOCS}


PRACTICE = {
    "question": "A tool_use extraction schema makes every field required, and the model invents dates and amounts "
                "when documents lack them. Best fix?",
    "options": {"A": "Make those fields optional/nullable", "B": "Switch to prompt-based JSON",
                "C": "Add a 'do not hallucinate' instruction", "D": "Add post-extraction validation"},
    "answer": "A",
    "why": "Required fields pressure the model to fill them; nullable fields allow an honest null.",
}


# ---- mock model --------------------------------------------------------------------------------------

def _fields(text_: str, required: list[str]) -> dict:
    get = lambda p: (m.group(1) if (m := re.search(p, text_)) else None)
    category = "other" if "neither" in text_ else "goods" if "Goods" in text_ else \
        "services" if "services" in text_ else "unclear"
    out = {"vendor": get(r"from ([\w ]+?)\."), "invoice_number": get(r"(INV-\d+)"), "total": float(get(r"Total (\d+(?:\.\d+)?)")),
           "due_date": get(r"due (\d{4}-\d{2}-\d{2})"), "po_number": get(r"(PO-\d+)"),
           "tax": float(t) if (t := get(r"tax (\d+(?:\.\d+)?)")) else None, "category": category,
           "category_detail": "map licence" if category == "other" else None}
    for f in ("due_date", "po_number", "tax"):  # a REQUIRED non-nullable field pushes the model to fill it
        if out[f] is None and f in required:
            out[f] = {"due_date": "2026-12-31", "po_number": "PO-0000", "tax": 0.0}[f]
    return out


def mock_model(kwargs: dict):
    content = kwargs["messages"][0]["content"]
    choice = kwargs.get("tool_choice") or {}
    tools = {t["name"]: t for t in kwargs["tools"]}
    doc = next(d for d in DOCS if content.startswith(d["id"] + ":"))
    if choice.get("type") == "tool":
        name = choice["name"]
    elif choice.get("type") == "any" or "Respond ONLY" in content:
        name = "extract_invoice" if "extract_invoice" in tools else next(iter(tools))
    elif doc["id"] == "d4":  # auto: for a sparse document the model just answers in prose
        return message(text("This looks like a short invoice from Delta Co for 450.00."))
    else:
        name = "extract_invoice"
    if name == "extract_receipt":
        return message(tool_use(name, {"store": "Acme Ltd", "total": 1200.0}))
    schema = tools[name]["input_schema"]
    nullable = {k for k, v in schema["properties"].items() if "anyOf" in v}
    return message(tool_use(name, _fields(doc["text"], [r for r in schema["required"] if r not in nullable])))


def main():
    print(mode_banner())
    auto = extract_all(get_client(mock_model))
    print(f"step 2 auto  : text instead of a tool call for {[d for d, v in auto.items() if v is None]}")
    forced_any = extract_all(get_client(mock_model), {"type": "any"})
    print(f"step 3 any   : every doc returned structured data = {all(v is not None for v in forced_any.values())}")
    named = tool_input(create(get_client(mock_model), DOCS[0], [EXTRACT_RECEIPT, EXTRACT_INVOICE],
                              {"type": "tool", "name": "extract_receipt"}))
    print(f"step 4 named : extract_receipt forced even for an invoice -> {named}")
    print(f"step 5 d4/d5 : {forced_any['d4']} | {forced_any['d5']}")


if __name__ == "__main__":
    main()
