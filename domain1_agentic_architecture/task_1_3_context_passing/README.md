# Task 1.3 — Context Passing with Structured Metadata

## Theory

**The spawn gate.** The coordinator can spawn *any* subagent only if the spawn tool is explicitly in `allowedTools`. Having subagent definitions in `options.agents` does **not** imply permission to invoke them. It's a deliberate, separate grant.

**Scoped subagent tools** rule out whole categories of attribution error at the tool level:

| Subagent | Tools |
|---|---|
| Web search agent | `WebSearch` only, no file access |
| Document analysis agent | `Read` / `Grep` only, no web access |

**The Finding schema** separates content from metadata:

| Field | Kind |
|---|---|
| `claim` | Content |
| `source_url` | Metadata, only when `retrieved_by = web_search_agent` |
| `document_name`, `page_number` | Metadata, only when `retrieved_by = document_analysis_agent` |
| `confidence` | `high` / `medium` / `low` |
| `retrieved_by` | Tells you which optional metadata fields must be populated |

**Parallel spawning vs `fork_session`:**

- **Parallel subagent calls** are for independent work with no shared state. The coordinator waits for all of them. Use this for web search + document analysis.
- **`fork_session`** branches an existing conversation's full history into a new session. It's for continuing from shared prior context, not for running independent work concurrently.

## Exam trap

An unsourced claim in the synthesis output is **never** the synthesis prompt's fault. It traces back to the coordinator stripping metadata before the handoff, typically via `.map(f => f.claim).join(...)`, which silently discards every metadata field. The fix is to pass the full structured array (`JSON.stringify(allFindings)`).

**Diagnostic order:** first check what data actually reached the synthesis prompt. Don't start by rewording the synthesis agent.

## Exam answer vs current docs

| | Exam answer | Current docs |
|---|---|---|
| Spawn tool name | **`Task`** must be in `allowedTools` | Renamed **`Agent`** in current Claude Code / Agent SDK. `can_spawn_subagents()` accepts either. |
| Options shape | `allowedTools`, `options.agents` | Python Agent SDK spells these `allowed_tools` and `agents={name: AgentDefinition(description, prompt, tools)}`. The dicts in this demo mirror that shape. |

## Code walkthrough

**`good_example.py`**

- **Config:** `COORDINATOR_OPTIONS` grants `"Agent"`. `SUBAGENTS` scopes the web agent to `WebSearch` and the doc agent to `Read`/`Grep`. `can_spawn_subagents()` and `tool_scope_violations()` check both rules.
- **Schema:** `Finding` is a Pydantic model. Its validator rejects a web finding without `source_url`, or a document finding without `document_name` + `page_number`.
- **Fan-out:** `gather_findings()` runs both subagents in parallel (`ThreadPoolExecutor`). Each is one isolated request against fixed source material, so the demo also works live without real web access.
- **Synthesis handoff:** `build_synthesis_prompt()` embeds `json.dumps([f.model_dump() …])`, the full structured records.
- **Mock synthesis model:** it can only cite what reached it. With the full records, every line carries a URL or `doc p.N`.

**`anti_pattern.py`**

- `BROKEN_OPTIONS` defines both agents but leaves `Agent` out of `allowed_tools`, and gives each agent the other's tools.
- `build_synthesis_prompt()` does `"\n".join(f.claim for f in findings)`. The prompt still *asks* for citations, but the data is already gone, so the report is unsourced.

**`test_task_1_3.py`** proves:

- The spawn gate, tool scoping and schema validation all work.
- Subagents run as two separate requests.
- URLs and page numbers survive into the good synthesis prompt and report.
- The anti-pattern's prompt contains the claims but zero metadata.

## Run

```bash
.venv/bin/python -m domain1_agentic_architecture.task_1_3_context_passing.good_example
.venv/bin/python -m domain1_agentic_architecture.task_1_3_context_passing.anti_pattern
.venv/bin/pytest domain1_agentic_architecture/task_1_3_context_passing
```
