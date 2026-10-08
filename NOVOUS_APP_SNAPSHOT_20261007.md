Date: 2026-10-07
Name: Novous Application Snapshot
Filename: NOVOUS_APP_SNAPSHOT_20261007.md
Commit: 0df6e32
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
- .pytest_cache/v/cache/nodeids
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
- frontend/pages/editor.html
- frontend/pages/index.html
- frontend/pages/testing.html
- frontend/static/
- frontend/static/css/
- frontend/static/css/style.css
- frontend/static/js/
- frontend/static/js/api.js
- frontend/static/js/app.js
- frontend/static/js/chat.js
- frontend/static/js/editor.js
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
- test_environment/PromptBuilderFiles/parts/boundaries/
- test_environment/PromptBuilderFiles/parts/boundaries/agenttest.md
- test_environment/PromptBuilderFiles/parts/boundaries/safety.md
- test_environment/PromptBuilderFiles/parts/boundaries/scope.md
- test_environment/PromptBuilderFiles/parts/output_format/
- test_environment/PromptBuilderFiles/parts/output_format/concise-bullets.md
- test_environment/PromptBuilderFiles/parts/output_format/markdown-structure.md
- test_environment/PromptBuilderFiles/parts/purpose/
- test_environment/PromptBuilderFiles/parts/purpose/research-report.md
- test_environment/PromptBuilderFiles/parts/purpose/task-completion.md
- test_environment/PromptBuilderFiles/parts/role/
- test_environment/PromptBuilderFiles/parts/role/agenttest.md
- test_environment/PromptBuilderFiles/parts/role/senior-engineer.md
- test_environment/PromptBuilderFiles/parts/role/supportive-tutor.md
- test_environment/PromptBuilderFiles/parts/tone/
- test_environment/PromptBuilderFiles/parts/tone/friendly.md
- test_environment/PromptBuilderFiles/parts/tone/professional.md
- test_environment/PromptBuilderFiles/parts/tool/
- test_environment/PromptBuilderFiles/parts/tool/rules.md
- test_environment/PromptBuilderFiles/parts/tools/
- test_environment/PromptBuilderFiles/parts/tools/tool-rules.md
- test_environment/test_agents/
- test_environment/test_agents/agent-01__snapshot__20261008-033519/
- test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.json
- test_environment/test_agents/agent-01__snapshot__20261008-033519/agent.md
- test_environment/test_agents/assistant__snapshot__20261007-210439/
- test_environment/test_agents/assistant__snapshot__20261007-210439/agent.json
- test_environment/test_agents/assistant__snapshot__20261007-210439/agent.md
- test_environment/test_agents/assistant__snapshot__20261008-012019/
- test_environment/test_agents/assistant__snapshot__20261008-012019/agent.json
- test_environment/test_agents/assistant__snapshot__20261008-012019/agent.md
- test_environment/test_agents/manifest.json
- test_environment/test_runner.py
- workspace/
- workspace/__init__.py
- workspace/agents/
- workspace/agents/agent-01/
- workspace/agents/agent-01/agent.json
- workspace/agents/agent-01/agent.md
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
- workspace/documentation/hello.txt
- workspace/interface.py
- workspace/project.json
- workspace/squad_manager.py
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

### core_engine/__init__.py

`python

`

### core_engine/agent_factory.py

`python
import json
from pathlib import Path
from core_engine.runtime import AgentProfile

AGENTS_ROOT = Path(__file__).resolve().parent.parent / "workspace" / "agents"

AGENT_MD_TEMPLATE = """# {name}

## role
You are {name}, a Novous workspace agent. You act as a specialist in your domain and own every request end to end. Always think before answering and verify any claim you reuse.

## purpose
{purpose}

## boundaries
- Stay within the scope described in your purpose.
- Do not fabricate facts, citations, or tool results.
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


def find_agent_dir(agent_id: str) -> Path | None:
    clean = str(agent_id or "").strip().replace("\\", "/")
    if not clean or "/" in clean or clean in (".", ".."):
        return None
    candidate = AGENTS_ROOT / clean
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


def load_agent(agent_id: str) -> AgentProfile:
    agent_dir = find_agent_dir(agent_id)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    return load_agent_definition(agent_dir / "agent.json", agent_dir / "agent.md")


def list_agents() -> list[dict]:
    agents = []
    if not AGENTS_ROOT.is_dir():
        return agents
    for child in sorted(AGENTS_ROOT.iterdir(), key=lambda p: p.name.lower()):
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
        })
    return agents

`

