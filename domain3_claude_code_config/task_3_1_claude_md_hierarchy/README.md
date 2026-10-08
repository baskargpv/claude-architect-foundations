# Task 3.1 — CLAUDE.md Hierarchy, Scoping, and Modular Organisation

Lesson: <https://claudecertificationguide.com/learn/3-claude-code-config/3-1-claude-md-hierarchy>

## What you need to know

- **Three levels:**
  - **User:** `~/.claude/CLAUDE.md`. Personal, not in git.
  - **Project:** `.claude/CLAUDE.md` or root `CLAUDE.md`. Shared via git.
  - **Directory:** a subdirectory's `CLAUDE.md`, scoped to that directory.
- **Concatenation, not precedence.** All the files are joined into context, broadest to most specific, and none overrides another. Conflicting rules may be resolved arbitrarily.
- **`CLAUDE.local.md`** loads after `CLAUDE.md` in the same directory. It's gitignored by convention.
- **CLAUDE.md is guidance, not enforcement.** Rules that must always hold belong in `settings.json` (client-enforced, with precedence managed > local > project > user) or in hooks.
- **`@path` imports inline eagerly**, so they don't save context. Paths resolve **relative to the file containing the `@` line**. There's no `@import` keyword.
- **`.claude/rules/` files:** without `paths:` frontmatter they load every session; with `paths:` they load only for matching files.
- **After `/compact`**, the project-root CLAUDE.md is re-read from disk. Nested files and path rules come back only when a matching file is read.

## Exam traps

| Trap | Demo |
|---|---|
| A new teammate on the same repo and branch doesn't get the instructions | `trap1_conventions_in_user_config`: developer B's context lacks the rule |
| Thinking `/memory` loads configuration | `trap2_memory_loads_nothing`: what's loaded is unchanged |
| A directory-level CLAUDE.md for conventions that span many directories | `trap3_directory_level_for_cross_cutting`: 50 copies, and they drift |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Which command shows the loaded files | **`/memory`** | `/memory` lists and opens memory locations. `/context` shows what actually loaded ("Memory files"). Neither command loads anything. |

## Practice scenario

Developer A's conventions work, but Developer B on the same repo gets inconsistent naming. Root cause?

**C: the conventions live in A's `~/.claude/CLAUDE.md`.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. `.claude/CLAUDE.md` with naming, error-handling and review sections | `PROJECT_FILES`, written by `build_project()` |
| 2. `packages/api/CLAUDE.md` | same |
| 3. `.claude/rules/testing.md` | `paths: ["**/*.test.ts"]`, plus an always-on `security.md` for contrast |
| 4. An `@` import of `standards/naming.md` | `@../standards/naming.md`, inlined by `expand_imports()` |
| 5. `/context` at the root and in `packages/api/` | `loaded_memory()`: root loads 2 files; `packages/api` (touching a test file) loads 4 |
| 6. Move a convention to `~/.claude/CLAUDE.md` | `in_repo()` shows it's outside the repo; trap 1 shows a fresh clone doesn't get it |

`loaded_memory()` models the **documented** loading rules:

1. Walk from the root down to the launch directory.
2. Load subdirectory files on demand when a file there is read.
3. Load rules by `paths:` match.

## Run

```bash
.venv/bin/python -m domain3_claude_code_config.task_3_1_claude_md_hierarchy.good_example
.venv/bin/python -m domain3_claude_code_config.task_3_1_claude_md_hierarchy.anti_pattern
.venv/bin/pytest domain3_claude_code_config/task_3_1_claude_md_hierarchy
```
