# Task 1.7 — Session State and Resumption

Lesson: <https://claudecertificationguide.com/learn/1-agentic-architecture/1-7-session-state-resumption>

## What you need to know

| Option | Use when |
|---|---|
| `--resume <name>` | Prior context is still valid: nothing changed. Continues the same session with its full history, tool results included. |
| `fork_session` | Comparing divergent approaches from a shared baseline. Each fork is independent, and the original stays untouched. |
| Fresh start + summary injection | Tool results are stale (files changed) or the history is cluttered |

- **The stale-context problem:** after files change, a resumed session still reasons from the *old* tool results, so its advice contradicts the current code.
- **The naive fix doesn't work:** resuming and asking for a re-read leaves the old results in history.
- **The correct fix:**
  1. Start fresh.
  2. Inject a summary of conclusions.
  3. Name the changed files so only those get re-analysed. The summary covers the rest.

**Decision matrix** (`DECISION_MATRIX`, tested row by row):

| Scenario | Option |
|---|---|
| No files changed | resume |
| Comparing two refactors | fork |
| 3 of 50 files modified | fresh + summary |
| Cluttered history | fresh + summary |
| Testing strategy vs documentation strategy | fork |
| Dependency updates | fresh + summary |

## Exam traps

| Trap | Demo |
|---|---|
| Re-exploring all files when only 3 changed | `trap1_full_reexploration`: 10 reads for 3 changes |
| `--resume` after files changed | `trap2_resume_after_modification`: recommends the 3 fixes already applied. `trap2b_resume_and_reread` shows the naive fix is still stale. |
| Confusing `fork_session` with `--resume` | `trap3_resume_instead_of_fork`: approach B's history contains approach A |
| `fork_session` to handle stale context | `trap4_fork_to_fix_staleness`: the fork carries the old reads and gives the same stale advice |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Naming and resuming | `--resume <name>` | Name a session at start with `--name` / `-n`, or with `/rename` mid-session. `claude --resume <name>` continues it, and **only resumes sessions that already exist** (`SessionStore.load()` raises `SessionNotFound`). `-c` / `--continue` resumes the latest session in the directory. |
| `fork_session` | A separate session control | Set **alongside** `resume` in the SDK (`resume=<id>, fork_session=True`). The CLI pairs `--fork-session` with `--resume` / `--continue`. |

## Practice scenario

After modifying 3 of 50 files, a resumed session gives contradictory advice. Best approach?

**C: a fresh session with an injected summary, naming the 3 changed files.**

- A (resume + re-read) keeps the stale results.
- B (re-analyse all 50) is wasteful.
- D (fork) inherits the stale history.

## Build exercise → code

The exercise is "Implement Session Management Strategies" (45 min).

| Step | Where |
|---|---|
| 1. A named session that analyses a 10-file codebase | `analyse_codebase()` over `sample_codebase/` (10 `.ts` files), persisted by name in `SessionStore`, the analogue of `--name` / `--resume` |
| 2. A structured summary per file (issues, severity, recommendations), conclusions only | `structured_summary()` |
| 3. Modify 3 files | `apply_fixes()` copies `fixed_versions/` over `auth.ts`, `session.ts` and `middleware.ts`, the lesson's example |
| 4. Resume and observe stale symptoms | `resume()` + `stale_symptoms()`: recommends the 3 fixes already applied |
| 5. A fresh session with the summary, naming the 3 changed files | `fresh_start()`: re-reads only those 3 files and lists only the remaining fixes (logger, payments, users) |
| 6. Compare the two | `compare_sessions()` |

**About the mock reviewer.** It's rule-based and reasons from **every** version of a file visible anywhere in its request. That's exactly how stale tool results in history contaminate an answer.

`changed_since()` compares file hashes saved with the session, so the decision to start fresh comes from data, not memory.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_7_session_resumption.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_7_session_resumption.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_7_session_resumption
```
