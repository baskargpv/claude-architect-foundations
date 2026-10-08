# Claude Certified Architect — Foundations: runnable study repo

Every exam task statement (5 domains, 30 tasks) gets its own folder, built from the matching lesson at
**<https://claudecertificationguide.com/learn>**. That site is the content source; each task README links its lesson.

| File | Purpose |
|---|---|
| `README.md` | Key concepts, exam traps, the practice scenario and its answer, **exam answer vs current docs** where they differ, and a map from build-exercise steps to code |
| `good_example.py` | The lesson's **Build Exercise**, implemented step by step |
| `anti_pattern.py` | One runnable function per **Exam Trap**, built so you can watch it fail |
| `test_task_X_Y.py` | Checks every build step, every trap and the practice answer. Always offline. |

Every domain, including Domain 3 (Claude Code configuration), is written as Python. Domain 3's programs generate and validate
config files (`CLAUDE.md`, `.claude/`, YAML, shell).

## Domain map

Status: ✅ built and tested · 🧱 not built yet

### Domain 1 — Agentic Architecture & Orchestration (27%) ✅

| Task | Folder | Build exercise |
|---|---|---|
| 1.1 | [Agentic Loops](domain1_agentic_architecture/task_1_1_agentic_loop/) | Multi-tool agent loop driven by `stop_reason` |
| 1.2 | [Multi-Agent Orchestration](domain1_agentic_architecture/task_1_2_orchestration/) | Hub-and-spoke research coordinator with coverage-driven refinement |
| 1.3 | [Subagent Invocation & Context Passing](domain1_agentic_architecture/task_1_3_subagent_context/) | `Agent`-tool coordinator, structured findings, parallel spawns |
| 1.4 | [Workflow Enforcement & Handoff](domain1_agentic_architecture/task_1_4_workflow_enforcement/) | Prerequisite gate for refunds, structured handoff |
| 1.5 | [Agent SDK Hooks](domain1_agentic_architecture/task_1_5_sdk_hooks/) | MCP tools + PostToolUse normalisation + PreToolUse policies |
| 1.6 | [Task Decomposition Strategies](domain1_agentic_architecture/task_1_6_task_decomposition/) | Multi-pass code review pipeline |
| 1.7 | [Session State & Resumption](domain1_agentic_architecture/task_1_7_session_resumption/) | Resume vs fork vs fresh start with summary |

### Domain 2 — Tool Design & MCP Integration (18%) ✅

| Task | Folder | Build exercise |
|---|---|---|
| 2.1 | [Tool Interface Design](domain2_tool_design_mcp/task_2_1_tool_interface_design/) | Routing accuracy before/after rewriting MCP tool descriptions |
| 2.2 | [Structured Error Responses](domain2_tool_design_mcp/task_2_2_structured_errors/) | Four error categories + valid empty result, category-driven recovery |
| 2.3 | [Tool Distribution & Tool Choice](domain2_tool_design_mcp/task_2_3_tool_distribution/) | Role-scoped toolsets, scoped `verify_fact`, forced first tool, `load_document` |
| 2.4 | [MCP Server Integration](domain2_tool_design_mcp/task_2_4_mcp_integration/) | `.mcp.json` scopes, `${VAR}` secrets, MCP resources |
| 2.5 | [Built-in Tools](domain2_tool_design_mcp/task_2_5_builtin_tools/) | Grep → Glob → Read → Edit deprecation workflow |

### Domain 3 — Claude Code Configuration & Workflows (20%) 🧱

| Task | Folder |
|---|---|
| 3.1 | [CLAUDE.md Hierarchy, Scoping & Modular Organisation](domain3_claude_code_config/task_3_1_claude_md_hierarchy/) |
| 3.2 | [Custom Slash Commands & Skills](domain3_claude_code_config/task_3_2_commands_and_skills/) |
| 3.3 | [Path-Specific Rules](domain3_claude_code_config/task_3_3_path_rules/) |
| 3.4 | [Plan Mode vs Direct Execution](domain3_claude_code_config/task_3_4_plan_mode/) |
| 3.5 | [Iterative Refinement Techniques](domain3_claude_code_config/task_3_5_iterative_refinement/) |
| 3.6 | [CI/CD Integration](domain3_claude_code_config/task_3_6_ci_cd/) |

### Domain 4 — Prompt Engineering & Structured Output (20%) 🧱

| Task | Folder |
|---|---|
| 4.1 | [System Prompts with Explicit Criteria](domain4_prompt_engineering/task_4_1_explicit_criteria/) |
| 4.2 | [Few-Shot Prompting](domain4_prompt_engineering/task_4_2_few_shot/) |
| 4.3 | [Structured Output with Tool Use](domain4_prompt_engineering/task_4_3_structured_output/) |
| 4.4 | [Validation, Retry & Feedback Loops](domain4_prompt_engineering/task_4_4_validation_retry/) |
| 4.5 | [Batch Processing Strategies](domain4_prompt_engineering/task_4_5_batch_processing/) |
| 4.6 | [Multi-Instance & Multi-Pass Review](domain4_prompt_engineering/task_4_6_multi_pass_review/) |

### Domain 5 — Context Management & Reliability (15%) 🧱

| Task | Folder |
|---|---|
| 5.1 | [Context Window Management](domain5_context_reliability/task_5_1_context_window/) |
| 5.2 | [Escalation & Ambiguity Resolution](domain5_context_reliability/task_5_2_escalation/) |
| 5.3 | [Error Propagation in Multi-Agent Systems](domain5_context_reliability/task_5_3_error_propagation/) |
| 5.4 | [Codebase Exploration & Context Degradation](domain5_context_reliability/task_5_4_context_degradation/) |
| 5.5 | [Human Review & Confidence Calibration](domain5_context_reliability/task_5_5_human_review_calibration/) |
| 5.6 | [Information Provenance & Multi-Source Synthesis](domain5_context_reliability/task_5_6_provenance/) |

## Setup

You need Python 3.11+.

```bash
# with uv
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# or with plain pip
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Dependencies: `anthropic`, `pydantic`, `pyyaml`, and `mcp`. MCP tools in Domains 1–2 run on a real in-process MCP server.

### Mock mode vs live mode

- **Mock (default):** without `ANTHROPIC_API_KEY`, every demo runs offline against `common.mock.MockClient`. It returns real
  `anthropic.types.Message` objects from a scripted responder, so mock and live go through identical code.
- **Live:** export a key and the same demos call the Messages API.

```bash
cp .env.example .env              # add your key; .env is gitignored
export $(grep -v '^#' .env | xargs)
```

| Env var | Default | Effect |
|---|---|---|
| `ANTHROPIC_API_KEY` | unset | Set it to run live |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Model for live runs |
| `CCA_FORCE_MOCK` | unset | `1` forces mock mode even with a key (the test suite sets this) |

Where the lesson's exam answer and the live API disagree, the task README says so. For example, forced `tool_choice` returns a 400 on
`claude-sonnet-5-5`. Some anti-patterns depend on model *unreliability* (e.g. "a prompt works 92% of the time"); those use a
clearly labelled **simulated** model, because the point is architectural, not a measurement.

### Run a demo

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.anti_pattern
```

### Run the tests

```bash
.venv/bin/pytest                                   # whole repo, always offline
.venv/bin/pytest domain1_agentic_architecture      # one domain
```

## Repo layout

```
common/                  get_client(), MockClient, ask_json(), config (model, mock/live switch)
domainN_<name>/
  task_N_M_<name>/
    README.md
    good_example.py
    anti_pattern.py
    test_task_N_M.py
    (sample data the build exercise needs, e.g. sample_repo/)
```
