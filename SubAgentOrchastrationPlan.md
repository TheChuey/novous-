# Sub-Agent Orchestration Architecture and Implementation Plan

## 1. Executive Overview

This specification defines the architectural design, module layout, tool contracts, and implementation plan for the **Sub-Agent Orchestration Subsystem** in the Novous platform.

The primary objective of this subsystem is to decouple complex background tasks—such as RAG vector retrieval, static code analysis, security auditing, and document processing—from user-facing primary agents. By establishing dedicated background utility workers in `subAgentLibrary/` and orchestrating them through a 7-module engine in `orchestration/`, Novous achieves modular separation of concerns, context clarity, diagnostic observability, and hardware-aware resource control.

```
                               User / REST API
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │  server.py (FastAPI App Entry)       │
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │  orchestration/                      │
                   │  ├── README_orchestration.md         │
                   │  ├── orchestration_schemas.py        │
                   │  ├── orchestration_interface.py      │
                   │  ├── orchestration_patterns.py       │
                   │  ├── orchestration_registry.py       │
                   │  ├── orchestration_service.py        │
                   │  └── orchestration_router.py         │
                   └──────────────┬────────────────┬──────┘
                                  │                │
                                  ▼                ▼
                     ┌─────────────────┐      ┌─────────────────────────┐
                     │ library/        │      │ subAgentLibrary/        │
                     │ (Primary .md)   │      │ (Sub-Agents .yaml)      │
                     └────────┬────────┘      └────────────┬────────────┘
                              │                            │
                              └──────────────┬─────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────┐
                              │ agentMemory/scratchpad.json │
                              │ (Atomic Shared Memory)      │
                              └─────────────────────────────┘
```

---

## 2. Agent Architecture: Primary Agents vs. Sub-Agents

To prevent UI clutter and ensure clean functional boundaries, Novous categorizes agents into two distinct types:

### 2.1 Primary Interactive Agents (`library/*.md`)
- **Location**: `library/{agent_id}.md`
- **Format**: Markdown with YAML frontmatter.
- **Role**: Handles direct user conversations, synthesizes complex multi-step findings, presents formatted answers, and edits workspace files.
- **Tooling**: Bound to user-facing tools, including `call_subagent`, `read_agent_scratchpad`, `read_file`, and `write_file`.

### 2.2 Utility Sub-Agents (`subAgentLibrary/*.yaml`)
- **Location**: `subAgentLibrary/{subagent_id}.yaml`
- **Format**: Pure YAML (`.yaml`).
- **Role**: Single-purpose, background utility workers executing domain-specific tasks (e.g., branch vector search, AST code linting, security scanning).
- **Parsing**: Directly parsed using `yaml.safe_load()` without frontmatter delimiter splitting.
- **Tooling**: Bound to specialized execution tools and `write_agent_scratchpad`.

#### Example Sub-Agent Definition (`subAgentLibrary/code-analyzer.yaml`)
```yaml
id: code-analyzer
name: Code Analysis Sub-Agent
description: Background worker that inspects code files and writes structural diagnostics to the shared scratchpad.
type: subagent
mode: agent
model: qwen2.5-coder:latest
environment: workspace
squad: code-squad
version: 1
tools:
  - read_file
  - map_files
  - read_agent_scratchpad
  - write_agent_scratchpad
prompt: |
  # Code Analysis Sub-Agent Prompt

  ## role
  You are the Code Analysis Sub-Agent. Your task is to inspect code files and write structured diagnostics to the shared agent scratchpad.

  ## purpose
  Read target files using `read_file` and post findings to the scratchpad using `write_agent_scratchpad`.

  ## boundaries
  - Do not modify workspace files directly.
  - Output clean, structured diagnostic output without conversational chitchat.

  ## output format & scratchpad handoff
  Always call `write_agent_scratchpad`:
  {
    "subagent_id": "code-analyzer",
    "task_type": "code_analysis",
    "status": "success",
    "payload": {
      "analyzed_file": "<path>",
      "issues_found": [],
      "suggestions": []
    }
  }
```

