# Task 3.3 — Path-Specific Rules

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- `.claude/rules/<name>.md` with `paths:` glob frontmatter loads only when Claude works on a matching file.
- Solves "one convention, many directories" (e.g. co-located tests across 50+ folders) without per-directory copies.
- Decision table: universal -> root CLAUDE.md; one package -> directory CLAUDE.md; a file type everywhere -> path rules; an occasional task -> skill.

## Exam trap

Directory-level CLAUDE.md copied into 50+ folders, or file-type conventions in the root CLAUDE.md.

## Exam answer vs current docs

Field note (not an exam correction): live testing found `paths:` rules did not reliably load; some bug reports say an undocumented `globs:` field works better. Give the documented answer on the exam.

## Code walkthrough

_To be built:_ `good_example/` and `anti_pattern/` hold demo configs (YAML / Markdown / shell); `test_task_3_3.py` validates their structure.
