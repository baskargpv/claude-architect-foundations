"""Task 5.3 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-3-error-propagation

Trap 1  catching a timeout and returning empty results marked as success
Trap 2  terminating the whole pipeline when one subagent times out
Trap 3  a generic "search unavailable" after retries run out
Trap 4  retrying a valid empty result because it looks like a failure
"""

from __future__ import annotations

from domain5_context_reliability.task_5_3_error_propagation.good_example import Source


def trap1_silent_suppression() -> dict:
    src = Source("journals", ["geothermal efficiency study"], fails_times=-1)
    try:
        results = src.query("geothermal")
    except TimeoutError:
        results = []  # WRONG: looks exactly like "no sources exist"
    return {"status": "success", "results": results, "coordinator_concludes": "geothermal is irrelevant"}


def trap2_terminate_pipeline() -> dict:
    completed = {"solar": ["solar output up 12%"], "wind": ["offshore growth 18%"]}
    try:
        Source("journals", None, fails_times=-1).query("geothermal")
    except TimeoutError:
        completed = {}  # one failure throws away every other subagent's work
    return {"results_kept": completed}


def trap3_generic_status() -> dict:
    return {"status": "error", "message": "search unavailable"}  # which source? what was tried? any partial data? no idea


def trap4_retry_valid_empty(retries: int = 3) -> dict:
    src = Source("patents", [])
    calls = [src.query("space solar") for _ in range(retries)]
    return {"calls": retries, "all_empty": all(c == [] for c in calls), "note": "the answer was 'no patents' the first time"}


def main():
    print(f"trap 1 silent suppression : {trap1_silent_suppression()}")
    print(f"trap 2 terminate pipeline : {trap2_terminate_pipeline()}")
    print(f"trap 3 generic status     : {trap3_generic_status()}")
    print(f"trap 4 retry valid empty  : {trap4_retry_valid_empty()}")


if __name__ == "__main__":
    main()
