# Task 2.5 — Built-in Tools

Lesson: <https://claudecertificationguide.com/learn/2-tool-design-mcp/2-5-built-in-tools>

## What you need to know

- **Six built-in tools:** Read, Write, Edit, Bash, Grep, Glob.
- **Grep searches file contents** (callers, error messages, imports). **Glob matches file paths** (test files, configs, everything in a folder).
- **Edit** replaces a **unique** `old_string`. A non-unique match is refused, as a safety feature.
- **Explore incrementally:**
  1. Grep for entry points.
  2. Read to follow imports.
  3. Grep again for renamed exports (barrel files and wrappers).
  4. Read only what matters.

  Never read every file up front.
- **Deprecation workflow:**
  1. Grep for the function name.
  2. Glob for sibling test files.
  3. Grep for wrapper names to catch indirect callers.

## Exam traps

| Trap | Demo |
|---|---|
| Glob to find function callers | `trap1_glob_for_callers`: returns `[]` |
| Grep to find files by name pattern | `trap2_grep_for_test_files`: returns `[]`, while Glob finds both tests |
| Reading every file up front | `trap3_read_everything`: ~16k chars vs ~1.3k for the whole incremental migration |
| Read + Write for every change | `trap4_read_write_every_change`: 726 vs 76 chars |
| Answering "widen / replace_all" on the exam's non-unique question | `trap5_exam_answer_after_non_unique` |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| After Edit reports a non-unique match | **Read + Write** | Widen `old_string` with surrounding context, or set `replace_all: true`, and use Read + Write only as a last resort. `edit_with_recovery()` does it the current way. Both agree: try Edit first. |

## Practice scenario

Which sequence finds all callers of `processLegacyOrder()` and their test files?

**C: Grep for callers, then Glob for sibling tests.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Grep for all callers | `find_callers()`: direct callers, plus a second Grep for the alias re-exported by the barrel file `src/utils/index.ts` (`submitLegacyOrder`) |
| 2. Glob for test files matching the callers | `find_tests()` → `tests/{stem}.test.*` |
| 3. Read each caller | `migrate()` reads only the 5 files the searches justified |
| 4. Edit the deprecated call | `edit_with_recovery()` |
| 5. Non-unique match → widen or `replace_all`, Read + Write last | `checkout.ts` calls the function twice, so `replace_all` changes every occurrence, or widening changes just one |

`Tools` is a small Python version of Grep, Glob, Read, Edit and Write that counts the characters each call pulls into context. It runs on a copy of `sample_codebase/` plus 40 unrelated modules, standing in for the rest of a real repo. No model calls are involved.

## Run

```bash
.venv/bin/python -m domain2_tool_design_mcp.task_2_5_builtin_tools.good_example
.venv/bin/python -m domain2_tool_design_mcp.task_2_5_builtin_tools.anti_pattern
.venv/bin/pytest domain2_tool_design_mcp/task_2_5_builtin_tools
```
