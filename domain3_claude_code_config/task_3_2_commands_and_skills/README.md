# Task 3.2 — Custom Slash Commands and Skills

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-2-slash-commands-skills>

## What you need to know

- **A skill loads on demand**, via `/name` or when Claude matches its `description`. CLAUDE.md loads every session.
- **Commands and skills are one system now.** Two file shapes both create `/name`:
  - `.claude/commands/<name>.md`: a flat file, kept for backward compatibility.
  - `.claude/skills/<name>/SKILL.md`: a folder with an entrypoint. This is the canonical shape, and it wins a name clash.

  A loose `.md` file directly in `.claude/skills/` creates nothing.
- **Scope:** repo `.claude/` is shared via git; `~/.claude/` is personal. Name personal variants differently so they don't override team skills.
- **Frontmatter the exam tests:** `context: fork`, `allowed-tools`, `argument-hint`.
- **`description` does the most real work.** Without it, Claude Code falls back to the body's first paragraph.

## Exam traps

| Trap | Demo |
|---|---|
| A flat Markdown file directly in `.claude/skills/` | `trap1_flat_file_in_skills`: no command |
| A team command in a user-scoped path | `trap2_team_command_in_user_path`: the teammate has no `/review` |
| Expecting a skill to behave like CLAUDE.md | `trap3_skill_as_always_on`: the rule isn't in session context |
| Not using `context: fork` for verbose output | `trap4_no_fork`: 600+ chars dumped into the main thread |
| Task-specific workflows in CLAUDE.md | `trap5_workflow_in_claude_md`: paid every session (10× the cost) |

## Exam answer vs current docs

| Field | Exam answer | Current docs |
|---|---|---|
| `allowed-tools` | **Restricts** the skill to those tools | **Pre-approves** them (no permission prompt); other tools stay callable. The real restriction is `disallowed-tools` or deny rules. See `tool_permissions()`. |
| `argument-hint` | Prompts for missing arguments | Just an autocomplete label |
| `context: fork` | Runs in an isolated sub-agent | Same |
| More fields | — | `disallowed-tools`, `disable-model-invocation`, `model`, `effort`, `when_to_use`, `paths` |

## Practice scenario

Where should a team `/review` command and a personal verbose `/brainstorm` skill go?

**C: `/review` in `.claude/commands/`; `/brainstorm` at `~/.claude/skills/brainstorm/SKILL.md` with `context: fork`.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. `.claude/commands/review.md` | `REVIEW_COMMAND` |
| 2–4. `~/.claude/skills/brainstorm/SKILL.md` with `context: fork`, `allowed-tools` and `argument-hint` | `BRAINSTORM_SKILL` |
| 5. `/review` exists in any clone; `/brainstorm` only in your sessions | `discover_commands(repo, home)` |
| 6. Verbose output stays out of the main conversation | `run_skill()`: a forked skill returns only its `SUMMARY:` line |

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_2_commands_and_skills.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_2_commands_and_skills.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_2_commands_and_skills
```
