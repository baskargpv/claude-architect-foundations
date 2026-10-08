"""Task 4.6 — Multi-Instance and Multi-Pass Review (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-6-multi-pass-review

Independent instances review (not the generating session). Per-file passes + one integration pass
beat a single pass. Confidence routes findings - but only after calibration against labelled verdicts.
Reuses Task 1.6's 12-file sample repo and review passes.
"""

from __future__ import annotations

from common.client import ask_json, get_client, mode_banner
from common.mock import json_message, last_user_text
from domain1_agentic_architecture.task_1_6_task_decomposition.good_example import (
    dilution_artefacts,
    load_repo,
    mock_model as review_mock,
    multi_pass_review,
    single_pass_review,
)

FILES = load_repo()

# Plausible-sounding findings that are wrong (they creep into real reviews)
NOISE = [{"file": "07_format.js", "line": 2, "severity": "major", "kind": "race_condition", "description": "possible race condition"},
         {"file": "09_invoice.js", "line": 5, "severity": "major", "kind": "unhandled_promise", "description": "unhandled promise"},
         {"file": "04_db.js", "line": 2, "severity": "minor", "kind": "magic_number", "description": "magic number 4200"}]


def is_noise(finding: dict) -> bool:
    return finding["kind"] in {n["kind"] for n in NOISE}


def self_reported_confidence(finding: dict) -> float:
    """SIMULATED raw confidence: reflects how sure the model sounds, not how often it's right."""
    if finding["kind"] in ("race_condition", "unhandled_promise"):
        return 0.85  # confidently wrong
    return {"critical": 0.92, "major": 0.82, "minor": 0.72}.get(finding.get("severity"), 0.8)


# ---- Steps 1-3: single pass vs per-file + integration ----------------------------------------------

def review_with_confidence(client) -> list[dict]:
    multi = multi_pass_review(client, FILES)
    findings = multi["issues"] + [{**c, "file": c["files"][1], "line": 0, "severity": "critical"} for c in multi["cross_file"]]
    findings += NOISE
    return [{**f, "confidence": self_reported_confidence(f)} for f in findings]


# ---- Step 5: a fresh instance verifies findings; calibrate thresholds from those labels -------------------

VERDICT = {"type": "object", "additionalProperties": False, "required": ["valid"], "properties": {"valid": {"type": "boolean"}}}


def verify(client, finding: dict) -> bool:
    """A separate instance with no generation or review context judges each finding on its own."""
    return ask_json(client, f"[VERIFY] Is this finding correct?\n{finding}\n--- {finding['file']} ---\n{FILES[finding['file']]}",
                    VERDICT)["valid"]


def calibrate(labelled: list[tuple[float, bool]], target: float = 0.9) -> float:
    """Lowest confidence at which every finding at or above it is right >= target of the time."""
    for t in sorted({c for c, _ in labelled}):
        above = [ok for c, ok in labelled if c >= t]
        if above and sum(above) / len(above) >= target:
            return t
    return 1.01  # nothing qualifies: everything goes to humans


# ---- Step 4: route by calibrated threshold ---------------------------------------------------------

def route(findings: list[dict], threshold: float) -> dict:
    return {"developers": [f for f in findings if f["confidence"] >= threshold],
            "human_queue": [f for f in findings if f["confidence"] < threshold]}


def pipeline(review_client, verify_client) -> dict:
    findings = review_with_confidence(review_client)
    labelled = [(f["confidence"], verify(verify_client, f)) for f in findings]
    threshold = calibrate(labelled)
    routed = route(findings, threshold)
    return {"threshold": threshold, "to_developers": len(routed["developers"]), "to_humans": len(routed["human_queue"]),
            "false_positives_to_developers": sum(1 for f in routed["developers"] if is_noise(f)), "routed": routed}


PRACTICE = {
    "question": "A 14-file PR gets uneven depth and contradictory findings. How should the review be restructured?",
    "options": {"A": "One pass with a larger-context model", "B": "Per-file passes plus a cross-file integration pass",
                "C": "Three runs, keep findings with majority agreement", "D": "Require 3-4 file PRs"},
    "answer": "B",
    "why": "Attention quality, not context size: focused per-file passes plus an integration pass.",
}


def verify_mock(kwargs: dict):
    prompt = last_user_text(kwargs)
    return json_message({"valid": not any(n["description"] in prompt for n in NOISE)})


def main():
    print(mode_banner())
    single = single_pass_review(get_client(review_mock), FILES)
    print(f"step 1 single pass: {len(single['issues'])} findings, artefacts: {[a['kind'] for a in dilution_artefacts(single, FILES)]}")
    r = pipeline(get_client(review_mock), get_client(verify_mock))
    print(f"steps 2-5: calibrated threshold {r['threshold']} -> developers {r['to_developers']}, humans {r['to_humans']}, "
          f"false positives sent to developers {r['false_positives_to_developers']}")


if __name__ == "__main__":
    main()