---

## 3. Shared Scratchpad Handoff Mechanism (`agentMemory/`)

Communication between sub-agents and primary agents is domain-agnostic and asynchronous, mediated by atomic updates to `agentMemory/data/scratchpad.json`.

### 3.1 Memory State Engine (`agentMemory/scratchpad.py`)
We extend the scratchpad engine with thread-safe atomic writes for generic sub-agent payloads:

```python
def store_subagent_result(subagent_id: str, task_type: str, status: str, payload: Any) -> dict[str, Any]:
    """Store generic sub-agent task execution payloads in the shared agent scratchpad."""
    entry = {
        "subagent_id": subagent_id,
        "task_type": task_type,
        "status": status,
        "payload": payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        data = _read()
        history = data.get("subagent_history")
        if not isinstance(history, list):
            history = []
        history.append(entry)
        data["subagent_history"] = history[-MAX_READ_HISTORY:]
        data["latest_subagent_result"] = entry
        _write(data)
    return {"path": "agentMemory/data/scratchpad.json", "updated_at": entry["updated_at"]}


def read_memory(memory_type: str = "all") -> dict[str, Any]:
    """Read saved scratchpad entries with backward compatibility for legacy keys."""
    valid_types = {"all", "latest_read", "latest_map", "latest_subagent_result", "latest_rag_result"}
    if memory_type not in valid_types:
        raise ValueError(f"memory_type must be one of {valid_types}.")
    with _LOCK:
        data = _read()
    if memory_type == "all":
        return data
    if memory_type in ("latest_subagent_result", "latest_rag_result"):
        return {"latest_subagent_result": data.get("latest_subagent_result", data.get("latest_rag_result", {}))}
    return {memory_type: data[memory_type]} if memory_type in data else {}
```

### 3.2 Agent Tooling Extensions (`tools/agent_memory_tool.py`)
To enable dynamic orchestration, primary agents receive `call_subagent`, while sub-agents use `write_agent_scratchpad`:

```python
@tool(provider="agentMemory")
def call_subagent(subagent_id: str, task_prompt: str, parameters: str = "{}") -> str:
    """Dynamically invoke a background sub-agent from subAgentLibrary/ with a task prompt and parameters."""
    from orchestration.orchestration_interface import run_agent_turn
    try:
        parsed_params = json.loads(parameters) if isinstance(parameters, str) and parameters.startswith("{") else {}
    except Exception:
        parsed_params = {}

    full_prompt = f"Task: '{task_prompt}'. Parameters: {parsed_params}"
    result = run_agent_turn(subagent_id, full_prompt)
    return json.dumps({"subagent_id": subagent_id, "result": result}, ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def write_agent_scratchpad(subagent_id: str = "subagent", task_type: str = "general", status: str = "success", payload: str = "") -> str:
    """Write structured sub-agent execution payloads into the shared scratchpad."""
    try:
        parsed_payload = json.loads(payload) if isinstance(payload, str) and payload.startswith(("[", "{")) else payload
    except Exception:
        parsed_payload = payload

    result = interface.store_subagent_result(subagent_id=subagent_id, task_type=task_type, status=status, payload=parsed_payload)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def read_agent_scratchpad(memory_type: str = "all") -> str:
    """Read saved scratchpad entries ('latest_subagent_result', 'latest_read', 'latest_map', 'all')."""
    return json.dumps(interface.read_memory(memory_type), ensure_ascii=False, indent=2)
```

---

## 4. The 7-Module `orchestration/` Pillar

The `orchestration/` directory is structured into **7 clean modules** alongside a dedicated documentation file:

```
orchestration/
├── __init__.py                  # Package exports & router doorway
├── README_orchestration.md      # Prompt design & architecture documentation
├── orchestration_schemas.py     # Pydantic data contracts & execution trace models
├── orchestration_interface.py   # Gateway bridging core_engine, memory, & YAML loader
├── orchestration_patterns.py    # Execution strategies (Sequential, Fan-Out, Router)
├── orchestration_registry.py    # Pattern registry lookup
├── orchestration_service.py     # Workflow execution supervisor
└── orchestration_router.py      # FastAPI REST API endpoints
```

