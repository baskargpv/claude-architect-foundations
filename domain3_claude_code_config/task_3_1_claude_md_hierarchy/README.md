# Task 3.1 — CLAUDE.md Hierarchy, Scoping, Modular Organisation

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Three levels: user (`~/.claude/CLAUDE.md`, not shared), project (`CLAUDE.md` / `.claude/CLAUDE.md`, shared), directory (`<subdir>/CLAUDE.md`).
- No precedence - all applicable files are concatenated; contradictions resolve arbitrarily. CLAUDE.md is delivered as a user message, so it can't guarantee compliance - settings.json / hooks can.
- `@path` imports inline eagerly: an organisational tool, not a token saver. Path-scoped `.claude/rules/` are the token saver.
- Project-root CLAUDE.md survives `/compact` (re-read from disk); nested and path-scoped files reload only on the next matching read.

## Exam trap

New teammate gets inconsistent behaviour -> the conventions live in the original developer's `~/.claude/CLAUDE.md`. Fix: move them to project level. `git status` showing nothing about the user file is the proof.

## Exam answer vs current docs

Exam guide v1.0 keys `/memory` as the way to see what loaded. Current Claude Code: `/context` reports what actually loaded ("Memory files"). Answer `/memory` on the exam.

## Code walkthrough

_To be built:_ `good_example/` and `anti_pattern/` hold demo configs (YAML / Markdown / shell); `test_task_3_1.py` validates their structure.
