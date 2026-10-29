# Sub-Agent Orchestration

The orchestration pillar coordinates user-facing primary agents with single-purpose background sub-agents. It keeps complex utility work (retrieval, code analysis, security auditing, document processing) out of the primary conversation while preserving a shared, observable handoff.

## Architecture

```
server.py
  └── orchestration_router.py
        └── orchestration_service.py
              └── orchestration_registry.py
                    └── orchestration_patterns.py
                          ├── orchestration_interface.py
                          │     ├── library/*.md
                          │     ├── subAgentLibrary/*.yaml
                          │     ├── core_engine (agent_factory, runtime)
                          │     └── agentMemory.interface
                          └── orchestration_schemas.py
```

## Primary Agents vs. Sub-Agents

| Type | Location | Format | Purpose |
| :--- | :--- | :--- | :--- |
| Primary agent | `library/{agent_id}.md` | Markdown with YAML frontmatter | Handles the user conversation, synthesizes findings, and edits workspace files when asked. |
| Sub-agent | `subAgentLibrary/{subagent_id}.yaml` | Pure YAML | Executes one background domain task and writes its payload to the shared scratchpad. |

Primary agents can call `call_subagent` and read results with `read_agent_scratchpad`. Sub-agents write results with `write_agent_scratchpad` and do not edit workspace files directly.

For regular `/api/chat` and `/api/chat/stream` turns with `rag-presenter`, the chat runtime
executes `call_subagent("rag-retriever", ...)` and reads `latest_subagent_result` before
asking the primary model to answer. This handoff is enforced by the runtime rather than
depending on the model to choose the tool call.

### Sub-Agent YAML Contract

```yaml
id: example-worker
name: Example Worker
description: One-line description of the background task.
type: subagent
mode: agent
model: qwen2.5-coder:latest
environment: workspace
squad: example-squad
version: 1
tools:
  - read_file
  - write_agent_scratchpad
prompt: |
  # Example Worker Prompt

  ## role
  ...
  ## purpose
  ...
  ## boundaries
  ...
  ## output format & scratchpad handoff
  ...
```

The file is parsed with `yaml.safe_load()`; no frontmatter delimiters are used.

## Prompt Design Principles

1. **Single responsibility:** each sub-agent owns one task and one output shape.
2. **Explicit tool contract:** list only the tools the worker needs and describe when to call them.
3. **Evidence over prose:** require tool results as the basis for every claim.
4. **Structured handoff:** require a `write_agent_scratchpad` call with a stable `task_type` and JSON payload.
5. **No silent failure:** report tool errors and missing evidence instead of fabricating results.
6. **Hardware safety:** prefer a small number of sequential workers on local Ollama models.
7. **Primary synthesis:** the primary agent reads the scratchpad and owns the final user-facing answer.

## Scratchpad Handoff

Results are stored atomically in `agentMemory/data/scratchpad.json`.

```json
{
  "subagent_id": "rag-retriever",
  "task_type": "rag_retrieval",
  "status": "success",
  "payload": {
    "query": "leadership styles",
    "knowledge_branch_id": "branch-id",
    "results": []
  },
  "updated_at": "2026-10-28T00:00:00+00:00"
}
```

The engine keeps a bounded `subagent_history` and exposes the newest entry as `latest_subagent_result`. `read_memory("latest_subagent_result")` falls back to the legacy `latest_rag_result` key.

The deterministic `rag-retriever` handoff always writes one of three statuses:
`success` when relevant passages are found, `nothing_found` when the search completes
without relevant passages, or `error` when retrieval fails. Errors include a message
in the payload. Search skips incompatible legacy vectors while reporting their count;
it fails explicitly if no indexed vectors are compatible with the query embedding.

## Execution Patterns

- **sequential** (default): runs each sub-agent one at a time, then the scratchpad barrier, then the primary agent. This is the safest choice for local VRAM and thread limits.
- **fanout**: currently delegates to the sequential pipeline and reports `pattern="fanout"`.
- **router**: currently delegates to the sequential pipeline and reports `pattern="router"`.

