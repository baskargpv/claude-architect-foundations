"""Task 5.1 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-1-context-window-management

Trap 1  progressive summarisation trusted with transactional data
Trap 2  "pay attention to everything" as the fix for lost-in-the-middle
Trap 3  keeping full tool results "in case they're needed later"
Trap 4  selectively truncating conversation history
"""

from __future__ import annotations

import json

from common.client import get_client
from domain5_context_reliability.task_5_1_context_window.good_example import ORDER_LOOKUP, mock_model, run_conversation, trim


def trap1_summarisation_only(client) -> str:
    return run_conversation(client, use_facts_block=False)[-1]


def trap2_attention_instruction(findings: int = 9, key_index: int = 4) -> dict:
    """SIMULATED position effect: the start and end of long input get attention, the middle less so.
    Adding 'pay attention to everything' doesn't move the key finding."""
    sections = [f"Finding {i}: routine detail" for i in range(findings)]
    sections[key_index] = "Finding 4: the supplier contract expires next week"
    prompt = "Pay close attention to EVERYTHING below.\n" + "\n".join(sections)
    attended = sections[:2] + sections[-2:]  # what a long middle-heavy input effectively gets read as
    return {"instruction_added": prompt.startswith("Pay close attention"), "key_finding_used": sections[key_index] in attended}


def trap3_untrimmed_results(turns: int = 8) -> dict:
    full, trimmed = len(json.dumps(ORDER_LOOKUP)), len(json.dumps(trim(ORDER_LOOKUP)))
    return {"chars_over_conversation_untrimmed": full * turns, "trimmed": trimmed * turns}


def trap4_truncate_history() -> dict:
    """Drop the 'old' turns - and with them the tool_use that a later tool_result answers."""
    history = [{"role": "user", "content": "refund order 8891"},
               {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "lookup_order", "input": {}}]},
               {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "{...}"}]},
               {"role": "assistant", "content": "Found it."}]
    truncated = history[2:]
    ids_used = {b["id"] for m in truncated if isinstance(m["content"], list) for b in m["content"] if b.get("type") == "tool_use"}
    orphans = [b["tool_use_id"] for m in truncated if isinstance(m["content"], list)
               for b in m["content"] if b.get("type") == "tool_result" and b["tool_use_id"] not in ids_used]
    return {"orphaned_tool_results": orphans, "first_message_role": truncated[0]["role"]}


def main():
    print(f"trap 1 summary only      : {trap1_summarisation_only(get_client(mock_model))}")
    print(f"trap 2 'pay attention'   : {trap2_attention_instruction()}")
    print(f"trap 3 untrimmed results : {trap3_untrimmed_results()}")
    print(f"trap 4 truncated history : {trap4_truncate_history()}  <- the API is stateless; this history is broken")


if __name__ == "__main__":
    main()
