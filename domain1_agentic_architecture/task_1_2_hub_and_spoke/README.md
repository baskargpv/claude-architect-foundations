# Task 1.2 — Orchestration Patterns (Hub-and-Spoke)

## Theory

**Structure:** all communication flows through one coordinator. Subagents never talk to each other. A subagent knows only what the coordinator explicitly puts in its prompt.

**Breadth-first decomposition** runs in two phases:

1. **Generate** broad categories: "at least N, and don't stop at N if more exist".
2. **Validate** in a *separate* pass: "is anything major missing?" A dedicated second look beats self-critique done in the same breath as generation.

**Isolation principle:** every subagent call explicitly restates:

- the specific subtopic
- the broader research goal
- the expected output format
- any relevant prior findings

Nothing carries over, not even things that seem constant like the goal.

**Aggregation and refinement:**

- Build a coverage map that asks, per subtopic, whether *substantive* evidence exists (not just non-empty).
- Re-delegate **only the gaps**.
- The real exit is the coverage threshold. A max-iteration cap is only the safety net.

## Exam trap

A rigid "divide into **exactly** N subtopics" prompt is a narrow-decomposition failure one level up. It forces categories to be merged or dropped to hit the number, instead of letting breadth be discovered.

## Exam answer vs current docs

No material difference for this task. For live runs, the demo uses `output_config.format` (structured outputs) so every coordinator and subagent reply is parseable JSON. That's a current-API detail; the exam doesn't test it here.

## Code walkthrough

**`good_example.py`**

- `decompose()` asks for "at least 4 … do not stop at 4 … do not merge". `validate_breadth()` is a **separate** call that only looks for gaps. In the mock it finds *games and interactive media*.
- `build_subagent_prompt()` restates goal, subtopic, prior findings and output format on every call. Each subagent call is a fresh one-message request, so isolation holds by construction.
- `coverage_map()` counts a finding only if its evidence is substantive (≥ 20 chars of concrete evidence). In the mock, the first `music` result (`"it does"`) is non-empty but **not** substantive.
- `research()` re-delegates only the uncovered subtopics, passing their prior findings, and exits as soon as coverage meets the threshold. `max_rounds` is the safety net.

**`anti_pattern.py`**

- Uses "exactly 3 subtopics", so the mock merges `film and writing` and never finds games.
- Has no validation pass.
- Sends bare `"Research: music"` prompts with no goal, no format and no prior findings.
- Re-runs every subtopic for a fixed number of rounds.

**`test_task_1_2.py`** proves:

- Phase 2 adds the missing category.
- Every subagent prompt carries all four isolation elements.
- Round 2 re-delegates only `music`, with its prior findings.
- The run exits on coverage after 2 rounds, not on the cap.
- The anti-pattern merges categories, sends bare prompts and re-runs everything.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_2_hub_and_spoke.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_2_hub_and_spoke.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_2_hub_and_spoke
```
