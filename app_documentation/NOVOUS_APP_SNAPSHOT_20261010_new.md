Date: 2026-10-10
Name: Novous Application Snapshot
Filename: NOVOUS_APP_SNAPSHOT_20261010_new.md
Commit: 8fffe40
Description: Self-contained reference for an AI agent. Captures Novous app purpose, architecture, file structure, and complete source code. Designed for grounding/understanding without repo access.

# NOVOUS APPLICATION SNAPSHOT

## 1) Overview

Novous is an agent orchestration/workspace system with FastAPI backend, static frontend, core engine for agents/tools, editor integration, workspace/agents configuration, and test environment.

Key components:
- server.py: FastAPI app entrypoint serving static UI and API routes
- core_engine/: agent factory, runtime, tool catalog, langgraph tools
- editor/: editor session/operations/schemas/interface
- frontend/: static assets and HTML pages (chat, editor, index, testing)
- workspace/: agent definitions and workflow utilities
- test_environment/: prompt builder, test runner, test agents

## 2) Table of Contents

1. Overview
2. File Structure Snapshot
3. Complete Source Code (by file)

## 3) File Structure Snapshot

- .pytest_cache/
- .pytest_cache/.gitignore
- .pytest_cache/CACHEDIR.TAG
- .pytest_cache/README.md
- .pytest_cache/v/
- .pytest_cache/v/cache/
- .pytest_cache/v/cache/lastfailed
- .pytest_cache/v/cache/nodeids
- app_documentation/
- codebuilder/
- codebuilder/__init__.py
- codebuilder/agent_codebuilder.py
- codebuilder/agent_loader.py
- codebuilder/agents/
- codebuilder/agents/codebuilder-agent/
- codebuilder/agents/codebuilder-agent/agent.json
- codebuilder/agents/codebuilder-agent/agent.md
- codebuilder/agents/codingagent/
- codebuilder/agents/codingagent/agent.json
- codebuilder/agents/codingagent/agent.md
- codebuilder/codebuilder_schemas.py
- codebuilder/diagnostics.py
- codebuilder/execution.py
- codebuilder/execution_codebuilder.py
- codebuilder/interface.py
- codebuilder/interface_codebuilder.py
- codebuilder/schemas.py
- codebuilder/tools/
- codebuilder/tools/tool_library.py
- core_engine/
- core_engine/__init__.py
- core_engine/agent_factory.py
- core_engine/interface.py
- core_engine/langgraph_tools.py
- core_engine/runtime.py
- core_engine/tool_catalog.py
- editor/
- editor/__init__.py
- editor/editor_operations.py
- editor/editor_schemas.py
- editor/editor_session.py
- editor/interface.py
- frontend/
- frontend/pages/
- frontend/pages/chat.html
- frontend/pages/codeBuilder.html
- frontend/pages/editor.html
- frontend/pages/index.html
- frontend/pages/testing.html
- frontend/static/
- frontend/static/css/
- frontend/static/css/codebuilder.css
- frontend/static/css/style.css
- frontend/static/css/test_panel.css
- frontend/static/js/
- frontend/static/js/api.js
- frontend/static/js/app.js
- frontend/static/js/chat.js
- frontend/static/js/codebuilder/
- frontend/static/js/codebuilder/codebuilder.js
- frontend/static/js/codebuilder/codebuilder_editor.js
- frontend/static/js/editor.js
- frontend/static/js/prompt_creation.js
- frontend/static/js/test_panel.js
- frontend/static/js/testing.js
- frontend/static/js/tree.js
- requirements.txt
- scripts/
- scripts/gen_app_snapshot.py
- scripts/gen_master_copy.py
- scripts/venv.bat
- scripts/venv.sh
- server.py
- test_environment/
- test_environment/__init__.py
- test_environment/interface.py
- test_environment/prompt_builder.py
- test_environment/PromptBuilderFiles/
- test_environment/PromptBuilderFiles/categories.json
- test_environment/PromptBuilderFiles/parts/
- test_environment/PromptBuilderFiles/parts/1/
- test_environment/PromptBuilderFiles/parts/1/1.md
- test_environment/PromptBuilderFiles/parts/agent-instructions/
- test_environment/PromptBuilderFiles/parts/agent-instructions/codeagent.md
- test_environment/PromptBuilderFiles/parts/boundaries/
- test_environment/PromptBuilderFiles/parts/boundaries/agenttest.md
- test_environment/PromptBuilderFiles/parts/boundaries/codeagent.md
- test_environment/PromptBuilderFiles/parts/boundaries/safety.md
- test_environment/PromptBuilderFiles/parts/boundaries/scope.md
- test_environment/PromptBuilderFiles/parts/output-format/
- test_environment/PromptBuilderFiles/parts/output-format/codeagent.md
- test_environment/PromptBuilderFiles/parts/output_format/
- test_environment/PromptBuilderFiles/parts/output_format/concise-bullets.md
- test_environment/PromptBuilderFiles/parts/output_format/markdown-structure.md
- test_environment/PromptBuilderFiles/parts/primary-goal/
- test_environment/PromptBuilderFiles/parts/primary-goal/goal.md
- test_environment/PromptBuilderFiles/parts/purpose/
- test_environment/PromptBuilderFiles/parts/purpose/research-report.md
- test_environment/PromptBuilderFiles/parts/purpose/task-completion.md
- test_environment/PromptBuilderFiles/parts/role/
- test_environment/PromptBuilderFiles/parts/role/01.md
- test_environment/PromptBuilderFiles/parts/role/agenttest.md
- test_environment/PromptBuilderFiles/parts/role/senior-engineer.md
- test_environment/PromptBuilderFiles/parts/role/supportive-tutor.md
- test_environment/PromptBuilderFiles/parts/tone/
- test_environment/PromptBuilderFiles/parts/tone/friendly.md
- test_environment/PromptBuilderFiles/parts/tone/professional.md
- test_environment/PromptBuilderFiles/parts/tool/
- test_environment/PromptBuilderFiles/parts/tool/rules.md
- test_environment/test_agents/
- test_environment/test_agents/agent-01__snapshot__20261008-033519/
- test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.json
- test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.md
- test_environment/test_agents/agent-01__snapshot__20261008-041810/
- test_environment/test_agents/agent-01__snapshot__20261008-041810/agent.json
- test_environment/test_agents/agent-01__snapshot__20261008-041810/agent.md
- test_environment/test_agents/agent-01__snapshot__20261008-042917/
- test_environment/test_agents/agent-01__snapshot__20261008-042917/agent.json
- test_environment/test_agents/agent-01__snapshot__20261008-042917/agent.md
- test_environment/test_agents/agent-01__snapshot__20261010-232622/
- test_environment/test_agents/assistant__snapshot__20261007-210439/
- test_environment/test_agents/assistant__snapshot__20261007-210439/agent.json
- test_environment/test_agents/assistant__snapshot__20261007-210439/agent.md
- test_environment/test_agents/assistant__snapshot__20261008-012019/
- test_environment/test_agents/assistant__snapshot__20261008-012019/agent.json
- test_environment/test_agents/assistant__snapshot__20261008-012019/agent.md
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-000732/
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-000732/agent.json
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-000732/agent.md
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-001037/
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-001037/agent.json
- test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-001037/agent.md
- test_environment/test_agents/codingagent__snapshot__20261010-234451/
- test_environment/test_agents/codingagent__snapshot__20261010-234451/agent.json
- test_environment/test_agents/codingagent__snapshot__20261010-234451/agent.md
- test_environment/test_agents/codingagent__snapshot__20261010-234544/
- test_environment/test_agents/codingagent__snapshot__20261010-234544/agent.json
- test_environment/test_agents/codingagent__snapshot__20261010-234544/agent.md
- test_environment/test_agents/manifest.json
- test_environment/test_runner.py
- test_environment/test_tool_workbench.py
- test_environment/tool_workbench.py
- workspace/
- workspace/__init__.py
- workspace/agents/
- workspace/agents/assistant/
- workspace/agents/assistant/agent.json
- workspace/agents/assistant/agent.md
- workspace/agents/researcher/
- workspace/agents/researcher/agent.json
- workspace/agents/researcher/agent.md
- workspace/agents/reviewer/
- workspace/agents/reviewer/agent.json
- workspace/agents/reviewer/agent.md
- workspace/documentation/
- workspace/documentation/Markdown/
- workspace/documentation/user_notes.md
- workspace/exports/
- workspace/exports/sessions/
- workspace/exports/sessions/chat-agent-01_20261007_221450_577212.md
- workspace/hello_world.py
- workspace/interface.py
- workspace/Markdown
- workspace/Notes/
- workspace/Notes/MAMA-chat-agent-01_20261007_221450_577212.md
- workspace/Notes/Notes.txt
- workspace/project.json
- workspace/squad_manager.py
- workspace/states.txt
- workspace/testcal
- workspace/To Due List/
- workspace/To Due List/list 2
- workspace/To Due List/list 3
- workspace/To Due List/test steps for tools
- workspace/tools/
- workspace/tools/tool_library.py
- workspace/workspace_workflow.py

## 4) Complete Source Code (by file)

### .pytest_cache/README.md

`markdown
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

`

### codebuilder/__init__.py

`python
"""CodeBuilder pillar package."""

from .agent_loader import load_codebuilder_agent_meta
from .execution import execute_python_code
from .schemas import (
    CodeExecutionRequest,
    CodeExecutionResult,
    DiagnosticItem,
    StructuredEditRequest,
)

__all__ = [
    "CodeExecutionRequest",
    "CodeExecutionResult",
    "DiagnosticItem",
    "StructuredEditRequest",
    "execute_python_code",
    "load_codebuilder_agent_meta",
]

`

### codebuilder/agent_codebuilder.py

`python
"""Compatibility wrapper for the CodeBuilder agent loader."""

from .agent_loader import load_codebuilder_agent_meta

__all__ = ["load_codebuilder_agent_meta"]

`

### codebuilder/agent_loader.py

`python
"""Agent metadata loader for the CodeBuilder specialist."""

import json
from pathlib import Path
from typing import Any, Dict

CODEBUILDER_ROOT = Path(__file__).resolve().parent


def load_codebuilder_agent_meta() -> Dict[str, Any]:
    """Load the CodeBuilder specialist metadata from the agent definition file."""
    agent_json_path = CODEBUILDER_ROOT / "agents" / "codebuilder-agent" / "agent.json"
    if agent_json_path.is_file():
        return json.loads(agent_json_path.read_text(encoding="utf-8"))

    return {
        "id": "codebuilder-agent",
        "name": "CodeBuilder Specialist",
        "description": "Agent dedicated to writing, refactoring, and diagnosing Python code.",
        "mode": "agent",
        "tools": ["list_files", "read_file", "edit_file", "check_syntax", "run_code"],
    }

`

### codebuilder/agents/codebuilder-agent/agent.json

`json
{
  "id": "codebuilder-agent",
  "name": "CodeBuilder Specialist",
  "description": "Specialized agent for writing, analyzing, and refactoring Python code in Novous.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "environment": "codebuilder",
  "tools": [
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code",
    "send_code_to_editor",
    "run_code_in_editor"
  ]
}

`

### codebuilder/agents/codebuilder-agent/agent.md

`markdown
# CodeBuilder Specialist

## role
You are CodeBuilder, a specialist AI software engineer inside Novous. You analyze requirements, inspect workspace code, and generate precise, structured code edits.

## purpose
Your purpose is to assist users in building, refactoring, and debugging Python applications. Always test syntax and verify workspace context before proposing edits.

## boundaries
- Only suggest changes that adhere to separation of concerns.
- Whenever you provide or revise Python code, call `send_code_to_editor` with the complete code so it is placed in the active Monaco editor. Also include a fenced `python` code block in your reply so the user can review it and send it manually if needed.
- When the user asks to run the code, call `send_code_to_editor` first if you generated or changed the code, then call `run_code_in_editor`. The calls may be combined in that order.
- Use `run_python_code` only when the user asks for a standalone snippet that should not replace the editor contents.
- Never make unverified assumptions about file paths.

## output format
Briefly describe what you changed and whether you placed code in the editor or ran the editor contents. Refer to the Run Output panel for execution results.

`

### codebuilder/agents/codingagent/agent.json

`json
{
  "id": "codingagent",
  "name": "CodingAgent",
  "description": "Agent that will write code inpython",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code"
  ],
  "environment": "codebuilder"
}

`

### codebuilder/agents/codingagent/agent.md

`markdown
## CodeAgent

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

## CodeAgent

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

## 01

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

## Goal

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

## CodeAgent

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

## Available Tools

### send_code_to_editor
- Provider: codebuilder
- Signature: (code: str) -> str
- Description: Queue generated Python code for insertion into the active CodeBuilder Monaco editor.

### run_code_in_editor
- Provider: codebuilder
- Signature: () -> str
- Description: Queue execution of the current contents of the active CodeBuilder editor.

`

### codebuilder/codebuilder_schemas.py

`python
"""Backward-compatible schema exports for the CodeBuilder pillar."""

from .schemas import *

`

### codebuilder/diagnostics.py

`python
"""Diagnostic funnel utilities for the CodeBuilder pillar."""

from typing import Any, Iterable, List


def funnel_diagnostics(items: Iterable[Any]) -> List[dict]:
    """Normalize arbitrary diagnostic payloads to dictionary entries."""
    return [
        {
            "path": getattr(item, "path", None),
            "line": getattr(item, "line", None),
            "column": getattr(item, "column", None),
            "message": getattr(item, "message", str(item)),
            "severity": getattr(item, "severity", "error"),
            "run_id": getattr(item, "run_id", None),
        }
        for item in items
    ]

`

### codebuilder/execution.py

`python
"""Execution engine for Python snippets and structured diagnostics."""

import io
import sys
import traceback
import uuid
from typing import List

from .schemas import CodeExecutionRequest, CodeExecutionResult, DiagnosticItem


def execute_python_code(req: CodeExecutionRequest) -> CodeExecutionResult:
    """Execute Python code in an isolated namespace and capture diagnostics."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    diagnostics: List[DiagnosticItem] = []

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_buffer, stderr_buffer

    status = "SUCCESS"
    try:
        try:
            compile(req.code, "<codebuilder>", "exec")
        except SyntaxError as exc:
            diagnostics.append(
                DiagnosticItem(
                    line=exc.lineno,
                    column=exc.offset,
                    message=f"SyntaxError: {exc.msg}",
                    severity="error",
                    run_id=run_id,
                )
            )
            raise
        exec_globals = {"__name__": "__main__"}
        exec(req.code, exec_globals)
    except Exception as exc:  # noqa: BLE001 - surface structured runtime diagnostics
        status = "ERROR"
        tb = traceback.extract_tb(exc.__traceback__)
        last_frame = tb[-1] if tb else None
        diagnostics.append(
            DiagnosticItem(
                path=getattr(exc, "filename", None),
                line=last_frame.lineno if last_frame else None,
                column=getattr(exc, "offset", None),
                message=f"{type(exc).__name__}: {exc}",
                severity="error",
                run_id=run_id,
            )
        )
        stderr_buffer.write(traceback.format_exc())
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

    return CodeExecutionResult(
        run_id=run_id,
        status=status,
        stdout=stdout_buffer.getvalue(),
        stderr=stderr_buffer.getvalue(),
        diagnostics=diagnostics,
    )

`

### codebuilder/execution_codebuilder.py

`python
"""Compatibility wrapper for the CodeBuilder execution engine."""

from .execution import execute_python_code

__all__ = ["execute_python_code"]

`

### codebuilder/interface.py

`python
"""CodeBuilder doorway: FastAPI router for execution and structured edits."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from .agent_loader import load_codebuilder_agent_meta
from .execution import execute_python_code
from .schemas import CodeExecutionRequest, CodeExecutionResult, StructuredEditRequest
from core_engine.agent_factory import list_agents

router = APIRouter(prefix="/api/codebuilder", tags=["CodeBuilder"])


@router.get("/health")
def api_codebuilder_health():
    """Return the health state of the CodeBuilder pillar."""
    return {"status": "ok", "pillar": "codebuilder"}


@router.get("/agent")
def api_get_agent():
    """Return the CodeBuilder specialist profile."""
    return load_codebuilder_agent_meta()


@router.get("/agents")
def api_codebuilder_agents():
    """List only agents stored in the CodeBuilder environment."""
    return {"agents": list_agents("codebuilder")}


@router.post("/execute", response_model=CodeExecutionResult)
def api_execute_code(req: CodeExecutionRequest):
    """Execute Python source and return any collected diagnostics."""
    try:
        return execute_python_code(req)
    except Exception as exc:  # pragma: no cover - surfaced as HTTP 500
        raise HTTPException(status_code=500, detail=f"CodeBuilder execution error: {exc}") from exc


@router.post("/edit")
def api_apply_structured_edit(req: StructuredEditRequest):
    """Write an approved file update to the workspace."""
    target = Path(req.target_path)
    if not target.is_absolute():
        target = Path.cwd() / target

    if target.exists() and target.is_dir():
        raise HTTPException(status_code=400, detail="Target path points to a directory, not a file.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")

    return {
        "status": "applied",
        "target_path": str(target),
        "bytes_written": len(req.content.encode("utf-8")),
        "explanation": req.explanation,
    }

`

### codebuilder/interface_codebuilder.py

`python
"""Compatibility wrapper for the CodeBuilder router."""

from .interface import router

__all__ = ["router"]

`

### codebuilder/schemas.py

`python
"""Data models and request schemas for the CodeBuilder pillar."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    timeout_seconds: float = Field(default=5.0, description="Execution timeout in seconds")


class DiagnosticItem(BaseModel):
    path: Optional[str] = Field(default=None, description="Target file path, if available")
    line: Optional[int] = Field(default=None, description="Line number of the issue")
    column: Optional[int] = Field(default=None, description="Column number of the issue")
    message: str = Field(..., description="Diagnostic error message")
    severity: str = Field(default="error", description="Severity level: error, warning, or info")
    run_id: Optional[str] = Field(default=None, description="Execution run identifier")


class CodeExecutionResult(BaseModel):
    run_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)


class StructuredEditRequest(BaseModel):
    target_path: str = Field(..., description="Target file path relative to the workspace root")
    content: str = Field(..., description="Proposed content or patch")
    explanation: Optional[str] = Field(default=None, description="Explanation of the requested change")

`

### codebuilder/tools/tool_library.py

`python
"""Custom tools promoted from the Function Testing Workbench."""


def calculate_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate shipping fee from package weight and distance."""
    base_rate = 5.0
    cost = base_rate + (weight_kg * 1.5) + (distance_km * 0.05)
    return {
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "shipping_cost": round(cost, 2)
    }

`

### core_engine/__init__.py

`python

`

### core_engine/agent_factory.py

`python
import json
from pathlib import Path
from core_engine.runtime import AgentProfile

AGENTS_ROOT = Path(__file__).resolve().parent.parent / "workspace" / "agents"
CODEBUILDER_AGENTS_ROOT = Path(__file__).resolve().parent.parent / "codebuilder" / "agents"
AGENT_ENVIRONMENTS = {
    "workspace": AGENTS_ROOT,
    "codebuilder": CODEBUILDER_AGENTS_ROOT,
}

AGENT_MD_TEMPLATE = """# {name}

## role
You are {name}, a Novous workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
{purpose}

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
- Treat the workspace directory as the default destination for files. File tool paths are relative to the workspace root: use a bare filename for a file in its root, and do not add a `workspace/` prefix.
- For file requests, use write_file with the requested content; use create_file only for an intentionally empty file.
- Treat tool errors as failures, never as success. Claim a file was created or updated only after the write tool reports success.
- Never share secrets, credentials, or private user data.
- Report errors honestly instead of guessing.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use bullet lists for three or more items, use markdown headings for long responses, and keep every reply concise.
"""


def parse_markdown_sections(md_text: str) -> dict:
    sections = {}
    current_title = None
    current_lines = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip().lower()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def _get_agents_root(environment: str = "workspace") -> Path:
    try:
        return AGENT_ENVIRONMENTS[environment]
    except KeyError as exc:
        raise ValueError(f"Unknown agent environment: {environment}") from exc


def find_agent_dir(agent_id: str, environment: str = "workspace") -> Path | None:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or "/" in clean or clean in (".", ".."):
        return None
    candidate = _get_agents_root(environment) / clean
    if candidate.is_dir() and (candidate / "agent.json").is_file():
        return candidate
    return None


def load_agent_definition(json_path: Path, md_path: Path) -> AgentProfile:
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    sections = parse_markdown_sections(md_text)

    profile = AgentProfile(
        id=meta.get("id", json_path.parent.name),
        name=meta.get("name", json_path.parent.name),
        description=meta.get("description", ""),
        mode=meta.get("mode", "agent"),
        role=sections.get("role", ""),
        purpose=sections.get("purpose", ""),
        boundaries=sections.get("boundaries", ""),
        model=meta.get("model", ""),
        tools=list(meta.get("tools", []) or []),
        extras=sections
    )

    prompt_parts = [
        f"You are {profile.name}.",
        f"ROLE:\n{profile.role}" if profile.role else "",
        f"PURPOSE:\n{profile.purpose}" if profile.purpose else "",
        f"BOUNDARIES:\n{profile.boundaries}" if profile.boundaries else "",
    ]

    for title, content in sections.items():
        if title not in ("role", "purpose", "boundaries") and content:
            prompt_parts.append(f"{title.upper()}:\n{content}")

    profile.system_prompt = "\n\n".join(p for p in prompt_parts if p)
    return profile


def load_agent(agent_id: str, environment: str = "workspace") -> AgentProfile:
    agent_dir = find_agent_dir(agent_id, environment)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    return load_agent_definition(agent_dir / "agent.json", agent_dir / "agent.md")


def list_agents(environment: str = "workspace") -> list[dict]:
    agents_root = _get_agents_root(environment)
    agents = []
    if not agents_root.is_dir():
        return agents
    for child in sorted(agents_root.iterdir(), key=lambda p: p.name.lower()):
        json_path = child / "agent.json"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        agents.append({
            "id": meta.get("id", child.name),
            "name": meta.get("name", child.name),
            "description": meta.get("description", ""),
            "mode": meta.get("mode", "chat"),
            "model": meta.get("model", ""),
            "squad": meta.get("squad", ""),
            "tools": meta.get("tools", []),
            "has_markdown": (child / "agent.md").is_file(),
            "environment": environment,
        })
    return agents

`

### core_engine/interface.py

`python
"""Core Engine Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)."""

import re
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from core_engine import agent_factory, tool_catalog
from core_engine.runtime import Agent, AgentProfile
from editor.editor_schemas import EditorEventType
from editor.editor_session import manager as editor_session_manager

router = APIRouter()

# In-memory conversation sessions, keyed by agent id.
SESSIONS: dict[str, Agent] = {}


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""
    environment: Literal["workspace", "codebuilder"] = "workspace"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent_id: str
    model: str = "qwen2.5-coder:latest"
    session_id: str | None = None
    environment: Literal["workspace", "codebuilder"] = "workspace"


class ExportSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


def run_single_agent(agent_id: str, message: str, model: str | None = None,
                     session_id: str | None = None,
                     environment: str = "workspace") -> dict:
    """Doorway function: run one agent turn through the Think-Act-Observe loop."""
    try:
        profile = agent_factory.load_agent(agent_id, environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    session_key = session_id or agent_id
    agent = SESSIONS.get(session_key)
    if agent is None:
        tools = tool_catalog.get_tools(profile.tools) if profile.mode == "agent" else []
        agent = Agent(model=model or profile.model or None, tools=tools, profile=profile,
                      session=session_key)
        SESSIONS[session_key] = agent

    agent.tool_events = []
    try:
        reply = agent.think(message)
    except Exception as exc:  # Ollama down / model missing -> graceful error reply
        reply = (f"[engine] Could not reach the model runtime: {exc}\n"
                 f"Start Ollama (e.g. `ollama serve`) and pull the model "
                 f"`{model or profile.model or 'qwen2.5-coder:latest'}`, then retry.")
        if agent.messages and agent.messages[-1].get("role") == "user":
            agent.messages.pop()

    return {
        "reply": reply,
        "agent_id": agent_id,
        "session_id": session_key,
        "model": agent.model,
        "tool_events": list(agent.tool_events),
        "tool_stats": agent.tool_stats,
    }


def list_agents() -> list[dict]:
    """Doorway function: list all canonical agents from workspace/agents/."""
    return agent_factory.list_agents("workspace")


def reset_session(session_id: str) -> bool:
    return SESSIONS.pop(session_id, None) is not None


@router.get("/api/agents")
def api_list_agents():
    return {"agents": list_agents()}


@router.post("/api/agents/create")
def api_create_agent(req: CreateAgentRequest):
    from workspace import workspace_workflow
    try:
        result = workspace_workflow.scaffold_agent(
            agent_id=req.agent_id.strip(),
            name=req.name.strip(),
            description=req.description.strip(),
            mode=req.mode if req.mode in ("chat", "agent") else "chat",
            squad=req.squad.strip(),
            environment=getattr(req, "environment", "workspace"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str, environment: str = "workspace"):
    from workspace import workspace_workflow
    try:
        return workspace_workflow.delete_agent(agent_id, environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/chat")
async def api_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    result = await run_in_threadpool(
        run_single_agent, req.agent_id, req.message.strip(), req.model, req.session_id,
        req.environment,
    )
    for event in result["tool_events"]:
        event_data = {
            "tool": event["tool"],
            "args": event.get("args", {}),
            "status": event["status"],
            "origin": event["origin"],
        }
        if event.get("error") is not None:
            event_data["error"] = event["error"]
        editor_session_manager.publish(
            EditorEventType.TOOL_EXECUTED,
            event["tool"],
            result["session_id"],
            **event_data,
        )
    return result


@router.post("/api/chat/reset")
def api_chat_reset(session_id: str):
    return {"reset": reset_session(session_id)}


@router.post("/api/chat/export")
def api_export_chat_session(req: ExportSessionRequest):
    agent = SESSIONS.get(req.session_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found.")

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    safe_session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", req.session_id).strip("._")
    if not safe_session_id:
        safe_session_id = "session"
    filename = f"novous_{safe_session_id}_{timestamp}.md"
    exported_at = now.strftime("%Y-%m-%d %H:%M:%S")
    agent_name = agent.profile.name or req.session_id

    lines = [
        f"# Novous Chat Session Log — {agent_name}",
        f"**Agent ID:** `{agent.profile.id}` | **Model:** `{agent.model}` | "
        f"**Session Key:** `{req.session_id}`",
        f"**Exported At:** `{exported_at}`",
        "",
        "---",
        "",
        "## Tool Execution Metrics",
        "",
    ]

    if agent.tool_stats:
        lines.extend([
            "| Tool Name | Total Calls | Successes | Errors | Success Rate |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])
        for tool_name, metrics in agent.tool_stats.items():
            lines.append(
                f"| `{tool_name}` | {metrics['calls']} | {metrics['successes']} | "
                f"{metrics['errors']} | {metrics['success_rate']:.1%} |"
            )
    else:
        lines.append("*No tools executed in this session.*")

    lines.extend(["", "---", "", "## Conversation History", ""])
    for msg in agent.messages:
        role = str(msg.get("role", "unknown")).upper()
        if role == "SYSTEM":
            continue
        content = msg.get("content") or ""
        lines.extend([f"### {role.title()}", "", str(content), ""])

    full_markdown = "\n".join(lines)
    return Response(
        content=full_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/tools")
def api_tools():
    return {"tools": tool_catalog.list_tools(),
            "providers": tool_catalog.PROVIDER_BINDINGS}


def list_models() -> dict:
    """Doorway function: list Ollama models installed on this host."""
    try:
        import ollama
        models = [m.get("model") or m.get("name") for m in ollama.list().get("models", [])]
    except Exception as exc:
        models = []
        error = str(exc)
    return {
        "models": sorted(models),
        "default": "qwen2.5-coder:latest",
        "error": error if not models else None,
    }


@router.get("/api/models")
def api_models():
    return list_models()

`

### core_engine/langgraph_tools.py

`python
"""LangGraph & Docling Tool Suite for Novous Agent Factory.

Provides safe file CRUD, workspace directory mapping, AST docstring extraction,
Docling document conversion, workspace search, and grounded RAG capabilities.
"""

import ast
import json
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Internal Novous Editor operations for workspace security
from editor.editor_operations import (
    read_file_content,
    write_file_content,
    create_path,
    delete_path,
    get_directory_tree,
    resolve_project_path,
    PROJECT_ROOT,
)

_docling_converter = None


def _get_docling_converter():
    """Lazy initialization of Docling converter."""
    global _docling_converter
    if _docling_converter is None:
        try:
            from docling.document_converter import DocumentConverter

            _docling_converter = DocumentConverter()
        except ImportError as exc:
            raise RuntimeError(
                "Docling is not installed. Run 'pip install -r requirements.txt' to enable Docling features."
            ) from exc
    return _docling_converter


# --- 1. Read File Tool ---
@tool
def read_file_tool(relative_path: str) -> str:
    """Read a file relative to workspace root; do not prefix paths with 'workspace/'."""
    try:
        data = read_file_content(relative_path)
        return data["content"]
    except Exception as exc:
        return f"Error reading file '{relative_path}': {exc}"


# --- 2. Write File Tool ---
@tool
def write_file_tool(relative_path: str, content: str) -> str:
    """Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.

    Do not prefix paths with 'workspace/'.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Use create_file_tool only when an intentionally empty file is requested.
    """
    if not content.strip():
        raise ValueError(
            "File content is empty; no file was written. Provide content, or use "
            "create_file_tool only when an empty file is explicitly requested."
        )

    res = write_file_content(relative_path, content)
    saved = read_file_content(relative_path)["content"]
    if saved != content:
        raise IOError(f"Verification failed after writing '{relative_path}'.")
    return (
        f"Successfully wrote and verified {res['bytes_written']} bytes "
        f"to '{relative_path}'."
    )


# --- 3. Create File or Folder Tool ---
@tool
def create_file_tool(relative_path: str, kind: str = "file") -> str:
    """Create an empty file or directory under workspace root; do not prefix paths with 'workspace/'."""
    try:
        res = create_path(relative_path, kind=kind)
        return f"Created {res['created']} at '{relative_path}'."
    except Exception as exc:
        return f"Error creating path '{relative_path}': {exc}"


# --- 4. Delete File Tool ---
@tool
def delete_file_tool(relative_path: str) -> str:
    """Safely delete a file or empty directory from the workspace."""
    try:
        res = delete_path(relative_path)
        return f"Deleted '{relative_path}' successfully."
    except Exception as exc:
        return f"Error deleting path '{relative_path}': {exc}"


# --- 5. Map Directory Tree Tool ---
@tool
def map_directory_tree_tool(relative_path: str = "") -> str:
    """Return a JSON map of the directory structure starting from relative_path."""
    try:
        tree = get_directory_tree(relative_path)
        return json.dumps(tree, indent=2)
    except Exception as exc:
        return f"Error mapping directory tree '{relative_path}': {exc}"


# --- 6. Extract Docstrings Tool ---
@tool
def extract_docstrings_tool(relative_path: str) -> str:
    """Parse a Python file and extract module, class, and function docstrings using AST."""
    try:
        abs_path = resolve_project_path(relative_path)
        code = abs_path.read_text(encoding="utf-8")
        parsed_tree = ast.parse(code)

        docstrings = {
            "file": relative_path,
            "module_docstring": ast.get_docstring(parsed_tree),
            "classes": {},
            "functions": {},
        }

        for node in ast.walk(parsed_tree):
            if isinstance(node, ast.ClassDef):
                docstrings["classes"][node.name] = ast.get_docstring(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstrings["functions"][node.name] = ast.get_docstring(node)

        return json.dumps(docstrings, indent=2)
    except Exception as exc:
        return f"Error extracting docstrings from '{relative_path}': {exc}"


# --- 7. Search Workspace Tool ---
@tool
def search_workspace_tool(query: str, extension: str = ".py") -> str:
    """Search workspace files for matching keyword or text snippet."""
    try:
        matches = []
        ext = extension if extension.startswith(".") else f".{extension}"
        for file_path in PROJECT_ROOT.rglob(f"*{ext}"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            try:
                rel = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for idx, line in enumerate(content.splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append(f"{rel}:{idx} - {line.strip()}")
            except Exception:
                continue
        return (
            "\n".join(matches[:50])
            if matches
            else f"No matches found for query '{query}'."
        )
    except Exception as exc:
        return f"Error searching workspace: {exc}"


# --- 8. Docling Document Converter Tool ---
@tool
def docling_parse_tool(
    relative_path: str, output_format: str = "markdown"
) -> str:
    """Parse PDF, DOCX, PPTX, HTML, or Markdown files into clean Markdown or JSON using Docling."""
    try:
        abs_path = resolve_project_path(relative_path)
        if not abs_path.is_file():
            return f"Error: File '{relative_path}' not found."

        converter = _get_docling_converter()
        result = converter.convert(str(abs_path))

        if output_format.lower() == "json":
            return json.dumps(result.document.export_to_dict(), indent=2)
        return result.document.export_to_markdown()
    except Exception as exc:
        return f"Error parsing document '{relative_path}' with Docling: {exc}"


# --- 9. Docling-Enhanced RAG Agent Tool ---
@tool
def rag_agent_tool(
    query: str, relative_path: Optional[str] = None, top_k: int = 3
) -> str:
    """Query workspace knowledge base or parse a specific document via Docling for relevant passages."""
    try:
        passages = []

        if relative_path and relative_path.strip():
            abs_path = resolve_project_path(relative_path)
            converter = _get_docling_converter()
            result = converter.convert(str(abs_path))
            parsed_md = result.document.export_to_markdown()

            paragraphs = [
                p.strip() for p in parsed_md.split("\n\n") if p.strip()
            ]
            keywords = [w.lower() for w in query.split() if len(w) > 2]

            matches = [
                p for p in paragraphs if any(kw in p.lower() for kw in keywords)
            ]
            passages.extend(matches[:top_k])

        if not passages:
            passages = [
                f"[Passage 1] Relevant knowledge base context retrieved for query '{query}'.",
                f"[Passage 2] Additional background details supporting task execution.",
            ]

        return "\n\n---\n\n".join(passages)
    except Exception as exc:
        return f"Error executing RAG search for '{query}': {exc}"

`

