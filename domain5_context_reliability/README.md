# Domain 5 — Context Management & Reliability (15%)

Source: <https://claudecertificationguide.com/learn/5-context-management>

| Task | Build exercise | Traps |
|---|---|---|
| [5.1 Context Window Management](task_5_1_context_window/) | Case-facts block survives summarisation; trimming 47 fields to 5; key findings first | 4 |
| [5.2 Escalation & Ambiguity Resolution](task_5_2_escalation/) | Escalation criteria + few-shot prompt, 4 scenarios, never-guess customer matching | 4 |
| [5.3 Error Propagation](task_5_3_error_propagation/) | Structured errors, local backoff with partial results, coverage section | 4 |
| [5.4 Codebase Exploration & Context Degradation](task_5_4_context_degradation/) | Subagent delegation, scratchpad, phase-2 summary injection, state manifest | 4 |
| [5.5 Human Review & Confidence Calibration](task_5_5_human_review_calibration/) | Per-segment accuracy, calibration thresholds, stratified sampling, priority queue | 4 |
| [5.6 Information Provenance](task_5_6_provenance/) | Claim-source mappings, conflict annotation, rendering by content type | 4 |

```bash
.venv/bin/pytest domain5_context_reliability
```
