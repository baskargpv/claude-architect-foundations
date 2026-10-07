# Task 1.7 — Session State and Resumption

## Theory

Three options, three distinct jobs:

| Option | Use when | Do NOT use when |
|---|---|---|
| `--resume <name>` | Prior context is still valid: no files changed since the last session | Files were modified, so old tool results in history are stale |
| `fork_session` | Divergent exploration from a shared, still-valid baseline (e.g. comparing two refactoring strategies) | To fix stale context. The fork inherits the stale history. |
| Fresh start + summary injection | Tool results are stale (files changed) or the context is degraded | Prior context is fully valid, where resume is cheaper |

**The stale context problem.** Resuming restores **every** prior tool result, including file reads from before modifications. The model reasons from that old data alongside anything new. The result is contradictions: recommending fixes already applied, or citing code that no longer exists.

**The naive fix doesn't work.** Resuming and asking the agent to re-read changed files doesn't remove the **old** tool result already in history. It can still sway reasoning on side decisions.

**The correct fix** is a fresh session plus:

- A structured summary: conclusions only, never raw tool output.
- An explicit list of the files that changed, so the agent re-analyses only those. The summary covers everything unchanged.

## Exam trap

- Recommending `--resume` after files changed: stale tool results remain in history.
- Using `fork_session` to fix stale context: the fork copies the same stale history.
- Re-exploring the whole codebase when only a few files changed: wasteful.
- Confusing fork with resume: **fork branches** (the original stays untouched), **resume appends** (the same session continues).

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Where these live | `--resume`, `fork_session` | They're Claude Code CLI / Agent SDK session features (`claude --resume`, the SDK's `resume` + `fork_session` options). On the raw Messages API there's no server-side session; you resend history yourself. This demo models a session as a saved history, so the same decision logic runs offline and on the Messages API. |

## Code walkthrough

**`good_example.py`**

- **`Session`** stores `messages` (with the raw tool results), `file_hashes` at read time, and distilled `conclusions`.
- **`choose_strategy()`** decides in this order:
  1. Any changed hash → `fresh`. This holds even if the intent is to explore alternatives, because a fork would carry the stale read.
  2. Otherwise, intent `explore_alternatives` → `fork`.
  3. Otherwise → `resume`.
- **`build_fresh_prompt()`** separates the conclusions about unchanged files (still true) from the conclusions about changed files (re-verify), names the changed files, and says "re-read ONLY those". It contains no raw tool output.
- **`continue_work()`** runs the chosen strategy through the Task 1.1 loop (`run_agent(history=...)` for resume and fork).
  - **Resume** mutates the same session.
  - **Fork** deep-copies, tags `parent`, and leaves the original's message count unchanged.
- **Mock model:** it reasons from whatever version of `auth.py` appears anywhere in the request. That's exactly how stale history contaminates an answer.

**`anti_pattern.py`**

- `resume_anyway()` recommends replacing `==` with `hmac.compare_digest`, a fix that's already applied.
- `resume_and_reread()` reads the new `auth.py`, but the old read is still in history and the answer is still wrong.
- `fork_to_fix_staleness()` copies the stale read into the fork.
- `fresh_full_reexploration()` reads all 3 files when only 1 changed.

**`test_task_1_7.py`** checks:

- The full strategy matrix.
- The fresh prompt holds no raw tool output.
- A fresh start reads only `auth.py` and gives the correct answer.
- Fork leaves the original untouched; resume appends to the same session.
- All four anti-patterns fail as described.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_7_session_state.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_7_session_state.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_7_session_state
```