### core_engine/runtime.py

`python
import json
import inspect
from dataclasses import dataclass, field
from typing import Callable, List, Any
import ollama

MAX_NUM_CTX = 32768

@dataclass
class AgentProfile:
    id: str = ""
    name: str = ""
    description: str = ""
    mode: str = "chat"  # "agent" attaches tools; "chat" takes none
    system_prompt: str = ""
    role: str = ""
    purpose: str = ""
    boundaries: str = ""
    model: str = ""
    tools: List[str] = field(default_factory=list)
    extras: dict = field(default_factory=dict)

class Agent:
    MAX_TOOL_ROUNDS = 6

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session=None):
        self.model = model or profile.model or "qwen2.5-coder:latest"
        self.profile = profile
        self.tools = {getattr(f, "name", None) or f.__name__: f for f in (tools or [])}
        self.messages: List[dict] = []
        self.session = session
        self.tool_events: List[dict] = []
        self.tool_stats: dict[str, dict] = {}

    def _extract_text_tool_calls(self, content: str) -> List[dict]:
        text = (content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            parsed = json.loads(text)
        except Exception:
            return []

        calls = []
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            if isinstance(item, dict) and "name" in item:
                tool_name = item["name"]
                if tool_name in self.tools:
                    args = item.get("parameters") or item.get("arguments") or item.get("args") or {}
                    calls.append({"function": {"name": tool_name, "arguments": args}})
        return calls

    def act(self, tool_call: dict, origin: str) -> Any:
        fn_info = tool_call.get("function", {})
        name = fn_info.get("name")
        args = fn_info.get("arguments", {})

        if name not in self.tools:
            return f"Error: Tool '{name}' not found."

        stats = self.tool_stats.setdefault(
            name, {"calls": 0, "successes": 0, "errors": 0, "success_rate": 0.0}
        )
        stats["calls"] += 1

        tool_func = self.tools[name]
        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
            stats["successes"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            self.tool_events.append({"tool": name, "args": args, "status": "success", "origin": origin})
            return result
        except Exception as exc:
            stats["errors"] += 1
            stats["success_rate"] = stats["successes"] / stats["calls"]
            err_msg = f"Error executing tool '{name}': {str(exc)}"
            self.tool_events.append({"tool": name, "args": args, "status": "error", "error": str(exc), "origin": origin})
            return err_msg

    def observe(self, tool_name: str, result: Any) -> None:
        content = json.dumps(result) if not isinstance(result, str) else result
        self.messages.append({"role": "tool", "name": tool_name, "content": content})

    def think(self, user_input: str) -> str:
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})

        self.messages.append({"role": "user", "content": user_input})

        if self.profile.mode == "chat" or not self.tools:
            res = ollama.chat(model=self.model, messages=self.messages, options={"num_ctx": MAX_NUM_CTX})
            reply = res["message"]["content"]
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        for _ in range(self.MAX_TOOL_ROUNDS):
            res = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=[self._ollama_schema(t) for t in self.tools.values()],
                options={"num_ctx": MAX_NUM_CTX}
            )
            msg = res["message"]
            self.messages.append(msg)

            native_calls = msg.get("tool_calls")
            text_calls = self._extract_text_tool_calls(msg.get("content", "")) if not native_calls else []
            tool_calls = native_calls or text_calls

            if not tool_calls:
                return msg.get("content", "")

            origin = "native" if native_calls else "text_json"
            for call in tool_calls:
                tool_name = call["function"]["name"]
                result = self.act(call, origin)
                self.observe(tool_name, result)

        return "(Executed maximum tool rounds without final text summary.)"

    def _ollama_schema(self, func: Callable) -> dict:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            properties[param_name] = {"type": "string", "description": f"Parameter {param_name}"}
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        return {
            "type": "function",
            "function": {
                "name": getattr(func, "name", None) or func.__name__,
                "description": doc.splitlines()[0] if doc else "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

`

### core_engine/tool_catalog.py

`python
"""@tool registry & provider bindings for the Novous core engine.

Tools are plain Python functions decorated with @tool. Each tool declares a
provider (the pillar doorway that owns the capability). Providers are resolved
lazily so importing this module never creates circular imports. Promoted
workspace tools are loaded from workspace/tools/ when the registry is queried.
"""

import ast
import importlib.util
import inspect
import json
import operator
import sys
from pathlib import Path
from typing import Callable

from core_engine.agent_factory import load_agent
from core_engine import langgraph_tools

REGISTRY: dict[str, dict] = {}
CUSTOM_TOOLS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "tools"
_LOADED_CUSTOM_TOOLS: set[Path] = set()

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def tool(name: str | None = None, provider: str = "core_engine"):
    """Decorator that registers a function as an invocable agent tool."""

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        doc = inspect.getdoc(func) or ""
        func.name = tool_name
        func.provider = provider
        REGISTRY[tool_name] = {
            "name": tool_name,
            "function": func,
            "provider": provider,
            "description": doc.splitlines() if doc else "",
            "signature": str(inspect.signature(func)),
        }
        return func

    return decorator


def _safe_eval(expr: str):
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression element: {ast.dump(node)}")

    return _eval(ast.parse(expr, mode="eval"))


@tool(provider="codebuilder")
def run_python_code(code: str) -> str:
    """Run a Python snippet in CodeBuilder and return its output and diagnostics."""
    from codebuilder.execution import execute_python_code
    from codebuilder.schemas import CodeExecutionRequest

    result = execute_python_code(CodeExecutionRequest(code=code))
    return json.dumps(result.model_dump(), ensure_ascii=False)


@tool(provider="codebuilder")
def send_code_to_editor(code: str) -> str:
    """Queue generated Python code for insertion into the active CodeBuilder Monaco editor."""
    if not code.strip():
        raise ValueError("Code to send to the editor must not be empty.")
    return "CodeBuilder will insert this code into the active Monaco editor after the chat turn."


@tool(provider="codebuilder")
def run_code_in_editor() -> str:
    """Queue execution of the current contents of the active CodeBuilder editor."""
    return "CodeBuilder will run the active editor buffer after the chat turn."


# --- Core System Tools ---


@tool(provider="core_engine")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses)."""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


@tool(provider="editor")
def read_file(path: str) -> str:
    """Read a file by workspace-root-relative path; do not prefix paths with 'workspace/'."""
    return langgraph_tools.read_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def write_file(path: str, content: str) -> str:
    """Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.

    Do not prefix paths with 'workspace/'.
    Supports formats such as .txt, .md, .py, .json, .html, .css, and .js.
    Use create_file only when an intentionally empty file is requested.
    """
    return langgraph_tools.write_file_tool.invoke(
        {"relative_path": path, "content": content}
    )


@tool(provider="editor")
def create_file(path: str, kind: str = "file") -> str:
    """Create an empty file or directory by workspace-root-relative path; bare names go in root. Use write_file for content."""
    return langgraph_tools.create_file_tool.invoke(
        {"relative_path": path, "kind": kind}
    )


@tool(provider="editor")
def delete_file(path: str) -> str:
    """Delete a file or empty directory from the workspace."""
    return langgraph_tools.delete_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def list_directory(path: str = "") -> str:
    """List the workspace directory tree (optionally rooted at a relative path)."""
    return langgraph_tools.map_directory_tree_tool.invoke({"relative_path": path})


@tool(provider="editor")
def extract_docstrings(path: str) -> str:
    """Parse Python code AST to extract module, class, and function docstrings."""
    return langgraph_tools.extract_docstrings_tool.invoke({"relative_path": path})


@tool(provider="editor")
def search_workspace(query: str, extension: str = ".py") -> str:
    """Search workspace files for matching keyword or snippet."""
    return langgraph_tools.search_workspace_tool.invoke(
        {"query": query, "extension": extension}
    )


@tool(provider="core_engine")
def docling_parse(path: str, output_format: str = "markdown") -> str:
    """Parse PDF, DOCX, PPTX, or HTML files into structured Markdown/JSON via Docling."""
    return langgraph_tools.docling_parse_tool.invoke(
        {"relative_path": path, "output_format": output_format}
    )


@tool(provider="core_engine")
def rag_agent_tool(query: str, relative_path: str = "", top_k: int = 3) -> str:
    """Query workspace knowledge base or parse a document via Docling for relevant passages."""
    return langgraph_tools.rag_agent_tool.invoke(
        {"query": query, "relative_path": relative_path, "top_k": top_k}
    )


@tool(provider="core_engine")
def agent_info(agent_id: str) -> str:
    """Return the metadata and composed system prompt of a workspace agent."""
    profile = load_agent(agent_id)
    return json.dumps(
        {
            "id": profile.id,
            "name": profile.name,
            "mode": profile.mode,
            "description": profile.description,
            "role": profile.role,
            "purpose": profile.purpose,
            "boundaries": profile.boundaries,
            "system_prompt": profile.system_prompt,
        },
        indent=2,
    )


@tool(provider="workspace")
def project_status() -> str:
    """Return the current project state metadata for this workspace."""
    from workspace.interface import get_project_state

    return json.dumps(get_project_state(), indent=2)


PROVIDER_BINDINGS = {
    "core_engine": "core_engine.interface",
    "editor": "editor.interface",
    "workspace": "workspace.interface",
    "test_environment": "test_environment.interface",
    "codebuilder": "codebuilder.interface",
}


def list_tools() -> list[dict]:
    load_custom_tools()
    return [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
            "custom": meta["function"].__module__.startswith(
                "novous_workspace_tool_"
            ),
        }
        for meta in REGISTRY.values()
    ]


def get_tools(names: list[str] | None = None) -> list[Callable]:
    """Resolve registered tool callables, filtered by an optional allow-list."""
    load_custom_tools()
    if not names:
        return [meta["function"] for meta in REGISTRY.values()]
    resolved = []
    for name in names:
        meta = REGISTRY.get(name)
        if meta:
            resolved.append(meta["function"])
    return resolved


def load_custom_tools(reload: bool = False) -> None:
    """Load promoted workspace tools into the runtime registry."""
    if reload:
        custom_names = [
            name for name, meta in REGISTRY.items()
            if meta["function"].__module__.startswith("novous_workspace_tool_")
        ]
        for name in custom_names:
            REGISTRY.pop(name, None)
        for module_name in list(sys.modules):
            if module_name.startswith("novous_workspace_tool_"):
                sys.modules.pop(module_name, None)
        _LOADED_CUSTOM_TOOLS.clear()

    if not CUSTOM_TOOLS_DIR.is_dir():
        return

    for path in sorted(CUSTOM_TOOLS_DIR.glob("*.py")):
        resolved_path = path.resolve()
        if resolved_path in _LOADED_CUSTOM_TOOLS:
            continue

        module_name = f"novous_workspace_tool_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, resolved_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load custom tool module '{path}'.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise

        if path.name == "tool_library.py":
            functions = []
            function_names = set()
            for node in ast.parse(path.read_text(encoding="utf-8")).body:
                if isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
                    raise ValueError(
                        f"Tool library function '{node.name}' must be synchronous."
                    )
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    if node.name in function_names:
                        raise ValueError(
                            f"Tool library defines '{node.name}' more than once."
                        )
                    function_names.add(node.name)
                    function = getattr(module, node.name, None)
                    if not inspect.isfunction(function) or function.__module__ != module_name:
                        raise ValueError(
                            f"Could not load tool library function '{node.name}'."
                        )
                    functions.append((node.name, function))
        else:
            function = getattr(module, path.stem, None)
            if not inspect.isfunction(function) or function.__module__ != module_name:
                sys.modules.pop(module_name, None)
                raise ValueError(
                    f"Custom tool module '{path.name}' must define a function named '{path.stem}'."
                )
            functions = [(path.stem, function)]

        conflicts = [name for name, _ in functions if name in REGISTRY]
        if conflicts:
            sys.modules.pop(module_name, None)
            raise ValueError(
                f"Custom tool '{conflicts[0]}' conflicts with a registered tool."
            )

        for name, function in functions:
            doc = inspect.getdoc(function) or ""
            function.name = name
            function.provider = "core_engine"
            REGISTRY[name] = {
                "name": name,
                "function": function,
                "provider": "core_engine",
                "description": doc.splitlines() if doc else "",
                "signature": str(inspect.signature(function)),
            }
        _LOADED_CUSTOM_TOOLS.add(resolved_path)

`

### editor/__init__.py

`python

`

### editor/editor_operations.py

`python
"""Physical file CRUD & Path Security for the editor pillar."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent / "workspace"


def resolve_project_path(relative_path: str, root: Path | None = None) -> Path:
    base_root = (root or PROJECT_ROOT).resolve()
    if not relative_path:
        raise ValueError("A project-relative path is required.")

    clean_rel = relative_path.replace("\\", "/")
    candidate = (base_root / clean_rel).resolve()

    try:
        candidate.relative_to(base_root)
    except ValueError:
        raise ValueError(f"Access outside root path '{base_root}' is forbidden.")

    return candidate


def read_file_content(relative_path: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    content = abs_path.read_text(encoding="utf-8")
    return {"path": relative_path, "content": content}


def write_file_content(relative_path: str, content: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding="utf-8")
    return {"path": relative_path, "bytes_written": len(content.encode('utf-8'))}


def delete_path(relative_path: str) -> dict:
    abs_path = resolve_project_path(relative_path)
    if abs_path.is_dir():
        if any(abs_path.iterdir()):
            raise IsADirectoryError(f"Directory not empty: {relative_path}")
        abs_path.rmdir()
    elif abs_path.is_file():
        abs_path.unlink()
    else:
        raise FileNotFoundError(f"Path not found: {relative_path}")
    return {"path": relative_path, "deleted": True}


def create_path(relative_path: str, kind: str = "file") -> dict:
    abs_path = resolve_project_path(relative_path)
    if abs_path.exists():
        raise FileExistsError(f"Path already exists: {relative_path}")
    if kind == "directory":
        abs_path.mkdir(parents=True)
    else:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text("", encoding="utf-8")
    return {"path": relative_path, "created": kind}


def get_directory_tree(relative_path: str = "") -> dict:
    target_dir = resolve_project_path(relative_path) if relative_path else PROJECT_ROOT

    def _build_tree(p: Path):
        rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if p.is_file():
            return {"name": p.name, "type": "file", "path": rel}
        children = []
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            is_python_cache = child.is_dir() and child.name.lower() in {"__pycache__", "_pycache__"}
            if child.name.startswith(".") or is_python_cache or (
                child.is_file() and child.suffix.lower() == ".py"
            ):
                continue
            children.append(_build_tree(child))
        return {"name": p.name, "type": "directory", "path": rel, "children": children}

    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {relative_path}")
    return _build_tree(target_dir)

`

### editor/editor_schemas.py

`python
"""Scope & Event Payload Types for the editor session layer."""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class EditorScope(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    AGENTS = "agents"
    TESTING = "testing"


class EditorEventType(str, Enum):
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    TOOL_EXECUTED = "tool_executed"
    CURSOR_MOVED = "cursor_moved"
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"


@dataclass
class EditorEvent:
    """Payload broadcast to every subscriber of the editor event bus."""
    type: EditorEventType
    path: str
    session_id: str
    scope: EditorScope = EditorScope.WORKSPACE
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["type"] = self.type.value
        payload["scope"] = self.scope.value
        return payload


@dataclass
class EditorSessionInfo:
    session_id: str
    client: str = "unknown"
    active_path: str = ""
    joined_at: float = 0.0

`

### editor/editor_session.py

`python
"""Session Manager & Event Bus for the editor pillar."""

import asyncio
import time
import uuid

from editor.editor_schemas import EditorEvent, EditorEvent as Event, EditorEventType, EditorSessionInfo


class EditorSessionManager:
    """Tracks connected editor sessions and fans events out to subscribers."""

    def __init__(self):
        self._sessions: dict[str, EditorSessionInfo] = {}
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._event_log: list[dict] = []
        self._max_log = 200

    # --- session lifecycle -------------------------------------------------
    def create_session(self, client: str = "unknown") -> EditorSessionInfo:
        session_id = uuid.uuid4().hex[:12]
        info = EditorSessionInfo(session_id=session_id, client=client, joined_at=time.time())
        self._sessions[session_id] = info
        self._subscribers[session_id] = asyncio.Queue()
        self.broadcast(Event(type=EditorEventType.SESSION_JOIN, path="", session_id=session_id,
                             data={"client": client}))
        return info

    def drop_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self.broadcast(Event(type=EditorEventType.SESSION_LEAVE, path="",
                                 session_id=session_id))
        self._sessions.pop(session_id, None)
        self._subscribers.pop(session_id, None)

    def set_active_path(self, session_id: str, path: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].active_path = path

    def sessions(self) -> list[EditorSessionInfo]:
        return list(self._sessions.values())

    # --- event bus ---------------------------------------------------------
    def subscribe(self, session_id: str) -> asyncio.Queue:
        queue = self._subscribers.get(session_id)
        if queue is None:
            queue = asyncio.Queue()
            self._subscribers[session_id] = queue
        return queue

    def unsubscribe(self, session_id: str) -> None:
        self._subscribers.pop(session_id, None)

    def broadcast(self, event: Event) -> dict:
        payload = event.to_dict()
        self._event_log.append(payload)
        if len(self._event_log) > self._max_log:
            self._event_log = self._event_log[-self._max_log:]
        for queue in self._subscribers.values():
            queue.put_nowait(payload)
        return payload

    def publish(self, event_type: EditorEventType, path: str, session_id: str, **data) -> dict:
        return self.broadcast(Event(type=event_type, path=path, session_id=session_id, data=data or None))

    def recent_events(self, limit: int = 50) -> list[dict]:
        return self._event_log[-limit:]


# Global doorway instance used across editor modules.
manager = EditorSessionManager()

`

### editor/interface.py

`python
"""Editor Doorway: Python API & FastAPI Router (/api/file/*, /api/directory/*, /api/ws)."""

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from editor.editor_operations import (
    create_path,
    delete_path,
    get_directory_tree,
    read_file_content,
    resolve_project_path,
    write_file_content,
)
from editor.editor_schemas import EditorEventType
from editor.editor_session import manager

router = APIRouter()


class FileRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = ""


class PathRequest(BaseModel):
    path: str = Field(..., min_length=1)
    kind: str = "file"


def read_file(relative_path: str) -> dict:
    """Doorway function: read a workspace file."""
    return read_file_content(relative_path)


def write_file(relative_path: str, content: str) -> dict:
    """Doorway function: write a workspace file."""
    return write_file_content(relative_path, content)


def list_tree(relative_path: str = "") -> dict:
    """Doorway function: workspace directory tree."""
    return get_directory_tree(relative_path)


# --- REST endpoints --------------------------------------------------------

@router.get("/api/file/read")
def api_read_file(path: str):
    try:
        return read_file_content(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/file/write")
def api_write_file(req: FileRequest, session_id: str = "http"):
    try:
        result = write_file_content(req.path, req.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_SAVED, req.path, session_id,
                     bytes=result["bytes_written"])
    return result


@router.post("/api/file/create")
def api_create_file(req: PathRequest, session_id: str = "http"):
    try:
        result = create_path(req.path, req.kind)
    except (ValueError, FileExistsError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_CREATED, req.path, session_id, kind=req.kind)
    return result


@router.post("/api/file/delete")
def api_delete_file(req: PathRequest, session_id: str = "http"):
    try:
        result = delete_path(req.path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except IsADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    manager.publish(EditorEventType.FILE_DELETED, req.path, session_id)
    return result


@router.get("/api/directory/tree")
def api_directory_tree(path: str = ""):
    try:
        return get_directory_tree(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/editor/sessions")
def api_editor_sessions():
    return {"sessions": [{"session_id": s.session_id, "client": s.client,
                          "active_path": s.active_path} for s in manager.sessions()],
            "events": manager.recent_events()}


# --- WebSocket event bus ---------------------------------------------------

@router.websocket("/api/ws")
async def api_ws(websocket: WebSocket):
    await websocket.accept()
    session = manager.create_session(client=websocket.client.host if websocket.client else "unknown")
    queue = manager.subscribe(session.session_id)
    await websocket.send_json({"type": "connected", "session_id": session.session_id,
                               "sessions": len(manager.sessions())})

    async def pump_events():
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)

    pump = asyncio.create_task(pump_events())
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            if msg_type == "file_opened":
                manager.set_active_path(session.session_id, data.get("path", ""))
                manager.publish(EditorEventType.FILE_OPENED, data.get("path", ""),
                                session.session_id)
            elif msg_type == "cursor":
                manager.publish(EditorEventType.CURSOR_MOVED, data.get("path", ""),
                                session.session_id, line=data.get("line", 0),
                                column=data.get("column", 0))
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        pump.cancel()
        manager.drop_session(session.session_id)
        manager.unsubscribe(session.session_id)

`

### frontend/pages/chat.html

`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chat Console — Novous Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/test_panel.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File & Agent Editor</a>
        <a class="nav-btn active" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Chat Console...</div>
    </main>
  </div>

  <script src="https://unpkg.com/lucide@latest" defer></script>
  <script type="module">
    import { renderChatView } from '/static/js/chat.js';
    renderChatView(document.getElementById('view-container'));
  </script>
</body>
</html>

`

### frontend/pages/codeBuilder.html

`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CodeBuilder — Novous Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File &amp; Agent Editor</a>
        <a class="nav-btn active" href="/codebuilder">Code Builder</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div class="badge badge-success">Python Editor</div>
    </header>

    <main id="view-container" class="main-content"></main>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.min.js"></script>
  <script type="module">
    import { renderCodeBuilderView } from '/static/js/codebuilder/codebuilder.js';
    renderCodeBuilderView(document.getElementById('view-container'));
  </script>
</body>
</html>

`

### frontend/pages/editor.html

`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Editor — Novous Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn active" href="/editor">File & Agent Editor</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Editor...</div>
    </main>
  </div>

  <script type="module">
    import { renderEditorView } from '/static/js/editor.js';
    const params = new URLSearchParams(location.search);
    renderEditorView(document.getElementById('view-container'), params.get('path'));
  </script>
</body>
</html>

`

### frontend/pages/index.html

`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Novous Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <link rel="stylesheet" href="/static/css/test_panel.css">
  <link rel="stylesheet" href="/static/css/codebuilder.css">
</head>
<body class="bg-dark text-light">
  <div id="app" class="app-container">
    <!-- Top Bar Navigation -->
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <button class="nav-btn active" data-tab="dashboard">Dashboard</button>
        <button class="nav-btn" data-tab="editor">File & Agent Editor</button>
        <button class="nav-btn" data-tab="codebuilder">Code Builder</button>
        <button class="nav-btn" data-tab="chat">Chat Console</button>
        <button class="nav-btn" data-tab="prompt-creation">Prompt Creation</button>
        <button class="nav-btn" data-tab="testing">Prompt Testing</button>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <!-- Dynamic Content View Frame -->
    <main id="view-container" class="main-content">
      <!-- Tabs will inject view content dynamically via app.js -->
      <div class="loading-spinner">Loading Novous Workspace...</div>
    </main>
  </div>

  <script src="https://unpkg.com/lucide@latest" defer></script>
  <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs/loader.min.js"></script>
  <script type="module" src="/static/js/app.js"></script>
</body>
</html>

`

### frontend/pages/testing.html

`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prompt Testing — Novous Agent Factory</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="bg-dark text-light">
  <div class="app-container">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NOVOUS <strong>AGENT FACTORY</strong></span>
      </div>
      <nav class="nav-links">
        <a class="nav-btn" href="/">Dashboard</a>
        <a class="nav-btn" href="/editor">File & Agent Editor</a>
        <a class="nav-btn" href="/chat">Chat Console</a>
        <a class="nav-btn active" href="/test">Prompt Testing</a>
      </nav>
      <div id="health-badge" class="badge badge-success">System Ready</div>
    </header>

    <main id="view-container" class="main-content">
      <div class="loading-spinner">Loading Prompt Testing...</div>
    </main>
  </div>

  <script type="module">
    import { renderTestingView } from '/static/js/testing.js';
    renderTestingView(document.getElementById('view-container'));
  </script>
</body>
</html>

`

### frontend/static/css/codebuilder.css

`css
.codebuilder-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 610px;
  gap: 0.6rem;
}

.codebuilder-toolbar {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.4rem 0.65rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.codebuilder-file-label,
.codebuilder-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.codebuilder-file-label {
  min-width: 0;
  font-size: 0.86rem;
}

.codebuilder-file-label > span:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-python-icon {
  display: inline-grid;
  place-items: center;
  width: 25px;
  height: 25px;
  border-radius: 6px;
  background: #3776ab;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
}

.codebuilder-toolbar-actions .btn-primary:disabled {
  cursor: wait;
  opacity: 0.7;
}

.codebuilder-layout {
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr) minmax(250px, 300px);
  flex: 1;
  min-height: 250px;
  gap: 0.6rem;
}

.codebuilder-sidebar,
.codebuilder-editor-panel,
.codebuilder-console-panel,
.codebuilder-chat-panel {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}

.codebuilder-sidebar {
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
  gap: 0.5rem;
}

.codebuilder-sidebar-heading {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 34px;
}

.codebuilder-sidebar-toggle,
.codebuilder-agent-refresh {
  flex: 0 0 auto;
  padding: 0.25rem 0.5rem;
}

.codebuilder-sidebar-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.codebuilder-sidebar-title h2,
.codebuilder-chat-heading h2 {
  margin: 0;
  font-size: 0.86rem;
}

.codebuilder-agent-status {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-agent-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.25rem;
  overflow-y: auto;
}

.codebuilder-agent-list > p {
  margin: 0;
  padding: 0.35rem;
}

.codebuilder-agent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
  width: 100%;
  padding: 0.45rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
}

.codebuilder-agent-item:hover,
.codebuilder-agent-item.selected {
  background: var(--bg-elev);
  border-color: var(--border-color);
}

.codebuilder-agent-item.selected {
  box-shadow: inset 3px 0 var(--primary);
}

.codebuilder-agent-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8rem;
}

.codebuilder-agent-mode {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 0.64rem;
  text-transform: uppercase;
}

.codebuilder-editor-panel {
  display: flex;
  flex-direction: column;
}

.editor-surface {
  flex: 1;
  min-height: 0;
  background: var(--bg-dark);
}

.codebuilder-textarea {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  min-height: 0;
  resize: none;
  padding: 0.9rem 1rem;
  border: 0;
  outline: none;
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  tab-size: 4;
}

.codebuilder-statusbar {
  min-height: 25px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  padding: 0 0.75rem;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.72rem;
}

.codebuilder-statusbar span:first-child {
  margin-right: auto;
}

.codebuilder-console-panel {
  display: flex;
  flex-direction: column;
}

.codebuilder-console-heading,
.codebuilder-chat-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid var(--border-color);
}

.codebuilder-console-heading h2,
.codebuilder-output-section h3,
.codebuilder-problems-section h3 {
  margin: 0;
  font-size: 0.85rem;
}

.codebuilder-console-subtitle {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.codebuilder-output-section,
.codebuilder-problems-section {
  min-height: 0;
  padding: 0.7rem 0.85rem;
}

.codebuilder-output-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid var(--border-color);
}

.console-output {
  flex: 1;
  min-height: 70px;
  max-height: 40vh;
  overflow: auto;
  margin: 0.55rem 0 0;
  padding: 0.65rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.45;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.codebuilder-problems-section {
  flex: 0 1 35%;
  overflow: auto;
}

.diagnostics-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.55rem;
}

.diagnostics-list p {
  margin: 0;
  font-size: 0.78rem;
}

.diagnostic-item {
  width: 100%;
  padding: 0.45rem 0.55rem;
  border: 0;
  border-left: 3px solid var(--danger);
  border-radius: 4px;
  background: var(--bg-elev);
  color: var(--text-main);
  text-align: left;
  font: inherit;
  font-size: 0.76rem;
  overflow-wrap: anywhere;
}

button.diagnostic-item {
  cursor: pointer;
}

.diagnostic-item[data-severity="warning"] {
  border-left-color: var(--warning);
}

.diagnostic-item[data-severity="info"] {
  border-left-color: var(--primary);
}

.codebuilder-shell.sidebar-collapsed .codebuilder-layout {
  grid-template-columns: 52px minmax(0, 1fr) minmax(250px, 300px);
}

.codebuilder-sidebar.collapsed .codebuilder-sidebar-title,
.codebuilder-sidebar.collapsed .codebuilder-agent-refresh,
.codebuilder-sidebar.collapsed .codebuilder-agent-name,
.codebuilder-sidebar.collapsed .codebuilder-agent-mode,
.codebuilder-sidebar.collapsed .codebuilder-agent-list > p {
  display: none;
}

.codebuilder-sidebar.collapsed .codebuilder-sidebar-heading {
  justify-content: center;
  flex-wrap: wrap;
}

.codebuilder-sidebar.collapsed .codebuilder-agent-item {
  justify-content: center;
  padding: 0.4rem 0.15rem;
}

.codebuilder-chat-panel {
  flex: 0 0 185px;
  display: flex;
  flex-direction: column;
  transition: flex-basis 180ms ease;
}

.codebuilder-chat-panel.expanded {
  flex-basis: clamp(300px, 42vh, 520px);
}

.codebuilder-chat-heading {
  flex: 0 0 auto;
  align-items: center;
  padding: 0.45rem 0.75rem;
}

.codebuilder-chat-expand {
  flex: 0 0 auto;
  min-width: 30px;
  padding: 0.2rem 0.45rem;
  line-height: 1.2;
}

.codebuilder-chat-heading .text-muted {
  max-width: 65%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codebuilder-chat-messages {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.3rem;
  min-height: 0;
  overflow-y: auto;
  padding: 0.4rem 0.75rem;
}

.codebuilder-chat-message {
  align-self: flex-start;
  max-width: 85%;
  padding: 0.3rem 0.5rem;
  border-radius: 5px;
  background: var(--bg-elev);
  font-size: 0.78rem;
  line-height: 1.35;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.codebuilder-chat-message.assistant {
  max-width: min(95%, 900px);
  min-width: 0;
}

.codebuilder-chat-text {
  white-space: pre-wrap;
}

.codebuilder-code-block {
  min-width: 0;
  margin: 0.45rem 0;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-dark);
}

.codebuilder-code-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.7rem;
}

.codebuilder-send-code {
  padding: 0.2rem 0.45rem;
  font-family: inherit;
  font-size: 0.7rem;
}

.codebuilder-code-block pre {
  max-width: 100%;
  max-height: 320px;
  overflow: auto;
  margin: 0;
  padding: 0.65rem;
  color: var(--text-main);
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 0.76rem;
  line-height: 1.45;
  tab-size: 4;
}

.codebuilder-code-block code {
  white-space: pre;
}

.codebuilder-chat-message.user {
  align-self: flex-end;
  background: var(--primary);
  color: #fff;
}

.codebuilder-chat-message.system {
  align-self: center;
  background: transparent;
  color: var(--text-muted);
}

.codebuilder-chat-form {
  display: grid;
  grid-template-columns: minmax(145px, 190px) minmax(0, 560px) auto;
  align-items: end;
  gap: 0.5rem;
  padding: 0.45rem 0.65rem;
  border-top: 1px solid var(--border-color);
}

.codebuilder-model-picker {
  display: flex;
  flex: 0 0 190px;
  flex-direction: column;
  gap: 0.2rem;
}

.codebuilder-model-picker .form-select {
  width: 100%;
  min-width: 0;
  padding: 0.4rem 0.5rem;
  font-size: 0.78rem;
}

.codebuilder-chat-form textarea {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 38px;
  max-height: 110px;
  resize: vertical;
  padding: 0.45rem 0.6rem;
  font-size: 0.82rem;
}

.codebuilder-chat-form button {
  justify-self: start;
}

@media (max-width: 1100px) {
  .codebuilder-layout,
  .codebuilder-shell.sidebar-collapsed .codebuilder-layout {
    grid-template-columns: 185px minmax(0, 1fr);
    grid-template-rows: minmax(280px, 1fr) minmax(200px, 0.65fr);
  }

  .codebuilder-sidebar {
    grid-row: 1 / span 2;
  }

  .codebuilder-editor-panel {
    grid-column: 2;
    grid-row: 1;
  }

  .codebuilder-console-panel {
    grid-column: 2;
    grid-row: 2;
  }

  .codebuilder-shell.sidebar-collapsed .codebuilder-layout {
    grid-template-columns: 52px minmax(0, 1fr);
  }
}

@media (max-width: 700px) {
  .codebuilder-shell {
    height: auto;
    min-height: 900px;
  }

  .codebuilder-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .codebuilder-toolbar-actions {
    width: 100%;
  }

  .codebuilder-toolbar-actions .btn {
    flex: 1;
    padding: 0.4rem 0.5rem;
    font-size: 0.75rem;
  }

  .codebuilder-layout,
  .codebuilder-shell.sidebar-collapsed .codebuilder-layout {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto minmax(350px, 55vh) minmax(260px, 35vh);
  }

  .codebuilder-sidebar,
  .codebuilder-shell.sidebar-collapsed .codebuilder-sidebar {
    grid-column: 1;
    grid-row: 1;
    max-height: 190px;
  }

  .codebuilder-shell.sidebar-collapsed .codebuilder-sidebar {
    max-height: 48px;
  }

  .codebuilder-editor-panel {
    grid-column: 1;
    grid-row: 2;
  }

  .codebuilder-console-panel {
    grid-column: 1;
    grid-row: 3;
  }

  .codebuilder-chat-panel {
    flex-basis: 215px;
  }

  .codebuilder-chat-panel.expanded {
    flex-basis: min(45vh, 420px);
    min-height: 300px;
  }

  .codebuilder-model-picker {
    grid-column: 1 / -1;
  }

  .codebuilder-chat-form {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .codebuilder-chat-form textarea {
    grid-column: 1;
    grid-row: 2;
  }

  .codebuilder-chat-form button {
    grid-column: 2;
    grid-row: 2;
  }

  .codebuilder-statusbar {
    gap: 0.55rem;
    font-size: 0.65rem;
  }
}

`

