# Task 3.3 — Path-Specific Rules for Conditional Convention Loading

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-3-path-specific-rules>

## What you need to know

- **What a path rule is:** a file in `.claude/rules/<name>.md` with a `paths:` list of globs in its YAML frontmatter. It loads only when Claude works on a matching file.
- **Glob syntax:** `**/` means any folder at any depth; `*.test.tsx` means any filename ending that way.
- **When to use one:** for one convention spread across many directories. A directory CLAUDE.md would need a copy per folder, and they drift. The root CLAUDE.md would spend tokens on irrelevant work.
- **Rules vs skills:** rules are background guidance that applies automatically. Skills are on-demand workflows.

| Scope | Put it in |
|---|---|
| Universal standards | Root CLAUDE.md |
| One directory | That directory's CLAUDE.md |
| A file type across many directories | `.claude/rules/` with `paths:` |
| An occasional task workflow | A skill |

## Exam traps

| Trap | Demo |
|---|---|
| A directory-level CLAUDE.md for a cross-directory convention | `trap1_directory_copies`: 50 files, already 2 versions |
| File-type conventions in the root CLAUDE.md | `trap2_everything_in_root`: 352 of 479 chars wasted while editing Terraform |
| Confusing skills with path rules | `trap3_skill_instead_of_rule`: never applied unless someone invokes it |

## Exam answer vs current docs

No difference on the lesson. `/context` shows which rules actually loaded.

## Practice scenario

Test files sit in 50+ directories, and the team wants uniform conventions.

**C: a path-scoped rule in `.claude/rules/` with test-file globs.**

## Build exercise → code

| Step | Where |
|---|---|
| 1–3. `testing.md`, `api-conventions.md`, `terraform.md`, each with `paths:` globs | `RULES`, written by `write_rules()` |
| 4. Edit a test file → only the testing rule loads | `rules_for(project, "src/billing/invoice.test.ts")` |
| 5. Edit an API handler → only the API rule loads | `rules_for(project, "src/api/users/handler.ts")` |
| 6. Token footprint: root CLAUDE.md vs split rules | `footprint()` |

Glob matching (`**/` = any depth) lives in `common/claude_config.py`, and the tests cover it.

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_3_path_rules.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_3_path_rules.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_3_path_rules
```
