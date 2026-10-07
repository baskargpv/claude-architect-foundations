# Claude Certified Architect — Foundations: runnable study repo

Every exam task statement (5 domains, 30 tasks) gets its own folder with:

| File | Purpose |
|---|---|
| `README.md` | Theory, the exam trap, a code walkthrough, and **exam answer vs current docs** where they differ |
| `good_example.py` | The pattern the exam rewards |
| `anti_pattern.py` | The distractor the exam wants you to reject, built so you can watch it fail |
| `test_task_X_Y.py` | Proves the good example works and the anti-pattern fails the way the notes say it does |

Domain 3 (Claude Code configuration) is config-heavy: its tasks use `good_example/` and `anti_pattern/`
**directories** of real configs (`CLAUDE.md`, `.claude/` trees, YAML, shell scripts) instead of Python files.

Source of truth for all content: [`notes/CCA_Foundations-Study_notes.pdf`](notes/CCA_Foundations-Study_notes.pdf).

## Domain map

Status: ✅ built and tested · 🧱 skeleton (theory written, demo pending)

### Domain 1 — Agentic Architecture & Orchestration (27%) ✅

| Task | Folder | One-liner |
|---|---|---|
| 1.1 | [Agentic Loop Lifecycle](domain1_agentic_architecture/task_1_1_agentic_loop/) | `stop_reason` is authoritative; nothing else decides the loop |
| 1.2 | [Hub-and-Spoke Orchestration](domain1_agentic_architecture/task_1_2_hub_and_spoke/) | Breadth-first decomposition + strict subagent isolation, all through one hub |
| 1.3 | [Context Passing with Structured Metadata](domain1_agentic_architecture/task_1_3_context_passing/) | Never let structured metadata become plain text before synthesis |
| 1.4 | [Prerequisite Gates](domain1_agentic_architecture/task_1_4_prerequisite_gates/) | Code enforces what prompts can only request |
| 1.5 | [Agent SDK Hooks](domain1_agentic_architecture/task_1_5_sdk_hooks/) | Block in PreToolUse; PostToolUse is too late to prevent anything |
| 1.6 | [Task Decomposition](domain1_agentic_architecture/task_1_6_task_decomposition/) | Match the pattern to whether the plan is knowable; fix dilution with multi-pass |
| 1.7 | [Session State & Resumption](domain1_agentic_architecture/task_1_7_session_state/) | Stale history beats good intentions — start fresh, inject only what's true |

### Domain 2 — Tool Design & MCP Integration (18%) 🧱

| Task | Folder | One-liner |
|---|---|---|
| 2.1 | [Tool Interface Design](domain2_tool_design_mcp/task_2_1_tool_interface_design/) | Descriptions are the primary tool-selection signal |
| 2.2 | [Structured Error Responses](domain2_tool_design_mcp/task_2_2_structured_errors/) | `isError` = did it run; `isRetryable` = will this exact call work again |
| 2.3 | [Tool Distribution & Tool Choice](domain2_tool_design_mcp/task_2_3_tool_distribution/) | 4–5 tools per agent, scoped to role |
| 2.4 | [MCP Server Integration](domain2_tool_design_mcp/task_2_4_mcp_integration/) | Project config is shared, user config is personal |
| 2.5 | [Built-in Tools](domain2_tool_design_mcp/task_2_5_builtin_tools/) | Grep for contents, Glob for paths, Edit before Read+Write |

### Domain 3 — Claude Code Configuration & Workflows (20%) 🧱

| Task | Folder | One-liner |
|---|---|---|
| 3.1 | [CLAUDE.md Hierarchy](domain3_claude_code_config/task_3_1_claude_md_hierarchy/) | Concatenation, not precedence; no enforcement guarantee |
| 3.2 | [Commands & Skills](domain3_claude_code_config/task_3_2_commands_and_skills/) | Skills are on-demand; CLAUDE.md is always-on |
| 3.3 | [Path-Specific Rules](domain3_claude_code_config/task_3_3_path_rules/) | One convention, many directories → glob-scoped rules |
| 3.4 | [Plan Mode vs Direct Execution](domain3_claude_code_config/task_3_4_plan_mode/) | Ambiguity decides the mode, not difficulty |
| 3.5 | [Iterative Refinement](domain3_claude_code_config/task_3_5_iterative_refinement/) | Show, don't better-describe |
| 3.6 | [CI/CD Integration](domain3_claude_code_config/task_3_6_ci_cd/) | `-p` is non-negotiable for CI |