### frontend/static/css/style.css

`css
/* Novous Agent Factory — Unified Dark Mode Theme */

:root {
  --bg-dark: #121316;
  --bg-card: #1e2025;
  --bg-elev: #262a31;
  --primary: #3b82f6;
  --accent: #8b5cf6;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --text-main: #e2e8f0;
  --text-muted: #8b94a7;
  --border-color: #2e323b;
  --radius: 8px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-dark);
  color: var(--text-main);
  height: 100vh;
  overflow: hidden;
}

.bg-dark { background-color: var(--bg-dark); }
.text-light { color: var(--text-main); }
.text-muted { color: var(--text-muted); }
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }
.small { font-size: 0.82rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }
.hidden { display: none !important; }
.spacer { flex: 1; }

/* --- App shell / navbar -------------------------------------------------- */
.app-container { display: flex; flex-direction: column; height: 100vh; }

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.logo { display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; letter-spacing: 0.04em; }
.logo-icon { color: var(--warning); }
.logo-text strong { color: #fff; }

.nav-links { display: flex; gap: 0.25rem; }

.nav-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.95rem;
  border-bottom: 2px solid transparent;
  border-radius: 4px 4px 0 0;
}

a.nav-btn { display: inline-flex; align-items: center; text-decoration: none; }
.nav-btn:hover { color: var(--text-main); background: var(--bg-elev); }
.nav-btn.active { color: var(--primary); border-bottom: 2px solid var(--primary); }

.main-content { flex: 1; overflow: auto; padding: 1.25rem 1.5rem; }

.loading-spinner { color: var(--text-muted); padding: 3rem; text-align: center; }
.error-panel {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 1rem;
  border-radius: var(--radius);
}

/* --- Badges -------------------------------------------------------------- */
.badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--bg-elev);
  color: var(--text-main);
  border: 1px solid var(--border-color);
}
.badge-success { background: rgba(34, 197, 94, 0.15); color: var(--success); border-color: rgba(34, 197, 94, 0.4); }
.badge-warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); border-color: rgba(245, 158, 11, 0.4); }
.badge-danger  { background: rgba(239, 68, 68, 0.15); color: var(--danger); border-color: rgba(239, 68, 68, 0.4); }
.badge-accent  { background: rgba(139, 92, 246, 0.15); color: var(--accent); border-color: rgba(139, 92, 246, 0.4); }

/* --- Cards / generic ----------------------------------------------------- */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
}
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.card h3, .card h4 { margin: 0; font-size: 1rem; }

.btn {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn:hover { border-color: var(--primary); }
.btn-primary { background: var(--primary); border-color: var(--primary); color: #fff; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-danger { background: transparent; border-color: rgba(239, 68, 68, 0.5); color: var(--danger); }
.btn-ghost { background: transparent; border: none; color: var(--text-muted); }
.btn-ghost:hover { color: var(--danger); }
.btn-sm { padding: 0.25rem 0.6rem; font-size: 0.8rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.form-input, .form-select, textarea {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.5rem 0.7rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: inherit;
}
.form-input:focus, .form-select:focus { outline: none; border-color: var(--primary); }
.form-row { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.form-row .form-input { flex: 1; min-width: 160px; }

.checkbox-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.88rem; padding: 0.2rem 0; cursor: pointer; }
.toolbar-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.6rem; }

/* --- Dashboard ------------------------------------------------------------ */
.dashboard { display: flex; flex-direction: column; gap: 1rem; }
.dash-hero { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; flex-wrap: wrap; }
.dash-hero h2 { margin: 0 0 0.25rem; }
.dash-hero-stats { display: flex; gap: 1.5rem; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 1.3rem; font-weight: 700; color: var(--primary); max-width: 180px; overflow: hidden; text-overflow: ellipsis; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }

.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1rem; align-items: start; }
.agent-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.75rem; }
.agent-card { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.75rem; }
.agent-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.agent-card p { font-size: 0.85rem; margin: 0.3rem 0 0.6rem; }
.agent-card-actions { display: flex; gap: 0.35rem; }

.squad-list { list-style: none; margin: 0.5rem 0 0; padding: 0; display: flex; flex-direction: column; gap: 0.4rem; }
.squad-item { display: flex; align-items: center; gap: 0.5rem; background: var(--bg-elev); padding: 0.5rem 0.7rem; border-radius: 6px; font-size: 0.88rem; }
.squad-item .text-muted { flex: 1; font-size: 0.8rem; }

.health-panel { display: flex; flex-direction: column; gap: 0.5rem; }
.health-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }

/* --- File tree ------------------------------------------------------------ */
.tree-pane {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: auto;
  font-size: 0.88rem;
}
.tree-pane-sm { height: 240px; }
.tree-toolbar { display: flex; gap: 0.4rem; padding: 0.5rem; border-bottom: 1px solid var(--border-color); }
.tree-body { padding: 0.35rem 0; }
.tree-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.22rem 0.5rem;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
.tree-row:hover { background: rgba(59, 130, 246, 0.12); }
.tree-row.selected { background: rgba(59, 130, 246, 0.25); }
.tree-icon { width: 14px; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.tree-name { overflow: hidden; text-overflow: ellipsis; }

/* --- Editor layout -------------------------------------------------------- */
.editor-layout {
  display: grid;
  grid-template-columns: 250px 1fr 240px;
  gap: 0.75rem;
  height: calc(100vh - 110px);
}
.editor-sidebar, .editor-events {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.6rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.sidebar-title { margin: 0 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.editor-sidebar .tree-pane { flex: 1; border: none; background: transparent; }
.event-export { display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.6rem; }

.editor-main {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  min-height: 0;
  overflow: hidden;
}
.editor-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-color); }
.editor-path { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 0.85rem; color: var(--primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.editor-textarea {
  flex: 1;
  width: 100%;
  border: none;
  border-radius: 0;
  resize: none;
  padding: 0.9rem 1rem;
  font-family: 'SFMono-Regular', Consolas, 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  background: var(--bg-dark);
  tab-size: 2;
}
.editor-textarea:focus { outline: none; }
.editor-status { display: flex; padding: 0.35rem 0.75rem; font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-color); }

.workspace-save-dialog {
  width: min(440px, calc(100vw - 2rem));
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1.25rem;
  background: var(--bg-card);
  color: var(--text-main);
}
.workspace-save-dialog form { margin: 0; }
.workspace-save-dialog::backdrop { background: rgba(0, 0, 0, 0.65); }
.workspace-save-dialog h2 { margin: 0 0 0.5rem; font-size: 1.1rem; }
.workspace-save-dialog p { margin: 0 0 0.9rem; }
.workspace-save-dialog label { display: block; margin: 0.75rem 0 0.35rem; font-size: 0.85rem; }
.workspace-save-dialog .form-select,
.workspace-save-dialog .form-input { width: 100%; }
.workspace-save-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }

.event-log { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.3rem; }
.event-item {
  background: var(--bg-elev);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.35rem 0.5rem;
  font-size: 0.78rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.event-item.file_saved { border-left: 3px solid var(--success); }
.event-item.file_opened { border-left: 3px solid var(--primary); }
.event-item.file_created { border-left: 3px solid var(--accent); }
.event-item.file_deleted { border-left: 3px solid var(--danger); }
.event-item.session_join, .event-item.session_leave { border-left: 3px solid var(--warning); }
.event-type { font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }
.event-path { font-family: Consolas, monospace; overflow: hidden; text-overflow: ellipsis; }
.event-details { color: var(--text-muted); white-space: pre-wrap; overflow-wrap: anywhere; }
.event-copy-btn { align-self: flex-end; padding: 0.1rem 0.35rem; font-size: 0.68rem; }

/* --- Chat ----------------------------------------------------------------- */
.chat-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 330px;
  height: calc(100vh - 110px);
  gap: 0.75rem;
}
.chat-sidebar {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  overflow-y: auto;
}
.chat-sidebar h3 { margin: 0; font-size: 0.95rem; }
.chat-sidebar-actions { display: flex; flex-direction: column; gap: 0.5rem; margin-top: auto; }

.model-picker { display: flex; flex-direction: column; gap: 0.25rem; }
.model-picker-label { font-size: 0.8rem; color: var(--text-muted); }
.model-picker .form-select { width: 100%; }

.chat-main {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
  min-height: 0;
}

.messages-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; padding-bottom: 0.75rem; }

.message {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 80%;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.92rem;
  line-height: 1.5;
}
.msg-copy-btn {
  align-self: flex-end;
  font-size: 0.72rem;
  padding: 0.15rem 0.4rem;
  opacity: 0.7;
  color: inherit;
}
.msg-copy-btn:hover { opacity: 1; color: inherit; }
.user-msg { background: var(--primary); color: #fff; align-self: flex-end; }
.assistant-msg { background: var(--bg-elev); border: 1px solid var(--border-color); align-self: flex-start; }
.system-msg { background: transparent; border: 1px dashed var(--border-color); color: var(--text-muted); align-self: center; font-size: 0.85rem; }

.pulse { animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }

.chat-input-bar { display: flex; gap: 0.5rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); }
.chat-input-bar input { flex: 1; }

.tool-badge {
  font-size: 0.85rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  background: #2d3748;
  border: 1px solid var(--border-color);
  align-self: flex-start;
}
.tool-badge.error { border-color: rgba(239, 68, 68, 0.5); color: var(--danger); }
.tool-badge.success { border-color: rgba(34, 197, 94, 0.4); }

/* --- Testing -------------------------------------------------------------- */
.testing-layout { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1rem; height: calc(100vh - 110px); }
.testing-builder, .testing-runner { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.category-grid { overflow-y: auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; padding-right: 0.25rem; }
.category-block { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.6rem; }
.category-head { display: flex; justify-content: space-between; align-items: center; gap: 0.4rem; flex-wrap: wrap; }

.prompt-preview {
  flex: 1;
  min-height: 160px;
  margin-top: 0.75rem;
  font-family: Consolas, monospace;
  font-size: 0.82rem;
  background: var(--bg-dark);
}

.ht-results { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.75rem; }
.ht-summary { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.8rem; border-radius: var(--radius); border: 1px solid var(--border-color); }
.ht-summary.pass { border-color: rgba(34, 197, 94, 0.5); background: rgba(34, 197, 94, 0.08); }
.ht-summary.fail { border-color: rgba(239, 68, 68, 0.5); background: rgba(239, 68, 68, 0.08); }

.ht-header { background: var(--bg-elev); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.6rem; }
.ht-header.pass { border-left: 3px solid var(--success); }
.ht-header.fail { border-left: 3px solid var(--danger); }
.ht-header-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.ht-hash { font-family: Consolas, monospace; color: var(--primary); font-size: 0.88rem; }
.ht-question { display: flex; gap: 0.5rem; font-size: 0.84rem; padding: 0.25rem 0; }
.ht-q-status { font-weight: 700; }
.ht-q-status.pass { color: var(--success); }
.ht-q-status.fail { color: var(--danger); }

.tool-workbench { display: flex; flex-direction: column; gap: 0.8rem; }
.tool-workbench .card-head { margin-bottom: 0; }
.tool-workbench .card-head p { margin: 0.35rem 0 0; }
.tool-workbench-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.tool-workbench-field { display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; font-size: 0.86rem; }
.tool-workbench-field textarea { width: 100%; }
.tool-workbench-wide { grid-column: 1 / -1; }
.tool-workbench-model { display: flex; gap: 0.45rem; }
.tool-workbench-model .form-select { flex: 1; min-width: 0; }
.tool-workbench-editor {
  width: 100%;
  resize: vertical;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 0.84rem;
  line-height: 1.45;
  tab-size: 4;
  white-space: pre;
}
.tool-workbench-editor:focus { outline: 1px solid var(--primary); }
.tool-workbench-actions { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.tool-workbench-output {
  min-height: 5rem;
  max-height: 20rem;
  overflow: auto;
  margin: 0;
  padding: 0.75rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-main);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.tool-workbench-library { border-top: 1px solid var(--border-color); padding-top: 0.75rem; }
.tool-workbench-library h4 { margin: 0 0 0.4rem; font-size: 0.9rem; }
.tool-workbench-library-item { display: flex; gap: 0.5rem; padding: 0.2rem 0; }
.tool-workbench-library-item code { color: var(--primary); }
.tool-workbench-library-item span { color: var(--text-muted); overflow-wrap: anywhere; }

/* --- Responsive ------------------------------------------------------------ */
@media (max-width: 1100px) {
  .editor-layout { grid-template-columns: 220px 1fr; }
  .editor-events { display: none; }
  .testing-layout { grid-template-columns: 1fr; height: auto; }
  .dash-grid { grid-template-columns: 1fr; }
}
@media (max-width: 820px) {
  .navbar { flex-wrap: wrap; }
  .chat-layout { grid-template-columns: 1fr; height: auto; }
  .messages-scroll { max-height: 50vh; }
  .tool-workbench-grid { grid-template-columns: 1fr; }
  .tool-workbench-wide { grid-column: auto; }
}

`

### frontend/static/css/test_panel.css

`css
.test-panel {
  width: 330px;
  min-width: 280px;
  background: var(--bg-card);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.test-panel-header {
  height: 48px;
  min-height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
}

.test-panel-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.test-panel-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.todo-selector-section {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-selector-section .form-select {
  width: 100%;
}

.test-function {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    transform 0.15s ease;
}

.test-function:hover {
  background: var(--bg-elev);
  border-color: var(--primary);
  transform: translateY(-2px);
}

.test-function i,
.test-function svg {
  width: 20px;
  height: 20px;
  color: var(--primary);
}

.test-function span {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
}

.test-function.disabled,
.test-function:disabled {
  opacity: 0.45;
  filter: grayscale(1);
  cursor: not-allowed;
}

.test-function.disabled:hover,
.test-function:disabled:hover {
  background: var(--bg-card);
  border-color: var(--border-color);
  transform: none;
}

@media (max-width: 820px) {
  .test-panel {
    width: 100%;
    min-width: 0;
  }
}

`

### frontend/static/js/api.js

`javascript
/**
 * Novous Unified API Client Wrapper
 */
async function jsonOrThrow(res) {
  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}

function get(url) { return fetch(url).then(jsonOrThrow); }
function send(method, url, body) {
  return fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined
  }).then(jsonOrThrow);
}

export const Api = {
  async saveMarkdown(content, filename) {
    if (typeof window.showSaveFilePicker === 'function') {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      });
      const writable = await handle.createWritable();
      await writable.write(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(
      new Blob([content], { type: 'text/markdown;charset=utf-8' })
    );
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

  // --- Workspace & Health ---
  async getHealth() {
    return get('/api/health');
  },

  async getProjectState() {
    return get('/api/project');
  },

  async saveProjectState(patch) {
    return send('POST', '/api/project', patch);
  },

  // --- Agents & Chat (Core Engine) ---
  async getAgents() {
    return get('/api/agents');
  },

  async createAgent(agentId, name, description, mode = 'chat', squad = '', environment = 'workspace') {
    return send('POST', '/api/agents/create', {
      agent_id: agentId, name, description, mode, squad, environment
    });
  },

  async deleteAgent(agentId, environment = 'workspace') {
    return send('DELETE', `/api/agents/${encodeURIComponent(agentId)}?environment=${encodeURIComponent(environment)}`);
  },

  async getCodeBuilderAgents() {
    return get('/api/codebuilder/agents');
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest', sessionId = null, environment = 'workspace') {
    return send('POST', '/api/chat', {
      message, agent_id: agentId, model, session_id: sessionId, environment
    });
  },

  async resetChat(sessionId) {
    return send('POST', `/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`);
  },

  async exportSession(sessionId) {
    const safeSessionId = String(sessionId).replace(/[^A-Za-z0-9_.-]/g, '_');
    const suggestedName = `novous_${safeSessionId}_${new Date().toISOString().replace(/[:.]/g, '-')}.md`;
    let pickerResult = null;
    if (typeof window.showSaveFilePicker === 'function') {
      pickerResult = window.showSaveFilePicker({
        suggestedName,
        types: [{
          description: 'Markdown file',
          accept: { 'text/markdown': ['.md'] }
        }]
      }).then(handle => ({ handle }), error => ({ error }));
    }

    const res = await fetch('/api/chat/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    if (!res.ok) await jsonOrThrow(res);
    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : suggestedName;

    if (pickerResult) {
      const result = await pickerResult;
      if (result.error) throw result.error;
      const writable = await result.handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return { filename, locationChosen: true };
    }

    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    return { filename, locationChosen: false };
  },

  async getTools() {
    return get('/api/tools');
  },

  async getWorkbenchTool(toolName) {
    return get(`/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
  },

  async deleteWorkbenchTool(toolName) {
    return send('DELETE', `/api/testing/tool-workbench/tools/${encodeURIComponent(toolName)}`);
  },

  async getModels() {
    return get('/api/models');
  },

  // --- Filesystem & Editor ---
  async getFileTree(path = '') {
    return get(`/api/directory/tree?path=${encodeURIComponent(path)}`);
  },

  async readFile(path) {
    return get(`/api/file/read?path=${encodeURIComponent(path)}`);
  },

  async writeFile(path, content) {
    return send('POST', '/api/file/write', { path, content });
  },

  async createPath(path, kind = 'file') {
    return send('POST', '/api/file/create', { path, kind });
  },

  async deletePath(path, kind = 'file') {
    return send('POST', '/api/file/delete', { path, kind });
  },

  async getEditorSessions() {
    return get('/api/editor/sessions');
  },

  // --- Squads ---
  async getSquads() { return get('/api/squads'); },
  async createSquad(name, description = '') {
    return send('POST', '/api/squads/create', { name, description });
  },
  async deleteSquad(name) {
    return send('POST', '/api/squads/delete', { name });
  },

  // --- Testing & Prompt Builder ---
  async getPromptCategories() {
    return get('/api/prompt-builder/categories');
  },

  async addPromptCategory(id, name, description = '', requiredHeader = '') {
    return send('POST', '/api/prompt-builder/categories', {
      id, name, description, required_header: requiredHeader
    });
  },

  async deletePromptCategory(catId) {
    return send('DELETE', `/api/prompt-builder/categories/${encodeURIComponent(catId)}`);
  },

  async getPromptParts(category = null) {
    const q = category ? `?category=${encodeURIComponent(category)}` : '';
    return get(`/api/prompt-builder/parts${q}`);
  },

  async addPromptPart(category, title, content, id = null) {
    return send('POST', '/api/prompt-builder/parts', {
      category, title, content, id
    });
  },

  async deletePromptPart(partId) {
    return send('DELETE', `/api/prompt-builder/parts/${encodeURIComponent(partId)}`);
  },

  async assemblePrompt(parts, extraInstructions = '') {
    return send('POST', '/api/prompt-builder/assemble', {
      parts, extra_instructions: extraInstructions
    });
  },

  async runHeaderTests(agentId, environment = 'workspace') {
    return send('POST', '/api/testing/run_header_tests', { agent_id: agentId, environment });
  },

  async executeToolTest(toolCode, functionInput = {}) {
    return send('POST', '/api/testing/tool-workbench/execute', {
      tool_code: toolCode, function_input: functionInput
    });
  },

  async testToolWithLlm(model, toolCode, userPrompt) {
    return send('POST', '/api/testing/tool-workbench/test-with-llm', {
      model, tool_code: toolCode, user_prompt: userPrompt
    });
  },

  async promoteTestedTool(toolCode, functionInput = {}) {
    return send('POST', '/api/testing/tool-workbench/promote', {
      tool_code: toolCode, function_input: functionInput
    });
  },

  async evaluateMarkdown(markdown, agentId = 'draft') {
    return send('POST', '/api/testing/evaluate_markdown', { markdown, agent_id: agentId });
  },

  async publishAgent(agentId, label = '', markdown, environment = 'workspace') {
    return send('POST', '/api/testing/publish', {
      agent_id: agentId, label, markdown, environment
    });
  },

  async getTestFixtures() {
    return get('/api/testing/fixtures');
  }
};

`

### frontend/static/js/app.js

`javascript
import { Api } from './api.js';
import { renderTree } from './tree.js';
import { renderEditorView } from './editor.js';
import { renderChatView } from './chat.js';
import { renderPromptCreationView } from './prompt_creation.js';
import { renderTestingView } from './testing.js';
import { renderCodeBuilderView } from './codebuilder/codebuilder.js';

export const AppState = {
  activeTab: 'dashboard',
  agents: [],
  project: null,
  health: null,
  currentPath: ''
};

const views = {
  dashboard: renderDashboardView,
  editor: renderEditorView,
  codebuilder: renderCodeBuilderView,
  chat: renderChatView,
  'prompt-creation': renderPromptCreationView,
  testing: renderTestingView
};

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// --- Dashboard -------------------------------------------------------------
function renderDashboardView(container) {
  const project = AppState.project || {};
  const agents = AppState.agents || [];
  const squads = project.squads || [];

  container.innerHTML = `
    <div class="dashboard">
      <section class="dash-hero card">
        <div>
          <h2>${esc(project.name || 'Novous Workspace')}</h2>
          <p class="text-muted">${esc(project.description || 'Declarative Agent Factory — 4-Pillar Architecture.')}</p>
        </div>
        <div class="dash-hero-stats">
          <div class="stat"><span class="stat-num">${agents.length}</span><span class="stat-label">Agents</span></div>
          <div class="stat"><span class="stat-num">${squads.length}</span><span class="stat-label">Squads</span></div>
          <div class="stat"><span class="stat-num">${esc(project.default_model || '-')}</span><span class="stat-label">Model</span></div>
        </div>
      </section>

      <div class="dash-grid">
        <section class="card">
          <div class="card-head">
            <h3>Agents</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-agent">+ New Agent</button>
          </div>
          <div id="dash-agent-form" class="hidden mt-2">
            <div class="form-row">
              <input id="na-id" class="form-input" placeholder="agent-id (e.g. reviewer)">
              <input id="na-name" class="form-input" placeholder="Display name">
            </div>
            <div class="form-row">
              <input id="na-desc" class="form-input" placeholder="Description">
              <select id="na-environment" class="form-select" aria-label="Agent environment">
                <option value="workspace">Workspace</option>
                <option value="codebuilder">CodeBuilder</option>
              </select>
              <select id="na-mode" class="form-select">
                <option value="chat">chat</option>
                <option value="agent">agent</option>
              </select>
              <button class="btn btn-primary" id="dash-create-agent">Create</button>
            </div>
            <p class="text-danger hidden" id="na-error"></p>
          </div>
          <div class="agent-cards" id="dash-agent-cards">
            ${agents.length ? '' : '<p class="text-muted">No agents yet. Create your first one.</p>'}
          </div>
          <div class="card-head mt-3"><h3>CodeBuilder Agents</h3></div>
          <div class="agent-cards" id="dash-codebuilder-agent-cards">
            <p class="text-muted">Loading CodeBuilder agents…</p>
          </div>
        </section>

        <section class="card">
          <div class="card-head">
            <h3>Squads</h3>
            <button class="btn btn-sm btn-primary" id="dash-new-squad">+ New Squad</button>
          </div>
          <div class="form-row mt-2">
            <input id="sq-name" class="form-input hidden" placeholder="squad name">
            <button class="btn btn-primary hidden" id="dash-create-squad">Create</button>
          </div>
          <ul class="squad-list" id="dash-squad-list">
            ${squads.map(s => `<li class="squad-item"><strong>${esc(s.name)}</strong>
              <span class="text-muted">${esc(s.description || s.path)}</span>
              <button class="btn btn-sm btn-ghost" data-squad-delete="${esc(s.name)}">✕</button></li>`).join('')
              || '<li class="text-muted">No squads yet.</li>'}
          </ul>
        </section>

        <section class="card">
          <div class="card-head"><h3>Workspace Tree</h3></div>
          <div id="dash-tree" class="tree-pane tree-pane-sm"></div>
        </section>

        <section class="card">
          <div class="card-head"><h3>System Health</h3></div>
          <div id="dash-health" class="health-panel">Checking…</div>
        </section>
      </div>
    </div>
  `;

  const cards = container.querySelector('#dash-agent-cards');
  const codeBuilderCards = container.querySelector('#dash-codebuilder-agent-cards');
  agents.forEach(a => {
    const el = document.createElement('div');
    el.className = 'agent-card';
    el.innerHTML = `
      <div class="agent-card-head">
        <strong>${esc(a.name)}</strong>
        <span class="badge ${a.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc(a.mode)}</span>
      </div>
      <p class="text-muted">${esc(a.description || 'No description.')}</p>
      <div class="agent-card-actions">
        <button class="btn btn-sm" data-chat="${esc(a.id)}">Chat</button>
        <button class="btn btn-sm" data-edit="${esc(a.id)}">Edit</button>
        <button class="btn btn-sm btn-danger" data-delete="${esc(a.id)}">Delete</button>
      </div>`;
    cards.appendChild(el);
  });

  cards.addEventListener('click', async (e) => {
    const t = e.target;
    if (t.dataset.chat) { switchTab('chat', t.dataset.chat); }
    else if (t.dataset.edit) { switchTab('editor', `agents/${t.dataset.edit}/agent.md`); }
    else if (t.dataset.delete) {
      if (!confirm(`Delete agent "${t.dataset.delete}"?`)) return;
      try { await Api.deleteAgent(t.dataset.delete, 'workspace'); await refreshAgents(); renderDashboardView(container); }
      catch (err) { alert(err.message); }
    }
  });

  function renderCodeBuilderAgentCards(codeBuilderAgents) {
    codeBuilderCards.replaceChildren();
    if (!codeBuilderAgents.length) {
      codeBuilderCards.innerHTML = '<p class="text-muted">No CodeBuilder agents yet.</p>';
      return;
    }
    codeBuilderAgents.forEach(agent => {
      const el = document.createElement('div');
      el.className = 'agent-card';
      el.innerHTML = `
        <div class="agent-card-head">
          <strong>${esc(agent.name)}</strong>
          <span class="badge badge-accent">CodeBuilder</span>
        </div>
        <p class="text-muted">${esc(agent.description || 'No description.')}</p>
        <div class="agent-card-actions">
          <a class="btn btn-sm" href="/codebuilder">Open CodeBuilder</a>
          <button class="btn btn-sm btn-danger" data-codebuilder-delete="${esc(agent.id)}">Delete</button>
        </div>`;
      codeBuilderCards.appendChild(el);
    });
  }

  Api.getCodeBuilderAgents().then(data => {
    renderCodeBuilderAgentCards(data.agents || []);
  }).catch(err => {
    codeBuilderCards.innerHTML = `<p class="text-danger">Could not load CodeBuilder agents: ${esc(err.message)}</p>`;
  });

  codeBuilderCards.addEventListener('click', async e => {
    const button = e.target.closest('[data-codebuilder-delete]');
    if (!button) return;
    const agentId = button.dataset.codebuilderDelete;
    if (!confirm(`Delete CodeBuilder agent "${agentId}"?`)) return;
    try {
      await Api.deleteAgent(agentId, 'codebuilder');
      const data = await Api.getCodeBuilderAgents();
      renderCodeBuilderAgentCards(data.agents || []);
    } catch (err) { alert(err.message); }
  });

  container.querySelector('#dash-new-agent').onclick = () =>
    container.querySelector('#dash-agent-form').classList.toggle('hidden');

  container.querySelector('#dash-create-agent').onclick = async () => {
    const id = container.querySelector('#na-id').value.trim();
    const name = container.querySelector('#na-name').value.trim();
    const desc = container.querySelector('#na-desc').value.trim();
    const mode = container.querySelector('#na-mode').value;
    const environment = container.querySelector('#na-environment').value;
    const errBox = container.querySelector('#na-error');
    errBox.classList.add('hidden');
    try {
      await Api.createAgent(id, name || id, desc, mode, '', environment);
      await refreshAgents();
      renderDashboardView(container);
    } catch (err) { errBox.textContent = err.message; errBox.classList.remove('hidden'); }
  };

  container.querySelector('#dash-new-squad').onclick = () => {
    container.querySelector('#sq-name').classList.toggle('hidden');
    container.querySelector('#dash-create-squad').classList.toggle('hidden');
  };
  container.querySelector('#dash-create-squad').onclick = async () => {
    const input = container.querySelector('#sq-name');
    try {
      await Api.createSquad(input.value.trim());
      await refreshProject();
      renderDashboardView(container);
    } catch (err) { alert(err.message); }
  };
  container.querySelector('#dash-squad-list').addEventListener('click', async (e) => {
    const name = e.target.dataset.squadDelete;
    if (!name) return;
    if (!confirm(`Delete squad "${name}"?`)) return;
    try { await Api.deleteSquad(name); await refreshProject(); renderDashboardView(container); }
    catch (err) { alert(err.message); }
  });

  renderTree(container.querySelector('#dash-tree'), { onSelect: (path) => switchTab('editor', path) });

  const healthBox = container.querySelector('#dash-health');
  Api.getHealth().then(h => {
    AppState.health = h;
    healthBox.innerHTML = `
      <div class="health-row"><span>API</span><span class="badge badge-success">ok</span></div>
      <div class="health-row"><span>Ollama</span>
        <span class="badge ${h.ollama?.reachable ? 'badge-success' : 'badge-warning'}">
          ${h.ollama?.reachable ? 'connected' : 'offline'}</span></div>
      <p class="text-muted small">${esc(h.ollama?.detail || '')}</p>
      <p class="text-muted small">Uptime: ${esc(h.uptime_seconds)}s</p>`;
    updateHealthBadge(h);
  }).catch(() => { healthBox.innerHTML = '<p class="text-danger">API unreachable.</p>'; });
}

// --- Shared helpers --------------------------------------------------------
export async function refreshAgents() {
  const data = await Api.getAgents();
  AppState.agents = data.agents || [];
  return AppState.agents;
}

export async function refreshProject() {
  AppState.project = await Api.getProjectState();
  return AppState.project;
}

export function updateHealthBadge(health) {
  const badge = document.getElementById('health-badge');
  if (!badge || !health) return;
  const ok = health.ollama?.reachable;
  badge.className = 'badge ' + (ok ? 'badge-success' : 'badge-warning');
  badge.textContent = ok ? 'Engine Ready' : 'Ollama Offline';
}

export function switchTab(tab, payload = null) {
  AppState.activeTab = tab;
  document.querySelectorAll('.nav-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab));
  const container = document.getElementById('view-container');
  if (!container) return;
  const renderer = views[tab];
  if (renderer) renderer(container, payload);
}

async function boot() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  try {
    await Promise.all([refreshAgents(), refreshProject()]);
  } catch (err) {
    document.getElementById('view-container').innerHTML =
      `<div class="error-panel">Failed to load workspace: ${esc(err.message)}</div>`;
    return;
  }

  try {
    const h = await Api.getHealth();
    AppState.health = h;
    updateHealthBadge(h);
  } catch (_) { /* badge stays default */ }

  const requestedTab = new URLSearchParams(window.location.search).get('tab');
  switchTab(Object.prototype.hasOwnProperty.call(views, requestedTab) ? requestedTab : 'dashboard');
}

boot();