All patterns emit a colorized terminal trace with one step per sub-agent, a scratchpad inspection step, and a primary synthesis step.

## Code Development Squad pipeline

`code-squad` runs through `orchestration/code_squad_pipeline.py`, not the patterns above. It powers the CodeBuilder buttons:

| Action | What happens |
| :--- | :--- |
| `plan` | `code-planer` streams a plan (reused by a later `build`). |
| `build` | `code-builder` returns one complete ```python module; the orchestrator applies it to the editor. |
| `test` | The orchestrator compiles the buffer, import-runs it with `__name__` overridden (so the main guard does not run), then runs the `tester`'s assert snippet after the module. |
| `fix` | `code-troubleshooter` gets the real stderr/traceback and returns the corrected module; fix → test repeats up to `MAX_FIX_ATTEMPTS` (3). `troubleshoot` is an alias. |
| `all` | plan → build → test → fix loop. |

The code sub-agents have no tools: they answer with text and a fenced code block, and the orchestrator applies code, runs checks, and records factual handoffs. That keeps small local models from having to emit large tool-call arguments.

Telemetry for the editor: `AGENT_STARTED`, `AGENT_TOKEN` (live only, not replayed), `AGENT_DONE`, `STEP_STATUS`, `EDITOR_CODE_UPDATE` (full content and changed lines), and `EDITOR_CODE_EXECUTION`. The SSE stream resumes from `Last-Event-ID` or `?after=<sequence>`. `POST /api/orchestration/runs/{trace_id}/cancel` stops a run between steps or mid-stream.

## Live Squad Observability

The dashboard's **Registered agent squads** panel is separate from the existing
Workspace squad-folder manager. It currently registers `rag-squad` and
`code-squad`, displays their primary-agent/sub-agent topology, and records
persistent run counts, success/failure counts, average duration, and aggregate
health in `agentMemory/data/orchestration_squad_metrics.json`.

The dashboard starts an asynchronous run with `POST /api/orchestration/run/start`
and subscribes to `GET /api/orchestration/stream/{trace_id}` using Server-Sent
Events. `GET /api/orchestration/squads` returns registered squad definitions and
their metrics. `GET /api/orchestration/catalog` lists selectable primary agents
and sub-agents from `subAgentLibrary/`. Create and delete registered squads with
`POST /api/orchestration/squads` and `DELETE /api/orchestration/squads/{squad_id}`;
deleting a squad does not remove its primary-agent or sub-agent definitions.
Completed run results and the run's captured scratchpad snapshot are available at
`GET /api/orchestration/runs/{trace_id}` and
`GET /api/orchestration/runs/{trace_id}/scratchpad`. Result payloads are held in
a bounded in-memory cache; `GET /api/orchestration/squads/{squad_id}/latest`
returns a squad's newest cached result for the dashboard's View result and View
scratchpad buttons. Telemetry remains free of prompts and document text.
CodeBuilder workflow requests include the active editor buffer. The
`preview_editor_code` tool stores a trace-scoped editor preview retrievable from
`GET /api/orchestration/runs/{trace_id}/editor-preview`; `run_python_code`
execution results are similarly available from
`GET /api/orchestration/runs/{trace_id}/editor-execution`. The CodeBuilder UI
loads previews and diagnostics from these endpoints rather than putting code or
execution output into the telemetry stream. Editor-buffer previews are not
saved automatically. When a builder or troubleshooter does not call the editor
preview tool but returns exactly one complete fenced code block, orchestration
uses that block as a fallback editor handoff. If neither mechanism produces a
preview, CodeBuilder reports that explicitly instead of showing only a success
status. Code Development workflows use only the handoff recorded by their own
run, not the shared scratchpad's previous result. If a code sub-agent returns
without writing its required handoff, orchestration saves its response to the
scratchpad with error status and surfaces it for review; that fallback is not
evidence that a fix or check succeeded. For HTTP 404 reports,
the troubleshooter can use `inspect_http_routes(path)` to statically list Python
route declarations; it must not guess at missing request details, run a server
as a test, or make unrelated feature changes. In build, troubleshoot, and full-squad runs
whose user request mentions a 404, editor previews and workspace writes are
blocked until the request includes both the exact URL/path and HTTP method.
The synchronous `POST /api/orchestration/run` remains available.

The default Code Development Squad uses the `code-planer` primary agent and the
`code-builder`, `tester`, and `code-troubleshooter` sub-agents. Build and
full-squad workflows first ask the planner for an implementation plan, pass that
plan to the builder, and then run the tester on the builder's actual output. The
builder implements the plan in Python. The tester is read-only and runs only
focused, safe Python checks; a test failure is
passed with its observed diagnostics to the troubleshooter. The troubleshooter
is skipped when the builder and tester report no error. Saved default squad
definitions using the old triager topology are migrated to this order. The
existing `codingagent` and `code-analyzer` definitions are not deleted; they are
simply not part of that default squad.

The CodeBuilder agent panel offers **Plan**, **Build**, **Troubleshoot**, and
**Run full squad** actions. Plan runs the read-only planner without a
sub-agent. Build and Run full squad run the planner, builder, tester, and
conditionally the troubleshooter in that order. Troubleshoot runs only the
troubleshooter against the supplied evidence. Each code-agent handoff is
run-scoped and passed to the primary planner for the final response.

Troubleshoot examines the relevant code and, when the request is to troubleshoot
or repair and the root cause is confirmed, applies a minimal fix. It must preview
each exact proposed file write before applying it, report only tool-confirmed
changes, and must not claim tests were run unless it actually ran a focused check.

While a CodeBuilder workflow runs, its editor activity bar displays tool calls
and workflow status, and the chat transcript receives planner/builder/tester/
troubleshooter stage updates and tool activity. Tester execution output and
diagnostics appear in the editor console and chat; diagnostic line highlights
are shown only when the executed source matches the editor buffer. Code previews
load the current workspace file (unless that
would replace unsaved editor work), highlight and count changed lines, and
collapse unchanged regions with nearby context. **Show full file** restores the
complete file. Successful writes reload the changed workspace file when safe and
mark the changed lines as applied.

Code Builder and Troubleshooter can call `preview_code_change(path,
proposed_content)`. It validates the target under the active file-manager root,
compares the proposed text without writing it, and emits only the relative path
and changed line numbers to telemetry. Builder instructions require a successful
preview before each `write_file`. Successful writes emit a separate applied
change event. The dashboard's **Review code changes** button opens the managed
workspace file in the editor and highlights the reported lines; source text,
tool arguments, and proposed content are not included in telemetry.
For a new file, the review button becomes available after the file is written.

Telemetry is bounded and thread-safe. It records orchestration stages, agent
handoffs, tool names/status/duration, scratchpad status/result counts, and
completion status. It deliberately omits user prompts, tool arguments, tool
results, scratchpad payloads, and retrieved document text. Trace history,
per-trace event counts, listener queues, and SSE lifetimes are capped.

## REST API

`POST /api/orchestration/run`

```json
{
  "pattern": "sequential",
  "primary_agent": "rag-presenter",
  "subagents": ["rag-retriever", "code-analyzer"],
  "user_query": "Summarize the indexed leadership notes",
  "parameters": {"top_k": 5}
}
```

The response contains `trace_id`, `pattern`, `query`, `status`, `final_answer`, `result_payload`, and the full `execution_trace`.

To start a dashboard workflow asynchronously, post the registered squad and the
requested work:

```json
{
  "squad_id": "rag-squad",
  "user_query": "Summarize the indexed leadership notes"
}
```

The response contains a `trace_id` for the live SSE endpoint. The asynchronous
endpoint uses the selected squad's registered agent topology rather than
accepting arbitrary agents from the browser.

## Testing

```bash
python -m pytest tests/test_orchestration.py tests/test_orchestration_observability.py -q
```

The suite validates YAML loading, the documentation contract, and the sequential trace structure. Agent turns are mocked so the tests do not require a running Ollama server.