### Domain 4 — Prompt Engineering & Structured Output (20%) 🧱

| Task | Folder | One-liner |
|---|---|---|
| 4.1 | [Explicit Criteria](domain4_prompt_engineering/task_4_1_explicit_criteria/) | Categorical criteria beat vague instructions |
| 4.2 | [Few-Shot Prompting](domain4_prompt_engineering/task_4_2_few_shot/) | Examples with reasoning teach the principle |
| 4.3 | [Structured Output](domain4_prompt_engineering/task_4_3_structured_output/) | A schema guarantees shape, never correctness |
| 4.4 | [Validation & Retry](domain4_prompt_engineering/task_4_4_validation_retry/) | Retries fix what's wrong, never what's missing |
| 4.5 | [Batch Processing](domain4_prompt_engineering/task_4_5_batch_processing/) | Match the API to the wait |
| 4.6 | [Multi-Pass Review](domain4_prompt_engineering/task_4_6_multi_pass_review/) | Fresh eyes catch what generating eyes defend |

### Domain 5 — Context Management & Reliability (15%) 🧱

| Task | Folder | One-liner |
|---|---|---|
| 5.1 | [Context Window Management](domain5_context_reliability/task_5_1_context_window/) | Case-facts blocks stop destruction; findings-first stops mispositioning |
| 5.2 | [Escalation & Ambiguity](domain5_context_reliability/task_5_2_escalation/) | Escalate on request, policy gaps, genuine stuck points — never sentiment |
| 5.3 | [Error Propagation](domain5_context_reliability/task_5_3_error_propagation/) | Structured error context closes off both anti-patterns |
| 5.4 | [Context Degradation](domain5_context_reliability/task_5_4_context_degradation/) | Scratchpads preserve; delegation prevents pile-up |
| 5.5 | [Human Review & Calibration](domain5_context_reliability/task_5_5_human_review_calibration/) | Aggregate accuracy hides the failures that matter |
| 5.6 | [Provenance & Synthesis](domain5_context_reliability/task_5_6_provenance/) | Annotate both sources; never pick a winner |

## Setup

Requires Python 3.11+.

```bash
# with uv
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# or with plain pip
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### Mock mode vs live mode

- **Mock (default):** with no `ANTHROPIC_API_KEY`, every demo runs offline against `common.mock.MockClient`.
  It returns real `anthropic.types.Message` objects from a scripted responder, so the code paths are identical to live.
- **Live:** export a key and the same demos call the Messages API.

```bash
cp .env.example .env              # fill in your key; .env is gitignored
export $(grep -v '^#' .env | xargs)
```

| Env var | Default | Effect |
|---|---|---|
| `ANTHROPIC_API_KEY` | unset | Set it to run live |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Model used for live runs |
| `CCA_FORCE_MOCK` | unset | `1` forces mock mode even with a key (the test suite sets this) |

Live output varies run to run. Mock output is deterministic, and that's what the tests assert on.

### Run a demo

Run each demo as a module from the repo root:

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_1_agentic_loop.anti_pattern
```

### Run the tests

```bash
.venv/bin/pytest                                   # whole repo, always offline
.venv/bin/pytest domain1_agentic_architecture      # one domain
```

Skeleton tasks show as skipped until they're built.

## Repo layout

```
common/                  get_client(), MockClient, config (model, mock/live switch)
domainN_<name>/
  task_N_M_<name>/
    README.md
    good_example.py      (Domain 3: good_example/ directory of configs)
    anti_pattern.py      (Domain 3: anti_pattern/ directory of configs)
    test_task_N_M.py
notes/                   the study notes PDF (source of truth)
```