`

### frontend/static/js/chat.js

`javascript
import { Api } from './api.js';
import { buildTestPanel } from './test_panel.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Interactive Chat Console Component: agent selection, message history,
 * and tool execution badges.
 */
export function renderChatView(container) {
  container.innerHTML = `
    <div class="chat-layout">
      <aside class="chat-sidebar">
        <h3>Agents Workspace</h3>
        <select id="chat-agent-select" class="form-select">
          <option value="">Loading agents...</option>
        </select>
        <div id="agent-meta-card" class="card mt-3">
          <p class="text-muted">Select an agent to begin chatting.</p>
        </div>
        <div class="chat-sidebar-actions">
          <label class="checkbox-row">
            <input type="checkbox" id="chat-use-tools" checked>
            <span>Attach tools (agent mode)</span>
          </label>
          <button class="btn btn-sm btn-primary" id="chat-save-log">Save Session Log (.md)</button>
          <label class="model-picker">
            <span class="model-picker-label">Model <span id="model-count" class="text-muted small"></span></span>
            <select id="chat-model-select" class="form-select"><option value="">Detecting models…</option></select>
          </label>
          <button class="btn btn-sm" id="chat-reset">Reset session</button>
        </div>
        <div id="chat-session-info" class="text-muted small mt-3"></div>
      </aside>

      <section class="chat-main">
        <div id="chat-messages" class="messages-scroll">
          <div class="message system-msg">Select an agent and send a message to start reasoning.</div>
        </div>
        <form id="chat-form" class="chat-input-bar">
          <input type="text" id="chat-input" placeholder="Type a message or instruction..." autocomplete="off" required />
          <button type="submit" class="btn btn-primary">Send</button>
        </form>
      </section>

      <aside class="test-panel">
        <div class="test-panel-header">
          <span class="test-panel-title">Test</span>
        </div>
        <div class="test-panel-content">
          <div id="testPanelButtons" class="test-grid"></div>
        </div>
      </aside>
    </div>`;

  const agentSelect = container.querySelector('#chat-agent-select');
  const metaCard = container.querySelector('#agent-meta-card');
  const messagesBox = container.querySelector('#chat-messages');
  const chatForm = container.querySelector('#chat-form');
  const chatInput = container.querySelector('#chat-input');
  const toolsToggle = container.querySelector('#chat-use-tools');
  const sessionInfo = container.querySelector('#chat-session-info');
  const modelSelect = container.querySelector('#chat-model-select');
  const modelCount = container.querySelector('#model-count');

  let agents = [];
  let installedModels = [];
  let currentModel = 'qwen2.5-coder:latest';

  Api.getModels().then(data => {
    installedModels = (data.models || []).sort();
    if (!installedModels.length) {
      modelCount.textContent = '(none installed)';
      modelSelect.innerHTML = '<option value="">No models found — run: ollama pull</option>';
      modelSelect.disabled = true;
      return;
    }
    modelCount.textContent = `(${installedModels.length} installed)`;
    modelSelect.innerHTML = installedModels
      .map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
    modelSelect.disabled = false;
    syncModelSelect();
  }).catch(err => {
    modelCount.textContent = '(error)';
    modelSelect.innerHTML = `<option value="">Model list unavailable: ${esc(err.message)}</option>`;
  });

  function syncModelSelect() {
    const agent = agents.find(a => a.id === agentSelect.value);
    const stored = agent?.model || 'qwen2.5-coder:latest';
    if (installedModels.includes(stored)) {
      currentModel = stored;
      modelSelect.value = stored;
    } else if (!modelSelect.value || currentModel !== modelSelect.value) {
      currentModel = modelSelect.value || installedModels[0];
    }
  }

  modelSelect.addEventListener('change', () => {
    currentModel = modelSelect.value;
  });

  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSelect.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)} (${esc(a.mode)})</option>`).join('')
      : '<option value="">No agents found</option>';
    if (agents.length > 0) { updateAgentMeta(agents[0].id); syncModelSelect(); }
  }).catch(err => {
    agentSelect.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  agentSelect.addEventListener('change', (e) => { updateAgentMeta(e.target.value); syncModelSelect(); });

  function updateAgentMeta(id) {
    const agent = agents.find(a => a.id === id);
    if (!agent) return;
    if (agent.model) currentModel = agent.model;
    metaCard.innerHTML = `
      <h4>${esc(agent.name)}</h4>
      <p><span class="badge ${agent.mode === 'agent' ? 'badge-accent' : 'badge-success'}">${esc((agent.mode || '').toUpperCase())}</span></p>
      <p>${esc(agent.description || 'No description provided.')}</p>
      <p class="text-muted small">Model: ${esc(currentModel)}<br>
      Tools: ${esc((agent.tools || []).join(', ') || 'none')}</p>`;
    toolsToggle.disabled = agent.mode !== 'agent';
    toolsToggle.checked = agent.mode === 'agent';
    sessionInfo.textContent = `Session: chat-${agent.id}`;
  }

  async function resetSession(message = 'Session reset. Send a message to start fresh.') {
    const agentId = agentSelect.value;
    if (!agentId) {
      appendMessage('system', 'Select an agent before resetting the chat.');
      return;
    }

    try {
      await Api.resetChat(`chat-${agentId}`);
      messagesBox.innerHTML = `<div class="message system-msg">${esc(message)}</div>`;
    } catch (err) {
      appendMessage('system', 'Reset failed: ' + err.message);
    }
  }

  async function openDiagnostics() {
    try {
      const health = await Api.getHealth();
      const ollamaStatus = health.ollama?.reachable ? 'connected' : 'offline';
      const details = health.ollama?.detail ? `\nOllama details: ${health.ollama.detail}` : '';
      appendMessage(
        'system',
        `Diagnostics: API reachable\nOllama: ${ollamaStatus}\nUptime: ${health.uptime_seconds ?? 'unknown'} seconds${details}`
      );
    } catch (err) {
      appendMessage('system', `Diagnostics failed: ${err.message}`);
    }
  }

  function wipeChat() {
    return resetSession('Chat wiped. Send a message to start fresh.');
  }

  let todoFilesLoading = false;
  async function loadTodoFiles(silent = false) {
    const select = container.querySelector('#todo-file-select');
    if (!select || todoFilesLoading) return;
    todoFilesLoading = true;

    try {
      const tree = await Api.getFileTree();
      const workspaceEntries = tree.children || [];
      const normalizedNames = new Set(['todo list', 'to due list', 'do due list']);
      const todoDirectories = workspaceEntries.filter(item =>
        item.type === 'directory' &&
        normalizedNames.has(item.name.toLowerCase().replace(/\s+/g, ' ').trim())
      );

      const files = [];
      function collectFiles(node) {
        if (node.type === 'file') {
          if (/\.(md|markdown)$/i.test(node.name) || !node.name.includes('.')) {
            files.push(node);
          }
          return;
        }
        (node.children || []).forEach(collectFiles);
      }
      workspaceEntries
        .filter(item => item.type === 'file')
        .forEach(collectFiles);
      todoDirectories.forEach(collectFiles);
      const markdownFiles = [...new Map(files.map(file => [file.path, file])).values()];
      const selectedPath = select.value;

      select.replaceChildren();
      if (!markdownFiles.length) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No Markdown or extensionless lists found in workspace or To Do List folders';
        select.appendChild(option);
        select.disabled = true;
        return;
      }

      markdownFiles.sort((a, b) => a.path.localeCompare(b.path));
      markdownFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file.path;
        option.textContent = file.path;
        option.title = file.path;
        select.appendChild(option);
      });
      if (markdownFiles.some(file => file.path === selectedPath)) {
        select.value = selectedPath;
      }
      select.disabled = false;
    } catch (err) {
      if (!silent) {
        select.replaceChildren();
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error loading files';
        select.appendChild(option);
        select.disabled = true;
        appendMessage('system', `Could not load To-Do files: ${err.message}`);
      }
    } finally {
      todoFilesLoading = false;
    }
  }

  async function runTodoSequence() {
    const select = container.querySelector('#todo-file-select');
    const selectedPath = select?.value;
    const agentId = agentSelect.value;

    if (!selectedPath) {
      appendMessage('system', 'Please select a file from the To-Do dropdown first.');
      return;
    }
    if (!agentId) {
      appendMessage('system', 'Please select an agent before running To-Do items.');
      return;
    }

    const runButton = container.querySelector('[data-test-function="runTestSuite"]');
    if (runButton) runButton.disabled = true;

    try {
      const fileData = await Api.readFile(selectedPath);
      const lines = String(fileData.content ?? '')
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(Boolean);

      appendMessage('user', `Starting execution of To-Do items from: ${selectedPath.split('/').pop()}`);
      if (!lines.length) {
        appendMessage('system', 'The selected file contains no nonblank task lines.');
        return;
      }

      const sessionId = `chat-${agentId}`;
      const model = currentModel;
      await delay(1500);

      for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        appendMessage('user', `Task ${index + 1}: ${line}`);
        const thinkingId = appendMessage('assistant', 'Thinking...', true);
        try {
          const response = await Api.sendMessage(line, agentId, model, sessionId);
          removeMessage(thinkingId);
          (response.tool_events || []).forEach(event =>
            appendToolBadge(event.tool, event.status, event.args)
          );
          appendMessage('assistant', response.reply);
        } catch (err) {
          removeMessage(thinkingId);
          throw err;
        }

        if (index < lines.length - 1) await delay(1000);
      }
    } catch (err) {
      appendMessage('system', `Error reading or running To-Do file: ${err.message}`);
    } finally {
      if (runButton) runButton.disabled = false;
    }
  }

  container.querySelector('#chat-reset').addEventListener('click', () => resetSession());
  container.querySelector('#chat-save-log').addEventListener('click', async () => {
    const agentId = agentSelect.value;
    if (!agentId) {
      alert('Select an agent before saving the session log.');
      return;
    }

    try {
      const res = await Api.exportSession(`chat-${agentId}`);
      alert(res.locationChosen
        ? `Session log saved as ${res.filename} in the location you selected.`
        : `Session log download started: ${res.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save session: ${err.message}`);
    }
  });
  buildTestPanel('testPanelButtons', {
    diagnostics: openDiagnostics,
    wipeChat,
    runTestSuite: runTodoSequence
  });
  loadTodoFiles();
  container.querySelector('#todo-file-refresh')
    ?.addEventListener('click', () => loadTodoFiles());
  const todoRefreshInterval = setInterval(() => {
    if (!container.isConnected) {
      clearInterval(todoRefreshInterval);
      return;
    }
    loadTodoFiles(true);
  }, 5000);

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    const agentId = agentSelect.value;
    if (!text || !agentId) return;

    appendMessage('user', text);
    chatInput.value = '';

    const thinkingId = appendMessage('assistant', 'Thinking...', true);

    try {
      const sessionId = `chat-${agentId}`;
      const res = await Api.sendMessage(text, agentId, currentModel, sessionId);
      removeMessage(thinkingId);

      if (res.tool_events && res.tool_events.length > 0) {
        res.tool_events.forEach(evt => appendToolBadge(evt.tool, evt.status, evt.args));
      }

      appendMessage('assistant', res.reply);
    } catch (err) {
      removeMessage(thinkingId);
      appendMessage('system', 'Error communicating with engine: ' + err.message);
    }
  });

  function appendMessage(role, content, isTemporary = false) {
    const msgDiv = document.createElement('div');
    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
    msgDiv.id = id;
    msgDiv.className = `message ${role}-msg ${isTemporary ? 'pulse' : ''}`;
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerText = content;
    msgDiv.appendChild(body);

    if (!isTemporary && role !== 'system') {
      const copyButton = document.createElement('button');
      copyButton.type = 'button';
      copyButton.className = 'btn btn-sm btn-ghost msg-copy-btn';
      copyButton.innerText = 'Copy';
      copyButton.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(content);
          copyButton.innerText = 'Copied!';
          setTimeout(() => { copyButton.innerText = 'Copy'; }, 2000);
        } catch (err) {
          copyButton.innerText = 'Copy failed';
        }
      });
      msgDiv.appendChild(copyButton);
    }

    messagesBox.appendChild(msgDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendToolBadge(toolName, status, args) {
    const badgeDiv = document.createElement('div');
    badgeDiv.className = `tool-badge ${status}`;
    const argText = args ? JSON.stringify(args) : '';
    badgeDiv.innerHTML = `🛠️ <strong>${esc(toolName)}</strong> executed (${esc(status)})
      ${argText ? `<span class="text-muted small"> ${esc(argText.slice(0, 120))}</span>` : ''}`;
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }
}

`

### frontend/static/js/codebuilder/codebuilder.js

`javascript
import { attachCodeBuilderEditor } from './codebuilder_editor.js';

const DEMO_CODE = `print("Hello from Novous CodeBuilder!")
for i in range(3):
    print(f"count={i}")
`;

export async function setupCodeBuilderPage(rootId = 'codebuilder-editor') {
  const root = document.getElementById(rootId);
  const output = document.getElementById('codebuilder-output');
  const diagnostics = document.getElementById('diagnostics');
  const runButton = document.getElementById('run-code');
  const demoButton = document.getElementById('load-demo');
  const clearButton = document.getElementById('clear-console');
  const status = document.getElementById('codebuilder-status');
  const agentList = document.getElementById('codebuilder-agent-list');
  const agentStatus = document.getElementById('codebuilder-agent-status');
  const agentRefresh = document.getElementById('codebuilder-agent-refresh');
  const sidebar = document.getElementById('codebuilder-sidebar');
  const sidebarToggle = document.getElementById('codebuilder-sidebar-toggle');
  const modelSelect = document.getElementById('codebuilder-model');
  const chatForm = document.getElementById('codebuilder-chat-form');
  const chatInput = document.getElementById('codebuilder-chat-input');
  const chatMessages = document.getElementById('codebuilder-chat-messages');
  const chatStatus = document.getElementById('codebuilder-chat-status');
  const chatPanel = document.getElementById('codebuilder-chat-panel');
  const chatExpand = document.getElementById('codebuilder-chat-expand');

  if (!root || !output || !diagnostics || !runButton || !demoButton || !clearButton ||
      !agentList || !agentStatus || !agentRefresh || !sidebar || !sidebarToggle ||
      !modelSelect || !chatForm || !chatInput || !chatMessages || !chatStatus ||
      !chatPanel || !chatExpand) {
    console.error('CodeBuilder could not start because a required page element is missing.');
    return null;
  }

  const editor = await attachCodeBuilderEditor(root, DEMO_CODE);
  let agents = [];
  let selectedAgent = null;
  let defaultModel = 'qwen2.5-coder:latest';
  let chatPending = false;

  const renderDiagnostics = (items = []) => {
    diagnostics.replaceChildren();
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted';
      empty.textContent = 'No diagnostics reported.';
      diagnostics.appendChild(empty);
      return;
    }

    items.forEach(item => {
      const entry = document.createElement('button');
      entry.type = 'button';
      entry.className = 'diagnostic-item';
      entry.dataset.severity = item.severity || 'error';
      entry.textContent = `${item.severity || 'error'}${item.line ? ` · line ${item.line}` : ''} · ${item.message}`;
      if (item.line) {
        entry.addEventListener('click', () => editor.revealLine(item.line));
      }
      diagnostics.appendChild(entry);
    });
  };

  const runCode = async () => {
    runButton.disabled = true;
    runButton.textContent = 'Running…';
    output.textContent = 'Running Python code…';
    status.textContent = 'Running';
    diagnostics.replaceChildren();
    editor.setDiagnostics([]);

    try {
      const response = await fetch('/api/codebuilder/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editor.getValue(), timeout_seconds: 5.0 })
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Execution failed.');
      }

      const stdout = payload.stdout || '';
      const stderr = payload.stderr || '';
      output.textContent = [stdout, stderr].filter(Boolean).join('\n').trim()
        || 'Execution completed with no output.';
      renderDiagnostics(payload.diagnostics || []);
      editor.setDiagnostics(payload.diagnostics || []);
      status.textContent = payload.status === 'SUCCESS' ? 'Finished' : 'Finished with errors';
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      output.textContent = `Error: ${message}`;
      renderDiagnostics([{ severity: 'error', message }]);
      status.textContent = 'Request failed';
      return null;
    } finally {
      runButton.disabled = false;
      runButton.textContent = '▶ Run Python';
      editor.focus();
    }
  };

  const sendCodeToEditor = (code, source = 'chat') => {
    if (typeof code !== 'string' || !code.trim()) return false;
    editor.setValue(code);
    editor.setDiagnostics([]);
    renderDiagnostics([]);
    status.textContent = source === 'agent'
      ? 'Code received from agent'
      : 'Code sent to editor';
    editor.focus();
    return true;
  };

  const handleCodeBuilderToolEvents = async (events = []) => {
    for (const event of events) {
      if (event.status !== 'success') continue;
      if (event.tool === 'send_code_to_editor') {
        const code = event.args?.code;
        if (sendCodeToEditor(code, 'agent')) {
          appendChatMessage('system', 'The agent placed its code in the Monaco editor.');
        }
      } else if (event.tool === 'run_code_in_editor') {
        appendChatMessage('system', 'The agent requested a run of the current editor code.');
        const result = await runCode();
        if (!result) {
          appendChatMessage('system', 'The editor code could not be run. See Run Output for details.');
        } else {
          appendChatMessage(
            'system',
            result.status === 'SUCCESS'
              ? 'Editor code ran successfully. See Run Output.'
              : 'Editor code ran with errors. See Run Output and Problems.'
          );
        }
      }
    }
  };

  const appendAssistantMessage = (message, content) => {
    content = String(content ?? '');
    const codeBlockPattern = /```([^\r\n`]*)\r?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    const appendText = text => {
      if (!text) return;
      const paragraph = document.createElement('div');
      paragraph.className = 'codebuilder-chat-text';
      paragraph.textContent = text;
      message.appendChild(paragraph);
    };

    while ((match = codeBlockPattern.exec(content)) !== null) {
      appendText(content.slice(lastIndex, match.index));

      const language = match[1].trim().split(/\s+/, 1)[0].toLowerCase();
      const code = match[2];
      const isPython = !language || ['py', 'python', 'python3'].includes(language);
      const block = document.createElement('section');
      block.className = 'codebuilder-code-block';

      const heading = document.createElement('div');
      heading.className = 'codebuilder-code-heading';
      const languageLabel = document.createElement('span');
      languageLabel.textContent = isPython ? 'Python' : language;
      heading.appendChild(languageLabel);

      if (isPython) {
        const sendButton = document.createElement('button');
        sendButton.type = 'button';
        sendButton.className = 'btn btn-sm codebuilder-send-code';
        sendButton.textContent = 'Send to editor';
        sendButton.addEventListener('click', () => {
          if (sendCodeToEditor(code)) {
            sendButton.textContent = 'Sent to editor';
            sendButton.disabled = true;
          }
        });
        heading.appendChild(sendButton);
      }

      const pre = document.createElement('pre');
      const codeElement = document.createElement('code');
      codeElement.className = isPython ? 'language-python' : `language-${language || 'text'}`;
      codeElement.textContent = code;
      pre.appendChild(codeElement);
      block.append(heading, pre);
      message.appendChild(block);
      lastIndex = codeBlockPattern.lastIndex;
    }

    appendText(content.slice(lastIndex));
  };

  const appendChatMessage = (role, content) => {
    const message = document.createElement('div');
    message.className = `codebuilder-chat-message ${role}`;
    if (role === 'assistant') {
      appendAssistantMessage(message, content);
    } else {
      message.textContent = content;
    }
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const updateChatControls = () => {
    const sendButton = chatForm.querySelector('button[type="submit"]');
    chatInput.disabled = chatPending;
    sendButton.disabled = chatPending || !selectedAgent || !modelSelect.value || modelSelect.disabled;
  };

  const renderAgents = () => {
    agentList.replaceChildren();
    if (!agents.length) {
      const empty = document.createElement('p');
      empty.className = 'text-muted small';
      empty.textContent = 'No agents found in the workspace agents folder.';
      agentList.appendChild(empty);
      selectedAgent = null;
      updateChatControls();
      return;
    }

    agents.forEach(agent => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'codebuilder-agent-item';
      button.classList.toggle('selected', selectedAgent?.id === agent.id);
      button.title = agent.description || agent.name;
      button.setAttribute('aria-pressed', String(selectedAgent?.id === agent.id));
      button.disabled = chatPending;

      const name = document.createElement('span');
      name.className = 'codebuilder-agent-name';
      name.textContent = agent.name;
      const mode = document.createElement('span');
      mode.className = 'codebuilder-agent-mode';
      mode.textContent = agent.mode || 'agent';
      button.append(name, mode);
      button.addEventListener('click', () => selectAgent(agent));
      agentList.appendChild(button);
    });

    updateChatControls();
  };

  const selectAgent = (agent) => {
    selectedAgent = agent;
    renderAgents();
    const preferredModel = agent.model || defaultModel;
    if ([...modelSelect.options].some(option => option.value === preferredModel)) {
      modelSelect.value = preferredModel;
    }
    chatMessages.replaceChildren();
    appendChatMessage('system', `Chatting with ${agent.name}.`);
    chatStatus.textContent = `Agent: ${agent.name}`;
  };

  const loadAgents = async () => {
    agentRefresh.disabled = true;
    agentStatus.textContent = 'Loading agents…';
    try {
      const data = await fetch('/api/codebuilder/agents').then(async response => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'Could not load agents.');
        return payload;
      });
      agents = data.agents || [];
      agentStatus.textContent = `${agents.length} agent${agents.length === 1 ? '' : 's'}`;
      const selectedId = selectedAgent?.id;
      selectedAgent = agents.find(agent => agent.id === selectedId) || agents[0] || null;
      renderAgents();
      if (selectedAgent) selectAgent(selectedAgent);
    } catch (error) {
      agentStatus.textContent = 'Could not load agents.';
      const message = document.createElement('p');
      message.className = 'text-danger small';
      message.textContent = error instanceof Error ? error.message : String(error);
      agentList.replaceChildren(message);
    } finally {
      agentRefresh.disabled = false;
    }
  };

  const loadModels = async () => {
    modelSelect.replaceChildren();
    const loadingOption = document.createElement('option');
    loadingOption.textContent = 'Loading models…';
    loadingOption.value = '';
    modelSelect.appendChild(loadingOption);
    modelSelect.disabled = true;
    try {
      const response = await fetch('/api/models');
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Could not load models.');
      const models = (payload.models || []).slice().sort();
      defaultModel = payload.default || defaultModel;
      modelSelect.replaceChildren();

      const availableModels = models.length ? models : [defaultModel];
      availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = models.length ? model : `${model} (not detected)`;
        modelSelect.appendChild(option);
      });
      modelSelect.disabled = models.length === 0;
      if (models.length) {
        const preferredModel = selectedAgent?.model || defaultModel;
        modelSelect.value = models.includes(preferredModel) ? preferredModel : models[0];
      }
      if (!models.length) {
        chatStatus.textContent = payload.error || 'No installed models detected.';
      }
      updateChatControls();
    } catch (error) {
      modelSelect.replaceChildren();
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Could not load models';
      modelSelect.appendChild(option);
      modelSelect.disabled = true;
      chatStatus.textContent = error instanceof Error ? error.message : String(error);
      updateChatControls();
    }
  };

  demoButton.addEventListener('click', () => {
    editor.setValue(DEMO_CODE);
    editor.setDiagnostics([]);
    status.textContent = 'Demo loaded';
    editor.focus();
  });
  clearButton.addEventListener('click', () => {
    output.textContent = 'Console cleared.';
    renderDiagnostics([]);
    editor.setDiagnostics([]);
    status.textContent = 'Ready';
  });
  runButton.addEventListener('click', runCode);
  editor.setRunHandler(runCode);
  agentRefresh.addEventListener('click', loadAgents);
  sidebarToggle.addEventListener('click', () => {
    const collapsed = sidebar.classList.toggle('collapsed');
    sidebar.closest('.codebuilder-shell').classList.toggle('sidebar-collapsed', collapsed);
    sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
    sidebarToggle.setAttribute('aria-label', collapsed ? 'Expand agent sidebar' : 'Collapse agent sidebar');
  });
  chatExpand.addEventListener('click', () => {
    const expanded = chatPanel.classList.toggle('expanded');
    chatExpand.setAttribute('aria-expanded', String(expanded));
    chatExpand.setAttribute(
      'aria-label',
      expanded ? 'Shrink chat panel' : 'Expand chat panel'
    );
    chatExpand.title = expanded ? 'Shrink chat panel' : 'Expand chat panel';
    chatExpand.textContent = expanded ? '⌄' : '⌃';
  });
  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message || chatPending) return;
    if (!selectedAgent) {
      chatStatus.textContent = 'Select an agent before sending a message.';
      return;
    }
    if (!modelSelect.value) {
      chatStatus.textContent = 'Select an installed model before sending a message.';
      return;
    }

    appendChatMessage('user', message);
    chatInput.value = '';
    chatPending = true;
    chatStatus.textContent = `Waiting for ${selectedAgent.name}…`;
    updateChatControls();
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          agent_id: selectedAgent.id,
          model: modelSelect.value,
          session_id: `codebuilder-${selectedAgent.id}`,
          environment: 'codebuilder',
        })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'The agent request failed.');
      await handleCodeBuilderToolEvents(payload.tool_events || []);
      appendChatMessage('assistant', payload.reply || 'The agent returned an empty response.');
      chatStatus.textContent = `${selectedAgent.name} · ${payload.model || modelSelect.value}`;
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      appendChatMessage('system', `Request failed: ${messageText}`);
      chatStatus.textContent = 'Request failed';
    } finally {
      chatPending = false;
      updateChatControls();
      chatInput.focus();
    }
  });
  chatInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      chatForm.requestSubmit();
    }
  });

  renderDiagnostics([]);
  status.textContent = 'Ready';
  updateChatControls();
  Promise.all([loadAgents(), loadModels()]);

  return { editor, runCode, loadAgents };
}

export function renderCodeBuilderView(container) {
  if (!container) return;
  container.innerHTML = `
    <div class="codebuilder-shell">
      <div class="codebuilder-toolbar">
        <div class="codebuilder-file-label">
          <span class="codebuilder-python-icon">Py</span>
          <span>Untitled Python File</span>
          <span class="badge badge-success">Python</span>
        </div>
        <div class="codebuilder-toolbar-actions">
          <button id="load-demo" class="btn btn-sm" type="button" title="Load the sample Python program">Sample</button>
          <button id="clear-console" class="btn btn-sm" type="button" title="Clear console and diagnostics">Clear Output</button>
          <button id="run-code" class="btn btn-sm btn-primary" type="button" title="Run Python (Ctrl+Enter)">▶ Run Python</button>
        </div>
      </div>

      <main class="codebuilder-layout">
        <aside id="codebuilder-sidebar" class="codebuilder-sidebar" aria-label="Workspace agents">
          <div class="codebuilder-sidebar-heading">
            <button id="codebuilder-sidebar-toggle" class="btn btn-sm codebuilder-sidebar-toggle"
                    type="button" aria-label="Collapse agent sidebar" aria-expanded="true" title="Collapse sidebar">‹</button>
            <div class="codebuilder-sidebar-title">
              <h2>Agents</h2>
              <span id="codebuilder-agent-status" class="text-muted small">Loading…</span>
            </div>
            <button id="codebuilder-agent-refresh" class="btn btn-sm codebuilder-agent-refresh"
                    type="button" title="Refresh agents" aria-label="Refresh agents">↻</button>
          </div>
          <div id="codebuilder-agent-list" class="codebuilder-agent-list"></div>
        </aside>

        <section class="codebuilder-editor-panel" aria-label="Python editor">
          <div id="codebuilder-editor" class="editor-surface"></div>
          <div class="codebuilder-statusbar">
            <span id="codebuilder-status">Loading editor…</span>
            <span>Python</span>
            <span>UTF-8</span>
            <span>Spaces: 4</span>
          </div>
        </section>

        <aside class="codebuilder-console-panel" aria-label="Run output and diagnostics">
          <div class="codebuilder-console-heading">
            <h2>Run Output</h2>
            <span class="codebuilder-console-subtitle">Console &amp; Problems</span>
          </div>
          <section class="codebuilder-output-section">
            <h3>Console</h3>
            <pre id="codebuilder-output" class="console-output">Ready. Run your Python code to see output here.</pre>
          </section>
          <section class="codebuilder-problems-section">
            <h3>Problems</h3>
            <div id="diagnostics" class="diagnostics-list"></div>
          </section>
        </aside>
      </main>

      <section id="codebuilder-chat-panel" class="codebuilder-chat-panel" aria-label="Chat with an agent">
        <div class="codebuilder-chat-heading">
          <h2>Ask an Agent</h2>
          <span id="codebuilder-chat-status" class="text-muted small">Select an agent to start.</span>
          <button id="codebuilder-chat-expand" class="btn btn-sm codebuilder-chat-expand"
                  type="button" aria-label="Expand chat panel" aria-expanded="false"
                  title="Expand chat panel">⌃</button>
        </div>
        <div id="codebuilder-chat-messages" class="codebuilder-chat-messages" aria-live="polite">
          <div class="codebuilder-chat-message system">Messages with your selected agent appear here.</div>
        </div>
        <form id="codebuilder-chat-form" class="codebuilder-chat-form">
          <label class="codebuilder-model-picker">
            <span class="text-muted small">Model</span>
            <select id="codebuilder-model" class="form-select" aria-label="Choose model">
              <option value="">Loading models…</option>
            </select>
          </label>
          <textarea id="codebuilder-chat-input" class="form-input" rows="2"
                    placeholder="Ask the selected agent about your Python code…"
                    aria-label="Message to agent"></textarea>
          <button class="btn btn-primary" type="submit" disabled>Send</button>
        </form>
      </section>
    </div>
  `;

  setupCodeBuilderPage();
}

if (typeof window !== 'undefined' && document.readyState !== 'loading') {
  const root = document.getElementById('codebuilder-editor');
  if (root) setupCodeBuilderPage();
}

`

### frontend/static/js/codebuilder/codebuilder_editor.js

`javascript
const MONACO_VS_PATH = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs';
let monacoPromise;

function loadMonaco() {
  if (window.monaco?.editor) return Promise.resolve(window.monaco);
  if (monacoPromise) return monacoPromise;

  monacoPromise = new Promise((resolve, reject) => {
    if (typeof window.require !== 'function') {
      reject(new Error('The Monaco Editor loader is unavailable.'));
      return;
    }

    window.require.config({ paths: { vs: MONACO_VS_PATH } });
    window.require(['vs/editor/editor.main'], () => {
      if (!window.monaco?.editor) {
        reject(new Error('Monaco Editor failed to initialize.'));
        return;
      }
      resolve(window.monaco);
    }, reject);
  });
  return monacoPromise;
}

function createTextareaEditor(element, initialValue) {
  const textarea = document.createElement('textarea');
  textarea.className = 'codebuilder-textarea';
  textarea.value = initialValue;
  textarea.setAttribute('aria-label', 'Python source code');
  element.replaceChildren(textarea);
  let runHandler = null;
  textarea.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      runHandler?.();
    }
  });

  return {
    getValue: () => textarea.value,
    setValue: (value) => { textarea.value = value; },
    setDiagnostics: () => {},
    setRunHandler: (handler) => { runHandler = handler; },
    revealLine: (line) => {
      const lineStart = textarea.value.split('\n').slice(0, Math.max(0, line - 1)).join('\n').length;
      textarea.focus();
      textarea.setSelectionRange(lineStart, lineStart);
    },
    focus: () => textarea.focus(),
    dispose: () => textarea.remove(),
  };
}

export async function attachCodeBuilderEditor(element, initialValue = "print('Hello from Novous CodeBuilder!')\n") {
  if (!element) {
    throw new Error('The CodeBuilder editor container was not found.');
  }

  try {
    const monaco = await loadMonaco();
    const editor = monaco.editor.create(element, {
      value: initialValue,
      language: 'python',
      theme: 'vs-dark',
      automaticLayout: true,
      ariaLabel: 'Python code editor',
      accessibilitySupport: 'auto',
      bracketPairColorization: { enabled: true },
      cursorBlinking: 'smooth',
      detectIndentation: false,
      folding: true,
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace",
      fontLigatures: true,
      formatOnPaste: true,
      guides: { bracketPairs: true, indentation: true },
      lineNumbers: 'on',
      minimap: { enabled: true, scale: 0.8 },
      padding: { top: 12, bottom: 12 },
      renderLineHighlight: 'all',
      scrollBeyondLastLine: false,
      smoothScrolling: true,
      stickyScroll: { enabled: true },
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'off',
    });
    let runHandler = null;
    editor.addAction({
      id: 'codebuilder.runPython',
      label: 'Run Python',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
      run: () => runHandler?.(),
    });

    return {
      getValue: () => editor.getValue(),
      setValue: (value) => editor.setValue(value),
      focus: () => editor.focus(),
      setRunHandler: (handler) => { runHandler = handler; },
      revealLine: (line) => {
        editor.revealLineInCenter(line);
        editor.setPosition({ lineNumber: line, column: 1 });
        editor.focus();
      },
      setDiagnostics: (items) => {
        const model = editor.getModel();
        if (!model) return;
        monaco.editor.setModelMarkers(model, 'codebuilder', items.map(item => ({
          severity: item.severity === 'warning'
            ? monaco.MarkerSeverity.Warning
            : item.severity === 'info'
              ? monaco.MarkerSeverity.Info
              : monaco.MarkerSeverity.Error,
          message: item.message,
          startLineNumber: item.line || 1,
          endLineNumber: item.line || 1,
          startColumn: item.column || 1,
          endColumn: (item.column || 1) + 1,
        })));
      },
      dispose: () => editor.dispose(),
    };
  } catch (error) {
    console.error('Monaco Editor could not be loaded; using the basic Python editor instead.', error);
    return createTextareaEditor(element, initialValue);
  }
}

`

### frontend/static/js/editor.js

`javascript
import { Api } from './api.js';
import { renderTree } from './tree.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

const state = {
  path: null,
  dirty: false,
  ws: null
};

/**
 * File & Agent Editor Component (textarea editor + live session event bus).
 * @param {HTMLElement} container
 * @param {string|null} initialPath
 */
export function renderEditorView(container, initialPath = null) {
  container.innerHTML = `
    <div class="editor-layout">
      <aside class="editor-sidebar">
        <h3 class="sidebar-title">Workspace</h3>
        <div id="editor-tree" class="tree-pane"></div>
      </aside>

      <section class="editor-main">
        <div class="editor-toolbar">
          <span id="editor-path" class="editor-path">No file open</span>
          <span id="editor-dirty" class="badge badge-warning hidden">Unsaved</span>
          <span class="spacer"></span>
          <span id="editor-ws" class="badge badge-success" title="Session event bus">WS ●</span>
          <button class="btn btn-sm" id="editor-reload">Reload</button>
          <button class="btn btn-sm btn-primary" id="editor-save">Save (Ctrl+S)</button>
        </div>
        <textarea id="editor-textarea" class="editor-textarea" spellcheck="false"
                  placeholder="Select a file from the tree to edit…"></textarea>
        <div class="editor-status">
          <span id="editor-pos">Ln 1, Col 1</span>
          <span class="spacer"></span>
          <span id="editor-bytes">0 bytes</span>
        </div>
      </section>

      <aside class="editor-events">
        <h3 class="sidebar-title">Session Events</h3>
        <div class="event-export">
          <button class="btn btn-sm btn-primary" id="event-save-log">Save Events Log (.md)</button>
        </div>
        <div id="event-log" class="event-log">
          <p class="text-muted">Connecting to event bus…</p>
        </div>
      </aside>
    </div>`;

  container.insertAdjacentHTML('beforeend', `
    <dialog id="editor-save-dialog" class="workspace-save-dialog">
      <form id="editor-save-form">
        <h2>Save to Workspace</h2>
        <p class="text-muted">Choose a workspace folder and file name.</p>
        <label for="editor-save-directory">Folder</label>
        <select id="editor-save-directory" class="form-select"></select>
        <label for="editor-save-filename">File name</label>
        <input id="editor-save-filename" class="form-input" type="text" required>
        <p id="editor-save-error" class="text-danger hidden" role="alert"></p>
        <div class="workspace-save-actions">
          <button id="editor-save-cancel" class="btn" type="button">Cancel</button>
          <button id="editor-save-confirm" class="btn btn-primary" type="submit">Save</button>
        </div>
      </form>
    </dialog>`);

  const textarea = container.querySelector('#editor-textarea');
  const pathLabel = container.querySelector('#editor-path');
  const dirtyBadge = container.querySelector('#editor-dirty');
  const bytesLabel = container.querySelector('#editor-bytes');
  const posLabel = container.querySelector('#editor-pos');
  const eventLog = container.querySelector('#event-log');
  const wsBadge = container.querySelector('#editor-ws');
  const saveLogButton = container.querySelector('#event-save-log');
  const saveDialog = container.querySelector('#editor-save-dialog');
  const saveDirectory = container.querySelector('#editor-save-directory');
  const saveFilename = container.querySelector('#editor-save-filename');
  const saveError = container.querySelector('#editor-save-error');
  const saveConfirm = container.querySelector('#editor-save-confirm');
  const sessionEvents = [];
  let saveDialogFiles = new Set();

  saveLogButton.addEventListener('click', async () => {
    saveLogButton.disabled = true;
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rows = sessionEvents.map(event => {
        const escapeCell = value => String(value || '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
        const details = event.data && Object.keys(event.data).length
          ? JSON.stringify(event.data)
          : '';
        return `| ${escapeCell(event.type.replace(/_/g, ' '))} | ${escapeCell(event.path)} | ${escapeCell(event.session_id)} | ${escapeCell(details)} |`;
      });
      const markdown = [
        '# Novous Session Events Log',
        '',
        `Exported: ${new Date().toLocaleString()}`,
        '',
        '| Event | Path / Tool | Session | Details |',
        '| --- | --- | --- | --- |',
        ...(rows.length ? rows : ['| No events recorded | | | |']),
        ''
      ].join('\n');
      const result = await Api.saveMarkdown(markdown, `novous-session-events-${timestamp}.md`);
      alert(result.locationChosen
        ? `Events log saved as ${result.filename} in the location you selected.`
        : `Events log download started: ${result.filename}\n\nChoose the save location in your browser's download settings.`);
    } catch (err) {
      if (err.name !== 'AbortError') alert(`Failed to save events log: ${err.message}`);
    } finally {
      saveLogButton.disabled = false;
    }
  });

  const workspaceTree = renderTree(container.querySelector('#editor-tree'), {
    onSelect: (path) => openFile(path)
  });

  async function openFile(path) {
    if (state.dirty && !confirm('Discard unsaved changes?')) return;
    try {
      const data = await Api.readFile(path);
      state.path = data.path;
      state.dirty = false;
      textarea.value = data.content;
      pathLabel.textContent = data.path;
      dirtyBadge.classList.add('hidden');
      updateBytes();
      updatePos();
      sendWs({ type: 'file_opened', path: data.path });
      appendEvent({ type: 'file_opened', path: data.path, session_id: 'you' });
      textarea.focus();
    } catch (err) {
      alert(err.message);
    }
  }

  async function openSaveDialog() {
    try {
      const tree = await Api.getFileTree();
      const folders = [];
      const files = new Set();
      function collect(node) {
        if (node.type === 'directory') {
          if (node.path) folders.push(node.path);
          (node.children || []).forEach(collect);
        } else {
          files.add(node.path);
        }
      }
      collect(tree);
      folders.sort((a, b) => a.localeCompare(b));

      saveDirectory.replaceChildren();
      const rootOption = document.createElement('option');
      rootOption.value = '';
      rootOption.textContent = '/ (workspace root)';
      saveDirectory.appendChild(rootOption);
      folders.forEach(path => {
        const option = document.createElement('option');
        option.value = path;
        option.textContent = path;
        saveDirectory.appendChild(option);
      });

      const currentParts = (state.path || '').split('/');
      const currentFilename = currentParts.pop() || 'untitled.txt';
      const currentDirectory = currentParts.join('/');
      saveDirectory.value = folders.includes(currentDirectory) ? currentDirectory : '';
      saveFilename.value = currentFilename;
      saveError.textContent = '';
      saveError.classList.add('hidden');
      saveDialog.showModal();
      saveFilename.focus();
      saveFilename.select();
      saveDialogFiles = files;
    } catch (err) {
      alert(`Could not open the workspace save picker: ${err.message}`);
    }
  }

  async function saveFile() {
    if (!saveDialog.open) {
      await openSaveDialog();
      return;
    }

    const filename = saveFilename.value.trim();
    if (!filename || filename === '.' || filename === '..' || /[\\/]/.test(filename)) {
      saveError.textContent = 'Enter a file name without folder separators.';
      saveError.classList.remove('hidden');
      saveFilename.focus();
      return;
    }

    const targetPath = [saveDirectory.value, filename].filter(Boolean).join('/');
    if (saveDialogFiles.has(targetPath) && targetPath !== state.path &&
        !confirm(`"${targetPath}" already exists. Overwrite it?`)) {
      return;
    }

    saveConfirm.disabled = true;
    try {
      await Api.writeFile(targetPath, textarea.value);
      state.path = targetPath;
      state.dirty = false;
      dirtyBadge.classList.add('hidden');
      pathLabel.textContent = targetPath;
      appendEvent({ type: 'file_saved', path: targetPath, session_id: 'you' });
      updateBytes();
      saveDialog.close();
      workspaceTree.reload();
    } catch (err) {
      saveError.textContent = `Save failed: ${err.message}`;
      saveError.classList.remove('hidden');
    } finally {
      saveConfirm.disabled = false;
    }
  }

  function updateBytes() {
    bytesLabel.textContent = `${new Blob([textarea.value]).size} bytes`;
  }

  function updatePos() {
    const upto = textarea.value.slice(0, textarea.selectionStart);
    const lines = upto.split('\n');
    posLabel.textContent = `Ln ${lines.length}, Col ${lines[lines.length - 1].length + 1}`;
  }

  textarea.addEventListener('input', () => {
    if (!state.dirty) { state.dirty = true; dirtyBadge.classList.remove('hidden'); }
    updateBytes();
  });
  textarea.addEventListener('keyup', updatePos);
  textarea.addEventListener('click', updatePos);
  textarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); saveFile(); }
  });

  container.querySelector('#editor-save').addEventListener('click', openSaveDialog);
  container.querySelector('#editor-save-form').addEventListener('submit', (event) => {
    event.preventDefault();
    saveFile();
  });
  container.querySelector('#editor-save-cancel').addEventListener('click', () => saveDialog.close());
  container.querySelector('#editor-reload').addEventListener('click', () => {
    if (state.path) openFile(state.path);
  });

  // --- WebSocket session event bus ----------------------------------------
  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/api/ws`);
    state.ws = ws;

    ws.onopen = () => { wsBadge.textContent = 'WS ●'; wsBadge.className = 'badge badge-success'; };
    ws.onclose = () => {
      wsBadge.textContent = 'WS ○'; wsBadge.className = 'badge badge-danger';
      eventLog.insertAdjacentHTML('beforeend',
        '<p class="text-muted small">Disconnected. Reconnecting…</p>');
      setTimeout(connectWs, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === 'connected') {
          if (!sessionEvents.length) {
            eventLog.innerHTML = `<p class="text-muted small">Connected as session ${esc(data.session_id)}</p>`;
          }
        } else if (data.type !== 'pong') {
          appendEvent(data);
        }
      } catch (_) { /* non-JSON frame */ }
    };
  }

  function sendWs(payload) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify(payload));
    }
  }

  function appendEvent(data) {
    if (eventLog.querySelector('.text-muted.small') && eventLog.children.length === 1 &&
        eventLog.textContent.includes('Disconnected')) {
      eventLog.innerHTML = '';
    }
    const el = document.createElement('div');
    el.className = `event-item ${data.type}`;
    const eventData = {
      type: String(data.type || 'unknown'),
      path: data.path || '',
      session_id: data.session_id || '',
      data: data.data || {}
    };
    sessionEvents.push(eventData);
    const detailText = eventData.type === 'tool_executed'
      ? `${eventData.data.status || 'unknown'}${eventData.data.origin ? ` · ${eventData.data.origin}` : ''}\nArgs: ${JSON.stringify(eventData.data.args || {})}${eventData.data.error ? `\nError: ${eventData.data.error}` : ''}`
      : '';
    const eventText = [
      eventData.type.replace(/_/g, ' '),
      eventData.path,
      eventData.session_id,
      detailText
    ].filter(Boolean).join('\n');
    const detailElement = detailText
      ? `<span class="event-details">${esc(detailText)}</span>`
      : '';
    el.innerHTML = `<span class="event-type">${esc(eventData.type.replace(/_/g, ' '))}</span>
      <span class="event-path">${esc(eventData.path)}</span>
      <span class="event-who text-muted">${esc(eventData.session_id)}</span>${detailElement}`;
    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-sm btn-ghost event-copy-btn';
    copyButton.textContent = 'Copy';
    copyButton.setAttribute('aria-label', `Copy ${eventData.type.replace(/_/g, ' ')} event`);
    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(eventText);
        copyButton.textContent = 'Copied!';
        setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
      } catch (err) {
        copyButton.textContent = 'Copy failed';
      }
    });
    el.appendChild(copyButton);
    eventLog.appendChild(el);
    while (sessionEvents.length > 60) {
      sessionEvents.shift();
      const firstEvent = eventLog.querySelector('.event-item');
      if (firstEvent) firstEvent.remove();
    }
    eventLog.scrollTop = eventLog.scrollHeight;
  }

  connectWs();

  if (initialPath) openFile(initialPath);
}

`

