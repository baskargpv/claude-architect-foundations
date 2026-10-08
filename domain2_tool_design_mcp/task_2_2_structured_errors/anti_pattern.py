"""Task 2.2 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/2-tool-design-mcp/2-2-structured-error-responses

Trap 1  retrying an empty result from a successful query
Trap 2  generic "Operation failed" errors with no structured metadata
Trap 3  treating business errors as retryable
Trap 4  marking validation isRetryable: true because the agent can recover
Trap 5  reading isRetryable: false as "abandon the task"
Trap 6  a subagent silently returning empty results as success on failure
"""

from __future__ import annotations

from common.mcp_util import call
from domain2_tool_design_mcp.task_2_2_structured_errors.good_example import build_server


def trap1_retry_empty_result(email: str = "nobody@example.com") -> dict:
    srv, calls = build_server(), 0
    for _ in range(4):  # "empty looks like failure" -> retry three times, then escalate
        calls += 1
        if call(srv, "lookup_customer", {"email": email}).structured_content["resultCount"]:
            return {"calls": calls, "outcome": "found"}
    return {"calls": calls, "outcome": "escalated to a human (the account just doesn't exist)"}


def trap2_generic_errors() -> dict:
    """With only 'Operation failed', the agent can't tell retry-able from not - so it retries everything."""
    srv, outcomes = build_server(), {}
    for mode in ("business", "permission"):
        tries = 0
        for _ in range(3):
            tries += 1
            r = call(srv, "lookup_customer", {"email": "jane@example.com", "failure_mode": mode})
            message = "Operation failed" if r.is_error else "ok"  # metadata thrown away
            if message == "ok":
                break
        outcomes[mode] = f"{tries} identical retries, still failing"
    return outcomes


def trap3_business_as_retryable() -> dict:
    srv = build_server()
    results = [call(srv, "lookup_customer", {"email": "jane@example.com", "failure_mode": "business"}).is_error
               for _ in range(3)]
    return {"attempts": 3, "all_failed": all(results)}  # the policy says no every time


def trap4_validation_marked_retryable() -> dict:
    """isRetryable: true invites resending the EXACT call - which fails the same way."""
    srv = build_server()
    results = [call(srv, "lookup_customer", {"email": " Jane@Example.com"}).structured_content["errorCategory"]
               for _ in range(3)]
    return {"resent_unchanged": 3, "results": results}


def trap5_false_means_abandon() -> dict:
    r = call(build_server(), "lookup_customer", {"email": " Jane@Example.com"})
    if not r.structured_content["isRetryable"]:
        return {"outcome": "abandoned", "but_fixable_by": "lower-casing the email and sending a new call"}
    return {"outcome": "retried"}


def trap6_silent_suppression() -> dict:
    srv = build_server()

    def subagent_lookup(email):
        r = call(srv, "lookup_customer", {"email": email, "failure_mode": "transient"})
        return {"status": "success", "results": [] if r.is_error else r.structured_content["results"]}  # WRONG

    out = subagent_lookup("jane@example.com")
    verdict = "customer does not exist" if out["status"] == "success" and not out["results"] else "?"
    return {"subagent_said": out, "coordinator_concludes": verdict}


def main():
    print(f"trap 1 retry empty result : {trap1_retry_empty_result()}")
    print(f"trap 2 generic errors     : {trap2_generic_errors()}")
    print(f"trap 3 business retryable : {trap3_business_as_retryable()}")
    print(f"trap 4 validation retry   : {trap4_validation_marked_retryable()}")
    print(f"trap 5 false = abandon    : {trap5_false_means_abandon()}")
    print(f"trap 6 silent suppression : {trap6_silent_suppression()['coordinator_concludes']!r} (Jane exists - the CRM timed out)")


if __name__ == "__main__":
    main()