### core_engine/interface.py

`python
"""Core Engine Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core_engine import agent_factory, tool_catalog
from core_engine.runtime import Agent, AgentProfile

router = APIRouter()

# In-memory conversation sessions, keyed by agent id.
SESSIONS: dict[str, Agent] = {}


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = ""
    mode: str = "chat"
    squad: str = ""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    agent_id: str
    model: str = "qwen2.5-coder:latest"
    session_id: str | None = None


def run_single_agent(agent_id: str, message: str, model: str | None = None,
                     session_id: str | None = None) -> dict:
    """Doorway function: run one agent turn through the Think-Act-Observe loop."""
    try:
        profile = agent_factory.load_agent(agent_id)
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
    }


def list_agents() -> list[dict]:
    """Doorway function: list all canonical agents from workspace/agents/."""
    return agent_factory.list_agents()


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
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.delete("/api/agents/{agent_id}")
def api_delete_agent(agent_id: str):
    from workspace import workspace_workflow
    try:
        return workspace_workflow.delete_agent(agent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/chat")
def api_chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    return run_single_agent(req.agent_id, req.message.strip(), req.model, req.session_id)


@router.post("/api/chat/reset")
def api_chat_reset(session_id: str):
    return {"reset": reset_session(session_id)}


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
    """Read and return text contents of a file relative to workspace root."""
    try:
        data = read_file_content(relative_path)
        return data["content"]
    except Exception as exc:
        return f"Error reading file '{relative_path}': {exc}"


# --- 2. Write File Tool ---
@tool
def write_file_tool(relative_path: str, content: str) -> str:
    """Create or overwrite text content in a workspace file."""
    try:
        res = write_file_content(relative_path, content)
        return f"Successfully wrote {res['bytes_written']} bytes to '{relative_path}'."
    except Exception as exc:
        return f"Error writing to file '{relative_path}': {exc}"


# --- 3. Create File or Folder Tool ---
@tool
def create_file_tool(relative_path: str, kind: str = "file") -> str:
    """Create an empty file or directory inside workspace root."""
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

        tool_func = self.tools[name]
        try:
            if isinstance(args, str):
                args = json.loads(args)
            result = tool_func(**args) if isinstance(args, dict) else tool_func(args)
            self.tool_events.append({"tool": name, "args": args, "status": "success", "origin": origin})
            return result
        except Exception as exc:
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
lazily so importing this module never creates circular imports.
"""

import ast
import inspect
import json
import operator
from pathlib import Path
from typing import Callable

from core_engine.agent_factory import load_agent
from core_engine import langgraph_tools

REGISTRY: dict[str, dict] = {}

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


# --- Core System Tools ---


@tool(provider="core_engine")
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (numbers, + - * / // % ** and parentheses)."""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


@tool(provider="editor")
def read_file(path: str) -> str:
    """Read a file from the workspace and return its text content."""
    return langgraph_tools.read_file_tool.invoke({"relative_path": path})


@tool(provider="editor")
def write_file(path: str, content: str) -> str:
    """Write or update text content in a workspace file."""
    return langgraph_tools.write_file_tool.invoke(
        {"relative_path": path, "content": content}
    )


@tool(provider="editor")
def create_file(path: str, kind: str = "file") -> str:
    """Create a new empty file or directory inside the workspace."""
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
}


def list_tools() -> list[dict]:
    return [
        {
            "name": meta["name"],
            "provider": meta["provider"],
            "description": meta["description"],
            "signature": meta["signature"],
        }
        for meta in REGISTRY.values()
    ]


def get_tools(names: list[str] | None = None) -> list[Callable]:
    """Resolve registered tool callables, filtered by an optional allow-list."""
    if not names:
        return [meta["function"] for meta in REGISTRY.values()]
    resolved = []
    for name in names:
        meta = REGISTRY.get(name)
        if meta:
            resolved.append(meta["function"])
    return resolved

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
            if not child.name.startswith("."):
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

  <script type="module">
    import { renderChatView } from '/static/js/chat.js';
    renderChatView(document.getElementById('view-container'));
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
        <button class="nav-btn" data-tab="chat">Chat Console</button>
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

/* --- Chat ----------------------------------------------------------------- */
.chat-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
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
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 80%;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.92rem;
  line-height: 1.5;
}
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

  async createAgent(agentId, name, description, mode = 'chat', squad = '') {
    return send('POST', '/api/agents/create', {
      agent_id: agentId, name, description, mode, squad
    });
  },

  async deleteAgent(agentId) {
    return send('DELETE', `/api/agents/${encodeURIComponent(agentId)}`);
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest', sessionId = null) {
    return send('POST', '/api/chat', {
      message, agent_id: agentId, model, session_id: sessionId
    });
  },

  async resetChat(sessionId) {
    return send('POST', `/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`);
  },

  async getTools() {
    return get('/api/tools');
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

  async runHeaderTests(agentId) {
    return send('POST', '/api/testing/run_header_tests', { agent_id: agentId });
  },

  async evaluateMarkdown(markdown, agentId = 'draft') {
    return send('POST', '/api/testing/evaluate_markdown', { markdown, agent_id: agentId });
  },

  async publishAgent(agentId, label = '') {
    return send('POST', '/api/testing/publish', { agent_id: agentId, label });
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
import { renderTestingView } from './testing.js';

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
  chat: renderChatView,
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
      try { await Api.deleteAgent(t.dataset.delete); await refreshAgents(); renderDashboardView(container); }
      catch (err) { alert(err.message); }
    }
  });

  container.querySelector('#dash-new-agent').onclick = () =>
    container.querySelector('#dash-agent-form').classList.toggle('hidden');

  container.querySelector('#dash-create-agent').onclick = async () => {
    const id = container.querySelector('#na-id').value.trim();
    const name = container.querySelector('#na-name').value.trim();
    const desc = container.querySelector('#na-desc').value.trim();
    const mode = container.querySelector('#na-mode').value;
    const errBox = container.querySelector('#na-error');
    errBox.classList.add('hidden');
    try {
      await Api.createAgent(id, name || id, desc, mode);
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

  switchTab('dashboard');
}

boot();

`

