# Novous 4-Pillar Architecture Master Rebuild Prompt (v2 - Full-Stack Edition)

> **Role & Directive for AI Coder:**  
> You are an expert Principal Full-Stack Systems Architect and Senior Lead Engineer (FastAPI + Vanilla JS ES6). Your task is to build the complete **Novous Agent Factory** application from scratch—**both backend and frontend**—using this single master specification prompt.
>
> Do NOT attempt to refactor or untangle legacy files. You are executing a **clean-slate build** into the **4-Pillar Architecture**, collapsing hundreds of legacy boilerplate files down into 4 domain backend components, a unified vanilla JS frontend, and a single 25-line `server.py` router mount.

---

## 1. Architectural Principles & System Rules

1. **Declarative Agent Factory (Zero Python for Agents)**:
   - An agent is defined **purely by configuration and data**: `agent.json` (metadata, tools, model) and `agent.md` (markdown headers: `## role`, `## purpose`, `## boundaries`, `## output format`).
   - The core engine automatically loads these files, parses markdown sections, attaches tool schemas, and composes system prompts dynamically at runtime.

2. **The 4-Pillar Domain Model**:
   - **`core_engine/`**: The declarative loader, Think–Act–Observe loop, Ollama client, and `@tool` catalog.
   - **`editor/`**: Physical filesystem authority, path traversal security, and editor session manager.
   - **`workspace/`**: Project folder tree, squad hierarchy, and the single canonical home for all `agent.json` / `agent.md` definitions (`workspace/agents/`).
   - **`test_environment/`**: Prompt part builder, categories manifest, and 4-question section header test evaluator.

3. **Doorway Protocol (`interface.py`)**:
   - **Delete the top-level `interface/` directory entirely.**
   - Each component owns its API endpoints and public Python contracts inside its own `interface.py`.
   - In-process backend components communicate **exclusively** by calling Python functions exposed on target `interface.py` doorways (e.g., `from core_engine.interface import run_single_agent`).

4. **Frontend Architecture (Zero Build Tools, Pure Vanilla ES6)**:
   - No Node.js, Webpack, Vite, or npm bundler required.
   - Modular ES6 JavaScript (`frontend/static/js/*.js`) talking to the backend via a single unified API client wrapper (`frontend/static/js/api.js`).
   - Clean, dark-mode CSS theme (`frontend/static/css/style.css`) providing tabbed navigation across Workspace Dashboard, Editor, Chat Console, and Prompt Testing.

5. **Minimal Server Entry Point (`server.py`)**:
   - `server.py` is a ~25-line FastAPI app that imports the 4 component routers, mounts static assets, and serves HTML templates.

---

## 2. Target File Structure

```text
novous/
├── core_engine/                 ← Pillar 1: Declarative Engine & Think-Loop Runtime
│   ├── interface.py             ← Public Doorway: Python API & FastAPI Router (/api/chat, /api/agents, /api/tools)
│   ├── agent_factory.py         ← Parses agent.json/md & composes system prompts
│   ├── runtime.py               ← Generic Think-Act-Observe loop & Ollama client
│   └── tool_catalog.py          ← @tool registry & provider bindings
│
├── editor/                      ← Pillar 2: Monaco/Code Editor & Filesystem Authority
│   ├── interface.py             ← Public Doorway: Python API & FastAPI Router (/api/file/*, /api/directory/*, /api/ws)
│   ├── editor_operations.py     ← Physical file CRUD & Path Security (resolve_project_path)
│   ├── editor_session.py       ← Session Manager & Event Bus
│   └── editor_schemas.py       ← Scope & Event Payload Types
│
├── workspace/                   ← Pillar 3: Project State & Canonical Agent Storage
│   ├── agents/                  ← Single source of truth for all agent.json & agent.md files
│   ├── project.json             ← Project state metadata
│   ├── interface.py             ← Public Doorway: Python API & FastAPI Router (/api/project, /api/health)
│   ├── workspace_workflow.py   ← Agent Scaffolding & Squad Routing
│   └── squad_manager.py        ← Folder Hierarchy Engine
│
├── test_environment/           ← Pillar 4: Prompt Builder & Test Runner
│   ├── PromptBuilderFiles/      ← Prompt parts & categories.json
│   ├── test_agents/             ← Isolated published test fixtures
│   ├── interface.py             ← Public Doorway: Python API & FastAPI Router (/api/testing/*, /api/prompt-builder/*)
│   ├── test_runner.py          ← 4-Question Section Header Tests & Lexical Evaluator
│   └── prompt_builder.py       ← Prompt Part Assembler & Category Manifest
│
├── frontend/                    ← Web UI (Vanilla JS ES6 Modules & HTML5 Templates)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        ← Unified Dark Mode CSS Theme & Component Layouts
│   │   └── js/
│   │       ├── api.js           ← Unified REST API Client Wrapper
│   │       ├── app.js           ← Global App State & Tab Router
│   │       ├── tree.js          ← Interactive File Tree Component
│   │       ├── editor.js        ← File Editor Component (Monaco / Textarea)
│   │       ├── chat.js          ← Real-Time Agent Chat Console Component
│   │       └── testing.js       ← Prompt Builder & Header Test Runner Component
│   └── pages/                   ← HTML Templates
│       ├── index.html           ← Main Application Dashboard & Layout Host
│       ├── editor.html          ← File & Agent Editor Page View
│       ├── chat.html            ← Agent Chat Console Page View
│       └── testing.html         ← Prompt Builder & Test Suite Page View
│
├── scripts/                     ← Setup and dev scripts
│   ├── venv.bat / venv.sh       ← Virtualenv bootstrap
│   └── gen_master_copy.py       ← Code snapshot generator
│
└── server.py                    ← Clean FastAPI server mounting routers & static files
```