### 4.1 Module Specifications

#### 1. `orchestration/__init__.py`
Initializes the package and exposes the FastAPI router:
```python
"""Orchestration package initialization."""
from orchestration.orchestration_router import router

__all__ = ["router"]
```

#### 2. `orchestration/README_orchestration.md`
Provides comprehensive guidance for developers and prompt engineers building sub-agents and primary agents.

#### 3. `orchestration/orchestration_schemas.py`
Defines generic input contracts, diagnostic tracing models, and response structures:
```python
"""Pydantic schemas for generic orchestration tasks."""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    step_number: int
    agent_id: str
    phase: str
    status: str
    details: str
    error_reason: Optional[str] = None
    timestamp: str


class OrchestrationRequest(BaseModel):
    pattern: str = Field(default="sequential", description="Execution strategy: 'sequential' (default for local LLM hardware safety), 'fanout', or 'router'")
    primary_agent: str = Field(default="rag-presenter", description="Main user-facing agent ID from library/")
    subagents: List[str] = Field(default_factory=list, description="Ordered sub-agent IDs from subAgentLibrary/")
    user_query: str = Field(..., description="User query or task prompt")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Custom parameters")


class OrchestrationResponse(BaseModel):
    trace_id: str
    pattern: str
    query: str
    status: str
    final_answer: str
    result_payload: Optional[Any] = None
    execution_trace: List[TraceStep] = Field(default_factory=list)
```

#### 4. `orchestration/orchestration_interface.py`
Serves as the gateway bridging `core_engine` (`agent_factory`, `runtime`), `agentMemory`, and sub-agent YAML resolution:
```python
"""Gateway interfacing orchestration with core_engine and agentMemory."""

from pathlib import Path
from typing import Any, Tuple
import yaml

from core_engine import agent_factory, runtime
from agentMemory import interface as memory_interface

LIBRARY_ROOT = Path("library")
SUBAGENT_LIBRARY_ROOT = Path("subAgentLibrary")


def load_agent(agent_id: str) -> Tuple[dict[str, Any], str]:
    """Resolve Markdown agent from library/ or YAML sub-agent from subAgentLibrary/."""
    primary_file = LIBRARY_ROOT / f"{agent_id}.md"
    if primary_file.is_file():
        return agent_factory.parse_agent_markdown(primary_file.read_text(encoding="utf-8"))

    subagent_yaml = SUBAGENT_LIBRARY_ROOT / f"{agent_id}.yaml"
    if subagent_yaml.is_file():
        data = yaml.safe_load(subagent_yaml.read_text(encoding="utf-8")) or {}
        body = data.pop("prompt", "")
        return data, body

    raise FileNotFoundError(f"Agent definition '{agent_id}' not found in library/ or subAgentLibrary/.")


def read_latest_subagent_scratchpad() -> dict[str, Any]:
    memory = memory_interface.read_memory("latest_subagent_result")
    return memory.get("latest_subagent_result", {})


def run_agent_turn(agent_id: str, prompt_input: str) -> str:
    meta, body = load_agent(agent_id)
    agent_instance = runtime.Agent(meta=meta, body=body)
    return str(agent_instance.run(prompt_input))
```

#### 5. `orchestration/orchestration_patterns.py`
Implements hardware-aware execution patterns with live terminal tracing. `SequentialPattern` is the default to prevent hardware VRAM/thread exhaustion on local Ollama models:

