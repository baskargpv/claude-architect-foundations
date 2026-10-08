"""Task 2.2 — Structured Error Responses for All Four Categories (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-2-structured-error-responses

Two layers: protocol errors (JSON-RPC, handled by the host, the model never sees them) and
tool execution errors (a normal result with isError: true that the agent reasons about).
errorCategory / isRetryable / description are app-level conventions placed in structuredContent.
"""

from __future__ import annotations

import re
import time

from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent

from common.mcp_util import call

CUSTOMERS = {"jane@example.com": {"customer_id": "C-1042", "name": "Jane Roe"}}
VALID_EMAIL = re.compile(r"^[a-z0-9._]+@[a-z0-9.]+\.[a-z]+$")


def error(category: str, retryable: bool, description: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=description)], is_error=True,
                          structured_content={"errorCategory": category, "isRetryable": retryable,
                                              "description": description})


def ok(data: dict) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=str(data))], is_error=False, structured_content=data)


# ---- Steps 1-4: a customer-lookup MCP tool with a failure_mode switch ---------------------------

def build_server() -> MCPServer:
    srv = MCPServer("crm")
    attempts = {"transient": 0}

    @srv.tool()
    def lookup_customer(email: str, failure_mode: str = "none", principal: str = "agent") -> CallToolResult:
        """Look up a customer by email. failure_mode simulates: none | transient | business | permission."""
        if failure_mode == "transient":
            attempts["transient"] += 1
            if attempts["transient"] <= 2:  # fails twice, then the service recovers
                return error("transient", True, "CRM timed out after 5s - safe to retry the same call")
        if not VALID_EMAIL.match(email):
            return error("validation", False, f"'{email}' is not a valid email: use lowercase, no spaces")
        if failure_mode == "business":
            return error("business", False, "Account is under legal hold - lookups need the compliance team")
        if failure_mode == "permission" and principal != "supervisor":
            return error("permission", False, "VIP records need supervisor access")
        customer = CUSTOMERS.get(email)
        if customer is None:  # Step 4: a successful query that found nothing - NOT an error
            return ok({"resultCount": 0, "results": []})
        return ok({"resultCount": 1, "results": [customer]})

    return srv


# ---- Step 5: an agent loop that branches on the error category -----------------------------------

def lookup_with_recovery(server, email: str, failure_mode: str = "none", backoff: float = 0.001) -> dict:
    actions, principal = [], "agent"
    for attempt in range(5):
        r = call(server, "lookup_customer", {"email": email, "failure_mode": failure_mode, "principal": principal})
        if not r.is_error:
            if r.structured_content["resultCount"] == 0:
                return {"outcome": "no such customer", "actions": actions}  # valid empty: accept, don't retry
            return {"outcome": "found", "customer": r.structured_content["results"][0], "actions": actions}
        err = r.structured_content
        actions.append(err["errorCategory"])
        if err["errorCategory"] == "transient":  # same call again, after a delay
            time.sleep(backoff * 2 ** attempt)
        elif err["errorCategory"] == "validation":  # fix the input, send a NEW call
            email = email.strip().lower().replace(" ", "")
        elif err["errorCategory"] == "business":  # don't retry: take another path
            return {"outcome": "escalated", "reason": err["description"], "actions": actions}
        elif err["errorCategory"] == "permission":  # a different principal, not a better call
            principal = "supervisor"
    return {"outcome": "gave up", "actions": actions}


PRACTICE = {
    "question": "A lookup returns an empty array; the agent retries 3 times and escalates, but the account simply "
                "doesn't exist. Root cause?",
    "options": {"A": "Retry limit too low", "B": "Lookups should never be retried",
                "C": "Escalation threshold too high",
                "D": "The tool doesn't distinguish access failures from valid empty results"},
    "answer": "D",
    "why": "A successful empty query must look nothing like a failed one, so the agent knows not to retry.",
}


def main():
    srv = build_server()
    for email, mode in [("jane@example.com", "none"), ("nobody@example.com", "none"), ("jane@example.com", "transient"),
                        (" Jane@Example.com", "none"), ("jane@example.com", "business"), ("jane@example.com", "permission")]:
        r = lookup_with_recovery(srv, email, mode)
        print(f"{mode:10s} {email!r:22s} -> {r['outcome']:16s} actions={r['actions']}")


if __name__ == "__main__":
    main()