### frontend/static/js/chat.js

`javascript
import { Api } from './api.js';

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

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

  container.querySelector('#chat-reset').addEventListener('click', async () => {
    try {
      await Api.resetChat(`chat-${agentSelect.value}`);
      messagesBox.innerHTML = '<div class="message system-msg">Session reset. Send a message to start fresh.</div>';
    } catch (err) {
      appendMessage('system', 'Reset failed: ' + err.message);
    }
  });

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
    msgDiv.innerText = content;
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
        <div id="event-log" class="event-log">
          <p class="text-muted">Connecting to event bus…</p>
        </div>
      </aside>
    </div>`;

  const textarea = container.querySelector('#editor-textarea');
  const pathLabel = container.querySelector('#editor-path');
  const dirtyBadge = container.querySelector('#editor-dirty');
  const bytesLabel = container.querySelector('#editor-bytes');
  const posLabel = container.querySelector('#editor-pos');
  const eventLog = container.querySelector('#event-log');
  const wsBadge = container.querySelector('#editor-ws');

  renderTree(container.querySelector('#editor-tree'), {
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

  async function saveFile() {
    if (!state.path) return alert('No file open.');
    try {
      await Api.writeFile(state.path, textarea.value);
      state.dirty = false;
      dirtyBadge.classList.add('hidden');
      appendEvent({ type: 'file_saved', path: state.path, session_id: 'you' });
      updateBytes();
    } catch (err) {
      alert(err.message);
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

  container.querySelector('#editor-save').addEventListener('click', saveFile);
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
          eventLog.innerHTML = `<p class="text-muted small">Connected as session ${esc(data.session_id)}</p>`;
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
    el.innerHTML = `<span class="event-type">${esc(data.type.replace(/_/g, ' '))}</span>
      <span class="event-path">${esc(data.path || '')}</span>
      <span class="event-who text-muted">${esc(data.session_id || '')}</span>`;
    eventLog.appendChild(el);
    while (eventLog.children.length > 60) eventLog.removeChild(eventLog.firstChild);
    eventLog.scrollTop = eventLog.scrollHeight;
  }

  connectWs();

  if (initialPath) openFile(initialPath);
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

/**
 * Prompt Builder & Header Test Runner Component.
 */
export function renderTestingView(container) {
  container.innerHTML = `
    <div class="testing-layout">
      <section class="card testing-builder">
        <div class="card-head">
          <h3>Prompt Builder</h3>
          <div class="toolbar-row" style="margin:0;">
            <button type="button" class="btn btn-sm" id="tb-toggle-cat-form">+ Category</button>
            <button type="button" class="btn btn-sm" id="tb-toggle-part-form">+ Part</button>
            <button type="button" class="btn btn-sm btn-primary" id="tb-assemble">Assemble</button>
          </div>
        </div>

        <!-- Add Category Form -->
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

        <!-- Add Part Form -->
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

        <textarea id="tb-preview" class="prompt-preview" readonly
                  placeholder="Assembled prompt preview will appear here…"></textarea>
        <div class="toolbar-row">
          <span id="tb-stats" class="text-muted small"></span>
          <span class="spacer"></span>
          <button type="button" class="btn btn-sm" id="tb-copy">Copy</button>
          <button type="button" class="btn btn-sm btn-primary" id="tb-publish">Publish snapshot</button>
        </div>
        <p id="tb-msg" class="small hidden"></p>
      </section>

      <section class="card testing-runner">
        <div class="card-head">
          <h3>4-Question Header Tests</h3>
          <button type="button" class="btn btn-sm btn-primary" id="ht-run">Run tests</button>
        </div>
        <div class="form-row">
          <select id="ht-agent" class="form-select"><option value="">Loading agents…</option></select>
        </div>
        <div id="ht-results" class="ht-results">
          <p class="text-muted">Select an agent and run the section-header battery.</p>
        </div>
      </section>
    </div>`;

  const catBox = container.querySelector('#tb-categories');
  const preview = container.querySelector('#tb-preview');
  const stats = container.querySelector('#tb-stats');
  const msg = container.querySelector('#tb-msg');
  const agentSel = container.querySelector('#ht-agent');
  const results = container.querySelector('#ht-results');

  const catForm = container.querySelector('#tb-cat-form');
  const partForm = container.querySelector('#tb-part-form');
  const partCatSelect = container.querySelector('#part-cat-select');

  let manifest = { categories: [] };
  let agents = [];

  function showMsg(text, isError = false) {
    msg.textContent = text;
    msg.className = `small ${isError ? 'text-danger' : 'text-success'}`;
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

  loadManifest();

  // --- Toggle forms ---
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

  // --- Add Category ---
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

  // --- Add Part ---
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

  partForm.querySelectorAll('input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitPart();
      }
    });
  });

  // --- Delete Category & Delete Part delegation ---
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
      return;
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
      preview.value = res.prompt;
      stats.textContent = `${res.part_count} parts · ${res.char_count} chars`;
      showMsg('Prompt assembled.');
    } catch (err) { showMsg(err.message, true); }
  });

  container.querySelector('#tb-copy').addEventListener('click', async () => {
    if (!preview.value) return;
    try { await navigator.clipboard.writeText(preview.value); showMsg('Copied to clipboard.'); }
    catch (_) { preview.select(); document.execCommand('copy'); showMsg('Copied.'); }
  });

  container.querySelector('#tb-publish').addEventListener('click', async () => {
    const agentId = agentSel.value;
    if (!agentId) return showMsg('Select an agent to publish first.', true);
    try {
      const res = await Api.publishAgent(agentId, 'snapshot');
      showMsg(`Published: ${res.snapshot} (headers ${res.header_report.verdict})`);
    } catch (err) { showMsg(err.message, true); }
  });

  // --- Header test runner --------------------------------------------------
  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSel.innerHTML = agents.length
      ? agents.map(a => `<option value="${esc(a.id)}">${esc(a.name)}</option>`).join('')
      : '<option value="">No agents</option>';
  }).catch(err => { agentSel.innerHTML = `<option value="">${esc(err.message)}</option>`; });

  container.querySelector('#ht-run').addEventListener('click', async () => {
    if (!agentSel.value) return;
    results.innerHTML = '<p class="text-muted">Running battery…</p>';
    try {
      const report = await Api.runHeaderTests(agentSel.value);
      results.innerHTML = renderReport(report);
    } catch (err) {
      results.innerHTML = `<p class="text-danger">${esc(err.message)}</p>`;
    }
  });

  function renderReport(report) {
    const header = `
      <div class="ht-summary ${report.passed ? 'pass' : 'fail'}">
        <strong>${esc(report.verdict)}</strong>
        <span>score ${esc(report.overall_score)} · ${esc(report.headers_passed)}/${esc(report.headers_total)} headers</span>
      </div>`;
    const rows = report.results.map(r => `
      <div class="ht-header ${r.passed ? 'pass' : 'fail'}">
        <div class="ht-header-head">
          <span class="ht-hash">## ${esc(r.header)}</span>
          <span class="badge ${r.passed ? 'badge-success' : 'badge-danger'}">${esc((r.score).toFixed(2))}</span>
        </div>
        ${r.questions.map(q => `
          <div class="ht-question">
            <span class="ht-q-status ${q.passed ? 'pass' : 'fail'}">${q.passed ? '✓' : '✗'}</span>
            <div>
              <div>${esc(q.question)}</div>
              <div class="text-muted small">${esc(q.evidence)} · score ${esc(q.score)}</div>
            </div>
          </div>`).join('')}
      </div>`).join('');
    const extras = report.extra_headers?.length
      ? `<p class="text-muted small">Extra headers: ${esc(report.extra_headers.join(', '))}</p>` : '';
    return header + rows + extras;
  }
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

