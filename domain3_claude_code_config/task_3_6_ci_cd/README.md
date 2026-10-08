# Task 3.6 — CI/CD Integration

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-6-cicd-integration>

## What you need to know

- **`-p` / `--print` is the key CI flag.** It processes the prompt, prints to stdout and exits. Without it, a CI job hangs waiting for input. This is Sample Question 10.
- **Machine-readable output:**
  - `--output-format json` wraps the run in an envelope: result, session ID, cost/usage.
  - `--json-schema` validates the output; the data lands in `structured_output` (`jq '.structured_output'`).
- **Review in a separate invocation.** The generating session is biased toward decisions it already justified.
- **Incremental review:** pass prior findings in and ask only for new or unaddressed issues, so dismissed findings aren't re-flagged every push.
- **CI reads CLAUDE.md just like interactive mode**, so put testing standards, fixtures and severity criteria there.
- **GitHub Actions:** `anthropics/claude-code-action@v1`.
  - With no `prompt`, it answers `@claude` mentions; with a `prompt`, it runs on the triggering event.
  - CLI flags go through `claude_args`.
  - It needs `actions/checkout`, the key from a repository secret, and `id-token: write`.
- **Batch API vs real-time:** batch is 50% cheaper but takes up to 24h with no SLA. Use real-time for blocking pre-merge checks and batch for overnight or weekly work. This is Sample Question 11.

## Exam traps

| Trap | Demo |
|---|---|
| A CI job hanging on interactive input | `trap1_ci_hang_fixes`: `CLAUDE_HEADLESS=true`, `--batch` and `< /dev/null` all still hang; only `-p` finishes |
| Same-session self-review treated as equal to independent review | `trap2_same_session_self_review`: approves its own `eval()` (**simulated**), while the independent review finds 2 issues |
| The Batch API for pre-merge checks | `trap3_batch_for_pre_merge` |
| No prior findings in later runs | `trap4_no_prior_findings`: the same 2 comments on every push |

## Exam answer vs current docs

No conflicting answer. The lesson's "beyond the guide" material (GitHub Actions, worktrees) is checked against current docs. `claude --worktree <name>` creates `.claude/worktrees/<name>/` on branch `worktree-<name>`.

## Practice scenario

A CI job hangs waiting for interactive input.

**D: add `-p`.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. A CI script running `claude -p` | `ci_command()`, `CI_SCRIPT`, plus a generated GitHub Actions workflow checked by `validate_workflow()` |
| 2. `--output-format json` + `--json-schema` | `run_print_mode()` returns the same envelope, with the data in `structured_output` |
| 3. Parse and post inline comments | `post_inline_comments()` → `file:line [severity] message` |
| 4. A CI section in CLAUDE.md | `CI_CLAUDE_MD` |
| 5. Separate generation and review invocations | `generate()` and `review()`, each a fresh single-message request |
| 6. Store findings, pass them in, report only new ones | `incremental_runs()`: 2 comments, then 0, then 0 |

**Live mode** emulates the CLI's print-mode envelope on the Messages API, so it doesn't need `claude` installed. The generated script and workflow call the real CLI.

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_6_ci_cd.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_6_ci_cd.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_6_ci_cd
```