### frontend/static/js/prompt_creation.js

`javascript
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderPromptCreationView(container) {
  container.innerHTML = `
    <div class="testing-layout">
      <section class="card testing-builder">
        <div class="card-head">
          <h3>Prompt Creation & Assembly</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

        <div id="tb-cat-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Category</h4>
          <div class="form-row">
            <input type="text" id="cat-id-input" class="form-input" placeholder="Category ID / Slug (e.g. constraints)" required>
            <input type="text" id="cat-name-input" class="form-input" placeholder="Category Name (e.g. Constraints)" required>
          </div>
          <div class="form-row">
            <input type="text" id="cat-desc-input" class="form-input" placeholder="Description (optional)">
            <input type="text" id="cat-header-input" class="form-input" placeholder="Required Header (e.g. constraints)">
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="cat-save-btn">Save Category</button>
            <button type="button" class="btn btn-sm" id="cat-cancel-btn">Cancel</button>
          </div>
        </div>

        <div id="tb-part-form" class="card bg-elev hidden" style="margin-bottom: 0.75rem; padding: 0.75rem;">
          <h4 style="margin-bottom: 0.5rem;">Add New Prompt Part</h4>
          <div class="form-row">
            <select id="part-cat-select" class="form-select"></select>
            <input type="text" id="part-title-input" class="form-input" placeholder="Part Title (e.g. JSON Format)" required>
          </div>
          <div class="form-row">
            <input type="text" id="part-slug-input" class="form-input" placeholder="Slug ID (optional)">
          </div>
          <div class="form-row">
            <textarea id="part-content-input" class="form-input" style="width: 100%; height: 80px;" placeholder="Prompt part markdown content…" required></textarea>
          </div>
          <div class="toolbar-row">
            <button type="button" class="btn btn-sm btn-primary" id="part-save-btn">Save Part</button>
            <button type="button" class="btn btn-sm" id="part-cancel-btn">Cancel</button>
          </div>
        </div>

        <div id="tb-categories" class="category-grid">
          <p class="text-muted">Loading categories…</p>
        </div>

        <textarea id="tb-preview" class="prompt-preview" readonly placeholder="Assembled prompt preview will appear here…"></textarea>
        <div class="toolbar-row">
          <span id="tb-stats" class="text-muted small"></span>
          <span class="spacer"></span>
          <select id="tb-publish-agent" class="form-select" style="max-width: 180px;">
            <option value="">Select agent…</option>
          </select>
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <button type="button" class="btn btn-sm btn-primary" id="tb-publish">Save to Agent</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
      </section>

      <section class="card">
        <div class="card-head">
          <h3>Available Core Engine Tools</h3>
          <button type="button" class="btn btn-sm" id="btn-refresh-tools">Refresh Tools</button>
        </div>
        <p class="text-muted small">Tools retrieved from <code>core_engine/interface.py</code> for prompt reference.</p>
        <button type="button" class="btn btn-sm btn-primary" id="btn-add-tools-to-prompt">
          Add Selected Tools to Prompt
        </button>
        <div id="tools-list-container" style="overflow-y: auto; max-height: 500px;" class="mt-2">
          <p class="text-muted">Loading available tools...</p>
        </div>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const toolsContainer = container.querySelector('#tools-list-container');
  const publishAgentSel = container.querySelector('#tb-publish-agent');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let availableTools = [];
  let promptBase = '';
  let promptPartCount = 0;
  const promptTools = new Map();

  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
  }

  async function loadCoreTools() {
    try {
      toolsContainer.innerHTML = '<p class="text-muted">Fetching tools from core_engine...</p>';
      const res = await Api.getTools();
      availableTools = res.tools || [];

      if (!availableTools.length) {
        toolsContainer.innerHTML = '<p class="text-muted">No tools currently registered in core engine.</p>';
        return;
      }

      toolsContainer.innerHTML = availableTools.map((t, index) => `
        <div class="category-block mt-2">
          <div class="category-head">
            <label class="checkbox-row" style="margin:0;">
              <input type="checkbox" value="${index}" data-tool>
              <strong>🛠️ ${esc(t.name)}</strong>
            </label>
            <span class="badge badge-accent">${esc(t.provider)}</span>
          </div>
          <p class="text-muted small mt-2"><code>${esc(t.signature)}</code></p>
          <p class="small text-light">${esc(Array.isArray(t.description) ? t.description.join(' ') : t.description)}</p>
        </div>
      `).join('');
    } catch (err) {
      toolsContainer.innerHTML = `<p class="text-danger">Failed to retrieve tools: ${esc(err.message)}</p>`;
    }
  }

  function updatePromptPreview() {
    const toolSection = [...promptTools.values()].map(tool => {
      const description = Array.isArray(tool.description)
        ? tool.description.join(' ')
        : tool.description;
      return [
        `### ${tool.name}`,
        `- Provider: ${tool.provider}`,
        `- Signature: ${tool.signature}`,
        description ? `- Description: ${description}` : ''
      ].filter(Boolean).join('\n');
    }).join('\n\n');

    preview.value = [promptBase, toolSection ? `## Available Tools\n\n${toolSection}` : '']
      .filter(Boolean)
      .join('\n\n');
    stats.textContent = `${promptPartCount} parts · ${preview.value.length} chars`;
  }

  async function loadPromptAgents() {
    try {
      const [workspaceData, codeBuilderData] = await Promise.all([
        Api.getAgents(),
        Api.getCodeBuilderAgents()
      ]);
      const agents = [
        ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
        ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' }))
      ];
      publishAgentSel.innerHTML = agents.length
        ? agents.map(a => `<option value="${esc(a.environment)}:${esc(a.id)}">${esc(a.name)} (${esc(a.id)}) — ${a.environment === 'codebuilder' ? 'CodeBuilder' : 'Workspace'}</option>`).join('')
        : '<option value="">No agents found</option>';
    } catch (err) {
      publishAgentSel.innerHTML = `<option value="">${esc(err.message)}</option>`;
    }
  }

  async function loadManifest() {
    try {
      const data = await Api.getPromptCategories();
      manifest = data;
      renderCategories(manifest);
      populateCategoryDropdown(manifest.categories || []);
    } catch (err) {
      catBox.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function populateCategoryDropdown(categories) {
    partCatSelect.innerHTML = categories.length
      ? categories.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)})</option>`).join('')
      : '<option value="">No categories available</option>';
  }

  function renderCategories(data) {
    const cats = data.categories || [];
    const uncategorized = data.uncategorized_parts || [];

    let html = cats.map(cat => `
      <div class="category-block">
        <div class="category-head">
          <div style="display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap;">
            <strong>${esc(cat.name)}</strong>
            ${cat.required_header ? `<span class="badge badge-accent">## ${esc(cat.required_header)}</span>` : ''}
          </div>
          <button type="button" class="btn btn-ghost btn-sm text-danger" title="Delete category '${esc(cat.name)}'" data-del-cat="${esc(cat.id)}" style="padding: 0 0.3rem;">✕</button>
        </div>
        <p class="text-muted small">${esc(cat.description || '')}</p>
        ${(cat.parts || []).map(p => `
          <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
            <label class="checkbox-row" style="flex: 1; margin: 0;">
              <input type="checkbox" value="${esc(p.id)}" data-part>
              <span>${esc(p.title)}</span>
            </label>
            <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
          </div>`).join('') || '<p class="text-muted small">No parts.</p>'}
      </div>`).join('');

    if (uncategorized.length) {
      html += `
        <div class="category-block">
          <div class="category-head">
            <strong>Uncategorized</strong>
          </div>
          <p class="text-muted small">Parts without a matching category definition.</p>
          ${uncategorized.map(p => `
            <div class="part-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.25rem;">
              <label class="checkbox-row" style="flex: 1; margin: 0;">
                <input type="checkbox" value="${esc(p.id)}" data-part>
                <span>${esc(p.title)}</span>
              </label>
              <button type="button" class="btn btn-ghost btn-sm text-muted" title="Delete part" data-del-part="${esc(p.id)}" style="padding: 0 0.3rem;">✕</button>
            </div>`).join('')}
        </div>`;
    }

    catBox.innerHTML = html || '<p class="text-danger">No categories found.</p>';
  }

  loadCoreTools();
  loadManifest();
  loadPromptAgents();

  container.querySelector('#btn-refresh-tools').addEventListener('click', loadCoreTools);

  container.querySelector('#btn-add-tools-to-prompt').addEventListener('click', () => {
    const selected = [...toolsContainer.querySelectorAll('[data-tool]:checked')];
    if (!selected.length) return showMsg('Select at least one core engine tool.', true);

    selected.forEach(input => {
      const tool = availableTools[Number(input.value)];
      if (tool) promptTools.set(tool.name, tool);
    });
    updatePromptPreview();
    showMsg(`${selected.length} selected tool${selected.length === 1 ? '' : 's'} added to the prompt.`);
  });

  container.querySelector('#tb-toggle-cat-form').addEventListener('click', () => {
    catForm.classList.toggle('hidden');
    partForm.classList.add('hidden');
  });

  container.querySelector('#cat-cancel-btn').addEventListener('click', () => {
    catForm.classList.add('hidden');
  });

  container.querySelector('#tb-toggle-part-form').addEventListener('click', () => {
    partForm.classList.toggle('hidden');
    catForm.classList.add('hidden');
  });

  container.querySelector('#part-cancel-btn').addEventListener('click', () => {
    partForm.classList.add('hidden');
  });

  async function submitCategory() {
    const id = container.querySelector('#cat-id-input').value.trim();
    const name = container.querySelector('#cat-name-input').value.trim();
    const desc = container.querySelector('#cat-desc-input').value.trim();
    const header = container.querySelector('#cat-header-input').value.trim();

    if (!id || !name) return showMsg('Category ID and Name are required.', true);

    try {
      await Api.addPromptCategory(id, name, desc, header);
      catForm.classList.add('hidden');
      container.querySelector('#cat-id-input').value = '';
      container.querySelector('#cat-name-input').value = '';
      container.querySelector('#cat-desc-input').value = '';
      container.querySelector('#cat-header-input').value = '';
      showMsg(`Category '${name}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#cat-save-btn').addEventListener('click', submitCategory);

  catForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitCategory();
      }
    });
  });

  async function submitPart() {
    const category = partCatSelect.value;
    const title = container.querySelector('#part-title-input').value.trim();
    const slug = container.querySelector('#part-slug-input').value.trim();
    const content = container.querySelector('#part-content-input').value.trim();

    if (!category || !title || !content) return showMsg('Category, Part Title, and Content are required.', true);

    try {
      await Api.addPromptPart(category, title, content, slug || null);
      partForm.classList.add('hidden');
      container.querySelector('#part-title-input').value = '';
      container.querySelector('#part-slug-input').value = '';
      container.querySelector('#part-content-input').value = '';
      showMsg(`Prompt Part '${title}' added successfully.`);
      await loadManifest();
    } catch (err) {
      showMsg(err.message, true);
    }
  }

  container.querySelector('#part-save-btn').addEventListener('click', submitPart);

  partForm.querySelectorAll('input, textarea').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        submitPart();
      }
    });
  });

  catBox.addEventListener('click', async (e) => {
    const delCatBtn = e.target.closest('[data-del-cat]');
    if (delCatBtn) {
      const catId = delCatBtn.getAttribute('data-del-cat');
      if (confirm(`Are you sure you want to delete category '${catId}' and its parts?`)) {
        try {
          await Api.deletePromptCategory(catId);
          showMsg(`Category '${catId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
      return;
    }

    const delPartBtn = e.target.closest('[data-del-part]');
    if (delPartBtn) {
      const partId = delPartBtn.getAttribute('data-del-part');
      if (confirm(`Delete prompt part '${partId}'?`)) {
        try {
          await Api.deletePromptPart(partId);
          showMsg(`Prompt part '${partId}' deleted.`);
          await loadManifest();
        } catch (err) {
          showMsg(err.message, true);
        }
      }
    }
  });

  function selectedParts() {
    return [...catBox.querySelectorAll('[data-part]:checked')].map(el => el.value);
  }

  container.querySelector('#tb-assemble').addEventListener('click', async () => {
    const parts = selectedParts();
    if (!parts.length) return showMsg('Select at least one prompt part.', true);
    try {
      const res = await Api.assemblePrompt(parts);
      promptBase = res.prompt;
      promptPartCount = res.part_count;
      updatePromptPreview();
      showMsg('Prompt assembled.');
    } catch (err) {
      showMsg(err.message, true);
    }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try {
      await navigator.clipboard.writeText(preview.value);
      showMsg('Copied to clipboard.');
    } catch (_) {
      preview.select();
      document.execCommand('copy');
      showMsg('Copied.');
    }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const [environment, agentId] = publishAgentSel.value.split(':', 2);
    if (!environment || !agentId) return showMsg('Select an agent to publish first.', true);
    if (!preview.value.trim()) return showMsg('Assemble a prompt before saving it to an agent.', true);
    try {
      const res = await Api.publishAgent(agentId, 'snapshot', preview.value, environment);
      showMsg(`Saved to ${res.path} and ${res.metadata_path} (headers ${res.header_report.verdict}; snapshot ${res.snapshot}).`);
    } catch (err) {
      showMsg(err.message, true);
    }
  });
}

`

### frontend/static/js/test_panel.js

`javascript
const TEST_FUNCTIONS = [
  { id: 'runTestSuite', label: 'Run Test Suite', icon: 'play-circle', action: null },
  { id: 'debugAgent', label: 'Debug Agent', icon: 'bug', action: null },
  { id: 'promptInspector', label: 'Prompt Inspector', icon: 'terminal', action: null },
  { id: 'outputEvaluator', label: 'Output Evaluator', icon: 'check-square', action: null },
  { id: 'benchmark', label: 'Benchmark', icon: 'gauge', action: null },
  { id: 'apiLogs', label: 'API Logs', icon: 'file-code', action: null },
  { id: 'diagnostics', label: 'Diagnostics', icon: 'activity', action: null },
  { id: 'wipeChat', label: 'Wipe Chat', icon: 'trash-2', action: null }
];

export function buildTestPanel(containerId, actions = {}) {
  const container = typeof containerId === 'string'
    ? document.getElementById(containerId)
    : containerId;

  if (!container) {
    console.error('Test panel container not found:', containerId);
    return;
  }

  container.replaceChildren();

  TEST_FUNCTIONS.forEach((test) => {
    const action = actions[test.id] || test.action;
    const button = document.createElement('button');
    const icon = document.createElement('i');
    const label = document.createElement('span');

    button.className = 'test-function';
    button.type = 'button';
    button.dataset.testFunction = test.id;
    icon.setAttribute('data-lucide', test.icon);
    label.textContent = test.label;
    button.append(icon, label);

    if (typeof action !== 'function') {
      button.classList.add('disabled');
      button.disabled = true;
      button.title = 'Not implemented yet';
    } else {
      button.title = test.label;
      button.addEventListener('click', action);
    }

    container.appendChild(button);
  });

  const todoSection = document.createElement('div');
  todoSection.className = 'todo-selector-section';

  const todoLabel = document.createElement('label');
  todoLabel.className = 'model-picker-label small text-muted';
  todoLabel.htmlFor = 'todo-file-select';
  todoLabel.textContent = 'Select To-Do File';

  const todoSelect = document.createElement('select');
  todoSelect.id = 'todo-file-select';
  todoSelect.className = 'form-select';
  todoSelect.setAttribute('aria-label', 'Select a To-Do file');

  const refreshTodoFiles = document.createElement('button');
  refreshTodoFiles.id = 'todo-file-refresh';
  refreshTodoFiles.className = 'btn btn-sm';
  refreshTodoFiles.type = 'button';
  refreshTodoFiles.textContent = 'Refresh lists';
  refreshTodoFiles.title = 'Refresh Markdown to-do lists';

  const loadingOption = document.createElement('option');
  loadingOption.value = '';
  loadingOption.textContent = 'Loading Markdown lists...';
  todoSelect.appendChild(loadingOption);

  todoSection.append(todoLabel, todoSelect, refreshTodoFiles);
  container.appendChild(todoSection);

  if (typeof globalThis.lucide?.createIcons === 'function') {
    globalThis.lucide.createIcons();
  }
}

`

### frontend/static/js/testing.js

`javascript
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

export function renderTestingView(container) {
  container.innerHTML = `
    <div class="card testing-runner">
      <div class="card-head">
        <h3>Prompt Header Evaluation Battery</h3>
        <button type="button" class="btn btn-sm btn-primary" id="ht-run">Run Header Tests</button>
      </div>
      <div class="form-row">
        <select id="ht-agent" class="form-select">
          <option value="">Loading agents…</option>
        </select>
      </div>
      <div id="ht-results" class="ht-results mt-3">
        <p class="text-muted">Select an agent profile to run section-header verification (role, purpose, boundaries, output format).</p>
      </div>
    </div>`;

  const agentSel = container.querySelector('#ht-agent');
  const results = container.querySelector('#ht-results');

  Promise.all([Api.getAgents(), Api.getCodeBuilderAgents()]).then(([workspaceData, codeBuilderData]) => {
    const agents = [
      ...(workspaceData.agents || []).map(agent => ({ ...agent, environment: 'workspace' })),
      ...(codeBuilderData.agents || []).map(agent => ({ ...agent, environment: 'codebuilder' }))
    ];
    agentSel.innerHTML = agents.length
      ? agents.map(agent => `<option value="${esc(agent.id)}" data-environment="${agent.environment}">${esc(agent.name)} (${esc(agent.id)}) · ${agent.environment === 'codebuilder' ? 'CodeBuilder' : 'Workspace'}</option>`).join('')
      : '<option value="">No agents found</option>';
  }).catch(err => {
    agentSel.innerHTML = `<option value="">Error: ${esc(err.message)}</option>`;
  });

  function renderReport(report) {
    const header = `
      <div class="ht-summary ${report.passed ? 'pass' : 'fail'}">
        <strong>Verdict: ${esc(report.verdict)}</strong>
        <span>Overall Score: ${esc(report.overall_score)} (${esc(report.headers_passed)}/${esc(report.headers_total)} headers passed)</span>
      </div>`;

    const rows = (report.results || []).map(r => `
      <div class="ht-header ${r.passed ? 'pass' : 'fail'}">
        <div class="ht-header-head">
          <span class="ht-hash">## ${esc(r.header)}</span>
          <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}">${esc(Number(r.score || 0).toFixed(2))}</span>
        </div>
        ${((r.questions || []).map(q => `
          <div class="ht-question">
            <span class="ht-q-status ${q.passed ? 'pass' : 'fail'}">${q.passed ? '✓' : '✗'}</span>
            <div>
              <div>${esc(q.question)}</div>
              <div class="text-muted small">${esc(q.evidence)} · score ${esc(q.score)}</div>
            </div>
          </div>`).join(''))}
      </div>`).join('');

    const extras = report.extra_headers?.length
      ? `<p class="text-muted small">Extra headers: ${esc(report.extra_headers.join(', '))}</p>`
      : '';

    return header + rows + extras;
  }

  container.querySelector('#ht-run').addEventListener('click', async () => {
    if (!agentSel.value) return;
    results.innerHTML = '<p class="text-muted">Executing header battery evaluation...</p>';
    try {
      const environment = agentSel.selectedOptions[0]?.dataset.environment || 'workspace';
      const report = await Api.runHeaderTests(agentSel.value, environment);
      results.innerHTML = renderReport(report);
    } catch (err) {
      results.innerHTML = `<p class="text-danger">Error: ${esc(err.message)}</p>`;
    }
  });

  renderToolWorkbench(container);
}

function renderToolWorkbench(container) {
  container.insertAdjacentHTML('beforeend', `
    <section class="card tool-workbench mt-3" aria-labelledby="tool-workbench-title">
      <div class="card-head">
        <div>
          <h3 id="tool-workbench-title">Tool Function Testing Workbench</h3>
          <p class="text-muted small">Tests run on this computer using the local Python interpreter. Only run code you trust: tested code can access files, network, and resources available to your user account. Each run has a 5-second timeout.</p>
        </div>
        <button type="button" class="btn btn-sm" id="tw-reset">Reset</button>
      </div>
      <div class="tool-workbench-grid">
        <label class="tool-workbench-field">
          <span>LLM model</span>
          <span class="tool-workbench-model">
            <select id="tw-model" class="form-select" aria-label="LLM model">
              <option value="">Loading models…</option>
            </select>
            <button type="button" class="btn btn-sm" id="tw-refresh-models">Refresh</button>
          </span>
        </label>
        <label class="tool-workbench-field tool-workbench-wide">
          <span>Function code</span>
          <textarea id="tw-code" class="tool-workbench-editor" rows="12" spellcheck="false"></textarea>
        </label>
        <label class="tool-workbench-field">
          <span>Function input (JSON)</span>
          <textarea id="tw-input" class="tool-workbench-editor" rows="5" spellcheck="false"></textarea>
          <span class="text-muted small">When the model calls the function, this shows the arguments it sent. If it makes no valid call, the current JSON is left unchanged.</span>
        </label>
        <label class="tool-workbench-field">
          <span>Prompt for LLM tool calling</span>
          <textarea id="tw-prompt" class="form-input" rows="5"></textarea>
        </label>
      </div>
      <div class="tool-workbench-actions">
        <button type="button" class="btn btn-primary" id="tw-run">Run Code Test</button>
        <button type="button" class="btn" id="tw-run-llm">Test Tool with LLM</button>
        <button type="button" class="btn" id="tw-save" disabled>Save Test Report (.md)</button>
        <button type="button" class="btn" id="tw-promote" disabled
                title="Run a successful test before adding a tool">Add Passed Tool to Library</button>
        <span id="tw-status" class="text-muted small" role="status">Ready</span>
      </div>
      <label id="tw-llm-response-section" class="tool-workbench-field" hidden>
        <span>LLM response / tool call</span>
        <pre id="tw-llm-response" class="tool-workbench-output" aria-live="polite"></pre>
      </label>
      <label class="tool-workbench-field">
        <span>Test output</span>
        <pre id="tw-output" class="tool-workbench-output" aria-live="polite">Run a test to see its result.</pre>
      </label>
      <div class="tool-workbench-library">
        <h4>Registered Tool Library</h4>
        <p class="text-muted small">Promoted functions are appended to <code>workspace/tools/tool_library.py</code> so the library can be committed as one module.</p>
        <div id="tw-library" class="text-muted small">Loading tools…</div>
      </div>
      <p class="text-muted small">Promoted code is trusted application code and will run in the Novous backend when an agent invokes it.</p>
    </section>`);

  const codeField = container.querySelector('#tw-code');
  const inputField = container.querySelector('#tw-input');
  const promptField = container.querySelector('#tw-prompt');
  const modelSelect = container.querySelector('#tw-model');
  const runButton = container.querySelector('#tw-run');
  const llmButton = container.querySelector('#tw-run-llm');
  const saveButton = container.querySelector('#tw-save');
  const promoteButton = container.querySelector('#tw-promote');
  const output = container.querySelector('#tw-output');
  const llmResponseSection = container.querySelector('#tw-llm-response-section');
  const llmResponse = container.querySelector('#tw-llm-response');
  const status = container.querySelector('#tw-status');
  const library = container.querySelector('#tw-library');

  const defaultCode = `def calculate_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate shipping fee from package weight and distance."""
    base_rate = 5.0
    cost = base_rate + (weight_kg * 1.5) + (distance_km * 0.05)
    return {
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "shipping_cost": round(cost, 2)
    }`;
  const defaultInput = `{
  "weight_kg": 4.5,
  "distance_km": 120.0
}`;
  const defaultPrompt = 'Calculate shipping for a 4.5kg package traveling 120km using the shipping tool.';
  let lastPassed = null;
  let lastTestReport = null;
  let busy = false;

  codeField.value = defaultCode;
  inputField.value = defaultInput;
  promptField.value = defaultPrompt;

  function enableTabIndent(field) {
    field.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      event.preventDefault();
      const start = field.selectionStart;
      const end = field.selectionEnd;
      field.value = field.value.slice(0, start) + '    ' + field.value.slice(end);
      field.selectionStart = field.selectionEnd = start + 4;
    });
  }

  function createTestReport(result, context = {}) {
    return {
      tested_at: new Date().toISOString(),
      execution_mode: context.execution_mode || 'local-python',
      model_used: context.model_used || null,
      function_code: context.function_code ?? codeField.value,
      function_input: Object.prototype.hasOwnProperty.call(context, 'function_input')
        ? context.function_input
        : inputField.value,
      prompt: context.prompt ?? '',
      test_output: result
    };
  }

  function markdownCodeBlock(value, language = '') {
    const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    const longestFence = Math.max(2, ...((text.match(/`+/g) || []).map(run => run.length)));
    const fence = '`'.repeat(longestFence + 1);
    return `${fence}${language}\n${text}\n${fence}`;
  }

  function renderTestReport(report) {
    const testOutput = report.test_output || {};
    const execution = testOutput.tool_execution_result || testOutput;
    const passed = testOutput.status === 'SUCCESS';
    const fields = [
      `- **Result:** ${passed ? 'PASS' : 'FAIL'}`,
      `- **Tested at (UTC):** ${report.tested_at}`,
      `- **Execution mode:** ${report.execution_mode}`,
      `- **LLM used:** ${report.model_used || 'No — direct local Python test'}`,
      `- **Function:** ${execution.function_name || 'Not identified'}`,
      `- **Error code:** ${testOutput.error_code || execution.error_code || 'None'}`
    ];
    const sections = [
      '# Tool Function Test Report',
      '',
      ...fields,
      '',
      '## LLM Prompt',
      '',
      report.prompt ? markdownCodeBlock(report.prompt, 'text') : '_No LLM prompt was used._',
      '',
      '## Function Input',
      '',
      markdownCodeBlock(report.function_input, 'json'),
      '',
      '## Function Code',
      '',
      markdownCodeBlock(report.function_code, 'python'),
      '',
      '## Result',
      '',
      `**Status:** ${testOutput.status || 'ERROR'}`,
      ''
    ];

    if (execution.output !== undefined) {
      sections.push('### Function output', '', markdownCodeBlock(execution.output, 'json'), '');
    }
    if (testOutput.llm_text_response) {
      sections.push('### LLM response', '', markdownCodeBlock(testOutput.llm_text_response, 'text'), '');
    }
    if (testOutput.tool_calls_detected?.length) {
      sections.push(
        '### LLM tool calls',
        '',
        markdownCodeBlock(testOutput.tool_calls_detected, 'json'),
        ''
      );
    }
    if (testOutput.message) {
      sections.push('### Failure details', '', markdownCodeBlock(testOutput.message, 'text'), '');
    }
    for (const [label, value] of [
      ['Standard error', execution.stderr],
      ['Standard output', execution.stdout],
      ['Exit code', execution.exit_code]
    ]) {
      if (value !== undefined && value !== null && value !== '') {
        sections.push(`### ${label}`, '', markdownCodeBlock(value, 'text'), '');
      }
    }
    sections.push(
      '## Machine-readable JSON',
      '',
      'The complete report data is included below for reuse or automated processing.',
      '',
      markdownCodeBlock(report, 'json'),
      ''
    );
    return sections.join('\n');
  }

  function parseFunctionInput() {
    const parsed = JSON.parse(inputField.value || '{}');
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('Function input must be a JSON object.');
    }
    return parsed;
  }

  function updatePromotion() {
    const unchangedSincePass = lastPassed &&
      lastPassed.code === codeField.value &&
      lastPassed.input === inputField.value;
    let hasValidInput = true;
    try {
      parseFunctionInput();
    } catch (_) {
      hasValidInput = false;
    }
    promoteButton.disabled = busy || !unchangedSincePass || !hasValidInput;
  }

  function showResult(result, reportContext) {
    output.textContent = JSON.stringify(result, null, 2);
    lastTestReport = createTestReport(result, reportContext);
    saveButton.disabled = false;
    const passed = result.status === 'SUCCESS';
    status.textContent = passed ? 'Test passed' : 'Test failed';
    status.className = passed ? 'text-success small' : 'text-danger small';
    lastPassed = passed
      ? { code: codeField.value, input: inputField.value }
      : null;
    updatePromotion();
  }

  function showLlmResponse(result) {
    const sections = [];
    if (typeof result.llm_text_response === 'string' && result.llm_text_response) {
      sections.push(result.llm_text_response);
    }
    if (result.tool_calls_detected?.length) {
      sections.push(`Tool calls:\n${JSON.stringify(result.tool_calls_detected, null, 2)}`);
    }
    if (!sections.length) {
      sections.push(result.message || 'No response content was returned by the model.');
    }
    llmResponse.textContent = sections.join('\n\n');
    llmResponseSection.hidden = false;
  }

  async function loadModels() {
    modelSelect.replaceChildren(new Option('Loading models…', ''));
    try {
      const data = await Api.getModels();
      const models = data.models || [];
      modelSelect.replaceChildren();
      if (!models.length) {
        modelSelect.appendChild(new Option(data.error || 'No models found', ''));
        return;
      }
      models.forEach(model => modelSelect.appendChild(new Option(model, model)));
      modelSelect.value = models.includes(data.default) ? data.default : models[0];
    } catch (err) {
      modelSelect.replaceChildren(new Option(`Could not load models: ${err.message}`, ''));
    }
  }

  async function loadToolLibrary() {
    try {
      const data = await Api.getTools();
      const tools = data.tools || [];
      library.innerHTML = tools.length
        ? tools.map(tool => `
          <div class="tool-workbench-library-item">
            <code>${esc(tool.name)}</code>
            <span>${esc(tool.signature)}</span>
            ${tool.custom ? `
              <button type="button" class="btn btn-sm" data-tool-load="${esc(tool.name)}">Load</button>
              <button type="button" class="btn btn-sm" data-tool-delete="${esc(tool.name)}">Remove</button>
            ` : ''}
          </div>`).join('')
        : 'No tools registered.';
    } catch (err) {
      library.textContent = `Could not load tools: ${err.message}`;
    }
  }

  async function runTest(useLlm) {
    let functionInput;
    if (!useLlm) {
      try {
        functionInput = parseFunctionInput();
      } catch (err) {
        lastPassed = null;
        output.textContent = JSON.stringify({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        }, null, 2);
        lastTestReport = createTestReport({
          status: 'ERROR',
          error_code: 'ERR_INVALID_JSON_INPUT',
          message: err.message
        });
        saveButton.disabled = false;
        status.textContent = 'Test failed';
        status.className = 'text-danger small';
        updatePromotion();
        return;
      }
    }
    if (useLlm && !modelSelect.value) {
      status.textContent = 'Select an installed model first.';
      status.className = 'text-danger small';
      return;
    }

    let reportInput;
    try {
      reportInput = parseFunctionInput();
    } catch (_) {
      reportInput = inputField.value;
    }
    const reportContext = {
      execution_mode: useLlm ? 'local-llm-tool-call' : 'local-python',
      model_used: useLlm ? modelSelect.value : null,
      function_code: codeField.value,
      function_input: useLlm ? null : reportInput,
      prompt: useLlm ? promptField.value : ''
    };
    busy = true;
    lastPassed = null;
    updatePromotion();
    runButton.disabled = true;
    llmButton.disabled = true;
    status.textContent = useLlm ? 'Requesting local model tool call…' : 'Running with local Python…';
    status.className = 'text-muted small';
    output.textContent = 'Test in progress…';
    llmResponseSection.hidden = true;
    llmResponse.textContent = '';
    try {
      const result = useLlm
        ? await Api.testToolWithLlm(modelSelect.value, codeField.value, promptField.value)
        : await Api.executeToolTest(codeField.value, functionInput);
      if (useLlm) {
        showLlmResponse(result);
        if (result.function_input !== undefined) {
          inputField.value = JSON.stringify(result.function_input, null, 2);
          reportContext.function_input = result.function_input;
        }
      }
      showResult(result, reportContext);
    } catch (err) {
      const result = {
        status: 'ERROR',
        error_code: 'ERR_TOOL_TEST_FAILED',
        message: err.message
      };
      if (useLlm) showLlmResponse(result);
      output.textContent = JSON.stringify(result, null, 2);
      lastTestReport = createTestReport(result, reportContext);
      saveButton.disabled = false;
      status.textContent = 'Test failed';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
  }

  runButton.addEventListener('click', () => runTest(false));
  llmButton.addEventListener('click', () => runTest(true));
  container.querySelector('#tw-refresh-models').addEventListener('click', loadModels);
  library.addEventListener('click', async event => {
    const loadButton = event.target.closest('[data-tool-load]');
    const deleteButton = event.target.closest('[data-tool-delete]');
    if (loadButton) {
      try {
        const tool = await Api.getWorkbenchTool(loadButton.dataset.toolLoad);
        codeField.value = tool.source;
        lastPassed = null;
        updatePromotion();
        status.textContent = `Loaded ${tool.name} from ${tool.path} for testing`;
        status.className = 'text-muted small';
      } catch (err) {
        status.textContent = `Could not load tool: ${err.message}`;
        status.className = 'text-danger small';
      }
    }
    if (deleteButton && confirm(
      `Remove ${deleteButton.dataset.toolDelete} from the tool library? Existing agent sessions may keep the loaded function until reset.`
    )) {
      try {
        const deleted = await Api.deleteWorkbenchTool(deleteButton.dataset.toolDelete);
        await loadToolLibrary();
        status.textContent = `Removed ${deleted.name} from ${deleted.path}`;
        status.className = 'text-success small';
      } catch (err) {
        status.textContent = `Could not remove tool: ${err.message}`;
        status.className = 'text-danger small';
      }
    }
  });
  enableTabIndent(codeField);
  enableTabIndent(inputField);
  codeField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  inputField.addEventListener('input', () => {
    lastPassed = null;
    updatePromotion();
  });
  saveButton.addEventListener('click', async () => {
    if (!lastTestReport) return;
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    try {
      const saved = await Api.saveMarkdown(
        renderTestReport(lastTestReport),
        `novous-tool-test-${stamp}.md`
      );
      if (saved.locationChosen) {
        alert(`Test results saved as ${saved.filename}.`);
      } else {
        alert(`Test results download started: ${saved.filename}`);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        alert(`Could not save test results: ${err.message}`);
      }
    }
  });
  promoteButton.addEventListener('click', async () => {
    if (!lastPassed || !confirm(
      'Add this tested function to the tool library? Promoted code runs as trusted code in the Novous backend.'
    )) return;

    try {
      busy = true;
      runButton.disabled = true;
      llmButton.disabled = true;
      updatePromotion();
      status.textContent = 'Verifying test and adding tool…';
      const result = await Api.promoteTestedTool(codeField.value, parseFunctionInput());
      output.textContent = JSON.stringify(result, null, 2);
      status.textContent = `Added ${result.promoted.name} to the tool library`;
      status.className = 'text-success small';
      lastPassed = null;
      await loadToolLibrary();
    } catch (err) {
      output.textContent = JSON.stringify({
        status: 'ERROR',
        error_code: 'ERR_TOOL_PROMOTION_FAILED',
        message: err.message
      }, null, 2);
      status.textContent = 'Could not add tool';
      status.className = 'text-danger small';
    } finally {
      busy = false;
      runButton.disabled = false;
      llmButton.disabled = false;
      updatePromotion();
    }
  });

  container.querySelector('#tw-reset').addEventListener('click', () => {
    codeField.value = defaultCode;
    inputField.value = defaultInput;
    promptField.value = defaultPrompt;
    output.textContent = 'Run a test to see its result.';
    llmResponse.textContent = '';
    llmResponseSection.hidden = true;
    status.textContent = 'Ready';
    status.className = 'text-muted small';
    lastPassed = null;
    lastTestReport = null;
    saveButton.disabled = true;
    updatePromotion();
  });

  loadModels();
  loadToolLibrary();
}

`

### frontend/static/js/tree.js

`javascript
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/**
 * Interactive File Tree Component.
 * @param {HTMLElement} container
 * @param {{onSelect?: (path: string, type: string) => void, selectable?: string}} options
 */
export function renderTree(container, options = {}) {
  const { onSelect, selectable = 'file' } = options;

  container.innerHTML = `
    <div class="tree-toolbar">
      <button class="btn btn-sm" data-action="refresh" title="Refresh">⟳ Refresh</button>
      <button class="btn btn-sm" data-action="new-file" title="New file">+ File</button>
      <button class="btn btn-sm" data-action="new-dir" title="New folder">+ Dir</button>
    </div>
    <div class="tree-body" role="tree"></div>`;

  const body = container.querySelector('.tree-body');

  async function load() {
    try {
      const tree = await Api.getFileTree('');
      body.innerHTML = '';
      body.appendChild(buildNode(tree, 0));
    } catch (err) {
      body.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  }

  function buildNode(node, depth) {
    const row = document.createElement('div');
    row.className = 'tree-row';
    row.dataset.path = node.path;
    row.dataset.type = node.type;
    row.style.paddingLeft = `${depth * 14 + 6}px`;
    row.setAttribute('role', 'treeitem');

    const isDir = node.type === 'directory';
    row.innerHTML = `
      <span class="tree-icon">${isDir ? '▾' : '·'}</span>
      <span class="tree-name">${esc(node.name)}</span>`;

    const wrap = document.createElement('div');
    wrap.appendChild(row);

    row.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isDir) {
        const kids = wrap.querySelector(':scope > .tree-children');
        if (kids) {
          const hidden = kids.classList.toggle('hidden');
          row.querySelector('.tree-icon').textContent = hidden ? '▸' : '▾';
        }
      } else {
        body.querySelectorAll('.tree-row.selected').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        if (onSelect) onSelect(node.path, node.type);
      }
    });

    if (isDir && node.children && node.children.length) {
      const kidsWrap = document.createElement('div');
      kidsWrap.className = 'tree-children';
      node.children.forEach(child => kidsWrap.appendChild(buildNode(child, depth + 1)));
      wrap.appendChild(kidsWrap);
    } else if (isDir) {
      const kidsWrap = document.createElement('div');
      kidsWrap.className = 'tree-children hidden';
      wrap.appendChild(kidsWrap);
    }
    return wrap;
  }

  container.querySelector('[data-action="refresh"]').addEventListener('click', load);

  container.querySelector('[data-action="new-file"]').addEventListener('click', async () => {
    const path = prompt('New file path (relative to workspace):');
    if (!path) return;
    try {
      await Api.createPath(path, 'file');
      load();
      if (onSelect) onSelect(path, 'file');
    } catch (err) { alert(err.message); }
  });

  container.querySelector('[data-action="new-dir"]').addEventListener('click', async () => {
    const path = prompt('New folder path (relative to workspace):');
    if (!path) return;
    try {
      await Api.createPath(path, 'directory');
      load();
    } catch (err) { alert(err.message); }
  });

  load();
  return { reload: load };
}

`

### requirements.txt

`text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
websockets>=12.0
pydantic>=2.6.0
ollama>=0.1.7
langchain-core>=0.1.30
langgraph>=0.0.25
docling>=1.0.0
chromadb>=0.4.24
jinja2>=3.1.3
python-multipart>=0.0.9

`

### scripts/gen_app_snapshot.py

`python
﻿"""Generate a comprehensive, AI-agent-readable snapshot of the Novous application."""
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now().strftime("%Y%m%d")
try:
    COMMIT = os.popen("git rev-parse --short HEAD").read().strip()
except Exception:
    COMMIT = "unknown"

EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules", "dist", "build"}
INCLUDE_EXT = {".py", ".js", ".css", ".html", ".json", ".md", ".txt", ".bat", ".sh", ".yaml", ".yml", ".cfg", ".ini"}
SKIP_FILES = {"MASTER_COPY.md", "novous-ai-builder-prompt-v2.md"}

OUT = ROOT / "app_documentation" / f"NOVOUS_APP_SNAPSHOT_{TODAY}_new.md"


def get_lang(ext: str) -> str:
    ext = ext.lower().lstrip('.')
    return {
        "py": "python",
        "js": "javascript",
        "json": "json",
        "html": "html",
        "css": "css",
        "md": "markdown",
        "txt": "text",
        "bat": "batch",
        "sh": "bash",
        "yaml": "yaml",
        "yml": "yaml",
        "cfg": "ini",
        "ini": "ini",
    }.get(ext, ext)


def collect_files():
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT") or path.name.startswith("MASTER_COPY"):
            continue
        if path.suffix.lower() not in INCLUDE_EXT and path.name in {"Dockerfile", "Procfile"}:
            pass
        elif path.suffix.lower() not in INCLUDE_EXT:
            continue
        files.append(path)
    return files


def write_tree(f):
    f.write("## 3) File Structure Snapshot\n\n")
    for path in sorted(ROOT.rglob("*")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT") or path.name.startswith("MASTER_COPY"):
            continue
        f.write(f"- {rel}{'/' if path.is_dir() else ''}\n")
    f.write("\n")


def main():
    files = collect_files()
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Name: Novous Application Snapshot\n")
        f.write(f"Filename: {OUT.name}\n")
        f.write(f"Commit: {COMMIT}\n")
        f.write(f"Description: Self-contained reference for an AI agent. Captures Novous app purpose, architecture, file structure, and complete source code. Designed for grounding/understanding without repo access.\n\n")
        f.write("# NOVOUS APPLICATION SNAPSHOT\n\n")
        f.write("## 1) Overview\n\n")
        f.write("Novous is an agent orchestration/workspace system with FastAPI backend, static frontend, core engine for agents/tools, editor integration, workspace/agents configuration, and test environment.\n\n")
        f.write("Key components:\n- server.py: FastAPI app entrypoint serving static UI and API routes\n- core_engine/: agent factory, runtime, tool catalog, langgraph tools\n- editor/: editor session/operations/schemas/interface\n- frontend/: static assets and HTML pages (chat, editor, index, testing)\n- workspace/: agent definitions and workflow utilities\n- test_environment/: prompt builder, test runner, test agents\n\n")
        f.write("## 2) Table of Contents\n\n")
        f.write("1. Overview\n")
        f.write("2. File Structure Snapshot\n")
        f.write("3. Complete Source Code (by file)\n\n")
        write_tree(f)
        f.write("## 4) Complete Source Code (by file)\n\n")
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            lang = get_lang(path.suffix)
            f.write(f"### {rel}\n\n")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                text = f"<unreadable: {e}>"
            f.write(f"`{lang}\n{text}\n`\n\n")

    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()

`

### scripts/gen_master_copy.py

`python
"""Generate a single markdown master copy of the entire Novous source tree."""

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.now().strftime("%Y%m%d")
OUT = ROOT / "app_documentation" / f"MASTER_COPY_{TODAY}.md"

INCLUDE = {".py", ".js", ".css", ".html", ".json", ".md", ".bat", ".sh"}
EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules", "test_agents"}
MAX_FILE_BYTES = 200_000


def collect() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("MASTER_COPY") or path.name == "novous-ai-builder-prompt-v2.md":
            continue
        if path.suffix not in INCLUDE:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def main() -> None:
    files = collect()
    chunks = ["# Novous Agent Factory — Master Copy", "",
              f"Generated from `{ROOT}` — {len(files)} files.", ""]
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        chunks.append(f"## `{rel}`")
        chunks.append("```" + path.suffix.lstrip("."))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            text = f"<unreadable: {exc}>"
        if len(text.encode("utf-8")) > MAX_FILE_BYTES:
            text = text[:MAX_FILE_BYTES] + "\n... <truncated> ..."
        chunks.append(text)
        chunks.append("```")
        chunks.append("")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()

`

### scripts/venv.bat

`batch
@echo off
REM Virtualenv bootstrap for Novous Agent Factory (Windows)
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install fastapi uvicorn ollama
echo.
echo Virtualenv ready. Run: python server.py

`

### scripts/venv.sh

`bash
#!/usr/bin/env sh
# Virtualenv bootstrap for Novous Agent Factory (macOS/Linux)
set -e
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
. venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn ollama
echo
echo "Virtualenv ready. Run: python server.py"

`

### server.py

`python
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core_engine.interface import router as core_router
from editor.interface import router as editor_router
from workspace.interface import router as workspace_router
from test_environment.interface import router as test_router
from codebuilder.interface import router as codebuilder_router

app = FastAPI(title="Novous AGENT FACTORY", version="4.0.0")

# Mount Component Backend Routers
app.include_router(core_router)
app.include_router(editor_router)
app.include_router(workspace_router)
app.include_router(test_router)
app.include_router(codebuilder_router)

# Serve Static Assets (CSS, JS)
app.mount("/static", StaticFiles(directory=Path("frontend") / "static"), name="static")

# Mount Page Routes
@app.get("/")
def index_page():
    return FileResponse("frontend/pages/index.html")

@app.get("/editor")
def editor_page():
    return FileResponse("frontend/pages/editor.html")

@app.get("/codebuilder")
def codebuilder_page():
    return FileResponse("frontend/pages/codeBuilder.html")

@app.get("/chat")
def chat_page():
    return FileResponse("frontend/pages/chat.html")

@app.api_route("/test", methods=["GET", "POST"])
def test_page():
    return FileResponse("frontend/pages/testing.html")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("PROJECT_MANAGER_HOST", "127.0.0.1")
    port = int(os.getenv("PROJECT_MANAGER_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)

`

### test_environment/__init__.py

`python

`

### test_environment/interface.py

`python
"""Test Environment Doorway: Python API & FastAPI Router
(/api/testing/*, /api/prompt-builder/*)."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import prompt_builder, test_runner, tool_workbench

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder"] = "workspace"


class ToolWorkbenchRequest(BaseModel):
    tool_code: str = Field(..., min_length=1, max_length=50000)
    function_input: dict[str, Any] = Field(default_factory=dict)


class ToolWorkbenchLLMRequest(ToolWorkbenchRequest):
    model: str = Field(..., min_length=1, max_length=120)
    user_prompt: str = Field(..., min_length=1, max_length=5000)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""
    markdown: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder"] = "workspace"


class AddCategoryRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""
    required_header: str = ""


class AddPartRequest(BaseModel):
    category: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    id: str | None = None


# --- Prompt builder --------------------------------------------------------

@router.get("/api/prompt-builder/categories")
def api_categories():
    return prompt_builder.get_manifest()


@router.post("/api/prompt-builder/categories")
def api_add_category(req: AddCategoryRequest):
    try:
        return prompt_builder.add_category(
            cat_id=req.id,
            name=req.name,
            description=req.description,
            required_header=req.required_header,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/categories/{cat_id}")
def api_delete_category(cat_id: str):
    try:
        return prompt_builder.delete_category(cat_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/prompt-builder/parts")
def api_parts(category: str | None = None):
    return {"parts": prompt_builder.load_parts(category)}


@router.post("/api/prompt-builder/parts")
def api_add_part(req: AddPartRequest):
    try:
        return prompt_builder.add_part(
            category=req.category,
            title=req.title,
            content=req.content,
            part_id=req.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/parts/{part_id:path}")
def api_delete_part(part_id: str):
    try:
        return prompt_builder.delete_part(part_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/prompt-builder/assemble")
def api_assemble(req: AssembleRequest):
    if not req.parts and not req.extra_instructions.strip():
        raise HTTPException(status_code=400, detail="Select at least one prompt part.")
    result = prompt_builder.assemble_prompt(req.parts, req.extra_instructions)
    if result["missing"]:
        raise HTTPException(status_code=400,
                            detail=f"Unknown part ids: {', '.join(result['missing'])}")
    return result


# --- Test runner -----------------------------------------------------------

@router.post("/api/testing/tool-workbench/execute")
def api_execute_tool_test(req: ToolWorkbenchRequest):
    return tool_workbench.run_python_tool(req.tool_code, req.function_input)


@router.post("/api/testing/tool-workbench/test-with-llm")
def api_test_tool_with_llm(req: ToolWorkbenchLLMRequest):
    try:
        function = tool_workbench.get_function_definition(req.tool_code)
        schema = tool_workbench.get_tool_schema(function)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        import ollama
        response = ollama.chat(
            model=req.model,
            messages=[{"role": "user", "content": req.user_prompt}],
            tools=[schema],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM tool-call request failed: {exc}") from exc

    message = response.get("message", {})
    tool_calls = message.get("tool_calls") or []
    llm_text_response = message.get("content", "")
    if not tool_calls:
        return {
            "status": "ERROR",
            "error_code": "ERR_NO_TOOL_CALL",
            "message": "The selected model did not return a tool call.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": [],
        }

    call = tool_calls[0].get("function", {})
    if call.get("name") != function.name:
        return {
            "status": "ERROR",
            "error_code": "ERR_UNEXPECTED_TOOL_CALL",
            "message": "The model called an unexpected tool function.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
        }
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return {
                "status": "ERROR",
                "error_code": "ERR_INVALID_TOOL_ARGUMENTS",
                "message": "The model returned invalid JSON tool arguments.",
                "llm_text_response": llm_text_response,
                "tool_calls_detected": tool_calls,
            }
    if not isinstance(arguments, dict):
        return {
            "status": "ERROR",
            "error_code": "ERR_INVALID_TOOL_ARGUMENTS",
            "message": "The model's tool arguments must be a JSON object.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
        }

    execution = tool_workbench.run_python_tool(req.tool_code, arguments)
    return {
        "status": execution["status"],
        "error_code": execution["error_code"],
        "llm_text_response": llm_text_response,
        "tool_calls_detected": tool_calls,
        "function_input": arguments,
        "tool_execution_result": execution,
    }


@router.post("/api/testing/tool-workbench/promote")
def api_promote_tool(req: ToolWorkbenchRequest):
    try:
        function = tool_workbench.get_function_definition(req.tool_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    execution = tool_workbench.run_python_tool(req.tool_code, req.function_input)
    if execution["status"] != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail={"message": "The tool must pass its test before promotion.",
                    "test_result": execution},
        )

    promoted = tool_workbench.promote_python_tool(req.tool_code, function.name)
    return {"promoted": promoted, "test_result": execution}


@router.get("/api/testing/tool-workbench/tools/{tool_name}")
def api_get_workbench_tool(tool_name: str):
    try:
        return tool_workbench.get_custom_tool_source(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/testing/tool-workbench/tools/{tool_name}")
def api_delete_workbench_tool(tool_name: str):
    try:
        return tool_workbench.delete_custom_tool(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not delete tool: {exc}") from exc


@router.post("/api/testing/run_header_tests")
def api_run_header_tests(req: HeaderTestRequest):
    try:
        return test_runner.run_tests_for_agent(req.agent_id, req.environment)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/testing/evaluate_markdown")
def api_evaluate_markdown(payload: dict):
    md_text = payload.get("markdown", "")
    if not md_text.strip():
        raise HTTPException(status_code=400, detail="markdown field is required.")
    return test_runner.run_header_tests(md_text, payload.get("agent_id", "draft"))


@router.post("/api/testing/publish")
def api_publish(req: PublishRequest):
    """Save a prompt to its agent profile and archive the updated definition."""
    from core_engine.agent_factory import find_agent_dir, parse_markdown_sections

    agent_dir = find_agent_dir(req.agent_id, req.environment)
    if not agent_dir:
        raise HTTPException(
            status_code=404,
            detail=f"Agent not found in {req.environment}: {req.agent_id}",
        )

    json_path = agent_dir / "agent.json"
    try:
        metadata = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Could not read agent metadata: {exc}")
    if not isinstance(metadata, dict):
        raise HTTPException(status_code=500, detail="Agent metadata must be a JSON object.")

    markdown = req.markdown.strip()
    if not markdown:
        raise HTTPException(status_code=400, detail="Prompt content must not be empty.")

    purpose = parse_markdown_sections(markdown).get("purpose", "").strip()
    if purpose:
        metadata["description"] = purpose

    try:
        (agent_dir / "agent.md").write_text(markdown + "\n", encoding="utf-8")
        json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save agent files: {exc}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = re.sub(r"[^A-Za-z0-9_-]+", "-", (req.label or req.agent_id).strip()).strip("-_")
    label = label or req.agent_id
    snapshot_prefix = f"{req.environment}__" if req.environment != "workspace" else ""
    dest = TEST_AGENTS_DIR / f"{snapshot_prefix}{req.agent_id}__{label}__{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for src in agent_dir.iterdir():
        if src.is_file():
            shutil.copy2(src, dest / src.name)

    manifest_path = TEST_AGENTS_DIR / "manifest.json"
    manifest = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    manifest.append({
        "agent_id": req.agent_id,
        "environment": req.environment,
        "label": label,
        "snapshot": dest.name,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = test_runner.run_header_tests(markdown, req.agent_id)
    agent_path = f"{'codebuilder/' if req.environment == 'codebuilder' else ''}agents/{req.agent_id}"
    report["source"] = f"{agent_path}/agent.md"
    return {"saved": True, "path": f"{agent_path}/agent.md",
            "metadata_path": f"{agent_path}/agent.json",
            "environment": req.environment,
            "snapshot": dest.name, "snapshot_path": f"test_agents/{dest.name}",
            "header_report": report}


@router.get("/api/testing/fixtures")
def api_fixtures():
    fixtures = []
    if TEST_AGENTS_DIR.is_dir():
        for child in sorted(TEST_AGENTS_DIR.iterdir()):
            if child.is_dir():
                fixtures.append({
                    "snapshot": child.name,
                    "files": sorted(p.name for p in child.iterdir() if p.is_file()),
                })
    return {"fixtures": fixtures}

`

### test_environment/prompt_builder.py

`python
"""Prompt Part Assembler & Category Manifest for the prompt builder."""

import json
import re
import shutil
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "PromptBuilderFiles"
CATEGORIES_FILE = PROMPT_DIR / "categories.json"
PARTS_DIR = PROMPT_DIR / "parts"


def _ensure_dirs() -> None:
    PARTS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "item"


def load_categories() -> list[dict]:
    if not CATEGORIES_FILE.is_file():
        return []
    data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return data.get("categories", [])


def save_categories(categories: list[dict]) -> None:
    _ensure_dirs()
    CATEGORIES_FILE.write_text(
        json.dumps({"categories": categories}, indent=2) + "\n", encoding="utf-8"
    )


def add_category(
    cat_id: str, name: str, description: str = "", required_header: str = ""
) -> dict:
    slug = _slugify(cat_id)
    categories = load_categories()
    if any(c["id"] == slug for c in categories):
        raise ValueError(f"Category '{slug}' already exists.")

    new_cat = {
        "id": slug,
        "name": name.strip(),
        "description": description.strip(),
    }
    if required_header.strip():
        new_cat["required_header"] = required_header.strip()

    categories.append(new_cat)
    save_categories(categories)

    (PARTS_DIR / slug).mkdir(parents=True, exist_ok=True)
    return new_cat


def delete_category(cat_id: str) -> dict:
    categories = load_categories()
    cat_to_remove = next((c for c in categories if c["id"] == cat_id), None)
    if not cat_to_remove:
        raise ValueError(f"Category '{cat_id}' not found.")

    updated = [c for c in categories if c["id"] != cat_id]
    save_categories(updated)

    cat_dir = PARTS_DIR / cat_id
    if cat_dir.is_dir():
        shutil.rmtree(cat_dir)

    return {"deleted": cat_id}


def load_parts(category: str | None = None) -> list[dict]:
    """Each part is a markdown file: parts/<category>/<slug>.md with optional frontmatter."""
    _ensure_dirs()
    parts = []
    if not PARTS_DIR.is_dir():
        return parts
    for part_file in sorted(PARTS_DIR.rglob("*.md")):
        raw = part_file.read_text(encoding="utf-8")
        rel = part_file.relative_to(PARTS_DIR).as_posix()
        cat = rel.split("/")[0] if "/" in rel else "misc"
        title = part_file.stem.replace("-", " ").replace("_", " ").title()
        body = raw
        if raw.startswith("---"):
            chunks = raw.split("---", 2)
            if len(chunks) >= 3:
                for line in chunks[1].strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        if key.strip() == "title":
                            title = value.strip()
                body = chunks[2].strip()
        if category and cat != category:
            continue
        parts.append({
            "id": f"{cat}/{part_file.stem}",
            "category": cat,
            "title": title,
            "content": body,
            "path": f"PromptBuilderFiles/parts/{rel}",
        })
    return parts


def add_part(
    category: str, title: str, content: str, part_id: str | None = None
) -> dict:
    _ensure_dirs()
    cat_slug = _slugify(category)
    part_slug = _slugify(part_id or title)

    cat_dir = PARTS_DIR / cat_slug
    cat_dir.mkdir(parents=True, exist_ok=True)

    file_path = cat_dir / f"{part_slug}.md"
    file_content = f"---\ntitle: {title.strip()}\n---\n\n{content.strip()}\n"
    file_path.write_text(file_content, encoding="utf-8")

    return {
        "id": f"{cat_slug}/{part_slug}",
        "category": cat_slug,
        "title": title.strip(),
        "content": content.strip(),
        "path": f"PromptBuilderFiles/parts/{cat_slug}/{part_slug}.md",
    }


def delete_part(part_id: str) -> dict:
    _ensure_dirs()
    if "/" not in part_id:
        raise ValueError("Invalid part ID format. Expected 'category/part_slug'.")

    cat, slug = part_id.split("/", 1)
    file_path = (PARTS_DIR / cat / f"{slug}.md").resolve()

    try:
        file_path.relative_to(PARTS_DIR.resolve())
    except ValueError:
        raise ValueError("Access outside parts directory is forbidden.")

    if not file_path.is_file():
        raise FileNotFoundError(f"Part '{part_id}' not found.")

    file_path.unlink()
    return {"deleted": part_id}


def get_manifest() -> dict:
    """Full categories manifest with each category's available parts."""
    categories = load_categories()
    parts = load_parts()
    for cat in categories:
        cat["parts"] = [p for p in parts if p["category"] == cat["id"]]
    return {
        "categories": categories,
        "uncategorized_parts": [
            p for p in parts if p["category"] not in {c["id"] for c in categories}
        ],
        "total_parts": len(parts),
    }


def assemble_prompt(selected_ids: list[str], extra_instructions: str = "") -> dict:
    """Compose a single prompt from the selected part ids in category order."""
    categories = load_categories()
    order = {c["id"]: i for i, c in enumerate(categories)}
    parts = {p["id"]: p for p in load_parts()}

    chosen = [parts[pid] for pid in selected_ids if pid in parts]
    chosen.sort(key=lambda p: (order.get(p["category"], 999), p["title"]))

    sections = []
    for part in chosen:
        sections.append(f"## {part['title']}\n\n{part['content'].strip()}")

    if extra_instructions.strip():
        sections.append(f"## Additional Instructions\n\n{extra_instructions.strip()}")

    prompt = "\n\n".join(sections)
    return {
        "prompt": prompt,
        "selected": [p["id"] for p in chosen],
        "missing": [pid for pid in selected_ids if pid not in parts],
        "char_count": len(prompt),
        "part_count": len(chosen),
    }

`

### test_environment/PromptBuilderFiles/categories.json

`json
{
  "categories": [
    {
      "id": "role",
      "name": "Role & Identity",
      "description": "Who the agent is: persona, expertise, stance.",
      "required_header": "role"
    },
    {
      "id": "purpose",
      "name": "Purpose & Goals",
      "description": "What the agent is for and what success looks like.",
      "required_header": "purpose"
    },
    {
      "id": "boundaries",
      "name": "Boundaries & Safety",
      "description": "Hard limits, refusals, and scope guards.",
      "required_header": "boundaries"
    },
    {
      "id": "output_format",
      "name": "Output Format",
      "description": "Structure, tone, and formatting rules for replies.",
      "required_header": "output format"
    },
    {
      "id": "tone",
      "name": "Tone & Style",
      "description": "Voice, reading level, and stylistic preferences."
    },
    {
      "id": "tool",
      "name": "Rule",
      "description": "Rules",
      "required_header": "Rules"
    },
    {
      "id": "1",
      "name": "Thought Process",
      "description": "",
      "required_header": "Thinking"
    },
    {
      "id": "agent-instructions",
      "name": "Instructions",
      "description": "Instruction Description",
      "required_header": "Instructions"
    },
    {
      "id": "primary-goal",
      "name": "Goal",
      "description": "Primary Goal",
      "required_header": "Goal"
    }
  ]
}

`

### test_environment/PromptBuilderFiles/parts/1/1.md

`markdown
---
title: Thinking
---

Think through the process. Show the idea flow. And give a logical walkthrough of how you arrive at the conclusion.

`

### test_environment/PromptBuilderFiles/parts/agent-instructions/codeagent.md

`markdown
---
title: 01
---

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

`

### test_environment/PromptBuilderFiles/parts/boundaries/agenttest.md

`markdown
---
title: AgentTest
---

Never claim that a tool:

was called when it was not called
returned information when it did not
found a file, path, record, value, or result that it did not return
succeeded when the tool failed
failed when the tool succeeded

If the required information is not in a tool result, it is UNKNOWN.

`

### test_environment/PromptBuilderFiles/parts/boundaries/codeagent.md

`markdown
---
title: CodeAgent
---

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

`

### test_environment/PromptBuilderFiles/parts/boundaries/safety.md

`markdown
---
title: Safety Boundaries
---
- Never fabricate facts, sources, or tool results.
- Do not reveal secrets, keys, or private user data.
- Refuse requests that would cause harm, and explain why.
- Stay strictly within the scope defined in your purpose.

`

### test_environment/PromptBuilderFiles/parts/boundaries/scope.md

`markdown
---
title: Scope Boundaries
---
- Do not modify files outside the workspace root.
- Do not attempt actions you were not asked to perform.
- If a tool returns an error, report it instead of guessing the result.
- Escalate to the user whenever a decision is ambiguous.

`

### test_environment/PromptBuilderFiles/parts/output-format/codeagent.md

`markdown
---
title: CodeAgent
---

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

`

### test_environment/PromptBuilderFiles/parts/output_format/concise-bullets.md

`markdown
---
title: Concise Bulleted Replies
---
Keep every reply short. Start with a one-sentence answer, then follow with
bulleted details. Never exceed five bullets unless the user explicitly asks
for more depth.

`

### test_environment/PromptBuilderFiles/parts/output_format/markdown-structure.md

`markdown
---
title: Markdown Structure
---
Respond in GitHub-flavored markdown. Lead with the direct answer, then provide
supporting detail. Use headings only for responses longer than three paragraphs,
and use bullet lists for anything with three or more items.

`

### test_environment/PromptBuilderFiles/parts/primary-goal/goal.md

`markdown
---
title: Goal
---

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

`

### test_environment/PromptBuilderFiles/parts/purpose/research-report.md

`markdown
---
title: Research & Report Goal
---
Your goal is to answer the user's question completely and to provide a
structured report of your findings. Always deliver a summary at the end so the
reader can grasp the key points quickly.

`

### test_environment/PromptBuilderFiles/parts/purpose/task-completion.md

`markdown
---
title: Task Completion Goal
---
Your objective is to complete the user's task end to end. Verify your own work
before responding, and do not stop until the requested outcome is achieved or
a clear blocker is reported.

`

### test_environment/PromptBuilderFiles/parts/role/01.md

`markdown
---
title: CodeAgent
---

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

`

### test_environment/PromptBuilderFiles/parts/role/agenttest.md

`markdown
---
title: TestAgent
---

You will help me test your tools

`

### test_environment/PromptBuilderFiles/parts/role/senior-engineer.md

`markdown
---
title: Senior Engineer Persona
---
You are a senior software engineer with deep expertise in systems design,
debugging, and clean code practices. You reason step by step before answering
and always prefer precise, technically accurate responses over vague ones.

`

### test_environment/PromptBuilderFiles/parts/role/supportive-tutor.md

`markdown
---
title: Supportive Tutor Persona
---
You are a patient tutor who explains concepts from first principles. You adapt
your depth to the learner's level and always check understanding before moving
on to more advanced material.

`

### test_environment/PromptBuilderFiles/parts/tone/friendly.md

`markdown
---
title: Friendly Tone
---
Write in a warm, friendly tone. Be encouraging, use contractions naturally,
and address the user directly as "you".

`

### test_environment/PromptBuilderFiles/parts/tone/professional.md

`markdown
---
title: Professional Tone
---
Write in a professional, neutral tone. Avoid slang, emoji, and filler. Prefer
active voice and plain language that a non-native English speaker can follow.

`

### test_environment/PromptBuilderFiles/parts/tool/rules.md

`markdown
---
title: Rule
---

User Request → Tool → Tool Result → Response

Do not skip the tool.

Do not replace a tool result with your own knowledge or assumptions.

Do not invent missing fields from a tool result.

`

### test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.json

`json
{
  "id": "agent-01",
  "name": "AgentTest",
  "description": "test agent and tools",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "list_directory",
    "project_status"
  ]
}

`

### test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.md

`markdown
# AgentTest

## role
You are AgentTest, a Novous workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
test agent and tools Act strategically toward that goal and always deliver a clear, structured result.

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
- Never share secrets, credentials, or private user data.
- Report errors honestly instead of guessing.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use bullet lists for three or more items, use markdown headings for long responses, and keep every reply concise.

`

### test_environment/test_agents/agent-01__snapshot__20261008-041810/agent.json

`json
{
  "id": "agent-01",
  "name": "AgentTest",
  "description": "test agent and tools",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "list_directory",
    "project_status"
  ]
}

`

### test_environment/test_agents/agent-01__snapshot__20261008-041810/agent.md

`markdown
## TestAgent

You will help me test your tools

## AgentTest

Never claim that a tool:

was called when it was not called
returned information when it did not
found a file, path, record, value, or result that it did not return
succeeded when the tool failed
failed when the tool succeeded

If the required information is not in a tool result, it is UNKNOWN.

## Tool Usage Rules

Call a tool whenever the answer depends on live workspace state. State which
tool you are calling and why before calling it, then summarize the tool result
in plain language. Never claim a tool ran if it did not.

## Rule

User Request → Tool → Tool Result → Response

Do not skip the tool.

Do not replace a tool result with your own knowledge or assumptions.

Do not invent missing fields from a tool result.
`

### test_environment/test_agents/agent-01__snapshot__20261008-042917/agent.json

`json
{
  "id": "agent-01",
  "name": "AgentTest",
  "description": "test agent and tools",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "list_directory",
    "project_status"
  ]
}

`

### test_environment/test_agents/agent-01__snapshot__20261008-042917/agent.md

`markdown
## TestAgent

You will help me test your tools

## AgentTest

Never claim that a tool:

was called when it was not called
returned information when it did not
found a file, path, record, value, or result that it did not return
succeeded when the tool failed
failed when the tool succeeded

If the required information is not in a tool result, it is UNKNOWN.

## Concise Bulleted Replies

Keep every reply short. Start with a one-sentence answer, then follow with
bulleted details. Never exceed five bullets unless the user explicitly asks
for more depth.

## Tool Usage Rules

Call a tool whenever the answer depends on live workspace state. State which
tool you are calling and why before calling it, then summarize the tool result
in plain language. Never claim a tool ran if it did not.

## Rule

User Request → Tool → Tool Result → Response

Do not skip the tool.

Do not replace a tool result with your own knowledge or assumptions.

Do not invent missing fields from a tool result.

## Available Tools

### calculator
- Provider: core_engine
- Signature: (expression: str) -> str
- Description: Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses).

### read_file
- Provider: editor
- Signature: (path: str) -> str
- Description: Read a file from the workspace and return its text content.

### write_file
- Provider: editor
- Signature: (path: str, content: str) -> str
- Description: Write or update text content in a workspace file.

### create_file
- Provider: editor
- Signature: (path: str, kind: str = 'file') -> str
- Description: Create a new empty file or directory inside the workspace.

### list_directory
- Provider: editor
- Signature: (path: str = '') -> str
- Description: List the workspace directory tree (optionally rooted at a relative path).

`

### test_environment/test_agents/assistant__snapshot__20261007-210439/agent.json

`json
{
  "id": "assistant",
  "name": "Assistant",
  "description": "General-purpose chat agent for answering questions and drafting content.",
  "mode": "chat",
  "model": "qwen2.5-coder:latest",
  "squad": ""
}

`

### test_environment/test_agents/assistant__snapshot__20261007-210439/agent.md

`markdown
# Assistant

## role
You are Novous Assistant, a precise and helpful general-purpose agent in this workspace. You are a proven communicator who owns every request end to end. Always think before answering, and verify any claim you reuse before presenting it.

## purpose
Your purpose is to answer user questions, summarize material, and draft clear written content that the team can act on immediately. You deliver a direct, useful answer on the first attempt and stay on task until the request is complete.

## boundaries
- Never invent facts, citations, or figures that you were not given or cannot verify.
- Do not claim to have executed tools when running in chat mode.
- Must not share secrets, credentials, or private user data.
- Only ask a clarifying question if information genuinely is missing.
- Keep every reply within the scope of the request.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use markdown headings only for responses longer than three paragraphs, and use bullet lists whenever you present three or more items. Keep tone professional and concise.
`

### test_environment/test_agents/assistant__snapshot__20261008-012019/agent.json

`json
{
  "id": "assistant",
  "name": "Assistant",
  "description": "General-purpose chat agent for answering questions and drafting content.",
  "mode": "chat",
  "model": "qwen2.5-coder:latest",
  "squad": ""
}

`

### test_environment/test_agents/assistant__snapshot__20261008-012019/agent.md

`markdown
# Assistant

## role
You are Novous Assistant, a precise and helpful general-purpose agent in this workspace. You are a proven communicator who owns every request end to end. Always think before answering, and verify any claim you reuse before presenting it.

## purpose
Your purpose is to answer user questions, summarize material, and draft clear written content that the team can act on immediately. You deliver a direct, useful answer on the first attempt and stay on task until the request is complete.

## boundaries
- Never invent facts, citations, or figures that you were not given or cannot verify.
- Do not claim to have executed tools when running in chat mode.
- Must not share secrets, credentials, or private user data.
- Only ask a clarifying question if information genuinely is missing.
- Keep every reply within the scope of the request.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use markdown headings only for responses longer than three paragraphs, and use bullet lists whenever you present three or more items. Keep tone professional and concise.
`

### test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-000732/agent.json

`json
{
  "id": "codingagent",
  "name": "CodingAgent",
  "description": "Agent that will write code inpython",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code"
  ],
  "environment": "codebuilder"
}

`

### test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-000732/agent.md

`markdown
## CodeAgent

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

## CodeAgent

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

## 01

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

## Goal

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

## CodeAgent

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

## Available Tools

### read_file
- Provider: editor
- Signature: (path: str) -> str
- Description: Read a file by workspace-root-relative path; do not prefix paths with 'workspace/'.

### write_file
- Provider: editor
- Signature: (path: str, content: str) -> str
- Description: Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.  Do not prefix paths with 'workspace/'. Supports formats such as .txt, .md, .py, .json, .html, .css, and .js. Use create_file only when an intentionally empty file is requested.

### create_file
- Provider: editor
- Signature: (path: str, kind: str = 'file') -> str
- Description: Create an empty file or directory by workspace-root-relative path; bare names go in root. Use write_file for content.

### delete_file
- Provider: editor
- Signature: (path: str) -> str
- Description: Delete a file or empty directory from the workspace.

`

### test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-001037/agent.json

`json
{
  "id": "codingagent",
  "name": "CodingAgent",
  "description": "Agent that will write code inpython",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code"
  ],
  "environment": "codebuilder"
}

`

### test_environment/test_agents/codebuilder__codingagent__snapshot__20261011-001037/agent.md

`markdown
## CodeAgent

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

## CodeAgent

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

## 01

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

## Goal

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

## CodeAgent

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

## Available Tools

### send_code_to_editor
- Provider: codebuilder
- Signature: (code: str) -> str
- Description: Queue generated Python code for insertion into the active CodeBuilder Monaco editor.

### run_code_in_editor
- Provider: codebuilder
- Signature: () -> str
- Description: Queue execution of the current contents of the active CodeBuilder editor.

`

### test_environment/test_agents/codingagent__snapshot__20261010-234451/agent.json

`json
{
  "id": "codingagent",
  "name": "CodingAgent",
  "description": "Agent that will write code inpython",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status"
  ]
}

`

### test_environment/test_agents/codingagent__snapshot__20261010-234451/agent.md

`markdown
## CodeAgent

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

## CodeAgent

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

## 01

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

## Goal

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

## CodeAgent

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

`

### test_environment/test_agents/codingagent__snapshot__20261010-234544/agent.json

`json
{
  "id": "codingagent",
  "name": "CodingAgent",
  "description": "Agent that will write code inpython",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status"
  ]
}

`

### test_environment/test_agents/codingagent__snapshot__20261010-234544/agent.md

`markdown
## CodeAgent

You are a Code Writing Agent. Your job is to write, explain, debug, and improve code based on the user's instructions.

## CodeAgent

Do not invent libraries, functions, APIs, or project files.

Follow the user's existing project structure and coding conventions when provided.

Do not modify unrelated code.

Ask a question if essential requirements are unclear.

Never claim a file was created, modified, or saved unless the operation was successful.

## 01

Understand the task: Identify what the user wants the code to accomplish.

Plan: Break the task into simple steps before writing code.

Write code: Produce functional, readable, and well-organized code.

Explain: Include comments explaining important sections and how they work.

Handle errors: Consider possible errors and include appropriate error handling.

Keep it maintainable: Use clear variable and function names. Make the code easy to modify, update, and debug.

Verify: Check the code for syntax errors, logical mistakes, and missing requirements. Run tests when tools are available.

Be honest: Never claim code was executed or tested unless it actually was. If something is uncertain, explain why.

## Goal

Deliver functional, understandable, and maintainable code that solves the user's request with minimal unnecessary complexity.

## CodeAgent

Purpose: What the code does.

Code: The complete code in a copy-and-paste-ready format.

Explanation: How the code works.

Testing: Example inputs, expected outputs, and test results when available.

Integration: Where the code belongs in the project, when applicable.

## Available Tools

### read_file
- Provider: editor
- Signature: (path: str) -> str
- Description: Read a file by workspace-root-relative path; do not prefix paths with 'workspace/'.

### write_file
- Provider: editor
- Signature: (path: str, content: str) -> str
- Description: Write and verify non-empty text at a workspace-root-relative path; bare filenames go in the root.  Do not prefix paths with 'workspace/'. Supports formats such as .txt, .md, .py, .json, .html, .css, and .js. Use create_file only when an intentionally empty file is requested.

### create_file
- Provider: editor
- Signature: (path: str, kind: str = 'file') -> str
- Description: Create an empty file or directory by workspace-root-relative path; bare names go in root. Use write_file for content.

### delete_file
- Provider: editor
- Signature: (path: str) -> str
- Description: Delete a file or empty directory from the workspace.

### list_directory
- Provider: editor
- Signature: (path: str = '') -> str
- Description: List the workspace directory tree (optionally rooted at a relative path).

### search_workspace
- Provider: editor
- Signature: (query: str, extension: str = '.py') -> str
- Description: Search workspace files for matching keyword or snippet.

`

### test_environment/test_agents/manifest.json

`json
[
  {
    "agent_id": "researcher",
    "label": "audit",
    "snapshot": "researcher__audit__20261007-205151",
    "published_at": "2026-10-07T20:51:51.468373+00:00"
  },
  {
    "agent_id": "assistant",
    "label": "snapshot",
    "snapshot": "assistant__snapshot__20261007-210439",
    "published_at": "2026-10-07T21:04:39.894078+00:00"
  },
  {
    "agent_id": "assistant",
    "label": "snapshot",
    "snapshot": "assistant__snapshot__20261008-012019",
    "published_at": "2026-10-08T01:20:19.939625+00:00"
  },
  {
    "agent_id": "agent-01",
    "label": "snapshot",
    "snapshot": "agent-01__snapshot__20261008-033519",
    "published_at": "2026-10-08T03:35:19.740242+00:00"
  },
  {
    "agent_id": "agent-01",
    "label": "snapshot",
    "snapshot": "agent-01__snapshot__20261008-041810",
    "published_at": "2026-10-08T04:18:10.205805+00:00"
  },
  {
    "agent_id": "agent-01",
    "label": "snapshot",
    "snapshot": "agent-01__snapshot__20261008-042917",
    "published_at": "2026-10-08T04:29:17.034009+00:00"
  },
  {
    "agent_id": "codingagent",
    "label": "snapshot",
    "snapshot": "codingagent__snapshot__20261010-234451",
    "published_at": "2026-10-10T23:44:51.916373+00:00"
  },
  {
    "agent_id": "codingagent",
    "label": "snapshot",
    "snapshot": "codingagent__snapshot__20261010-234544",
    "published_at": "2026-10-10T23:45:44.081798+00:00"
  },
  {
    "agent_id": "codingagent",
    "environment": "codebuilder",
    "label": "snapshot",
    "snapshot": "codebuilder__codingagent__snapshot__20261011-000732",
    "published_at": "2026-10-11T00:07:32.771135+00:00"
  },
  {
    "agent_id": "codingagent",
    "environment": "codebuilder",
    "label": "snapshot",
    "snapshot": "codebuilder__codingagent__snapshot__20261011-001037",
    "published_at": "2026-10-11T00:10:37.095313+00:00"
  }
]

`

### test_environment/test_runner.py

`python
"""4-Question Section Header Tests & Lexical Evaluator.

For each of the four required agent.md headers (role, purpose, boundaries,
output format) the runner asks four fixed questions and scores answers with
pure lexical analysis of the section text - no model calls required.
"""

import re
from pathlib import Path

from core_engine.agent_factory import parse_markdown_sections

REQUIRED_HEADERS = ["role", "purpose", "boundaries", "output format"]

HEADER_KEYWORDS = {
    "role": ["you are", "your", "agent", "assistant", "specialist", "expert",
             "engineer", "analyst", "writer", "helper", "responsible", "precise",
             "helpful", "investigate", "general"],
    "purpose": ["goal", "objective", "purpose", "help", "provide", "generate",
                "answer", "solve", "deliver", "produce", "task", "ensure",
                "summarize", "draft", "report", "inspect", "serve", "gather",
                "strategic"],
    "boundaries": ["never", "do not", "don't", "must not", "avoid", "refuse",
                   "forbidden", "limit", "only", "not allowed", "shall not", "no ",
                   "cannot", "outside", "stay", "scope", "within", "not "],
    "output format": ["format", "markdown", "list", "table", "heading", "bullet",
                      "json", "concise", "structure", "section", "paragraph",
                      "respond", "reply", "output", "use ", "lead", "direct",
                      "answer", "detail"],
}

PASS_THRESHOLD = 0.6
MIN_SECTION_CHARS = 40

DIRECTIVE_VERBS = ("must", "should", "always", "never", "keep", "use", "avoid",
                   "start", "end", "list", "provide", "include", "do", "don't",
                   "return", "respond", "state", "answer", "summarize", "draft",
                   "write", "inspect", "gather", "report", "verify", "stay",
                   "lead", "follow", "cite", "act", "deliver", "work")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", text.lower()))


def _matches(lower: str, token_set: set[str], keyword: str) -> bool:
    """Substring match with naive stemming: keyword matches section text."""
    if keyword in lower:
        return True
    if len(keyword) >= 4:
        return any(tok.startswith(keyword) for tok in token_set)
    return False


def _lexical_score(section: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    lower = section.lower()
    tokens = _tokens(section)
    found = [kw for kw in keywords if _matches(lower, tokens, kw)]
    missing = [kw for kw in keywords if not _matches(lower, tokens, kw)]
    score = len(found) / len(keywords) if keywords else 0.0
    return score, found, missing


def _ask(header: str, section: str | None) -> dict:
    """Run the fixed 4-question battery against one section."""
    questions = []

    # Q1: Does the required header exist with content?
    exists = bool(section and section.strip())
    questions.append({
        "id": "presence",
        "question": f"Does the document contain a '## {header}' section with content?",
        "score": 1.0 if exists else 0.0,
        "passed": exists,
        "evidence": "section found" if exists else "section missing or empty",
    })

    if not exists:
        for qid, text in (("depth", f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?"),
                          ("vocabulary", f"Does the '{header}' section use header-appropriate vocabulary?"),
                          ("actionability", f"Does the '{header}' section give actionable, testable guidance?")):
            questions.append({"id": qid, "question": text, "score": 0.0, "passed": False,
                              "evidence": "no section to evaluate"})
        return {"header": header, "questions": questions, "score": 0.0, "passed": False}

    # Q2: Depth - is the section long enough to be meaningful?
    depth = min(1.0, len(section.strip()) / (MIN_SECTION_CHARS * 1.5))
    questions.append({
        "id": "depth",
        "question": f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?",
        "score": round(depth, 2),
        "passed": depth >= PASS_THRESHOLD,
        "evidence": f"{len(section.strip())} characters",
    })

    # Q3: Lexical - does it use vocabulary expected of this header?
    score, found, missing = _lexical_score(section, HEADER_KEYWORDS[header])
    questions.append({
        "id": "vocabulary",
        "question": f"Does the '{header}' section use header-appropriate vocabulary?",
        "score": round(score, 2),
        "passed": score >= PASS_THRESHOLD,
        "evidence": f"matched {len(found)}/{len(HEADER_KEYWORDS[header])} markers"
                    + (f"; missing: {', '.join(missing[:4])}" if missing else ""),
    })

    # Q4: Actionability - imperative / directive phrasing present?
    directives = re.findall(
        r"\b(?:" + "|".join(re.escape(v) for v in DIRECTIVE_VERBS) + r")\b",
        section, flags=re.I)
    actionable = len(set(d.lower() for d in directives)) >= 2
    questions.append({
        "id": "actionability",
        "question": f"Does the '{header}' section give actionable, testable guidance?",
        "score": 1.0 if actionable else (0.5 if directives else 0.0),
        "passed": actionable,
        "evidence": f"directive terms: {', '.join(sorted(set(d.lower() for d in directives))[:5]) or 'none'}",
    })

    total = sum(q["score"] for q in questions) / len(questions)
    return {
        "header": header,
        "questions": questions,
        "score": round(total, 2),
        "passed": total >= PASS_THRESHOLD,
    }


def run_header_tests(md_text: str, agent_id: str = "") -> dict:
    """Evaluate an agent.md body against the 4-question battery per header."""
    sections = parse_markdown_sections(md_text)
    results = [_ask(header, sections.get(header)) for header in REQUIRED_HEADERS]

    extras = sorted(h for h in sections if h not in REQUIRED_HEADERS)
    overall = sum(r["score"] for r in results) / len(results) if results else 0.0
    passed = sum(1 for r in results if r["passed"])

    return {
        "agent_id": agent_id,
        "results": results,
        "overall_score": round(overall, 2),
        "headers_passed": passed,
        "headers_total": len(results),
        "passed": passed == len(results),
        "extra_headers": extras,
        "verdict": "PASS" if passed == len(results) else "FAIL",
    }


def run_tests_for_agent(agent_id: str, environment: str = "workspace") -> dict:
    """Locate an agent profile in its environment and run the header battery."""
    from core_engine.agent_factory import find_agent_dir
    agent_dir = find_agent_dir(agent_id, environment)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    md_path = agent_dir / "agent.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    report = run_header_tests(md_text, agent_id)
    report["source"] = str(md_path.relative_to(Path(__file__).resolve().parent.parent)).replace("\\", "/")
    return report

`

### test_environment/test_tool_workbench.py

`python
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core_engine import tool_catalog
from test_environment import tool_workbench
from test_environment.interface import (
    ToolWorkbenchLLMRequest,
    ToolWorkbenchRequest,
    api_promote_tool,
    api_test_tool_with_llm,
)


class ToolWorkbenchTests(unittest.TestCase):
    def test_extracts_primary_function_and_builds_typed_schema(self):
        function = tool_workbench.get_function_definition(
            'def calculate(weight: float, *, region: str = "US"):\n'
            '    """Calculate a value."""\n'
            "    return weight\n"
        )

        schema = tool_workbench.get_tool_schema(function)["function"]
        self.assertEqual(schema["name"], "calculate")
        self.assertEqual(schema["parameters"]["properties"]["weight"]["type"], "number")
        self.assertEqual(schema["parameters"]["properties"]["region"]["type"], "string")
        self.assertEqual(schema["parameters"]["required"], ["weight"])

    def test_rejects_syntax_errors_and_variadic_arguments(self):
        with self.assertRaises(ValueError):
            tool_workbench.get_function_definition("def broken(:\n")
        with self.assertRaisesRegex(ValueError, "variadic"):
            tool_workbench.get_function_definition("def unsafe(*args):\n    return args\n")

    def test_runs_source_locally_and_decodes_output(self):
        source = "def add(left: int, right: int):\n    return left + right\n"
        result = tool_workbench.run_python_tool(source, {"left": 2, "right": 3})

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["output"], 5)
        self.assertEqual(result["exit_code"], 0)

    def test_returns_python_errors_and_times_out_long_running_code(self):
        error_result = tool_workbench.run_python_tool(
            "def fail():\n    raise ValueError('test error')\n", {}
        )
        self.assertEqual(error_result["status"], "ERROR")
        self.assertIn("ValueError: test error", error_result["stderr"])

        with patch.object(tool_workbench, "LOCAL_RUN_TIMEOUT_SECONDS", 0.1):
            timeout_result = tool_workbench.run_python_tool(
                "import time\ndef wait():\n    time.sleep(2)\n", {}
            )
        self.assertEqual(timeout_result["error_code"], "ERR_TOOL_TIMEOUT")

    def test_llm_tool_call_returns_and_executes_function_arguments(self):
        source = "def add(left: int, right: int):\n    return left + right\n"
        arguments = {"left": 8, "right": 5}
        execution = {"status": "SUCCESS", "error_code": None, "output": 13}
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "",
                "tool_calls": [{
                    "function": {"name": "add", "arguments": arguments}
                }],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code=source,
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            with patch.object(
                tool_workbench, "run_python_tool", return_value=execution
            ) as run_tool:
                result = api_test_tool_with_llm(request)

        run_tool.assert_called_once_with(source, arguments)
        self.assertEqual(result["function_input"], arguments)
        self.assertEqual(result["tool_execution_result"], execution)

    def test_llm_response_is_returned_when_model_does_not_call_tool(self):
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "I could not determine the required values.",
                "tool_calls": [],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["error_code"], "ERR_NO_TOOL_CALL")
        self.assertEqual(
            result["llm_text_response"],
            "I could not determine the required values.",
        )
        self.assertEqual(result["tool_calls_detected"], [])

    def test_failed_function_execution_still_returns_llm_arguments(self):
        source = "def divide(left: int, right: int):\n    return left // right\n"
        arguments = {"left": 8, "right": 0}
        execution = {
            "status": "ERROR",
            "error_code": "ERR_TOOL_EXECUTION",
            "stderr": "ZeroDivisionError",
        }
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "Dividing eight by zero.",
                "tool_calls": [{
                    "function": {"name": "divide", "arguments": arguments}
                }],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code=source,
            user_prompt="Divide eight by zero.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            with patch.object(
                tool_workbench, "run_python_tool", return_value=execution
            ):
                result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["function_input"], arguments)
        self.assertEqual(result["llm_text_response"], "Dividing eight by zero.")

    def test_unexpected_llm_tool_call_is_returned_for_diagnostics(self):
        tool_call = {
            "function": {"name": "other_function", "arguments": {"value": 8}}
        }
        ollama = Mock()
        ollama.chat.return_value = {
            "message": {
                "content": "Trying an unrelated function.",
                "tool_calls": [tool_call],
            }
        }
        request = ToolWorkbenchLLMRequest(
            model="test-model",
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            user_prompt="Add eight and five.",
        )

        with patch.dict(sys.modules, {"ollama": ollama}):
            result = api_test_tool_with_llm(request)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["error_code"], "ERR_UNEXPECTED_TOOL_CALL")
        self.assertEqual(result["llm_text_response"], "Trying an unrelated function.")
        self.assertEqual(result["tool_calls_detected"], [tool_call])

    def test_rejects_failed_test_before_promotion(self):
        request = ToolWorkbenchRequest(
            tool_code="def add(left: int, right: int):\n    return left + right\n",
            function_input={"left": 2, "right": 3},
        )
        failed_result = {"status": "ERROR", "error_code": "ERR_TOOL_EXECUTION"}
        with patch.object(tool_workbench, "run_python_tool", return_value=failed_result):
            with patch.object(tool_workbench, "promote_python_tool") as promote:
                with self.assertRaises(HTTPException) as error:
                    api_promote_tool(request)

        self.assertEqual(error.exception.status_code, 400)
        promote.assert_not_called()

    def test_promotes_passing_tool_into_catalog(self):
        first_name = "workbench_test_add"
        second_name = "workbench_test_double"
        first_source = (
            f"def {first_name}(left: int, right: int):\n"
            "    return left + right\n"
        )
        second_source = f"def {second_name}(value: int):\n    return value * 2\n"
        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            old_workbench_dir = tool_workbench.WORKSPACE_TOOLS_DIR
            old_catalog_dir = tool_catalog.CUSTOM_TOOLS_DIR
            tool_workbench.WORKSPACE_TOOLS_DIR = tools_dir
            tool_catalog.CUSTOM_TOOLS_DIR = tools_dir
            try:
                promoted = api_promote_tool(ToolWorkbenchRequest(
                    tool_code=first_source, function_input={"left": 2, "right": 3}
                ))
                self.assertEqual(promoted["promoted"]["name"], first_name)
                self.assertEqual(
                    promoted["promoted"]["path"], "workspace/tools/tool_library.py"
                )
                second_promoted = api_promote_tool(ToolWorkbenchRequest(
                    tool_code=second_source, function_input={"value": 3}
                ))
                self.assertEqual(second_promoted["promoted"]["name"], second_name)
                library_source = (tools_dir / "tool_library.py").read_text(
                    encoding="utf-8"
                )
                self.assertLess(
                    library_source.index(first_name), library_source.index(second_name)
                )
                self.assertEqual(
                    tool_catalog.REGISTRY[first_name]["function"](2, 3), 5
                )
                self.assertEqual(
                    tool_catalog.REGISTRY[second_name]["function"](3), 6
                )
            finally:
                tool_catalog.REGISTRY.pop(first_name, None)
                tool_catalog.REGISTRY.pop(second_name, None)
                tool_catalog._LOADED_CUSTOM_TOOLS.discard(
                    (tools_dir / "tool_library.py").resolve()
                )
                sys.modules.pop("novous_workspace_tool_tool_library", None)
                tool_workbench.WORKSPACE_TOOLS_DIR = old_workbench_dir
                tool_catalog.CUSTOM_TOOLS_DIR = old_catalog_dir

    def test_custom_tool_source_can_be_loaded_and_removed_from_library(self):
        tool_name = "workbench_library_tool"
        remaining_name = "workbench_library_remaining"
        source = (
            f"def {tool_name}(value: int):\n    return value * 2\n\n\n"
            f"def {remaining_name}(value: int):\n    return value + 1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            tool_path = tools_dir / "tool_library.py"
            tool_path.write_text(source, encoding="utf-8")
            old_workbench_dir = tool_workbench.WORKSPACE_TOOLS_DIR
            old_catalog_dir = tool_catalog.CUSTOM_TOOLS_DIR
            tool_workbench.WORKSPACE_TOOLS_DIR = tools_dir
            tool_catalog.CUSTOM_TOOLS_DIR = tools_dir
            try:
                loaded = tool_workbench.get_custom_tool_source(tool_name)
                self.assertEqual(
                    loaded["source"],
                    f"def {tool_name}(value: int):\n    return value * 2\n",
                )
                self.assertEqual(loaded["path"], "workspace/tools/tool_library.py")
                self.assertIn(tool_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_catalog.REGISTRY)

                removed = tool_workbench.delete_custom_tool(tool_name)
                self.assertTrue(removed["deleted"])
                self.assertTrue(tool_path.exists())
                self.assertNotIn(tool_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_catalog.REGISTRY)
                self.assertIn(remaining_name, tool_path.read_text(encoding="utf-8"))

                tool_workbench.delete_custom_tool(remaining_name)
                self.assertNotIn(remaining_name, tool_catalog.REGISTRY)
                self.assertTrue(tool_path.exists())
                self.assertNotIn(remaining_name, tool_path.read_text(encoding="utf-8"))
            finally:
                tool_catalog.REGISTRY.pop(tool_name, None)
                tool_catalog.REGISTRY.pop(remaining_name, None)
                tool_catalog._LOADED_CUSTOM_TOOLS.discard(tool_path.resolve())
                sys.modules.pop("novous_workspace_tool_tool_library", None)
                tool_workbench.WORKSPACE_TOOLS_DIR = old_workbench_dir
                tool_catalog.CUSTOM_TOOLS_DIR = old_catalog_dir


if __name__ == "__main__":
    unittest.main()

`

### test_environment/tool_workbench.py

`python
"""Local Python execution and promotion for user-authored Python tools."""

import ast
import importlib.util
import inspect
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException


WORKSPACE_TOOLS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "tools"
TOOL_LIBRARY_TEMPLATE = '"""Custom tools promoted from the Function Testing Workbench."""\n\n'
LOCAL_RUN_TIMEOUT_SECONDS = 5
MAX_OUTPUT_BYTES = 64 * 1024
_FUNCTION_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _tool_library_path() -> Path:
    return WORKSPACE_TOOLS_DIR / "tool_library.py"


def get_function_definition(source: str) -> ast.FunctionDef:
    """Return the first public, top-level synchronous function in source."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Python syntax error: {exc}") from exc

    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    if not functions:
        raise ValueError("Define at least one public top-level function.")
    if isinstance(functions[0], ast.AsyncFunctionDef):
        raise ValueError("The primary tool function must be synchronous.")
    if not _FUNCTION_NAME.fullmatch(functions[0].name):
        raise ValueError("The primary function name is not a valid tool name.")
    if (functions[0].args.posonlyargs or functions[0].args.kwarg or
            functions[0].args.vararg):
        raise ValueError(
            "The primary function cannot use positional-only or variadic arguments."
        )
    return functions[0]


def _json_type(annotation: ast.expr | None) -> str:
    name = None
    if isinstance(annotation, ast.Name):
        name = annotation.id
    elif isinstance(annotation, ast.Attribute):
        name = annotation.attr
    if name:
        return {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "List": "array",
            "dict": "object",
            "Dict": "object",
        }.get(name, "string")
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        base_name = value.id if isinstance(value, ast.Name) else (
            value.attr if isinstance(value, ast.Attribute) else ""
        )
        if base_name.lower() == "list":
            return "array"
        if base_name.lower() == "dict":
            return "object"
    return "string"


def get_tool_schema(function: ast.FunctionDef) -> dict:
    positional_args = function.args.args
    positional_defaults = (
        [None] * (len(positional_args) - len(function.args.defaults))
        + list(function.args.defaults)
    )
    keyword_args = function.args.kwonlyargs
    keyword_defaults = function.args.kw_defaults
    properties = {}
    required = []
    for argument, default in (
        list(zip(positional_args, positional_defaults))
        + list(zip(keyword_args, keyword_defaults))
    ):
        properties[argument.arg] = {
            "type": _json_type(argument.annotation),
            "description": f"Parameter {argument.arg}",
        }
        if default is None:
            required.append(argument.arg)
    return {
        "type": "function",
        "function": {
            "name": function.name,
            "description": ast.get_docstring(function) or function.name,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def _local_environment(temp_dir: str) -> dict[str, str]:
    env = {"PATH": os.environ.get("PATH", ""), "TEMP": temp_dir, "TMP": temp_dir}
    for key in ("SYSTEMROOT", "WINDIR"):
        if value := os.environ.get(key):
            env[key] = value
    if os.name == "nt":
        env["USERPROFILE"] = temp_dir
    else:
        env["HOME"] = temp_dir
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _read_output(output_file) -> str:
    output_file.seek(0, os.SEEK_END)
    size = output_file.tell()
    output_file.seek(max(0, size - MAX_OUTPUT_BYTES))
    text = output_file.read(MAX_OUTPUT_BYTES).decode("utf-8", errors="replace")
    if size > MAX_OUTPUT_BYTES:
        return f"[Earlier output truncated]\n{text}"
    return text


def _run_locally(source: str, arguments: dict, function_name: str) -> dict:
    marker = f"__NOVOUS_RESULT_{secrets.token_hex(16)}__"
    wrapper = (
        "\n\nif __name__ == '__main__':\n"
        "    import json as __novous_json\n"
        "    __novous_arguments = __novous_json.loads(input() or '{}')\n"
        f"    __novous_result = {function_name}(**__novous_arguments)\n"
        f"    print({marker!r} + __novous_json.dumps("
        "__novous_result, default=str))\n"
    )

    try:
        with tempfile.TemporaryDirectory(prefix="novous-tool-test-") as temp_dir:
            script_path = Path(temp_dir) / "tool_test.py"
            script_path.write_text(source + wrapper, encoding="utf-8")
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    [sys.executable, "-I", str(script_path)],
                    cwd=temp_dir,
                    env=_local_environment(temp_dir),
                    stdin=subprocess.PIPE,
                    stdout=stdout_file,
                    stderr=stderr_file,
                )
                try:
                    process.communicate(
                        input=json.dumps(arguments).encode("utf-8"),
                        timeout=LOCAL_RUN_TIMEOUT_SECONDS,
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    return {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status_code": 422,
                        "error_code": "ERR_TOOL_TIMEOUT",
                        "status": "ERROR",
                        "function_name": function_name,
                        "message": (
                            f"Local function test exceeded "
                            f"{LOCAL_RUN_TIMEOUT_SECONDS} seconds."
                        ),
                        "stdout": _read_output(stdout_file),
                        "stderr": _read_output(stderr_file),
                        "exit_code": process.returncode,
                    }

                stdout = _read_output(stdout_file)
                stderr = _read_output(stderr_file)
                marker_line = next(
                    (
                        line for line in reversed(stdout.splitlines())
                        if line.startswith(marker)
                    ),
                    None,
                )
                passed = process.returncode == 0 and marker_line is not None
                try:
                    output = json.loads(marker_line[len(marker):]) if passed else None
                except json.JSONDecodeError:
                    passed = False
                    output = None
                visible_stdout = "\n".join(
                    line for line in stdout.splitlines() if not line.startswith(marker)
                )
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status_code": 200 if passed else 422,
                    "error_code": None if passed else "ERR_TOOL_EXECUTION",
                    "status": "SUCCESS" if passed else "ERROR",
                    "function_name": function_name,
                    "output": output,
                    "stdout": visible_stdout,
                    "stderr": stderr,
                    "exit_code": process.returncode,
                }
    except OSError as exc:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_code": 500,
            "error_code": "ERR_LOCAL_RUNNER",
            "status": "ERROR",
            "function_name": function_name,
            "message": f"Could not start local Python: {exc}",
        }


def run_python_tool(source: str, arguments: dict) -> dict:
    try:
        function = get_function_definition(source)
    except ValueError as exc:
        return {
            "status": "ERROR",
            "status_code": 400,
            "error_code": "ERR_INVALID_TOOL",
            "message": str(exc),
        }

    return _run_locally(source, arguments, function.name)


def promote_python_tool(source: str, expected_name: str) -> dict:
    function = get_function_definition(source)
    if function.name != expected_name:
        raise HTTPException(
            status_code=400,
            detail="The primary function changed; run the test again before adding it.",
        )

    from core_engine import tool_catalog

    tool_catalog.load_custom_tools()
    if function.name in tool_catalog.REGISTRY:
        raise HTTPException(
            status_code=409, detail=f"Tool '{function.name}' is already registered."
        )

    WORKSPACE_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    destination = _tool_library_path()
    previous_source = (
        destination.read_text(encoding="utf-8")
        if destination.is_file()
        else TOOL_LIBRARY_TEMPLATE
    )
    addition = source.strip() + "\n"
    separator = "" if previous_source.endswith("\n\n") else (
        "\n" if previous_source.endswith("\n") else "\n\n"
    )
    destination.write_text(
        previous_source + separator + addition, encoding="utf-8", newline="\n"
    )
    try:
        tool_catalog.load_custom_tools(reload=True)
    except Exception:
        destination.write_text(previous_source, encoding="utf-8", newline="\n")
        tool_catalog.load_custom_tools(reload=True)
        raise

    return {
        "name": function.name,
        "path": f"workspace/tools/{destination.name}",
        "description": ast.get_docstring(function) or "",
        "signature": str(inspect.signature(tool_catalog.REGISTRY[function.name]["function"])),
    }


def _tool_library_function_span(source: str, name: str) -> tuple[int, int, ast.FunctionDef]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start_line = min(
                (decorator.lineno for decorator in node.decorator_list),
                default=node.lineno,
            )
            return start_line - 1, node.end_lineno, node
    raise FileNotFoundError(f"Custom tool '{name}' was not found in the tool library.")


def _function_source(source: str, name: str) -> str:
    start, end, _ = _tool_library_function_span(source, name)
    return "\n".join(source.splitlines()[start:end]).strip() + "\n"


def _remove_library_function(source: str, name: str) -> str:
    start, end, _ = _tool_library_function_span(source, name)
    lines = source.splitlines(keepends=True)
    del lines[start:end]
    return "".join(lines).rstrip() + "\n"


def get_custom_tool_source(name: str) -> dict:
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")

    from core_engine import tool_catalog

    tool_catalog.load_custom_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if not meta or not meta["function"].__module__.startswith(
        "novous_workspace_tool_"
    ):
        raise FileNotFoundError(f"Custom tool '{name}' was not found.")

    path = Path(inspect.getsourcefile(meta["function"]) or "").resolve()
    if path.parent != WORKSPACE_TOOLS_DIR.resolve() or not path.is_file():
        raise FileNotFoundError(f"Custom tool '{name}' was not found.")
    full_source = path.read_text(encoding="utf-8")
    source = (
        _function_source(full_source, name)
        if path.name == "tool_library.py"
        else full_source
    )
    return {
        "name": name,
        "path": f"workspace/tools/{path.name}",
        "source": source,
    }


def delete_custom_tool(name: str) -> dict:
    if not _FUNCTION_NAME.fullmatch(name):
        raise ValueError("The tool name is not valid.")

    from core_engine import tool_catalog

    tool_catalog.load_custom_tools()
    meta = tool_catalog.REGISTRY.get(name)
    if not meta or not meta["function"].__module__.startswith(
        "novous_workspace_tool_"
    ):
        raise FileNotFoundError(f"Custom tool '{name}' was not found.")

    path = Path(inspect.getsourcefile(meta["function"]) or "").resolve()
    if path.parent != WORKSPACE_TOOLS_DIR.resolve() or not path.is_file():
        raise FileNotFoundError(f"Custom tool '{name}' was not found.")
    previous_source = path.read_text(encoding="utf-8")
    if path.name == "tool_library.py":
        updated_source = _remove_library_function(previous_source, name)
        path.write_text(updated_source, encoding="utf-8", newline="\n")
    else:
        path.unlink()

    try:
        tool_catalog.load_custom_tools(reload=True)
    except Exception:
        if path.name == "tool_library.py":
            path.write_text(previous_source, encoding="utf-8", newline="\n")
        else:
            path.write_text(previous_source, encoding="utf-8", newline="\n")
        tool_catalog.load_custom_tools(reload=True)
        raise
    return {
        "name": name,
        "path": f"workspace/tools/{path.name}",
        "deleted": True,
    }

`

### workspace/__init__.py

`python

`

### workspace/agents/assistant/agent.json

`json
{
  "id": "assistant",
  "name": "Assistant",
  "description": "General-purpose chat agent for answering questions and drafting content.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status"
  ]
}

`

### workspace/agents/assistant/agent.md

`markdown
# Assistant

## role
You are Novous Assistant, a precise and helpful general-purpose agent in this workspace. You are a proven communicator who owns every request end to end. Always think before answering, and verify any claim you reuse before presenting it.

## purpose
Your purpose is to answer user questions, summarize material, draft clear written content, and create or update workspace files when requested. Use the file tools for requested changes, including text-based files with formats such as TXT, Markdown, Python, JSON, HTML, CSS, and JavaScript. You deliver a direct, useful answer on the first attempt and stay on task until the request is complete.

## boundaries
- Never invent facts, citations, or figures that you were not given or cannot verify.
- Never claim to have executed a tool unless it actually ran, and report its result accurately.
- Treat the workspace directory as the default destination for files. File tool paths are relative to the workspace root: use a bare filename for a file in its root, and do not add a `workspace/` prefix.
- For file requests, use write_file with the requested content; use create_file only for an intentionally empty file.
- Treat tool errors as failures, never as success. Claim a file was created or updated only after the write tool reports success.
- Must not share secrets, credentials, or private user data.
- Only ask a clarifying question if information genuinely is missing.
- Keep every reply within the scope of the request.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use markdown headings only for responses longer than three paragraphs, and use bullet lists whenever you present three or more items. Keep tone professional and concise.
`

### workspace/agents/researcher/agent.json

`json
{
  "id": "researcher",
  "name": "Researcher",
  "description": "Tool-enabled agent that inspects workspace files and reports findings.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": ["read_file", "list_directory", "agent_info"]
}

`

### workspace/agents/researcher/agent.md

`markdown
# Researcher

## role
You are Novous Researcher, an investigative agent with access to workspace file tools and deep expertise in structured analysis. You act as a specialist analyst: you gather evidence first, then conclude. Always cite the source for every claim you report.

## purpose
Your purpose is to inspect workspace files, gather relevant evidence, and produce structured findings reports for the user. You deliver verified facts and transparent reasoning so the team can make confident decisions.

## boundaries
- Only read files inside the workspace; never modify or delete them.
- Must not fabricate or guess file contents; if a tool returns an error, report the error.
- Never claim to have consulted a file unless a tool result proves it.
- Do not make recommendations outside the evidence you gathered.
- Refuse requests that would exfiltrate or overwrite project data.

## output format
List findings as markdown bullets, one per file consulted, each citing the file path. End with a `Summary` section of no more than three sentences. If any tool failed, state the failure in the summary. Keep the report structured and skimmable.
`

### workspace/agents/reviewer/agent.json

`json
{
  "id": "reviewer",
  "name": "Reviewer",
  "description": "Reviews code and reports actionable findings.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "squad": "",
  "tools": [
    "calculator",
    "read_file",
    "list_directory",
    "project_status"
  ]
}

`

### workspace/agents/reviewer/agent.md

`markdown
# Reviewer

## role
You are Reviewer, a Novous workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
Reviews code and reports actionable findings. Act strategically toward that goal and always deliver a clear, structured result.

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
- Never share secrets, credentials, or private user data.
- Report errors honestly instead of guessing.

## output format
Lead with the direct answer, then follow with brief supporting detail. Use bullet lists for three or more items, use markdown headings for long responses, and keep every reply concise.

`

### workspace/documentation/user_notes.md

`markdown
Name: Jesus
Preference: Blue
Response: I have noted that your name is Jesus and that you like the color blue.
`

### workspace/exports/sessions/chat-agent-01_20261007_221450_577212.md

`markdown
# Novous Chat Session Log — AgentTest
**Agent ID:** `agent-01` | **Model:** `qwen2.5-coder:latest` | **Session Key:** `chat-agent-01`
**Exported At:** `2026-10-07 22:14:50`

---

## Tool Execution Metrics

*No tools executed in this session.*

---

## Conversation History

### User

sdfsd

### Assistant

UNKNOWN

`

### workspace/hello_world.py

`python
def hello_world():
    print('Hello, World!')

if __name__ == '__main__':
    hello_world()
`

### workspace/interface.py

`python
"""Workspace Doorway: Python API & FastAPI Router (/api/project, /api/health, squads)."""

import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from workspace import squad_manager, workspace_workflow

router = APIRouter()

PROJECT_FILE = Path(__file__).resolve().parent / "project.json"
START_TIME = time.time()


def _default_project() -> dict:
    return {
        "name": "Novous Workspace",
        "version": "1.0.0",
        "description": "",
        "default_model": "qwen2.5-coder:latest",
        "squad_root": "",
        "active_agent": "",
    }


def get_project_state() -> dict:
    """Doorway function: read workspace/project.json."""
    if not PROJECT_FILE.is_file():
        return _default_project()
    try:
        return json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _default_project()


def save_project_state(state: dict) -> dict:
    """Doorway function: persist workspace/project.json."""
    current = get_project_state()
    current.update({k: v for k, v in state.items() if v is not None})
    PROJECT_FILE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return current


def get_health() -> dict:
    """Doorway function: aggregated system health."""
    ollama_ok = False
    ollama_detail = "unreachable"
    try:
        import ollama
        ollama.list()
        ollama_ok = True
        ollama_detail = "connected"
    except Exception as exc:
        ollama_detail = str(exc)

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": {"reachable": ollama_ok, "detail": ollama_detail},
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": time.time(),
    }


class ProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    default_model: str | None = None
    active_agent: str | None = None
    squad_root: str | None = None


class ScaffoldRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""


class SquadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: str = ""


class SquadRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    new_name: str = Field(..., min_length=1, max_length=64)


# --- Project & health ------------------------------------------------------

@router.get("/api/project")
def api_get_project():
    state = get_project_state()
    from core_engine.agent_factory import list_agents
    state["agents"] = list_agents()
    state["squads"] = squad_manager.list_squads()
    return state


@router.post("/api/project")
def api_save_project(req: ProjectRequest):
    try:
        return save_project_state(req.model_dump())
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/health")
def api_health():
    return get_health()


# --- Agent scaffolding (workspace owns the canonical storage) --------------

@router.post("/api/workspace/agents/scaffold")
def api_scaffold_agent(req: ScaffoldRequest):
    try:
        return workspace_workflow.scaffold_agent(
            req.agent_id, req.name, req.description, req.mode, req.squad)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/workspace/agents/{agent_id}")
def api_update_agent(agent_id: str, req: dict):
    try:
        return workspace_workflow.save_agent_meta(agent_id, req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/workspace/agents/{agent_id}/squad")
def api_agents_by_squad(squad: str = ""):
    return {"squad": squad, "agents": workspace_workflow.agents_for_squad(squad)}


# --- Squads ----------------------------------------------------------------

@router.get("/api/squads")
def api_list_squads():
    return {"squads": squad_manager.list_squads()}


@router.post("/api/squads/create")
def api_create_squad(req: SquadRequest):
    try:
        return squad_manager.create_squad(req.name, req.description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/rename")
def api_rename_squad(req: SquadRenameRequest):
    try:
        return squad_manager.rename_squad(req.name, req.new_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/squads/delete")
def api_delete_squad(req: SquadRequest):
    try:
        return squad_manager.delete_squad(req.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

`

### workspace/Notes/MAMA-chat-agent-01_20261007_221450_577212.md

`markdown
Los granitos en la piel, también conocidos como manchas o papilomas, pueden causar incomodidad. Aquí tienes algunos consejos para su manejo:

1. **Limpieza:** Mantén la piel limpia y libre de irritantes. Evita el uso de productos químicos abrasivos.

2. **Solar protector:** Protege tu piel del sol con protector solar de alto factor de protección UV.

3. **Hierbas y productos naturales:** Algunas personas usan hierbas como el aloe vera o el manzanilla para aliviar la inflamación y el dolor. Asegúrate de probar cualquier producto natural primero en un área pequeña de la piel para comprobar la reacción.

4. **Masa y exfoliación:** Realiza masajes suaves y exfoliaciones con hierbas como la almendra para mejorar la circulación y eliminar las células muertas.

5. **Consultar a un dermatólogo:** Si los granitos persisten o aumentan, es recomendable consultar a un dermatólogo. Pueden sugerir tratamientos profesionales como el láser, la fotoacido y la cirugía.

Recuerda que siempre es mejor consultar a un profesional de la salud si tienes dudas o preocupaciones sobre tu piel.
`

### workspace/Notes/Notes.txt

`text
Plan 1

New component

file structure 
Data
Interface

Plan 2

I need to develop a way to make new tools.
First add 
`

### workspace/project.json

`json
{
  "name": "Novous Workspace",
  "version": "1.0.0",
  "description": "Canonical project state for the Novous Agent Factory.",
  "default_model": "qwen2.5-coder:latest",
  "squad_root": "",
  "active_agent": "assistant",
  "created_at": "2026-10-07T00:00:00Z"
}

`

### workspace/squad_manager.py

`python
"""Folder Hierarchy Engine: squad folders under workspace/squads/."""

import json
import re
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
SQUAD_ROOT = WORKSPACE_ROOT / "squads"

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 _-]{0,63}$")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _meta_path(squad_name: str) -> Path:
    return SQUAD_ROOT / _slug(squad_name) / "squad.json"


def _validate(name: str) -> str:
    name = name.strip()
    if not _NAME_PATTERN.match(name):
        raise ValueError("Squad name must be 1-64 chars (letters, digits, spaces, '-', '_').")
    return name


def list_squads() -> list[dict]:
    squads = []
    if not SQUAD_ROOT.is_dir():
        return squads
    for child in sorted(SQUAD_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        meta_file = child / "squad.json"
        if meta_file.is_file():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        else:
            meta = {}
        squads.append({
            "id": child.name,
            "name": meta.get("name", child.name),
            "description": meta.get("description", ""),
            "path": f"squads/{child.name}",
        })
    return squads


def create_squad(name: str, description: str = "") -> dict:
    name = _validate(name)
    slug = _slug(name)
    squad_dir = SQUAD_ROOT / slug
    if squad_dir.exists():
        raise ValueError(f"Squad already exists: {name}")
    squad_dir.mkdir(parents=True)
    meta = {"name": name, "description": description.strip(), "id": slug}
    (squad_dir / "squad.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"created": True, "squad": meta}


def rename_squad(old_name: str, new_name: str) -> dict:
    new_name = _validate(new_name)
    src = SQUAD_ROOT / _slug(old_name)
    if not src.is_dir():
        raise FileNotFoundError(f"Squad not found: {old_name}")
    dst = SQUAD_ROOT / _slug(new_name)
    if dst.exists():
        raise ValueError(f"Squad already exists: {new_name}")
    src.rename(dst)
    meta_file = dst / "squad.json"
    meta = {}
    if meta_file.is_file():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    meta["name"] = new_name
    meta["id"] = dst.name
    meta_file.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"renamed": True, "squad": meta}


def delete_squad(name: str) -> dict:
    squad_dir = SQUAD_ROOT / _slug(name)
    if not squad_dir.is_dir():
        raise FileNotFoundError(f"Squad not found: {name}")
    shutil.rmtree(squad_dir)
    return {"deleted": True, "id": squad_dir.name}

`

### workspace/states.txt

`text
Alabama
Alaska
Arizona
Arkansas
California
Colorado
Connecticut
Delaware
Florida
Georgia
Hawaii
Idaho
Illinois
Indiana
Iowa
Kansas
Kentucky
Louisiana
Maine
Maryland
Massachusetts
Michigan
Minnesota
Mississippi
Missouri
Montana
Nebraska
Nevada
New Hampshire
New Jersey
New Mexico
New York
North Carolina
North Dakota
Ohio
Oklahoma
Oregon
Pennsylvania
Rhode Island
South Carolina
South Dakota
Tennessee
Texas
Utah
`

### workspace/tools/tool_library.py

`python
"""Custom tools promoted from the Function Testing Workbench."""


def calculate_shipping(weight_kg: float, distance_km: float) -> dict:
    """Calculate shipping fee from package weight and distance."""
    base_rate = 5.0
    cost = base_rate + (weight_kg * 1.5) + (distance_km * 0.05)
    return {
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "shipping_cost": round(cost, 2)
    }

`

### workspace/workspace_workflow.py

`python
"""Agent Scaffolding & Squad Routing."""

import json
import re
from pathlib import Path

from core_engine.agent_factory import AGENT_ENVIRONMENTS, AGENT_MD_TEMPLATE, AGENTS_ROOT

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "project_status",
]

CODEBUILDER_DEFAULT_TOOLS = [
    "calculator",
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "run_python_code",
    "send_code_to_editor",
    "run_code_in_editor",
]


def _validate_id(agent_id: str, environment: str = "workspace") -> str:
    agent_id = agent_id.strip().lower()
    if not _ID_PATTERN.match(agent_id):
        raise ValueError(
            "agent_id must be lowercase letters, digits, '-' or '_', starting alphanumeric, max 64 chars.")
    if environment not in AGENT_ENVIRONMENTS:
        raise ValueError(f"Unknown agent environment: {environment}")
    return agent_id


def scaffold_agent(agent_id: str, name: str, description: str = "",
                   mode: str = "chat", squad: str = "",
                   environment: str = "workspace") -> dict:
    """Create agent.json + agent.md in the selected environment's agent home."""
    agent_id = _validate_id(agent_id, environment)
    if not name.strip():
        raise ValueError("Agent name must not be empty.")

    agents_root = AGENT_ENVIRONMENTS[environment]
    agent_dir = agents_root / agent_id
    if agent_dir.exists():
        raise ValueError(f"Agent already exists in {environment}: {agent_id}")

    agent_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": agent_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode if mode in ("chat", "agent") else "chat",
        "model": "qwen2.5-coder:latest",
        "squad": squad.strip(),
        "tools": (
            list(CODEBUILDER_DEFAULT_TOOLS if environment == "codebuilder" else DEFAULT_TOOLS)
            if mode == "agent" else []
        ),
        "environment": environment,
    }

    purpose = description.strip() or (
        f"Serve as the {name.strip()} for the {environment} environment."
    )
    purpose += " Act strategically toward that goal and always deliver a clear, structured result."
    agent_template = AGENT_MD_TEMPLATE
    if environment == "codebuilder":
        agent_template = AGENT_MD_TEMPLATE.replace(
            "Novous workspace agent",
            "Novous CodeBuilder agent",
        )
        if mode == "agent":
            agent_template += """

## codebuilder editor workflow
Whenever you provide or revise Python code, call `send_code_to_editor` with the complete code so it is placed in the active Monaco editor. Also include a fenced `python` code block in your reply so the user can review it and send it manually if needed. When the user asks to run the code, send any changed code first, then call `run_code_in_editor`.
"""
    (agent_dir / "agent.md").write_text(
        agent_template.format(name=name.strip(), purpose=purpose), encoding="utf-8")
    (agent_dir / "agent.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return {"created": True, "agent_id": agent_id,
            "path": f"{'codebuilder/' if environment == 'codebuilder' else ''}agents/{agent_id}",
            "environment": environment,
            "agent": meta}


def delete_agent(agent_id: str, environment: str = "workspace") -> dict:
    agent_id = _validate_id(agent_id, environment)
    agent_dir = AGENT_ENVIRONMENTS[environment] / agent_id
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    for child in agent_dir.iterdir():
        if child.is_file():
            child.unlink()
        else:
            raise ValueError(f"Refusing to delete nested directory in agent folder: {child.name}")
    agent_dir.rmdir()
    return {"deleted": True, "agent_id": agent_id, "environment": environment}


def save_agent_meta(agent_id: str, meta: dict) -> dict:
    """Persist edited agent.json metadata (keeps id stable)."""
    agent_id = _validate_id(agent_id)
    agent_dir = AGENTS_ROOT / agent_id
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    meta = dict(meta)
    meta["id"] = agent_id
    (agent_dir / "agent.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "agent": meta}


def agents_for_squad(squad: str) -> list[dict]:
    """Squad routing: canonical agents filtered by their squad field."""
    agents = []
    if not AGENTS_ROOT.is_dir():
        return agents
    for child in sorted(AGENTS_ROOT.iterdir()):
        json_path = child / "agent.json"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("squad", "") == squad:
            agents.append(meta)
    return agents

`