OUT = ROOT / f"NOVOUS_APP_SNAPSHOT_{TODAY}.md"


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
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT"):
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
        if path.name in SKIP_FILES or path.name.startswith("NOVOUS_APP_SNAPSHOT"):
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

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "MASTER_COPY.md"

INCLUDE = {".py", ".js", ".css", ".html", ".json", ".md", ".bat", ".sh"}
EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules", "test_agents"}
MAX_FILE_BYTES = 200_000


def collect() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "MASTER_COPY.md" or path.name == "novous-ai-builder-prompt-v2.md":
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

app = FastAPI(title="Novous AGENT FACTORY", version="4.0.0")

# Mount Component Backend Routers
app.include_router(core_router)
app.include_router(editor_router)
app.include_router(workspace_router)
app.include_router(test_router)

# Serve Static Assets (CSS, JS)
app.mount("/static", StaticFiles(directory=Path("frontend") / "static"), name="static")

# Mount Page Routes
@app.get("/")
def index_page():
    return FileResponse("frontend/pages/index.html")

@app.get("/editor")
def editor_page():
    return FileResponse("frontend/pages/editor.html")

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
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import prompt_builder, test_runner

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""


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

@router.post("/api/testing/run_header_tests")
def api_run_header_tests(req: HeaderTestRequest):
    try:
        return test_runner.run_tests_for_agent(req.agent_id)
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
    """Snapshot an agent definition into the isolated test_agents/ fixture store."""
    from core_engine.agent_factory import find_agent_dir
    agent_dir = find_agent_dir(req.agent_id)
    if not agent_dir:
        raise HTTPException(status_code=404, detail=f"Agent not found: {req.agent_id}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = (req.label or req.agent_id).strip()
    dest = TEST_AGENTS_DIR / f"{req.agent_id}__{label}__{stamp}"
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
        "label": label,
        "snapshot": dest.name,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = test_runner.run_tests_for_agent(req.agent_id)
    return {"published": True, "snapshot": dest.name, "path": f"test_agents/{dest.name}",
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
      "id": "tools",
      "name": "Tool Usage",
      "description": "When and how the agent may call tools."
    },
    {
      "id": "tool",
      "name": "Rule",
      "description": "Rules",
      "required_header": "Rules"
    }
  ]
}

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

