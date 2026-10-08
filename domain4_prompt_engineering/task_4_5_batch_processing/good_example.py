"""Task 4.5 — Batch Processing Strategies (lesson Build Exercise, steps 1-5).

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-5-batch-processing

Message Batches API: 50% cheaper, up to 24h, no latency SLA, custom_id correlates results.
Blocking work stays synchronous. Resubmit only failures (errored or expired), with changes.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

from common import config
from common.client import mode_banner

# ---- Step 1: classify workflows ---------------------------------------------------------------------

WORKFLOWS = [("pre-merge security check", True), ("overnight tech-debt report", False), ("weekly dependency audit", False),
             ("real-time review comments in the IDE", True), ("nightly test generation", False)]


def classify(blocking: bool) -> str:
    return "synchronous - someone is waiting" if blocking else "batch - latency-tolerant, 50% cheaper"


# ---- Step 2: a 20-document batch with unique custom_ids ---------------------------------------------

DOCS = {f"doc-{i:02d}": f"Contract {i}: party A pays party B {1000 + i} GBP on delivery." for i in range(1, 21)}


def build_requests(docs: dict[str, str], prompt: str = "Extract the payer, payee and amount.", max_tokens: int = 1024) -> list[dict]:
    return [{"custom_id": cid, "params": {"model": config.model(), "max_tokens": max_tokens,
                                          "messages": [{"role": "user", "content": f"{prompt}\n{text_}"}]}}
            for cid, text_ in docs.items()]


# ---- Step 3: run, collect by custom_id, resubmit only failures with modifications -------------------

def run_batch(client, requests: list[dict], poll_seconds: float = 0.0, timeout_s: float = 24 * 3600) -> dict:
    batch = client.messages.batches.create(requests=requests)
    start = time.time()
    while client.messages.batches.retrieve(batch.id).processing_status != "ended":
        if time.time() - start > timeout_s:
            break
        time.sleep(poll_seconds or 30)
    return {r.custom_id: r.result for r in client.messages.batches.results(batch.id)}  # any order: key by custom_id


def retry_requests(failed: list[str], original: dict[str, dict]) -> list[dict]:
    out = []
    for cid in failed:
        params = original[cid]["params"]
        out.append({"custom_id": cid, "params": {**params, "max_tokens": params["max_tokens"] * 2}})  # e.g. raise max_tokens
    return out


def process_all(client, docs: dict[str, str]) -> dict:
    requests = build_requests(docs)
    results = run_batch(client, requests)
    failed = [cid for cid, r in results.items() if r.type in ("errored", "expired")]  # expired counts as failed
    retried = run_batch(client, retry_requests(failed, {r["custom_id"]: r for r in requests})) if failed else {}
    results.update(retried)
    return {"first_pass_failed": failed, "succeeded": sum(r.type == "succeeded" for r in results.values()),
            "resubmitted": len(retried)}


# ---- Step 4: submission cadence for an SLA ------------------------------------------------------------

def cadence_ok(cadence_h: float, sla_h: float, window_h: float = 24) -> bool:
    return cadence_h < sla_h - window_h  # must be SHORTER than the buffer, not equal to it


def recommended_cadence(sla_h: float, window_h: float = 24) -> int:
    buffer = sla_h - window_h
    return max(c for c in (1, 2, 3, 4, 6, 8, 12) if c < buffer)


# ---- Step 5: refine on a 5-document sample before the full batch ---------------------------------------

def expected_retries(n_docs: int, first_pass_rate: float) -> int:
    return round(n_docs * (1 - first_pass_rate))


PRACTICE = {
    "question": "A manager wants both a blocking pre-merge check and an overnight tech-debt report on the Batches API "
                "for 50% savings. Evaluate.",
    "options": {"A": "Batch the tech-debt report only; keep pre-merge checks real-time",
                "B": "Batch both, with a real-time fallback on timeout", "C": "Keep both real-time",
                "D": "Batch both and poll for completion"},
    "answer": "A",
    "why": "No latency SLA (up to 24h) is unacceptable for a blocking check; overnight work is a perfect fit.",
}


# ---- offline stand-in for client.messages.batches (same calls as the SDK) ------------------------------

class FakeBatches:
    FAIL_FIRST = {"doc-07": "errored", "doc-13": "errored", "doc-18": "expired"}

    def __init__(self):
        self._batches = {}

    def create(self, requests):
        bid = f"msgbatch_{len(self._batches) + 1}"
        self._batches[bid] = requests
        return SimpleNamespace(id=bid, processing_status="in_progress")

    def retrieve(self, bid):
        return SimpleNamespace(id=bid, processing_status="ended")

    def results(self, bid):
        for req in reversed(self._batches[bid]):  # results come back in any order
            cid, params = req["custom_id"], req["params"]
            outcome = self.FAIL_FIRST.get(cid) if params["max_tokens"] < 2048 else None
            if params.get("tools"):
                msg = SimpleNamespace(stop_reason="tool_use", content=[SimpleNamespace(type="tool_use", name=params["tools"][0]["name"])])
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))
            elif outcome:
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type=outcome, message=None))
            else:
                msg = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="payer A, payee B")])
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))


def batch_client():
    if config.is_live():
        import anthropic
        return anthropic.Anthropic()
    return SimpleNamespace(messages=SimpleNamespace(batches=FakeBatches()))


def main():
    print(mode_banner())
    for name, blocking in WORKFLOWS:
        print(f"step 1 {name:38s} -> {classify(blocking)}")
    print(f"step 2-3 {process_all(batch_client(), DOCS)}")
    print(f"step 4 30h SLA: buffer 6h; cadence 6h ok? {cadence_ok(6, 30)}; recommended every {recommended_cadence(30)}h")
    print(f"step 5 retries for 1,000 docs: 90% first pass -> {expected_retries(1000, 0.9)}, 60% -> {expected_retries(1000, 0.6)}")


if __name__ == "__main__":
    main()
