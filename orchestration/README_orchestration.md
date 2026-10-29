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

## Testing

```bash
python -m pytest tests/test_orchestration.py -q
```

The suite validates YAML loading, the documentation contract, and the sequential trace structure. Agent turns are mocked so the tests do not require a running Ollama server.