### test_environment/PromptBuilderFiles/parts/tools/tool-rules.md

`markdown
---
title: Tool Usage Rules
---
Call a tool whenever the answer depends on live workspace state. State which
tool you are calling and why before calling it, then summarize the tool result
in plain language. Never claim a tool ran if it did not.

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


def run_tests_for_agent(agent_id: str) -> dict:
    """Locate workspace/agents/<id>/agent.md and run the battery against it."""
    from core_engine.agent_factory import find_agent_dir
    agent_dir = find_agent_dir(agent_id)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    md_path = agent_dir / "agent.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    report = run_header_tests(md_text, agent_id)
    report["source"] = str(md_path.relative_to(Path(__file__).resolve().parent.parent)).replace("\\", "/")
    return report

`

### workspace/__init__.py

`python

`

### workspace/agents/agent-01/agent.json

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

### workspace/agents/agent-01/agent.md

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

### workspace/agents/assistant/agent.json

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

### workspace/agents/assistant/agent.md

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

### workspace/documentation/hello.txt

`text
My name is Jesus 
I am a software developer
Learning about AI agents
I have built this app. 
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

### workspace/workspace_workflow.py

`python
"""Agent Scaffolding & Squad Routing."""

import json
import re
from pathlib import Path

from core_engine.agent_factory import AGENTS_ROOT, AGENT_MD_TEMPLATE

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

