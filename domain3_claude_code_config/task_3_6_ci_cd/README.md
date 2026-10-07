# Task 3.6 — CI/CD Integration

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- `-p` / `--print` is the mode switch for CI: run once, print, exit. Without it the job hangs waiting for input.
- `--output-format json` wraps the result; `--json-schema` validates it and puts the data in `structured_output`.
- Review in an independent `claude -p` session - the generating session is biased toward its own decisions.
- Pass prior findings into incremental reviews; report only new or unaddressed issues.
- Batch API (50% cheaper, up to 24h) only for non-blocking work - never pre-merge checks.

## Exam trap

`CLAUDE_HEADLESS=true`, `--batch`, or `< /dev/null` as the CI-hang fix (only `-p` is real); Batch API for blocking checks; same-session self-review.

## Code walkthrough

_To be built:_ `good_example/` and `anti_pattern/` hold demo configs (YAML / Markdown / shell); `test_task_3_6.py` validates their structure.
