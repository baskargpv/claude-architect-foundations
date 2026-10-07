"""Task 1.6 — three decomposition mistakes.

1. Single-pass review of every file at once: attention dilution. Early files get
   detail, later files get skimmed, and cross-file contracts aren't connected.
   (A bigger model or a "be equally thorough" prompt doesn't change the architecture.)
2. Batching (groups of 2) with NO integration pass: fine within a batch, blind
   across batches. users.py and client.py land in different batches.
3. A fixed pipeline applied to open-ended debugging: the steps were chosen before
   the evidence, so the unexpected lead (payments-service) is never followed.
"""

from __future__ import annotations

import json

from common.client import ask_json, get_client, mode_banner
from domain1_agentic_architecture.task_1_6_task_decomposition.good_example import (
    FILES,
    FINDINGS_SCHEMA,
    SYMPTOM,
    SYSTEM_DATA,
    mock_model,
)


def single_pass_review(client, files: dict[str, str] = FILES) -> list[dict]:
    sources = "\n".join(f"--- {p} ---\n{s}" for p, s in files.items())
    prompt = f"[SINGLE PASS]\nReview all of these files with equal thoroughness.\n{sources}"
    return ask_json(client, prompt, FINDINGS_SCHEMA)["findings"]


def batched_review(client, files: dict[str, str] = FILES, batch_size: int = 2) -> list[dict]:
    paths = list(files)
    findings = []
    for i in range(0, len(paths), batch_size):
        batch = paths[i:i + batch_size]
        sources = "\n".join(f"--- {p} ---\n{files[p]}" for p in batch)
        findings += ask_json(client, f"[BATCH REVIEW]\n{sources}", FINDINGS_SCHEMA)["findings"]
    return findings  # no integration pass


FIXED_DEBUG_PLAN = ["app logs", "db metrics", "cdn status"]  # decided before looking at anything


def fixed_pipeline_investigation(symptom: str = SYMPTOM) -> dict:
    observations = {step: SYSTEM_DATA[step] for step in FIXED_DEBUG_PLAN}
    return {"steps": FIXED_DEBUG_PLAN, "observations": observations, "root_cause": None}


def _cross(findings):
    return [f for f in findings if len(f["files"]) > 1]


def main():
    print(mode_banner())
    sp = single_pass_review(get_client(mock_model))
    print(f"1) single pass: {len(sp)} findings on {sorted({f['files'][0] for f in sp})}, cross-file={len(_cross(sp))}")
    b = batched_review(get_client(mock_model))
    print(f"2) batched, no integration: {len(b)} findings, cross-file={len(_cross(b))}  <- users.py/client.py in different batches")
    inv = fixed_pipeline_investigation()
    print(f"3) fixed debug pipeline: steps={inv['steps']} root_cause={inv['root_cause']}")
    print(f"   app logs said: {json.dumps(inv['observations']['app logs'])}  <- lead never followed")


if __name__ == "__main__":
    main()
