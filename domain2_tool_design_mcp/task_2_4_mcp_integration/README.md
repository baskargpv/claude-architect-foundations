# Task 2.4 — MCP Server Integration

Lesson: <https://claudecertificationguide.com/learn/2-tool-design-mcp/2-4-mcp-server-integration>

## What you need to know

- **Two config files:**
  - **Project:** `.mcp.json` at the repo root. Version-controlled and shared with the team.
  - **User:** `~/.claude.json`. Personal and not version-controlled.
- **Two server types:**
  - **Remote:** `"type": "http"` + `url`.
  - **Local:** `command` + `args` over stdio.
  - A `url` with no `type` is read as stdio and skipped.
- **All servers are live at once.** Every server from both scopes is discovered at connection time, with no activation step.
- **`${VAR}` expansion keeps secrets out of `.mcp.json`.** `${VAR:-default}` falls back when the variable is unset.
- **Resources vs tools:** resources (schemas, issue lists, doc trees) show what data exists so the agent skips exploratory calls. Tools act on that data.
- **Use community servers for standard integrations** (Jira, GitHub, Slack, Linear, Notion). Build custom only for team-specific needs.
- **Write full MCP tool descriptions.** A sparse one loses to a richly described built-in like Grep, so write 3–5 sentences: what it does, what it returns, when to use it, and how it compares to the built-in.

## Exam traps

| Trap | Demo |
|---|---|
| A custom MCP server for a standard integration like Jira | `trap1_custom_jira_server` vs `choose_integration()` |
| Team-wide config in `~/.claude.json` | `trap2_team_config_in_user_scope`: developer B's fresh clone has no `jira` server |
| Credentials committed in `.mcp.json` | `trap3_committed_credentials`: the literal token shows up in the staged git diff |
| Sparse MCP tool descriptions | `trap4_sparse_description`: Grep wins (**simulated** selector) |

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Scopes | Two: project vs user | Three: `local` (default), `project`, `user`, chosen with `-s` / `--scope`. `~/.claude.json` holds both local and user entries. **On the exam, answer project vs user.** |
| Who attaches resources | — | Resources are application-controlled: the server lists them and the client decides when to attach one |
| Unset `${VAR}` with no default | — | Warns, and the rest of the config still loads (`expand_env()` does the same) |

## Practice scenario

A team wants Jira; a developer proposes a custom server. First step?

**A: evaluate the community Jira MCP server first.**

## Build exercise → code

| Step | Where |
|---|---|
| 1. Project-root `.mcp.json` with GitHub's remote endpoint | `PROJECT_CONFIG`, written by `write_configs()` and checked by `validate_entry()` |
| 2. Tokens as `${GITHUB_TOKEN}`, confirmed with `git diff` | `staged_diff()` runs real `git init`, `add`, `diff --cached`. `find_literal_secrets()` finds nothing. |
| 3. A personal server in `~/.claude.json` | `USER_CONFIG`. `load_servers()` merges both scopes and expands variables. |
| 4. A catalogue as an MCP resource (name, description, mimeType, URI) | `schema://warehouse/tables` on a real in-process `mcp` server |
| 5. A 3–5 sentence tool description | `query_warehouse`, checked by `description_quality()` |

## Run

```bash
.venv/bin/python -m domain2_tool_design_mcp.task_2_4_mcp_integration.good_example
.venv/bin/python -m domain2_tool_design_mcp.task_2_4_mcp_integration.anti_pattern
.venv/bin/pytest domain2_tool_design_mcp/task_2_4_mcp_integration
```
