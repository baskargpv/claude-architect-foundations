# Task 3.2 — Custom Slash Commands and Skills

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- CLAUDE.md loads every session; a skill loads only when invoked (`/name`) or matched by its `description`.
- Two shapes: `.claude/commands/<name>.md` (flat) or `.claude/skills/<name>/SKILL.md` (folder). A flat file directly in `.claude/skills/` creates nothing.
- Repo paths are team-shared; `~/.claude/skills|commands/` is personal.
- Frontmatter: `context: fork`, `allowed-tools`, `argument-hint` (plus `description`, which drives auto-invocation).

## Exam trap

A flat `.md` dropped in `.claude/skills/`; a team command placed under `~/.claude/`; treating a skill as always-on.

## Exam answer vs current docs

Exam answer: `allowed-tools` RESTRICTS the skill to those tools; `argument-hint` PROMPTS for missing args. Current behaviour: `allowed-tools` only pre-approves (real restriction is `disallowed-tools`); `argument-hint` is an autocomplete label. `context: fork` behaves as documented.

## Code walkthrough

_To be built:_ `good_example/` and `anti_pattern/` hold demo configs (YAML / Markdown / shell); `test_task_3_2.py` validates their structure.