```python
"""Execution strategies for multi-subagent orchestration workflows."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid

from orchestration import orchestration_interface as interface
from orchestration.orchestration_schemas import OrchestrationRequest, OrchestrationResponse, TraceStep


class BasePattern(ABC):

    @abstractmethod
    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        pass


class SequentialPattern(BasePattern):
    """Executes sub-agents sequentially to avoid local LLM hardware bottlenecks."""

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        trace_id = f"tr_{uuid.uuid4().hex[:8]}"
        trace_steps: list[TraceStep] = []
        step_counter = 1

        print(f"\n\033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Starting sequential pipeline for: '{request.user_query}'")

        workers = request.subagents if request.subagents else ["rag-retriever"]
        primary_id = request.primary_agent or "rag-presenter"

        for worker_id in workers:
            now = datetime.now(timezone.utc).isoformat()
            print(f" ├── [{step_counter}] Executing sub-agent '\033[93m{worker_id}\033[0m'...")
            
            try:
                worker_prompt = f"Task: '{request.user_query}'. Parameters: {request.parameters}"
                _ = interface.run_agent_turn(worker_id, worker_prompt)
                
                trace_steps.append(TraceStep(
                    step_number=step_counter,
                    agent_id=worker_id,
                    phase="SUBAGENT_EXECUTION",
                    status="SUCCESS",
                    details=f"Executed worker '{worker_id}' successfully",
                    timestamp=now
                ))
            except Exception as exc:
                err_msg = str(exc)
                print(f" │   \033[91m[ERROR]\033[0m Worker '{worker_id}' failed: {err_msg}")
                trace_steps.append(TraceStep(
                    step_number=step_counter,
                    agent_id=worker_id,
                    phase="SUBAGENT_EXECUTION",
                    status="ERROR",
                    details=f"Sub-agent '{worker_id}' raised an exception",
                    error_reason=err_msg,
                    timestamp=now
                ))
            step_counter += 1

        now = datetime.now(timezone.utc).isoformat()
        print(f" ├── [{step_counter}] Inspecting scratchpad barrier...")
        scratchpad_entry = interface.read_latest_subagent_scratchpad()
        status = scratchpad_entry.get("status", "success") if scratchpad_entry else "no_context_found"

        trace_steps.append(TraceStep(
            step_number=step_counter,
            agent_id="scratchpad",
            phase="SCRATCHPAD_BARRIER",
            status=status,
            details="Retrieved latest sub-agent payload from scratchpad",
            timestamp=now
        ))
        step_counter += 1

        now = datetime.now(timezone.utc).isoformat()
        print(f" ├── [{step_counter}] Executing primary agent '\033[95m{primary_id}\033[0m'...")
        
        primary_prompt = (
            f"User request: '{request.user_query}'. "
            "Inspect scratchpad using read_agent_scratchpad('latest_subagent_result') "
            "and synthesize the final output."
        )
        final_answer = interface.run_agent_turn(primary_id, primary_prompt)

        trace_steps.append(TraceStep(
            step_number=step_counter,
            agent_id=primary_id,
            phase="PRIMARY_SYNTHESIS",
            status="SUCCESS",
            details=f"Primary agent '{primary_id}' completed response",
            timestamp=now
        ))

        print(f" \033[94m[ORCHESTRATION TRACE: {trace_id}]\033[0m Pipeline complete.\n")

        return OrchestrationResponse(
            trace_id=trace_id,
            pattern="sequential",
            query=request.user_query,
            status=status,
            final_answer=final_answer,
            result_payload=scratchpad_entry.get("payload") if scratchpad_entry else None,
            execution_trace=trace_steps,
        )


class FanOutPattern(BasePattern):

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        seq = SequentialPattern()
        res = seq.execute(request)
        res.pattern = "fanout"
        return res


class RouterPattern(BasePattern):

    def execute(self, request: OrchestrationRequest) -> OrchestrationResponse:
        seq = SequentialPattern()
        res = seq.execute(request)
        res.pattern = "router"
        return res
```

#### 6. `orchestration/orchestration_registry.py`
Maps strategy keys to pattern classes:
```python
"""Pattern registry lookup."""

from typing import Dict, Type
from orchestration.orchestration_patterns import BasePattern, FanOutPattern, RouterPattern, SequentialPattern

_PATTERNS: Dict[str, Type[BasePattern]] = {
    "sequential": SequentialPattern,
    "fanout": FanOutPattern,
    "router": RouterPattern,
}


def get_pattern(pattern_name: str) -> BasePattern:
    key = pattern_name.lower().strip()
    pattern_cls = _PATTERNS.get(key, SequentialPattern)
    return pattern_cls()
```

