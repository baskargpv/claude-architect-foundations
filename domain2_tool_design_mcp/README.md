# Domain 2 — Tool Design & MCP Integration (18%)

Source: <https://claudecertificationguide.com/learn/2-tool-design-mcp>

| Task | Build exercise | Traps |
|---|---|---|
| [2.1 Tool Interface Design](task_2_1_tool_interface_design/) | Two MCP tools; 10 routing queries before and after rewriting descriptions (30% → 100%) | 4 |
| [2.2 Structured Error Responses](task_2_2_structured_errors/) | MCP lookup tool returning all four error categories plus a valid empty result; category-driven recovery | 6 |
| [2.3 Tool Distribution & Tool Choice](task_2_3_tool_distribution/) | 3 roles × 4–5 tools, scoped `verify_fact`, forced first tool, `load_document`, a tool guard | 4 |
| [2.4 MCP Server Integration](task_2_4_mcp_integration/) | `.mcp.json` with `${VAR}`, user scope, git-diff secret check, an MCP resource, rich descriptions | 4 |
| [2.5 Built-in Tools](task_2_5_builtin_tools/) | Grep → Glob → Read → Edit deprecation workflow, including barrel-file renames and non-unique Edit recovery | 5 |

MCP tools run on a real in-process `mcp` server. The helpers are in `common/mcp_util.py`.

```bash
.venv/bin/pytest domain2_tool_design_mcp
```