---

## 3. Server Entry Point Blueprint (`server.py`)

Build `server.py` as a clean mount point:

```python
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
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

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

@app.get("/test")
def test_page():
    return FileResponse("frontend/pages/testing.html")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("PROJECT_MANAGER_HOST", "127.0.0.1")
    port = int(os.getenv("PROJECT_MANAGER_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
```

---

## 4. Backend Execution Logic Chunks

### Chunk 1: Pillar 1 Runtime Engine (`core_engine/runtime.py`)

Implement the Think–Act–Observe execution loop, context window injector, and Ollama caller:

```python
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
    extras: dict = field(default_factory=dict)

class Agent:
    MAX_TOOL_ROUNDS = 6

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session=None):
        self.model = model or "qwen2.5-coder:latest"
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
```

---

### Chunk 2: Pillar 1 Prompt Composer (`core_engine/agent_factory.py`)

Parses `agent.json` + `agent.md` and composes unified system prompts:

```python
import json
from pathlib import Path
from core_engine.runtime import AgentProfile

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
```

---

### Chunk 3: Pillar 2 Filesystem Authority (`editor/editor_operations.py`)

```python
from pathlib import Path

PROJECT_ROOT = Path("workspace").resolve()

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

    return _build_tree(target_dir)
```

---

## 5. Frontend Code Chunks & Specs

### Chunk 4: Centralized API Client Wrapper (`frontend/static/js/api.js`)

This single file handles all asynchronous HTTP calls from the browser to the backend FastAPI endpoints:

```javascript
/**
 * Novous Unified API Client Wrapper
 */
export const Api = {
  // --- Workspace & Health ---
  async getHealth() {
    const res = await fetch('/api/health');
    return res.json();
  },

  async getProjectState() {
    const res = await fetch('/api/project');
    return res.json();
  },

  // --- Agents & Chat (Core Engine) ---
  async getAgents() {
    const res = await fetch('/api/agents');
    return res.json();
  },

  async createAgent(agentId, name, description) {
    const res = await fetch('/api/agents/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId, name, description })
    });
    return res.json();
  },

  async sendMessage(message, agentId, model = 'qwen2.5-coder:latest') {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, agent_id: agentId, model })
    });
    return res.json();
  },

  // --- Filesystem & Editor ---
  async getFileTree(path = '') {
    const res = await fetch(`/api/directory/tree?path=${encodeURIComponent(path)}`);
    return res.json();
  },

  async readFile(path) {
    const res = await fetch(`/api/file/read?path=${encodeURIComponent(path)}`);
    return res.json();
  },

  async writeFile(path, content) {
    const res = await fetch('/api/file/write', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content })
    });
    return res.json();
  },

  // --- Testing & Prompt Builder ---
  async getPromptCategories() {
    const res = await fetch('/api/prompt-builder/categories');
    return res.json();
  },

  async runHeaderTests(agentId) {
    const res = await fetch('/api/testing/run_header_tests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId })
    });
    return res.json();
  }
};
```

---

### Chunk 5: Global Layout Host (`frontend/pages/index.html`)

Build `index.html` as the master SPA layout frame with tabbed navigation:

```html
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
```

---

### Chunk 6: Interactive Chat Console Component (`frontend/static/js/chat.js`)

Provides interactive agent selection, message streaming, and tool execution badges:

