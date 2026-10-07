"""Task 1.5 — PreToolUse for enforcement, PostToolUse for normalisation and state.

Hook callbacks use the Claude Agent SDK's shape exactly:
    async def hook(input_data: dict, tool_use_id: str | None, context) -> dict
    PreToolUse deny  -> {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                          "permissionDecision": "deny", "permissionDecisionReason": "..."}}
    PostToolUse      -> {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                          "updatedToolOutput": {...}}}   (replace output before Claude sees it)

With the Agent SDK you'd register them as
    ClaudeAgentOptions(hooks={"PreToolUse": [HookMatcher(matcher="process_refund", hooks=[...])]}).
To keep the demo runnable offline and on the plain Messages API, HookedDispatcher
runs the same callbacks with the same ordering guarantees: Pre BEFORE the handler,
Post AFTER it, and any single deny wins.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from common.client import get_client, mode_banner
from common.mock import last_tool_results, message, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

REFUND_LIMIT = 500.0


# ---- the backend: heterogeneous formats, real side effects --------------------------------

ORDERS = {  # three backends, three date formats, three status vocabularies
    "O-1": {"source": "legacy", "placed": 1717200000, "status": "P", "total": 120.0},
    "O-2": {"source": "eu", "placed": "03/06/2024", "status": 2, "total": 80.0},
    "O-3": {"source": "modern", "placed": "2024-06-05T10:00:00Z", "status": "shipped", "total": 900.0},
}
STATUS_MAPS = {"legacy": {"P": "pending", "X": "processing", "S": "shipped"},
               "eu": {1: "pending", 2: "processing", 3: "shipped"}}
AML_RESULTS = {"ACC-CLEAN": "pass", "ACC-FLAGGED": "fail"}


@dataclass
class Ledger:
    refunds: list = field(default_factory=list)
    transfers: list = field(default_factory=list)


@dataclass
class SessionState:
    aml_passed: set = field(default_factory=set)


class Backend:
    def __init__(self):
        self.ledger = Ledger()

    def lookup_order(self, order_id: str) -> dict:
        return {"order_id": order_id, **ORDERS[order_id]}

    def process_refund(self, order_id: str, amount: float) -> dict:
        self.ledger.refunds.append((order_id, amount))  # money moves HERE
        return {"order_id": order_id, "refunded": amount, "status": "refunded"}

    def aml_check(self, account: str) -> dict:
        return {"account": account, "result": AML_RESULTS.get(account, "fail")}

    def transfer_funds(self, account: str, amount: float) -> dict:
        self.ledger.transfers.append((account, amount))
        return {"account": account, "transferred": amount, "status": "sent"}


# ---- hooks -------------------------------------------------------------------------------

def deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny", "permissionDecisionReason": reason}}


def to_iso_date(value, source: str) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()  # unix seconds
    if source == "eu":
        return datetime.strptime(value, "%d/%m/%Y").date().isoformat()  # DD/MM/YYYY, never MM/DD
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()


def build_hooks(state: SessionState) -> dict:
    async def refund_limit(input_data, tool_use_id, context):
        amount = input_data["tool_input"]["amount"]
        if amount > REFUND_LIMIT:
            return deny(f"Refunds above ${REFUND_LIMIT:.0f} require human approval (requested ${amount:.2f}). "
                        "Escalate instead of retrying.")
        return {}

    async def aml_gate(input_data, tool_use_id, context):
        account = input_data["tool_input"]["account"]
        if account not in state.aml_passed:
            return deny(f"transfer_funds blocked: no passing aml_check for {account} in this session.")
        return {}

    async def normalize_order(input_data, tool_use_id, context):
        raw = input_data["tool_response"]
        status = raw["status"] if raw["source"] == "modern" else STATUS_MAPS[raw["source"]][raw["status"]]
        clean = {"order_id": raw["order_id"], "placed_date": to_iso_date(raw["placed"], raw["source"]),
                 "status": status, "total": raw["total"]}
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": clean}}

    async def record_aml(input_data, tool_use_id, context):
        if input_data["tool_response"]["result"] == "pass":
            state.aml_passed.add(input_data["tool_input"]["account"])  # read later by aml_gate
        return {}

    return {
        "PreToolUse": [("^process_refund$", [refund_limit]), ("^transfer_funds$", [aml_gate])],
        "PostToolUse": [("^lookup_order$", [normalize_order]), ("^aml_check$", [record_aml])],
    }


# ---- dispatcher that honours the hook contract --------------------------------------------

class HookedDispatcher:
    def __init__(self, backend: Backend, hooks: dict):
        self.backend = backend
        self.hooks = hooks
        self.events: list[tuple[str, str]] = []  # (event, tool) in the order things happened

    def _matching(self, event: str, tool: str):
        return [cb for pattern, cbs in self.hooks.get(event, []) if re.search(pattern, tool) for cb in cbs]

    async def _execute(self, name: str, tool_input: dict, tool_use_id: str | None = None) -> dict:
        pre = {"hook_event_name": "PreToolUse", "tool_name": name, "tool_input": tool_input}
        self.events.append(("PreToolUse", name))
        outputs = await asyncio.gather(*(cb(pre, tool_use_id, None) for cb in self._matching("PreToolUse", name)))
        denials = [o["hookSpecificOutput"]["permissionDecisionReason"] for o in outputs
                   if o.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"]
        if denials:  # any single deny wins; the handler never runs
            return {"is_error": True, "denied": True, "error": " | ".join(denials)}

        self.events.append(("handler", name))
        result = getattr(self.backend, name)(**tool_input)

        post = {**pre, "hook_event_name": "PostToolUse", "tool_response": result}
        self.events.append(("PostToolUse", name))
        for cb in self._matching("PostToolUse", name):
            out = await cb(post, tool_use_id, None)
            specific = out.get("hookSpecificOutput", {})
            if "updatedToolOutput" in specific:
                result = specific["updatedToolOutput"]
            if out.get("decision") == "block":  # too late to prevent anything - just feedback
                result = {**result, "hook_feedback": out.get("reason")}
        return result

    def execute(self, name: str, tool_input: dict) -> dict:
        return asyncio.run(self._execute(name, tool_input))


def build(hooks_factory=build_hooks) -> HookedDispatcher:
    return HookedDispatcher(Backend(), hooks_factory(SessionState()))


# ---- end-to-end with a model ----------------------------------------------------------------

TOOLS = [
    {"name": "lookup_order", "description": "Look up an order (date, status, total).",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "process_refund", "description": "Refund an order. Moves money.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}},
                      "required": ["order_id", "amount"]}},
]


def mock_model(kwargs: dict):
    results = last_tool_results(kwargs)
    if not results:
        return message(tool_use("lookup_order", {"order_id": "O-3"}))
    last = json.loads(results[-1]["content"])
    if "placed_date" in last or "placed" in last:
        return message(tool_use("process_refund", {"order_id": "O-3", "amount": last["total"]}))
    if last.get("denied"):
        return message(text("That refund needs a supervisor's approval, so I've flagged it for review."))
    return message(text(f"Refunded ${last['refunded']:.2f}."))


def main():
    print(mode_banner())
    d = build()
    for oid in ORDERS:
        print(f"lookup {oid}: raw={ORDERS[oid]} -> model sees {d.execute('lookup_order', {'order_id': oid})}")
    print(f"refund $750: {d.execute('process_refund', {'order_id': 'O-3', 'amount': 750.0})}")
    print(f"transfer before AML: {d.execute('transfer_funds', {'account': 'ACC-CLEAN', 'amount': 1000})}")
    d.execute("aml_check", {"account": "ACC-CLEAN"})
    print(f"transfer after AML pass: {d.execute('transfer_funds', {'account': 'ACC-CLEAN', 'amount': 1000})}")
    print(f"ledger: {d.backend.ledger}")

    d = build()
    result = run_agent(get_client(mock_model), "Refund my order O-3 in full.", tools=TOOLS, execute=d.execute)
    print(f"\nagent run: calls={[c[1] for c in result.tool_calls]} ledger={d.backend.ledger.refunds} reply={result.final_text!r}")


if __name__ == "__main__":
    main()
