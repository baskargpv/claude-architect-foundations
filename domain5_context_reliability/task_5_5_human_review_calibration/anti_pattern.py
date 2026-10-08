"""Task 5.5 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-5-human-review-calibration

Trap 1  automating all high-confidence extractions because aggregate accuracy looks great
Trap 2  sampling only low-confidence extractions for human review
Trap 3  using raw confidence scores without calibration
Trap 4  spreading reviewer capacity evenly
"""

from __future__ import annotations

import random

from domain5_context_reliability.task_5_5_human_review_calibration.good_example import accuracy_by_segment, generate


def trap1_automate_on_aggregate(records: list[dict], threshold: float = 0.95) -> dict:
    auto = [r for r in records if r["confidence"] > threshold]
    wrong = [r for r in auto if not r["correct"]]
    return {"aggregate": accuracy_by_segment(records)["aggregate"], "automated": len(auto), "wrong_but_automated": len(wrong),
            "of_which_international_amounts": sum(r["doc_type"] == "international" and r["field"] == "amount" for r in wrong)}


def trap2_sample_low_confidence_only(records: list[dict], n: int = 200, seed: int = 1) -> dict:
    low = [r for r in records if r["confidence"] < 0.9]
    sample = random.Random(seed).sample(low, n)
    novel = [r for r in sample if r["doc_type"] == "international" and r["field"] == "amount" and not r["correct"]]
    return {"novel_high_confidence_errors_seen": len(novel)}  # they sit at 0.95+ and are never sampled


def trap3_raw_confidence(records: list[dict], lo: float = 0.85, hi: float = 0.95) -> dict:
    def acc(field):
        band = [r["correct"] for r in records if r["field"] == field and lo <= r["confidence"] < hi]
        return round(sum(band) / len(band), 3)
    return {"same_raw_band": f"{lo}-{hi}", "actual_accuracy": {f: acc(f) for f in ("date", "amount", "name")}}


def trap4_even_split(records: list[dict], capacity: int = 300, seed: int = 2) -> dict:
    even = random.Random(seed).sample(records, capacity)
    prioritised = sorted(records, key=lambda r: r["confidence"])[:capacity]
    return {"errors_caught_even_split": sum(not r["correct"] for r in even),
            "errors_caught_lowest_confidence_first": sum(not r["correct"] for r in prioritised)}


def main():
    records = generate()
    print(f"trap 1 automate on aggregate : {trap1_automate_on_aggregate(records)}")
    print(f"trap 2 sample low conf only  : {trap2_sample_low_confidence_only(records)}")
    print(f"trap 3 raw confidence        : {trap3_raw_confidence(records)}")
    print(f"trap 4 even reviewer split   : {trap4_even_split(records)}")


if __name__ == "__main__":
    main()