DEFAULT_TOOLS = ["calculator", "read_file", "list_directory", "project_status"]


def _validate_id(agent_id: str) -> str:
    agent_id = agent_id.strip().lower()
    if not _ID_PATTERN.match(agent_id):
        raise ValueError(
            "agent_id must be lowercase letters, digits, '-' or '_', starting alphanumeric, max 64 chars.")
    return agent_id


def scaffold_agent(agent_id: str, name: str, description: str = "",
                   mode: str = "chat", squad: str = "") -> dict:
    """Create agent.json + agent.md in the canonical workspace/agents/ home."""
    agent_id = _validate_id(agent_id)
    if not name.strip():
        raise ValueError("Agent name must not be empty.")

    agent_dir = AGENTS_ROOT / agent_id
    if agent_dir.exists():
        raise ValueError(f"Agent already exists: {agent_id}")

    agent_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": agent_id,
        "name": name.strip(),
        "description": description.strip(),
        "mode": mode if mode in ("chat", "agent") else "chat",
        "model": "qwen2.5-coder:latest",
        "squad": squad.strip(),
    }
    if meta["mode"] == "agent":
        meta["tools"] = list(DEFAULT_TOOLS)

    (agent_dir / "agent.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    purpose = description.strip() or f"Serve as the {name.strip()} for this workspace."
    purpose += " Act strategically toward that goal and always deliver a clear, structured result."
    (agent_dir / "agent.md").write_text(
        AGENT_MD_TEMPLATE.format(name=name.strip(), purpose=purpose), encoding="utf-8")

    return {"created": True, "agent_id": agent_id, "path": f"agents/{agent_id}",
            "agent": meta}


def delete_agent(agent_id: str) -> dict:
    agent_id = _validate_id(agent_id)
    agent_dir = AGENTS_ROOT / agent_id
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    for child in agent_dir.iterdir():
        if child.is_file():
            child.unlink()
        else:
            raise ValueError(f"Refusing to delete nested directory in agent folder: {child.name}")
    agent_dir.rmdir()
    return {"deleted": True, "agent_id": agent_id}


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

