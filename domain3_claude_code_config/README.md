# Domain 3 — Claude Code Configuration & Workflows (20%)

Source: <https://claudecertificationguide.com/learn/3-claude-code-config>

Every task is a Python program. It writes real config files (`CLAUDE.md`, `.claude/`, rules, skills, a CI script, a GitHub Actions workflow) into a temporary directory and then checks how Claude Code would treat them. The shared frontmatter and glob helpers are in `common/claude_config.py`.

| Task | Build exercise | Traps |
|---|---|---|
| [3.1 CLAUDE.md Hierarchy](task_3_1_claude_md_hierarchy/) | Project, directory and rule files, `@` import; what loads at root vs `packages/api` | 3 |
| [3.2 Commands & Skills](task_3_2_commands_and_skills/) | Team `/review` command, personal `/brainstorm` skill with `context: fork` | 5 |
| [3.3 Path-Specific Rules](task_3_3_path_rules/) | Testing, API and Terraform rules with `paths:` globs; token footprint | 3 |
| [3.4 Plan Mode vs Direct Execution](task_3_4_plan_mode/) | Decision framework, plan-mode write blocking, hybrid migration, Explore summary | 4 |
| [3.5 Iterative Refinement](task_3_5_iterative_refinement/) | Prose vs examples, test-driven loop, interview pattern, batched feedback | 3 |
| [3.6 CI/CD Integration](task_3_6_ci_cd/) | `claude -p` + JSON schema, workflow YAML, independent and incremental review | 4 |

```bash
.venv/bin/pytest domain3_claude_code_config
```
