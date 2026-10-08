"""Task 1.5 — Implement Agent SDK Hooks for Normalisation and Policy Enforcement (Build Exercise, steps 1-6).

Lesson: https://claudecertificationguide.com/learn/1-agentic-architecture/1-5-agent-sdk-hooks

Tools live on a real MCP server (mcp package, in-process). Hook callbacks use the Agent SDK's
signature and output shapes:
    async def hook(input_data, tool_use_id, context) -> dict
    PreToolUse  -> {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                           "permissionDecisionReason": "..."}}
    PostToolUse -> {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": {...}}}
With the SDK you'd register them via ClaudeAgentOptions(hooks={"PreToolUse": [HookMatcher(...)]});
HookedMCPDispatcher gives the same guarantees on the Messages API: Pre runs BEFORE the MCP call
(any deny wins, the handler never runs), Post runs AFTER it and may replace what the model sees.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from mcp import Client
from mcp.server.mcpserver import MCPServer

from common.client import get_client, mode_banner
from common.mock import last_tool_results, message, text, tool_use
from domain1_agentic_architecture.task_1_1_agentic_loop.good_example import run_agent

SERVER = "support"
REFUND_LIMIT = Decimal("500")
DISCOUNT_LIMIT_PCT = 20


def mcp_name(tool: str) -> str:
    return f"mcp__{SERVER}__{tool}"  # how MCP tools are named to the model (and to hook matchers)


# ---- Step 1: three MCP tools with mismatched formats (+ the money-moving tools) ----------------

@dataclass
class Ledger:
    refunds: list = field(default_factory=list)
    transfers: list = field(default_factory=list)
    discounts: list = field(default_factory=list)


def build_server(ledger: Ledger) -> MCPServer:
    srv = MCPServer(SERVER)

    @srv.tool()
    def get_customer(customer_id: str) -> dict:
        """Customer record. Dates are Unix epoch seconds; status is a numeric code; balance is a bare string."""
        return {"customer_id": customer_id, "created": 1710489600, "status": 200, "balance": "1234.5", "currency": "gbp"}

    @srv.tool()
    def lookup_order(order_id: str) -> dict:
        """Order record. Dates are ISO 8601; status is an English word; totals are integer cents."""
        return {"order_id": order_id, "placed": "2024-03-15T12:00:00Z", "status": "pending", "total_cents": 12999, "currency": "usd"}

    @srv.tool()
    def check_shipping(order_id: str) -> dict:
        """Shipping record. Dates are DD/MM/YYYY; status is one character (S/P/D); cost is a display string."""
        return {"order_id": order_id, "shipped_on": "04/03/2024", "status": "P", "cost": "€12,50"}

    @srv.tool()
    def process_refund(order_id: str, amount: float) -> dict:
        """Refund an order. Moves money."""
        ledger.refunds.append((order_id, amount))
        return {"order_id": order_id, "refunded": amount, "status": "refunded"}

    @srv.tool()
    def aml_check(account: str) -> dict:
        """Anti-money-laundering screen for an account."""
        return {"account": account, "result": "pass" if account.startswith("ACC-CLEAN") else "fail"}

    @srv.tool()
    def transfer_funds(account: str, amount: float) -> dict:
        """International transfer. Moves money."""
        ledger.transfers.append((account, amount))
        return {"account": account, "transferred": amount, "status": "sent"}

    @srv.tool()
    def approve_discount(order_id: str, percent: float) -> dict:
        """Apply a discount to an order."""
        ledger.discounts.append((order_id, percent))
        return {"order_id": order_id, "discount_pct": percent, "status": "applied"}

    return srv


# ---- Step 2: PostToolUse normalisation -----------------------------------------------------------

STATUS_MAPS = {"get_customer": {200: "active", 403: "suspended", 410: "closed"},
               "check_shipping": {"S": "shipped", "P": "pending", "D": "delivered"}}
DATE_FIELDS = ("created", "placed", "shipped_on")


def to_iso(value) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):  # DD/MM/YYYY - never read as MM/DD
        return datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00Z")
    return value


def to_money(raw: dict) -> dict | None:
    if "total_cents" in raw:
        return {"amount": str(Decimal(raw["total_cents"]) / 100), "currency": raw["currency"].upper()}
    if "balance" in raw:
        return {"amount": f"{Decimal(raw['balance']):.2f}", "currency": raw["currency"].upper()}
    if "cost" in raw:
        symbol, number = raw["cost"][0], raw["cost"][1:].replace(",", ".")
        return {"amount": f"{Decimal(number):.2f}", "currency": {"€": "EUR", "$": "USD", "£": "GBP"}[symbol]}
    return None


def normalise(tool: str, raw: dict) -> dict:
    out = {k: v for k, v in raw.items() if k not in ("total_cents", "balance", "cost", "currency")}
    for f in DATE_FIELDS:
        if f in out:
            out[f] = to_iso(out[f])
    if tool in STATUS_MAPS:
        out["status"] = STATUS_MAPS[tool][raw["status"]]
    money = to_money(raw)
    if money:
        out["money"] = money
    return out


# ---- hooks (Steps 2, 4, 5 + the lesson's manager-approval example) --------------------------------

@dataclass
class SessionState:
    aml_passed: set = field(default_factory=set)
    approval_queue: list = field(default_factory=list)
    manager_approved: set = field(default_factory=set)


def deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def build_hooks(state: SessionState) -> dict:
    async def normalise_output(input_data, tool_use_id, context):  # Step 2
        tool = input_data["tool_name"].removeprefix(f"mcp__{SERVER}__")
        clean = normalise(tool, input_data["tool_response"])
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": clean}}

    async def refund_threshold(input_data, tool_use_id, context):  # Step 4
        amount = Decimal(str(input_data["tool_input"]["amount"]))
        if amount > REFUND_LIMIT:
            return deny(f"Refunds above ${REFUND_LIMIT} need a human: escalate this ${amount} refund instead of retrying.")
        return {}

    async def aml_gate(input_data, tool_use_id, context):  # Step 5 (Pre half)
        account = input_data["tool_input"]["account"]
        if account not in state.aml_passed:
            return deny(f"transfer_funds blocked: no passing aml_check recorded for {account} in this session.")
        return {}

    async def record_aml(input_data, tool_use_id, context):  # Step 5 (Post half)
        if input_data["tool_response"].get("result") == "pass":
            state.aml_passed.add(input_data["tool_input"]["account"])
        return {}

    async def discount_approval(input_data, tool_use_id, context):  # lesson policy example
        key = (input_data["tool_input"]["order_id"], float(input_data["tool_input"]["percent"]))
        if key[1] > DISCOUNT_LIMIT_PCT and key not in state.manager_approved:
            state.approval_queue.append(key)
            return deny(f"Discounts above {DISCOUNT_LIMIT_PCT}% go to the manager approval queue; it will run once approved.")
        return {}

    return {
        "PreToolUse": [(f"^{mcp_name('process_refund')}$", [refund_threshold]),
                       (f"^{mcp_name('transfer_funds')}$", [aml_gate]),
                       (f"^{mcp_name('approve_discount')}$", [discount_approval])],
        "PostToolUse": [(f"^{mcp_name('(get_customer|lookup_order|check_shipping)')}$", [normalise_output]),
                        (f"^{mcp_name('aml_check')}$", [record_aml])],
    }


# ---- the dispatcher: SDK hook semantics around real MCP calls ----------------------------------

class HookedMCPDispatcher:
    def __init__(self, hooks_factory=build_hooks):
        self.ledger = Ledger()
        self.server = build_server(self.ledger)
        self.state = SessionState()
        self.hooks = hooks_factory(self.state)
        self.events: list[tuple[str, str]] = []  # (event, tool) in the order they happened

    def _matching(self, event: str, tool: str):
        return [cb for pattern, cbs in self.hooks.get(event, []) if re.search(pattern, tool) for cb in cbs]

    async def _execute(self, name: str, tool_input: dict) -> dict:
        pre = {"hook_event_name": "PreToolUse", "tool_name": name, "tool_input": tool_input}
        self.events.append(("PreToolUse", name))
        outs = await asyncio.gather(*(cb(pre, None, None) for cb in self._matching("PreToolUse", name)))
        reasons = [o["hookSpecificOutput"]["permissionDecisionReason"] for o in outs
                   if o.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"]
        if reasons:  # any deny wins; the MCP handler never runs
            return {"is_error": True, "denied": True, "error": " | ".join(reasons)}

        self.events.append(("handler", name))
        async with Client(self.server) as client:
            result = await client.call_tool(name.removeprefix(f"mcp__{SERVER}__"), tool_input)
        output = json.loads(result.content[0].text)

        post = {**pre, "hook_event_name": "PostToolUse", "tool_response": output}
        self.events.append(("PostToolUse", name))
        for cb in self._matching("PostToolUse", name):
            out = await cb(post, None, None)
            specific = out.get("hookSpecificOutput", {})
            if "updatedToolOutput" in specific:
                output = specific["updatedToolOutput"]
            if out.get("decision") == "block":  # PostToolUse can only give feedback - the tool already ran
                output = {**output, "hook_feedback": out.get("reason")}
        return output

    def execute(self, name: str, tool_input: dict) -> dict:
        return asyncio.run(self._execute(name, tool_input))

    def manager_approves(self, order_id: str, percent: float):
        self.state.manager_approved.add((order_id, float(percent)))

    def tool_definitions(self) -> list[dict]:
        async def _list():
            async with Client(self.server) as client:
                return (await client.list_tools()).tools
        return [{"name": mcp_name(t.name), "description": t.description, "input_schema": t.input_schema}
                for t in asyncio.run(_list())]


PRACTICE = {
    "question": "Transfers occasionally skip the AML check; compliance needs 100% (prompting gets ~95%). Correct approach?",
    "options": {"A": "PreToolUse hook blocking transfer_funds until aml_check returns a pass",
                "B": "A longer system prompt with AML instructions and penalty warnings",
                "C": "PostToolUse hook that flags transfers that skipped AML for manual review",
                "D": "Few-shot examples of the AML workflow"},
    "answer": "A",
    "why": "100% requirements need a hook that runs BEFORE execution; C runs after the money moved, B and D are probabilistic.",
}


# ---- mock model ------------------------------------------------------------------------------

def mock_model(kwargs: dict):
    first = kwargs["messages"][0]["content"]
    results = last_tool_results(kwargs)
    if first.startswith("Give me the full status"):  # Step 3: needs all three tools
        if not results:
            return message(text("Checking all three systems."),
                           tool_use(mcp_name("get_customer"), {"customer_id": "C-1001"}),
                           tool_use(mcp_name("lookup_order"), {"order_id": "O-77"}),
                           tool_use(mcp_name("check_shipping"), {"order_id": "O-77"}))
        seen = [json.loads(r["content"]) for r in results]
        return message(text("Status: " + "; ".join(f"{s.get('status')} ({next(s[f] for f in DATE_FIELDS if f in s)})" for s in seen)))
    if first.startswith("Refund"):
        amount = float(re.search(r"\$(\d+)", first).group(1))
        if not results:
            return message(tool_use(mcp_name("process_refund"), {"order_id": "O-77", "amount": amount}))
        last = json.loads(results[-1]["content"])
        return message(text("That refund needs a human - I've escalated it." if last.get("denied") else f"Refunded ${amount:.0f}."))
    if first.startswith("Transfer"):
        account = re.search(r"ACC-[\w-]+", first).group(0)
        if not results:  # this model "forgets" AML and goes straight to the transfer
            return message(tool_use(mcp_name("transfer_funds"), {"account": account, "amount": 1000}))
        last = json.loads(results[-1]["content"])
        if last.get("denied"):
            return message(tool_use(mcp_name("aml_check"), {"account": account}))
        if last.get("result") == "pass":
            return message(tool_use(mcp_name("transfer_funds"), {"account": account, "amount": 1000}))
        if last.get("result") == "fail":
            return message(text("The AML screen failed, so I can't send this transfer."))
        return message(text("Transfer sent."))
    raise ValueError(f"unexpected request: {first[:40]}")


def main():
    print(mode_banner())
    d = HookedMCPDispatcher()
    r = run_agent(get_client(mock_model), "Give me the full status of customer C-1001 and order O-77.",
                  tools=d.tool_definitions(), execute=d.execute)
    print(f"step 3 normalised answer: {r.final_text}")
    print(f"step 6 refund $750: {d.execute(mcp_name('process_refund'), {'order_id': 'O-77', 'amount': 750})}")
    print(f"step 6 refund $120: {d.execute(mcp_name('process_refund'), {'order_id': 'O-77', 'amount': 120})['status']}")
    r = run_agent(get_client(mock_model), "Transfer $1000 to ACC-CLEAN-9.", tools=d.tool_definitions(), execute=d.execute)
    print(f"step 6 transfer: calls={[c[1].split('__')[-1] for c in r.tool_calls]} -> {r.final_text}")
    print(f"discount 30%: {d.execute(mcp_name('approve_discount'), {'order_id': 'O-77', 'percent': 30})['error']}")
    d.manager_approves("O-77", 30)
    print(f"after manager approval: {d.execute(mcp_name('approve_discount'), {'order_id': 'O-77', 'percent': 30})['status']}")
    print(f"ledger: {d.ledger}")


if __name__ == "__main__":
    main()
