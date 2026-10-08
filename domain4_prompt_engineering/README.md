# Domain 4 — Prompt Engineering & Structured Output (20%)

Source: <https://claudecertificationguide.com/learn/4-prompt-engineering>

| Task | Build exercise | Traps |
|---|---|---|
| [4.1 System Prompts with Explicit Criteria](task_4_1_explicit_criteria/) | Vague vs explicit review criteria on 5 snippets; disable categories above 25% false positives | 3 |
| [4.2 Few-Shot Prompting](task_4_2_few_shot/) | 10-document extraction; 3 examples with reasoning take the empty rate from 27% to 3% | 3 |
| [4.3 Structured Output with Tool Use](task_4_3_structured_output/) | Nullable/enum schema; `auto` vs `any` vs a forced tool; nulls, not fabrication | 3 |
| [4.4 Validation, Retry & Feedback Loops](task_4_4_validation_retry/) | Pydantic semantic validation; retry only fixable errors | 4 |
| [4.5 Batch Processing Strategies](task_4_5_batch_processing/) | 20-request batch, `custom_id` failure resubmission, SLA cadence | 3 |
| [4.6 Multi-Instance & Multi-Pass Review](task_4_6_multi_pass_review/) | Per-file + integration review; verifier-calibrated confidence routing | 4 |

```bash
.venv/bin/pytest domain4_prompt_engineering
```
