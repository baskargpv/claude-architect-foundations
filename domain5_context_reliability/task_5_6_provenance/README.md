# Task 5.6 — Information Provenance & Multi-Source Synthesis

Lesson: <https://claudecertificationguide.com/learn/5-context-management/5-6-information-provenance>

## What you need to know

- **Every finding needs a claim-source mapping** with five fields: `claim`, `sourceUrl`, `documentName`, `relevantExcerpt`, `publicationDate`.
- **Attribution dies at summarisation** unless the synthesis step is told to preserve and merge mappings. It has to survive research → analysis → synthesis → report.
- **Conflicting values:** annotate **both**, with attribution, and never pick one.
  - Different dates, same method → a **trend** (8% in 2023 vs 12% in 2024).
  - Same date, different method → a **methodology note** (audited vs preliminary, calendar vs fiscal).
  - Everything the same → flag it as **unexplained**.
- **Separate well-established findings from contested ones.**
- **Render by content type:** financial data as tables, news as prose, technical findings as lists.
- **Analysis agents finish their work with the conflicts annotated**, and leave resolution to the coordinator or the consumer.

## Exam traps

| Trap | Demo |
|---|---|
| Picking the most recent source when two credible sources conflict | `trap1_pick_most_recent`: the 2023 figure and the trend disappear |
| Assuming different numbers are always contradictions | `trap2_everything_is_a_conflict`: a trend labelled "CONFLICT" |
| Paraphrasing without claim-source mappings | `trap3_paraphrase`: no sources left |
| One uniform format for everything | `trap4_uniform_prose`: no table, no list |

## Exam answer vs current docs

No difference.

## Practice scenario

12% (2023 data) vs 8% (2024 data); the agent keeps the newer figure.

**D: annotate both, with attribution and dates, and let the consumer decide.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A claim-source schema with the five required fields | `Finding` (Pydantic) |
| 2. Two research subagents returning findings in that schema | `research(client, "WEB" / "DOCS", ...)` |
| 3. Synthesis that keeps every mapping as an inline citation | `synthesise()`, `cite()` |
| 4. Conflict handling: keep both values with attribution and an explanation | `find_conflicts()`, `classify_conflict()` |
| 5. Tables for financial data, prose for news, lists for technical findings | `synthesise()` |

## Run

```bash
.venv/bin/python -m domain5_context_reliability.task_5_6_provenance.good_example
.venv/bin/python -m domain5_context_reliability.task_5_6_provenance.anti_pattern
.venv/bin/pytest domain5_context_reliability/task_5_6_provenance
```