#### 7. `orchestration/orchestration_service.py` & `orchestration/orchestration_router.py`
Supervises pipeline execution and exposes REST API endpoints:
```python
# orchestration_service.py
from orchestration.orchestration_registry import get_pattern
from orchestration.orchestration_schemas import OrchestrationRequest, OrchestrationResponse

def run_orchestration(request: OrchestrationRequest) -> OrchestrationResponse:
    pattern_handler = get_pattern(request.pattern)
    return pattern_handler.execute(request)


# orchestration_router.py
from fastapi import APIRouter, HTTPException
from orchestration.orchestration_schemas import OrchestrationRequest, OrchestrationResponse
from orchestration.orchestration_service import run_orchestration

router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])

@router.post("/run", response_model=OrchestrationResponse)
def run_orchestration_endpoint(request: OrchestrationRequest):
    try:
        return run_orchestration(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Orchestration execution failed: {exc}") from exc
```

---

## 5. Automated Test Suite (`tests/test_orchestration.py`)

A Pytest suite ensures component reliability:

```python
"""Automated Pytest suite for multi-subagent orchestration and hardware-aware patterns."""

from pathlib import Path
import yaml
from orchestration.orchestration_schemas import OrchestrationRequest
from orchestration.orchestration_service import run_orchestration
from agentMemory import interface as memory_interface


def test_subagent_yaml_loading():
    yaml_path = Path("subAgentLibrary/code-analyzer.yaml")
    assert yaml_path.is_file()
    content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert content["id"] == "code-analyzer"
    assert content["type"] == "subagent"


def test_readme_orchestration_exists():
    readme_path = Path("orchestration/README_orchestration.md")
    assert readme_path.is_file()
    text = readme_path.read_text(encoding="utf-8")
    assert "Prompt Design Principles" in text


def test_orchestration_sequential_default_pattern():
    req = OrchestrationRequest(
        pattern="sequential",
        primary_agent="rag-presenter",
        subagents=["code-analyzer", "rag-retriever"],
        user_query="Run hardware-safe sequential execution",
        parameters={"test": True}
    )
    res = run_orchestration(req)
    assert res.pattern == "sequential"
    assert res.trace_id.startswith("tr_")
    assert len(res.execution_trace) >= 3
```

---

## 6. Server Mount Integration

Mount the router in `server.py`:

```python
from orchestration import router as orchestration_router

app.include_router(orchestration_router)
```

---

## 7. Step-by-Step Implementation Roadmap

| Phase | Milestone | Action Items | Key Artifacts |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Sub-Agent Library & Memory** | Create `subAgentLibrary/` directory, write YAML sub-agents, and update `agentMemory/scratchpad.py` for generic payload storage. | `subAgentLibrary/*.yaml`, `agentMemory/scratchpad.py` |
| **Phase 2** | **Tooling & Factory Updates** | Expose `call_subagent` and `write_agent_scratchpad` in `tools/agent_memory_tool.py`; update `core_engine/agent_factory.py`. | `tools/agent_memory_tool.py`, `core_engine/agent_factory.py` |
| **Phase 3** | **7-Module Pillar Setup** | Implement `orchestration_*.py` modules and write `orchestration/README_orchestration.md`. | `orchestration/*` |
| **Phase 4** | **Tracing & Server Integration** | Add colorized ANSI terminal tracing to `SequentialPattern` and mount `orchestration_router` in `server.py`. | `server.py`, `orchestration_patterns.py` |
| **Phase 5** | **Testing & Verification** | Execute `pytest tests/test_orchestration.py` to verify sub-agent resolution, scratchpad barrier validation, and trace logging. | `tests/test_orchestration.py` |