```javascript
import { Api } from './api.js';

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
    </div>
  `;

  const agentSelect = container.querySelector('#chat-agent-select');
  const metaCard = container.querySelector('#agent-meta-card');
  const messagesBox = container.querySelector('#chat-messages');
  const chatForm = container.querySelector('#chat-form');
  const chatInput = container.querySelector('#chat-input');

  let agents = [];

  // Load available agents
  Api.getAgents().then(data => {
    agents = data.agents || [];
    agentSelect.innerHTML = agents.map(a => `<option value="${a.id}">${a.name} (${a.mode})</option>`).join('');
    if (agents.length > 0) updateAgentMeta(agents[0].id);
  });

  agentSelect.addEventListener('change', (e) => updateAgentMeta(e.target.value));

  function updateAgentMeta(id) {
    const agent = agents.find(a => a.id === id);
    if (!agent) return;
    metaCard.innerHTML = `
      <h4>${agent.name}</h4>
      <p class="badge">${agent.mode.toUpperCase()}</p>
      <p>${agent.description || 'No description provided.'}</p>
    `;
  }

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    const agentId = agentSelect.value;
    if (!text || !agentId) return;

    // Append User Message
    appendMessage('user', text);
    chatInput.value = '';

    // Show thinking indicator
    const thinkingId = appendMessage('assistant', 'Thinking...', true);

    try {
      const res = await Api.sendMessage(text, agentId);
      removeMessage(thinkingId);

      // Append tool badges if tool calls occurred
      if (res.tool_events && res.tool_events.length > 0) {
        res.tool_events.forEach(evt => {
          appendToolBadge(evt.tool, evt.status, evt.args);
        });
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
    badgeDiv.innerHTML = `🛠️ <strong>${toolName}</strong> executed (${status})`;
    messagesBox.appendChild(badgeDiv);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }
}
```

---

### Chunk 7: Application Router & CSS Styles (`frontend/static/css/style.css` & `app.js`)

Add CSS styling guidelines for clean dark-mode presentation:

```css
/* Dark Theme Base Styles */
:root {
  --bg-dark: #121316;
  --bg-card: #1e2025;
  --primary: #3b82f6;
  --text-main: #e2e8f0;
  --border-color: #2e323b;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-dark);
  color: var(--text-main);
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.nav-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.95rem;
}

.nav-btn.active {
  color: var(--primary);
  border-bottom: 2px solid var(--primary);
}

.chat-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  height: calc(100vh - 60px);
}

.chat-sidebar {
  background: var(--bg-card);
  padding: 1rem;
  border-right: 1px solid var(--border-color);
}

.chat-main {
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.messages-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 80%;
}

.user-msg {
  background: var(--primary);
  color: #fff;
  align-self: flex-end;
}

.assistant-msg {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  align-self: flex-start;
}

.tool-badge {
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: #2d3748;
  align-self: flex-start;
}
```

---

## 6. Full-Stack AI Execution Roadmap

When executing this build, work sequentially through these 6 phases:

1. **Phase 1: Environment & Directory Creation**:
   - Create backend and frontend directories: `core_engine/`, `editor/`, `workspace/agents/`, `test_environment/`, `frontend/static/css/`, `frontend/static/js/`, `frontend/pages/`.
2. **Phase 2: Pillar 1 (`core_engine/`)**:
   - Implement `runtime.py`, `agent_factory.py`, `tool_catalog.py`, and `interface.py`.
   - Expose FastAPI endpoints: `/api/chat`, `/api/agents`, `/api/agents/create`, `/api/tools`.
3. **Phase 3: Pillar 2 (`editor/`)**:
   - Implement `editor_operations.py`, `editor_session.py`, `editor_schemas.py`, and `interface.py`.
   - Expose FastAPI endpoints: `/api/file/read`, `/api/file/write`, `/api/directory/tree`, `/api/ws`.
4. **Phase 4: Pillar 3 (`workspace/`)**:
   - Scaffold `workspace/agents/` as canonical home.
   - Implement `workspace_workflow.py`, `squad_manager.py`, and `interface.py`.
   - Expose FastAPI endpoints: `/api/project`, `/api/health`.
5. **Phase 5: Pillar 4 (`test_environment/`)**:
   - Implement `test_runner.py`, `prompt_builder.py`, and `interface.py`.
   - Expose FastAPI endpoints: `/api/testing/run_header_tests`, `/api/prompt-builder/categories`.
6. **Phase 6: Frontend Assembly & Server Boot**:
   - Save `api.js`, `app.js`, `chat.js`, `editor.js`, `testing.js` in `frontend/static/js/`.
   - Create HTML templates (`index.html`, `editor.html`, `chat.html`, `testing.html`) in `frontend/pages/`.
   - Save `server.py` and boot application with `python server.py`.
   - Verify all API endpoints and UI tab views at `http://127.0.0.1:8000/`.
