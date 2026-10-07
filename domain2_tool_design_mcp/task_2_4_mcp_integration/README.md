# Task 2.4 — MCP Server Integration

> Status: **skeleton** — theory captured from the study notes; demo not built yet.

## Theory

- Project scope: `.mcp.json` at repo root - team-wide, version-controlled. User scope: `~/.claude.json` - personal, not shared.
- Remote servers declare `"type": "http"` + `url`; local servers declare `command` + `args` (stdio). A `url` without `type` is read as stdio and skipped.
- `${VAR}` / `${VAR:-default}` expansion keeps credentials out of git; an unset var only warns.
- Resources expose catalogues (schemas, doc trees) up front so the agent doesn't burn exploratory tool calls.
- Evaluate community servers first; build custom only for team-specific needs. Write 3-5 sentence MCP tool descriptions so they don't lose to built-ins.

## Exam trap

Team servers in `~/.claude.json`; credentials committed in `.mcp.json`; building a custom server for a standard integration.

## Exam answer vs current docs

Exam guide v1.0: two scopes (project vs. user). Current docs: three scopes (local, project, user), with `~/.claude.json` holding both local and user entries. Answer with two on the exam.

## Code walkthrough

_To be built:_ `good_example.py`, `anti_pattern.py`, `test_task_2_4.py`.
