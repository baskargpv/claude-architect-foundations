"""Task 4.5 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-5-batch-processing

Trap 1  switching every workflow to batch for the cost savings
Trap 2  assuming batch results arrive quickly because they usually do
Trap 3  the Batch API for workflows that need multi-turn tool calling
"""

from __future__ import annotations

from domain4_prompt_engineering.task_4_5_batch_processing.good_example import (
    WORKFLOWS,
    batch_client,
    build_requests,
    cadence_ok,
    run_batch,
)


def trap1_everything_to_batch() -> dict:
    blocked = [name for name, blocking in WORKFLOWS if blocking]
    return {"blocking_workflows_now_waiting_up_to_24h": blocked}


def trap2_design_for_typical_time(typical_h: float = 1, cadence_h: float = 6, sla_h: float = 30) -> dict:
    return {"looks_fine_typically": typical_h + cadence_h <= sla_h,
            "worst_case_hours": 24 + cadence_h, "meets_sla_in_worst_case": cadence_ok(cadence_h, sla_h)}


def trap3_multi_turn_tools_in_batch() -> dict:
    tool = {"name": "lookup_contract", "description": "Fetch a contract by id",
            "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}}}
    req = build_requests({"doc-01": "Check contract 7 against policy."})[0]
    req["params"]["tools"] = [tool]
    result = run_batch(batch_client(), [req])["doc-01"]
    return {"stop_reason": result.message.stop_reason,
            "what_now": "the item ends at tool_use; running the tool needs a follow-up request (synchronous API)"}


def main():
    print(f"trap 1 all to batch      : {trap1_everything_to_batch()}")
    print(f"trap 2 typical timing    : {trap2_design_for_typical_time()}")
    print(f"trap 3 tools in a batch  : {trap3_multi_turn_tools_in_batch()}")


if __name__ == "__main__":
    main()
