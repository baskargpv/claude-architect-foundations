"""Task 5.5 — Human Review & Confidence Calibration (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/5-context-management/5-5-human-review-calibration

97% aggregate accuracy can hide 45% on one document type. Measure by type AND field, calibrate
confidence per field per type against labelled data, sample high-confidence items too, and
spend reviewer time on the most uncertain items first.
"""

from __future__ import annotations

import heapq
import random
from collections import defaultdict

# ---- Step 1: a mock extraction system (per-field values + confidence) ------------------------------

ACCURACY = {  # the lesson's table: date, amount, name accuracy per document type
    "standard_invoice": {"date": 0.995, "amount": 0.982, "name": 0.978},
    "handwritten_receipt": {"date": 0.601, "amount": 0.553, "name": 0.712},
    "scanned_pdf": {"date": 0.724, "amount": 0.698, "name": 0.801},
    "international": {"date": 0.452, "amount": 0.521, "name": 0.634},
}
VOLUME = {"standard_invoice": 9200, "handwritten_receipt": 250, "scanned_pdf": 300, "international": 250}


def generate(seed: int = 7) -> list[dict]:
    rng, records = random.Random(seed), []
    for doc_type, n in VOLUME.items():
        for i in range(n):
            for field, acc in ACCURACY[doc_type].items():
                correct = rng.random() < acc
                if correct:
                    conf = rng.uniform(0.85, 0.99)
                elif doc_type == "international" and field == "amount":
                    conf = rng.uniform(0.95, 0.99)  # a novel currency-format error the model is SURE about
                else:  # how sure the model sounds when wrong depends on the field (miscalibration)
                    conf = rng.uniform(*{"date": (0.55, 0.8), "amount": (0.75, 0.95), "name": (0.6, 0.88)}[field])
                records.append({"id": f"{doc_type}-{i}", "doc_type": doc_type, "field": field,
                                "confidence": round(conf, 3), "correct": correct})
    return records


# ---- Step 2: accuracy by segment vs the aggregate ------------------------------------------------------

def accuracy_by_segment(records: list[dict]) -> dict:
    seg = defaultdict(list)
    for r in records:
        seg[(r["doc_type"], r["field"])].append(r["correct"])
    return {"aggregate": round(sum(r["correct"] for r in records) / len(records), 3),
            "by_segment": {k: round(sum(v) / len(v), 3) for k, v in seg.items()}}


# ---- Step 3: calibration curves and thresholds per field per document type -----------------------------

BANDS = [(0.5, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.0)]


def calibration(labelled: list[dict]) -> dict:
    curves = defaultdict(dict)
    for doc_type in VOLUME:
        for field in ("date", "amount", "name"):
            seg = [r for r in labelled if r["doc_type"] == doc_type and r["field"] == field]
            for lo, hi in BANDS:
                band = [r["correct"] for r in seg if lo <= r["confidence"] < hi]
                if band:
                    curves[(doc_type, field)][(lo, hi)] = round(sum(band) / len(band), 3)
    return dict(curves)


def thresholds(curves: dict, target: float = 0.95) -> dict:
    """Lowest band start at which this band AND every band above it meet the target; else never automate."""
    out = {}
    for seg, curve in curves.items():
        out[seg] = None
        for lo, hi in sorted(curve):
            if all(acc >= target for (l, _), acc in curve.items() if l >= lo):
                out[seg] = lo
                break
    return out


# ---- Step 4: stratified random sampling - includes high-confidence items -------------------------------

def stratified_sample(records: list[dict], per_stratum: int = 5, seed: int = 1) -> list[dict]:
    rng, strata = random.Random(seed), defaultdict(list)
    for r in records:
        band = next(b for b in BANDS if b[0] <= r["confidence"] < b[1] or r["confidence"] == 1.0)
        strata[(r["doc_type"], band)].append(r)
    return [r for items in strata.values() for r in rng.sample(items, min(per_stratum, len(items)))]


# ---- Step 5: a dynamic review queue - most uncertain first -----------------------------------------

class ReviewQueue:
    def __init__(self):
        self._heap = []

    def push(self, record: dict):
        heapq.heappush(self._heap, (record["confidence"], record["id"], record["field"], record))

    def pop(self) -> dict:
        return heapq.heappop(self._heap)[-1]


PRACTICE = {
    "question": "A 97%-accurate extraction system proposes auto-approving extractions above 95% model confidence. Critical risk?",
    "options": {"A": "Automated extractions always need human review", "B": "95% is too low - use 99%",
                "C": "The model will grow overconfident over time",
                "D": "The aggregate may hide poor per-type/field accuracy, and confidence needs calibration first"},
    "answer": "D",
    "why": "Validate by segment and calibrate against labelled data before reducing human review.",
}


def main():
    records = generate()
    acc = accuracy_by_segment(records)
    print(f"step 2 aggregate accuracy {acc['aggregate']:.1%}; worst segments: "
          f"{sorted(acc['by_segment'].items(), key=lambda kv: kv[1])[:3]}")
    th = thresholds(calibration(records))
    print(f"step 3 automate-above thresholds: standard date {th[('standard_invoice', 'date')]}, "
          f"international amount {th[('international', 'amount')]} (None = never automate)")
    sample = stratified_sample(records)
    print(f"step 4 stratified sample: {len(sample)} items, high-confidence included: {sum(r['confidence'] >= 0.95 for r in sample)}")
    q = ReviewQueue()
    for r in records[:200] + records[-200:]:
        q.push(r)
    print(f"step 5 next for review: {[round(q.pop()['confidence'], 3) for _ in range(3)]} (lowest confidence first)")


if __name__ == "__main__":
    main()
