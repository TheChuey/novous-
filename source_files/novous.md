# Novous — Code Snapshot

A complete verbatim copy of the Novous repository source, including its file structure and embedded file contents.

| Field | Value |
| ----- | ----- |
| Scope | `novous/` |
| Contains | file contents, verbatim |
| Files | 125 |
| Generated | 2026-10-05 |
| Generator | `scripts/gen_master_copy.py` |
| Regenerate | `.venv/Scripts/python -m scripts.gen_master_copy` |
| Companions | [`APP_CODE_SNAPSHOT.md`](APP_CODE_SNAPSHOT.md) — the existing canonical repository snapshot, [`headless_app_MASTER_COPY.md`](headless_app_MASTER_COPY.md) — `headless_app/` |

## What This Is

A verbatim copy of every source file in this repository, in one document,
behind one file structure. It exists for reference and AI lookup: to answer a
question about the code, or to rebuild it, the exact bytes of every file plus a
map of where everything lives are what is needed, and that is what this
document is.

There is deliberately **no description of what the code does here**. That
lives in the companion document, which describes the agent engine module by
module:

- [`headless_app_MASTER_COPY.md`](headless_app_MASTER_COPY.md) — the agent
  engine, its tools and its bridge.

Read the master copy to learn what a file is for, then come here for its
contents. The File Index below is sized so you can also jump straight to one
file and read only that.

---

## Boot Sequence

### Prerequisites

- Python 3.10 or newer. The virtual environment in this workspace is 3.14.
- Ollama running locally, with at least one model pulled. The picker list in
  `headless_app/config/models.json` names `llama3.1:8b`,
  `nomic-embed-text:latest`, `qwen2.5-coder:latest` and `gemma4:e2b`.
- A web browser. The interface is static HTML, CSS and vanilla JavaScript —
  there is no build step and no bundler.

### Create the environment and run

```bat
rem 1. Virtual environment at the repository root, shared by both halves.
scripts\venv.bat

rem 2. Dependencies. requirements.txt pins the server stack. The engine also
rem    needs ollama and pydantic, which venv.bat installs for you.
.venv\Scripts\python.exe -m pip install -r requirements.txt

rem 3. Start the web app: the editor, chat page and agent routes are served
rem    by this one process.
.venv\Scripts\python.exe server.py
```

Then open <http://127.0.0.1:8000>. The bind address and port come from
`PROJECT_MANAGER_HOST` and `PROJECT_MANAGER_PORT` (the repository-root
`server.py`).
The engine also runs without the server:

```bat
cd headless_app
..\.venv\Scripts\python.exe run.py list-agents
..\.venv\Scripts\python.exe run.py run-agent rag_assistant --message "what date is it today?"
```

### Layout requirement

The repository-root `server.py` imports the engine by putting
`<repo>/headless_app` on `sys.path`; the chat and agent routers also resolve
that path relative to their files.


## File Index

All 125 embedded files, with their size, so a reader can decide what to open. The contents are further down, in this same order, each under a `### path` heading and an `<!-- ==== n/total : path ==== -->` marker.

| # | File | Lines | Bytes |
| - | ---- | ----- | ----- |
| 1 | `.gitattributes` | 14 | 254 |
| 2 | `.gitignore` | 41 | 559 |
| 3 | `engine_components.py` | 55 | 1632 |
| 4 | `engine_interface.py` | 145 | 4856 |
| 5 | `engine_logic.py` | 169 | 6489 |
| 6 | `frontend/css/builder.css` | 196 | 5778 |
| 7 | `frontend/js/agentCards.js` | 98 | 3009 |
| 8 | `frontend/js/agentColors.js` | 70 | 2178 |
| 9 | `frontend/js/agents.js` | 101 | 3311 |
| 10 | `frontend/js/api.js` | 166 | 5510 |
| 11 | `frontend/js/builder.js` | 1349 | 49152 |
| 12 | `frontend/js/chat.js` | 631 | 22056 |
| 13 | `frontend/js/editor.js` | 83 | 1899 |
| 14 | `frontend/js/main.js` | 403 | 12396 |
| 15 | `frontend/js/orchestrator.js` | 228 | 7039 |
| 16 | `frontend/js/panels.js` | 382 | 13345 |
| 17 | `frontend/js/report.js` | 186 | 6965 |
| 18 | `frontend/js/session.js` | 63 | 1448 |
| 19 | `frontend/js/topbar.js` | 160 | 4401 |
| 20 | `frontend/js/tree.js` | 221 | 7339 |
| 21 | `frontend/pages/chat.html` | 1132 | 36338 |
| 22 | `frontend/pages/editor.html` | 403 | 12126 |
| 23 | `frontend/pages/home.html` | 373 | 9196 |
| 24 | `frontend/pages/index.html` | 718 | 22748 |
| 25 | `frontend/pages/prompt-builder.html` | 43 | 1652 |
| 26 | `frontend/pages/testing.html` | 866 | 33715 |
| 27 | `headless_app/bridge/__init__.py` | 11 | 236 |
| 28 | `headless_app/bridge/client.py` | 910 | 24212 |
| 29 | `headless_app/bridge/providers.py` | 119 | 3770 |
| 30 | `headless_app/bridge/routers/__init__.py` | 1 | 71 |
| 31 | `headless_app/bridge/routers/agents.py` | 558 | 16582 |
| 32 | `headless_app/bridge/routers/chat.py` | 259 | 6980 |
| 33 | `headless_app/bridge/tools_adapter.py` | 70 | 2198 |
| 34 | `headless_app/config/models.json` | 29 | 568 |
| 35 | `headless_app/config/pipeline.json` | 9 | 336 |
| 36 | `headless_app/engine/__init__.py` | 1 | 0 |
| 37 | `headless_app/engine/agent_library/Builder/agent.json` | 13 | 350 |
| 38 | `headless_app/engine/agent_library/Builder/agent.md` | 141 | 7888 |
| 39 | `headless_app/engine/agent_library/Enginner/agent.json` | 11 | 365 |
| 40 | `headless_app/engine/agent_library/Enginner/agent.md` | 59 | 2946 |
| 41 | `headless_app/engine/agent_library/Planner/agent.json` | 9 | 311 |
| 42 | `headless_app/engine/agent_library/Planner/agent.md` | 1 | 0 |
| 43 | `headless_app/engine/agent_library/rag_assistant/agent.json` | 38 | 1380 |
| 44 | `headless_app/engine/agent_library/rag_assistant/agent.md` | 37 | 2065 |
| 45 | `headless_app/engine/agents/__init__.py` | 1 | 0 |
| 46 | `headless_app/engine/agents/factory.py` | 235 | 9041 |
| 47 | `headless_app/engine/agents/loader.py` | 237 | 8492 |
| 48 | `headless_app/engine/agents/registry.py` | 95 | 3579 |
| 49 | `headless_app/engine/agents/roots.py` | 204 | 6202 |
| 50 | `headless_app/engine/core/__init__.py` | 1 | 0 |
| 51 | `headless_app/engine/core/agent.py` | 505 | 22011 |
| 52 | `headless_app/engine/core/llm.py` | 294 | 11316 |
| 53 | `headless_app/engine/core/prompt.py` | 126 | 4447 |
| 54 | `headless_app/engine/pipeline.py` | 189 | 6959 |
| 55 | `headless_app/interface_runner.py` | 342 | 12514 |
| 56 | `headless_app/run.py` | 200 | 6121 |
| 57 | `headless_app/tools/__init__.py` | 1 | 0 |
| 58 | `headless_app/tools/chatlog.py` | 221 | 7677 |
| 59 | `headless_app/tools/memory.py` | 20 | 526 |
| 60 | `headless_app/tools/project_tools.py` | 776 | 30593 |
| 61 | `headless_app/tools/registry.py` | 109 | 3190 |
| 62 | `headless_app/tools/state.py` | 66 | 2615 |
| 63 | `headless_app/tools/utility.py` | 23 | 583 |
| 64 | `headless_app/tools/workspace.py` | 74 | 2338 |
| 65 | `interface/clients/__init__.py` | 22 | 450 |
| 66 | `interface/clients/editor_client.py` | 696 | 16962 |
| 67 | `interface/core/__init__.py` | 22 | 572 |
| 68 | `interface/core/defaults.py` | 109 | 2437 |
| 69 | `interface/core/events.py` | 104 | 2439 |
| 70 | `interface/core/operations.py` | 486 | 12762 |
| 71 | `interface/core/session.py` | 130 | 3121 |
| 72 | `interface/routers/__init__.py` | 103 | 2471 |
| 73 | `interface/routers/agents.py` | 606 | 18040 |
| 74 | `interface/routers/chat.py` | 721 | 19751 |
| 75 | `interface/routers/directories.py` | 86 | 2024 |
| 76 | `interface/routers/errors.py` | 73 | 1475 |
| 77 | `interface/routers/files.py` | 172 | 3725 |
| 78 | `interface/routers/paths.py` | 58 | 1272 |
| 79 | `interface/routers/project.py` | 107 | 2491 |
| 80 | `interface/routers/testing.py` | 317 | 10202 |
| 81 | `interface/routers/ws.py` | 225 | 5759 |
| 82 | `interface_runner.py` | 12 | 399 |
| 83 | `parameters/__init__.py` | 6 | 171 |
| 84 | `parameters/filesystem.py` | 1194 | 27038 |
| 85 | `README.md` | 288 | 13437 |
| 86 | `requirements.txt` | 6 | 104 |
| 87 | `scripts/check_builder_css.py` | 175 | 4946 |
| 88 | `scripts/gen_master_copy.py` | 2032 | 55974 |
| 89 | `scripts/run.bat` | 15 | 327 |
| 90 | `scripts/run.sh` | 21 | 425 |
| 91 | `scripts/setup.sh` | 33 | 874 |
| 92 | `scripts/venv.bat` | 35 | 1120 |
| 93 | `scripts/venv.ps1` | 40 | 1675 |
| 94 | `server.py` | 158 | 4547 |
| 95 | `test_environment/agent_test.py` | 633 | 22113 |
| 96 | `test_environment/PromptBuilderFiles/categories.json` | 30 | 435 |
| 97 | `test_environment/PromptBuilderFiles/output/agents/jesus/agent.json` | 12 | 250 |
| 98 | `test_environment/PromptBuilderFiles/output/agents/jesus/agent.md` | 25 | 1281 |
| 99 | `test_environment/PromptBuilderFiles/output/agents/new_agent/agent.json` | 9 | 218 |
| 100 | `test_environment/PromptBuilderFiles/output/agents/new_agent/agent.md` | 21 | 1088 |
| 101 | `test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.json` | 9 | 234 |
| 102 | `test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.md` | 21 | 1088 |
| 103 | `test_environment/PromptBuilderFiles/output/agents/planner_prompt_3/agent.md` | 29 | 1314 |
| 104 | `test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_1/agent.md` | 26 | 1759 |
| 105 | `test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_2/agent.md` | 25 | 1178 |
| 106 | `test_environment/PromptBuilderFiles/output/agents/test_4/agent.md` | 22 | 1549 |
| 107 | `test_environment/PromptBuilderFiles/prompt_parts/hallucinations/chat_agent.txt` | 11 | 884 |
| 108 | `test_environment/PromptBuilderFiles/prompt_parts/hallucinations/planner_agent_hallucination_rules.txt` | 9 | 784 |
| 109 | `test_environment/PromptBuilderFiles/prompt_parts/hallucinations/rule_set_one_by_gemni.txt` | 10 | 1368 |
| 110 | `test_environment/PromptBuilderFiles/prompt_parts/output/output.txt` | 2 | 136 |
| 111 | `test_environment/PromptBuilderFiles/prompt_parts/role/chat_agent.txt` | 2 | 106 |
| 112 | `test_environment/PromptBuilderFiles/prompt_parts/role/planner.txt` | 2 | 95 |
| 113 | `test_environment/PromptBuilderFiles/prompt_parts/role/problem_anallyser.txt` | 2 | 214 |
| 114 | `test_environment/PromptBuilderFiles/prompt_parts/tools/resoources.txt` | 2 | 243 |
| 115 | `test_environment/PromptBuilderFiles/prompt_parts/user/greating.txt` | 2 | 74 |
| 116 | `test_environment/PromptBuilderFiles/prompt_parts/user/name.txt` | 2 | 7 |
| 117 | `test_environment/test_agent_test.py` | 53 | 1990 |
| 118 | `test_environment/test_agents/jesus/agent.json` | 12 | 250 |
| 119 | `test_environment/test_agents/jesus/agent.md` | 25 | 1281 |
| 120 | `test_environment/test_langchain_tools.py` | 111 | 3702 |
| 121 | `workspace/agents/Assistant/agent.json` | 12 | 228 |
| 122 | `workspace/agents/Assistant/agent.md` | 18 | 289 |
| 123 | `workspace/agents/jesus/agent.json` | 11 | 270 |
| 124 | `workspace/agents/jesus/agent.md` | 25 | 1281 |
| 125 | `workspace/project.json` | 6 | 95 |
| | **125 files** | **23522** | **746647** |

## File Structure

```text
novous/
├── frontend/
│   ├── css/
│   │   └── builder.css
│   ├── js/
│   │   ├── agentCards.js
│   │   ├── agentColors.js
│   │   ├── agents.js
│   │   ├── api.js
│   │   ├── builder.js
│   │   ├── chat.js
│   │   ├── editor.js
│   │   ├── main.js
│   │   ├── orchestrator.js
│   │   ├── panels.js
│   │   ├── report.js
│   │   ├── session.js
│   │   ├── topbar.js
│   │   └── tree.js
│   └── pages/
│       ├── chat.html
│       ├── editor.html
│       ├── home.html
│       ├── index.html
│       ├── prompt-builder.html
│       └── testing.html
├── headless_app/
│   ├── bridge/
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py
│   │   │   └── chat.py
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── providers.py
│   │   └── tools_adapter.py
│   ├── config/
│   │   ├── models.json
│   │   └── pipeline.json
│   ├── data/   # not embedded: runtime output: chat log, tool log, pipeline run records
│   ├── engine/
│   │   ├── agent_library/
│   │   │   ├── Builder/
│   │   │   │   ├── agent.json
│   │   │   │   └── agent.md
│   │   │   ├── Enginner/
│   │   │   │   ├── agent.json
│   │   │   │   └── agent.md
│   │   │   ├── Planner/
│   │   │   │   ├── agent.json
│   │   │   │   └── agent.md
│   │   │   └── rag_assistant/
│   │   │       ├── agent.json
│   │   │       └── agent.md
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py
│   │   │   ├── loader.py
│   │   │   ├── registry.py
│   │   │   └── roots.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── llm.py
│   │   │   └── prompt.py
│   │   ├── __init__.py
│   │   └── pipeline.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── chatlog.py
│   │   ├── memory.py
│   │   ├── project_tools.py
│   │   ├── registry.py
│   │   ├── state.py
│   │   ├── utility.py
│   │   └── workspace.py
│   ├── interface_runner.py
│   └── run.py
├── interface/
│   ├── clients/
│   │   ├── __init__.py
│   │   └── editor_client.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── defaults.py
│   │   ├── events.py
│   │   ├── operations.py
│   │   └── session.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agents.py
│   │   ├── chat.py
│   │   ├── directories.py
│   │   ├── errors.py
│   │   ├── files.py
│   │   ├── paths.py
│   │   ├── project.py
│   │   ├── testing.py
│   │   └── ws.py
│   └── static/
│       └── js/
├── parameters/
│   ├── __init__.py
│   └── filesystem.py
├── scripts/
│   ├── check_builder_css.py
│   ├── gen_master_copy.py
│   ├── run.bat
│   ├── run.sh
│   ├── setup.sh
│   ├── venv.bat
│   └── venv.ps1
├── source_files/
├── test_environment/
│   ├── output/   # not embedded: runtime output: header test results
│   ├── PromptBuilderFiles/
│   │   ├── output/
│   │   │   └── agents/
│   │   │       ├── jesus/
│   │   │       │   ├── agent.json
│   │   │       │   └── agent.md
│   │   │       ├── new_agent/
│   │   │       │   ├── agent.json
│   │   │       │   └── agent.md
│   │   │       ├── new_agent_planner/
│   │   │       │   ├── agent.json
│   │   │       │   └── agent.md
│   │   │       ├── planner_prompt_3/
│   │   │       │   └── agent.md
│   │   │       ├── planner_prompt_test_1/
│   │   │       │   └── agent.md
│   │   │       ├── planner_prompt_test_2/
│   │   │       │   └── agent.md
│   │   │       └── test_4/
│   │   │           └── agent.md
│   │   ├── prompt_parts/
│   │   │   ├── hallucinations/
│   │   │   │   ├── chat_agent.txt
│   │   │   │   ├── planner_agent_hallucination_rules.txt
│   │   │   │   └── rule_set_one_by_gemni.txt
│   │   │   ├── output/
│   │   │   │   └── output.txt
│   │   │   ├── role/
│   │   │   │   ├── chat_agent.txt
│   │   │   │   ├── planner.txt
│   │   │   │   └── problem_anallyser.txt
│   │   │   ├── tools/
│   │   │   │   └── resoources.txt
│   │   │   └── user/
│   │   │       ├── greating.txt
│   │   │       └── name.txt
│   │   └── categories.json
│   ├── test_agents/
│   │   ├── jesus/
│   │   │   ├── agent.json
│   │   │   └── agent.md
│   │   └── new_agent_planner/
│   ├── test_data/   # not embedded: runtime output: chat log and tool log of test runs
│   ├── agent_test.py
│   ├── test_agent_test.py
│   └── test_langchain_tools.py
├── workspace/
│   ├── agents/
│   │   ├── Assistant/
│   │   │   ├── agent.json
│   │   │   └── agent.md
│   │   └── jesus/
│   │       ├── agent.json
│   │       └── agent.md
│   ├── config/
│   ├── data/   # not embedded: runtime output: chat log and saved chat sessions
│   ├── documentation/
│   ├── project_scope/
│   ├── Tests/
│   ├── To Do/   # not embedded: personal working notes, gitignored and not part of the project
│   ├── updates/
│   └── project.json
├── .gitattributes
├── .gitignore
├── engine_components.py
├── engine_interface.py
├── engine_logic.py
├── interface_runner.py
├── README.md
├── requirements.txt
└── server.py
```

## Scope

This document embeds every source file under `novous/`, **125 files** in total, in case-insensitive path order, verbatim and unmodified.

The following are listed in the structure above but deliberately **not** covered:

| Path | Reason |
| ---- | ------ |
| `headless_app/data` | runtime output: chat log, tool log, pipeline run records |
| `test_environment/output` | runtime output: header test results |
| `test_environment/test_data` | runtime output: chat log and tool log of test runs |
| `workspace/To Do` | personal working notes, gitignored and not part of the project |
| `workspace/data` | runtime output: chat log and saved chat sessions |
| `workspace/skills` | personal chat skills, gitignored and managed by the chat page |

Also excluded everywhere: `.git`, `__pycache__/`, virtualenvs, editor and tool caches (`.venv`, `venv`, `.idea`, `.vscode`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`), compiled and runtime artifacts (`*.pyc`, `*.pyo`, `*.log`, `*.dll`).

Generated documents in `source_files/` are never embedded in each other, so no document can nest inside itself.

Regenerate all generated documents with:

```bat
.venv/Scripts/python -m scripts.gen_master_copy
```

Or just this document:

```bat
.venv/Scripts/python -m scripts.gen_master_copy --only novous
```

<!-- ==== 1/125 : .gitattributes ==== -->

### .gitattributes

```text
# Text files use LF line endings everywhere.
* text=auto eol=lf

# Explicit text / code files
*.py text eol=lf
*.sh text eol=lf
*.bat text eol=lf
*.html text eol=lf
*.css text eol=lf
*.js text eol=lf
*.json text eol=lf
*.md text eol=lf
*.txt text eol=lf
```

---

<!-- ==== 2/125 : .gitignore ==== -->

### .gitignore

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.eggs/
build/
dist/

# Virtual environments
.venv/
venv/
env/

# Test / tooling caches
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Editor / IDE
.idea/
.vscode/

# Logs and runtime data
*.log
*.jsonl
workspace/ws_evt_probe.txt
workspace/data/
workspace/skills/
workspace/legacy_project_manager_workspace/

# Test environment runtime output
test_environment/output/
test_environment/test_data/

# Local working notes
planSave.txt
workspace/To Do/
```

---

<!-- ==== 3/125 : engine_components.py ==== -->

### engine_components.py

```python
"""
engine_components.py
====================

The ONLY module the logic layer imports implementation from.

Everything below already exists in engine/, tools/ and bridge/. This file
does not wrap or rewrite any of it; it names the surface the logic layer is
allowed to use, so a rename or move inside the engine touches one file.

    engine_interface  ->  engine_logic  ->  engine_components  ->  engine/ tools/ bridge/
"""

from engine.agents.factory import (  # noqa: F401
    AgentDefinitionError,
    build_agent,
    build_agent_from_definition,
    replay_history,
)
from engine.agents.loader import (  # noqa: F401
    AgentNotFoundError,
    agent_json_path,
    agent_md_path,
    load_definition,
)
from engine.agents.registry import get_agent_meta, list_agents  # noqa: F401
from engine.agents.roots import (  # noqa: F401
    find_agent,
    register_agent_root,
    unregister_agent_root,
)
from engine.core.llm import CONFIG_DIR, refresh_models  # noqa: F401
from engine.pipeline import load_pipeline, run_pipeline as run_chain  # noqa: F401
from tools.chatlog import (  # noqa: F401
    append_chat,
    clear_chat,
    read_history,
    use_data_dir,
)
from tools.registry import _TOOL_REGISTRY, list_tools  # noqa: F401


def direct_provider():
    """In-process filesystem provider (needs the Project Manager importable)."""
    from bridge.providers import DirectProjectIO

    return DirectProjectIO()


def http_provider(base_url: str | None = None):
    """HTTP bridge provider for the standalone CLI."""
    from bridge.client import ProjectManagerBridge

    return ProjectManagerBridge(base_url=base_url)
```

---

<!-- ==== 4/125 : engine_interface.py ==== -->

### engine_interface.py

```python
"""
engine_interface.py
===================

THE public doorway into the agent engine. Callers (CLI, server routers,
test runner) import this module and nothing else from headless_app.

    import engine_interface as engine
    engine.configure(bridge=engine.direct_provider())
    engine.run_chat("hello", agent_id="rag_assistant")

Contract
--------
* Validates input, then delegates to engine_logic. No workflow lives here.
* Returns plain dicts / lists (JSON-ready).
* Raises only:
    ValueError            bad input                (HTTP 400)
    AgentNotFoundError    unknown agent id/path    (HTTP 404, a FileNotFoundError)
    anything else         genuine failure          (HTTP 500)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_ENGINE_ROOT = Path(__file__).resolve().parent / "headless_app"
if _ENGINE_ROOT.is_dir() and str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))

import engine_components as _c
import engine_logic as _logic
from engine_components import AgentDefinitionError, AgentNotFoundError  # noqa: F401
from engine_components import direct_provider, http_provider  # noqa: F401

MAX_MESSAGE_LENGTH = 2000

_runtime = _logic.EngineRuntime()


# ---- configuration -------------------------------------------------

def configure(bridge: Any = None, model: str | None = None,
              log_sink: Callable[[dict], None] | None = None) -> None:
    """Set the filesystem provider, default model and log mirror."""
    global _runtime
    _runtime = _logic.EngineRuntime(bridge=bridge, model=model, log_sink=log_sink)


def register_agent_root(name: str, path, source: str | None = None) -> None:
    """Make another folder of agent folders runnable (e.g. workspace/agents)."""
    _c.register_agent_root(name, path, source=source)


def unregister_agent_root(name: str) -> bool:
    return _c.unregister_agent_root(name)


# ---- validation ----------------------------------------------------

def _message(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Chat message cannot be empty.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Chat message is too long (max {MAX_MESSAGE_LENGTH} characters).")
    return text


# ---- runs ----------------------------------------------------------

def run_chat(message: str, agent_id: str | None = None,
             model: str | None = None) -> dict:
    """One chat turn. {reply, agent_id, name, model, tool_events, entries}"""
    return _runtime.run_chat(_message(message), agent_id=agent_id, model=model)


def run_single_agent(message: str, json_path: str | None = None,
                     md_path: str | None = None, agent_id: str | None = None,
                     model: str | None = None) -> dict:
    """Run one agent from agent.json + agent.md paths, or from an id."""
    return _runtime.run_single_agent(_message(message), json_path=json_path,
                                     md_path=md_path, agent_id=agent_id, model=model)


def run_pipeline(message: str, steps: list | None = None,
                 model: str | None = None) -> dict:
    """Cascade agents. steps: ids or {json_path, md_path}; None = config default.
    {reply, outputs, tool_events, model, entries}"""
    text = _message(message)
    if steps is not None and not steps:
        raise ValueError("Pipeline requires at least one step.")
    for step in steps or []:
        if isinstance(step, dict) and not (step.get("json_path") and step.get("md_path")):
            raise ValueError(f"Pipeline step dicts need json_path + md_path: {step!r}")
    return _runtime.run_pipeline(text, agent_configs=steps, model=model)


# ---- discovery -----------------------------------------------------

def list_agents() -> list[dict]:
    return _runtime.list_agents()


def get_agent(agent_id: str) -> dict:
    """Definition of one agent. Raises AgentNotFoundError."""
    return _logic.agent_definition(agent_id)


def default_pipeline() -> list:
    return _c.load_pipeline()


def list_models() -> list[dict]:
    return _logic.list_models()


def refresh_models() -> list[dict]:
    return _c.refresh_models()


def list_tools() -> list[str]:
    return _c.list_tools()


def tool_catalog() -> list[dict]:
    """[{id, summary, description, parameters:[{name, required, default}]}]"""
    return _logic.tool_catalog()


# ---- chat history --------------------------------------------------

def read_history(limit: int = 50, agent: str | None = None) -> list[dict]:
    return _c.read_history(limit, agent=agent)


def clear_history(agent: str | None = None) -> int:
    return _c.clear_chat(agent=agent)


def use_data_dir(path):
    """Context manager: write chat/tool logs under `path` (used by tests)."""
    return _c.use_data_dir(path)
```

---

<!-- ==== 5/125 : engine_logic.py ==== -->

### engine_logic.py

```python
"""
engine_logic.py
===============

Workflows of the agent engine: what happens, in what order.

    build agent -> replay history -> think -> log both sides
    pipeline    -> feed-forward chain -> log the exchange untagged

No input validation (that is engine_interface) and no implementation
(that is engine_components).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import engine_components as c

DEFAULT_HISTORY_LIMIT = 20


def _as_history(agent_id: str | None, limit: int | None = DEFAULT_HISTORY_LIMIT):
    """One agent's recent turns from the chat log, as model messages."""
    if not limit or limit <= 0:
        return None
    try:
        entries = c.read_history(limit=limit, agent=agent_id)
    except Exception as exc:  # a broken log must never block a conversation
        print(f"[ENGINE] history unavailable: {exc}")
        return None

    history = []
    for entry in entries:
        content = str(entry.get("message", "") or "")
        if not content:
            continue
        sender = str(entry.get("sender", ""))
        history.append({
            "role": "assistant" if sender in ("agent", "ai") else "user",
            "content": content,
        })
    return history or None


class EngineRuntime:
    """Runs agents. Holds configuration only; no conversation state."""

    def __init__(self, bridge: Any = None, model: str | None = None,
                 log_sink: Callable[[dict], None] | None = None) -> None:
        self.bridge = bridge
        self.model = model
        self.log_sink = log_sink

    # ---- internals -------------------------------------------------

    def _log(self, sender: str, message: str, agent_id: str | None) -> dict:
        entry = c.append_chat(sender, message, agent=agent_id)
        if self.log_sink is not None:
            try:
                self.log_sink(entry)
            except Exception as exc:
                print(f"[ENGINE] log sink failed: {exc}")
        return entry

    def _think(self, agent, message, agent_id, history):
        if history:
            c.replay_history(agent, history)
        reply = agent.think(message)
        entries = [self._log("user", message, agent_id),
                   self._log("agent", reply, agent_id)]
        return reply, entries

    def _default_agent_id(self) -> str:
        agents = self.list_agents()
        if not agents:
            raise RuntimeError("No agents are registered.")
        return agents[0]["id"]

    # ---- discovery -------------------------------------------------

    def list_agents(self) -> list[dict]:
        return c.list_agents()

    def get_agent(self, agent_id: str) -> dict | None:
        return c.get_agent_meta(agent_id)

    # ---- runs ------------------------------------------------------

    def run_chat(self, message, agent_id=None, model=None, history=None,
                 use_logged_history=True) -> dict:
        resolved = agent_id or self._default_agent_id()
        agent = c.build_agent(resolved, model=model or self.model, bridge=self.bridge)
        if history is None and use_logged_history:
            history = _as_history(resolved)
        reply, entries = self._think(agent, message, resolved, history)
        return {"reply": reply, "agent_id": resolved, "name": agent.profile.name,
                "model": agent.model, "tool_events": agent.tool_events,
                "entries": entries}

    def run_single_agent(self, user_input, json_path=None, md_path=None,
                         agent_id=None, model=None, history=None,
                         use_logged_history=False) -> dict:
        if json_path and md_path:
            agent = c.build_agent_from_definition(
                json_path, md_path, model=model or self.model, bridge=self.bridge)
            resolved = str(agent.profile.id)
        elif agent_id:
            resolved = agent_id
            agent = c.build_agent(agent_id, model=model or self.model,
                                  bridge=self.bridge)
        else:
            raise ValueError("Provide json_path + md_path, or an agent_id, to run.")
        if history is None and use_logged_history:
            history = _as_history(resolved)
        reply, entries = self._think(agent, user_input, resolved, history)
        return {"reply": reply, "agent_id": resolved, "name": agent.profile.name,
                "description": agent.profile.description, "model": agent.model,
                "tool_events": agent.tool_events, "entries": entries}

    def run_pipeline(self, user_input, agent_configs=None, model=None) -> dict:
        result = c.run_chain(user_input, model=model or self.model,
                             steps=agent_configs, bridge=self.bridge)
        # A cascade is not one agent: logged untagged.
        result["entries"] = [self._log("user", user_input, None),
                             self._log("agent", result["reply"], None)]
        result["model"] = model or self.model
        return result


# ---- read-only helpers (no runtime state needed) --------------------

def agent_definition(agent_id: str) -> dict:
    d = c.load_definition(agent_id)
    found = c.find_agent(agent_id)
    return {"source": found[0].source if found else "library",
            "meta": d["meta"], "sections": d["sections"],
            "json_path": c.agent_json_path(agent_id),
            "md_path": c.agent_md_path(agent_id)}


def list_models() -> list[dict]:
    path = c.CONFIG_DIR / "models.json"
    if not path.exists():
        return []
    models = json.loads(path.read_text(encoding="utf-8")).get("models") or []
    return [{"id": m.get("id", ""), "name": m.get("name", m.get("id", "")),
             "source": m.get("source", "ollama")} for m in models]


def tool_catalog() -> list[dict]:
    """Return UI descriptors from each registered LangChain tool schema."""
    out = []
    for tool_id in c.list_tools():
        registered_tool = c._TOOL_REGISTRY[tool_id]
        doc = registered_tool.description or ""
        params = [
            {
                "name": name,
                "required": field.is_required(),
                "default": None if field.is_required() else repr(field.default),
            }
            for name, field in registered_tool.args_schema.model_fields.items()
        ]
        out.append({"id": tool_id, "summary": doc.splitlines()[0] if doc else "",
                    "description": doc, "parameters": params})
    return out
```

---

<!-- ==== 6/125 : frontend/css/builder.css ==== -->

### frontend/css/builder.css

```css
/* ============================================================
   Agent Prompt Builder - panel styles
   ============================================================

   Shared by two hosts: /prompt-builder (standalone) and /test (the
   right-hand panel). Loaded by both rather than inlined, because the
   builder is no longer one page.

   Every rule is scoped under .pb, and the three rules that cannot be
   scoped are gone rather than prefixed:

     body  - the host owns it. In /test it is a flex column pinned to
             the viewport; a nested body cannot be reached from here at
             all, and in the standalone shell it is already correct.
     header / h1 / header p - page furniture, not builder furniture.
             Both hosts carry their own.
     main - the builder's own layout is .pb-cards below. A prefixing
             `main` selector would either miss the panel (the panel is
             an aside in /test) or hit the host's main and give it the
             builder's 1fr 1fr columns.

   Anything added here without the .pb prefix silently becomes a global
   rule and will hit whichever page embeds this. scripts/check_builder_css.py
   asserts that. */

.pb-cards {
    display: flex;
    flex-direction: column;
    gap: 16px;
    /* Caps and centres the cards on the standalone page, where there is
       no panel to bound them. Inside the /test panel it never binds:
       the panel's own max is narrower than this. */
    max-width: 1200px;
    margin: 0 auto;
}

.pb .card { background: #151a20; border: 1px solid #303741; border-radius: 8px; padding: 16px; }

/* The 2-column grid the standalone page used is dropped rather than
   narrowed: at panel width every card would be an unreadable column. */
.pb h2 {
    margin: 0 0 12px;
    font-size: 16px;
    color: #dfe6ee;
    border-bottom: 1px solid #303741;
    padding-bottom: 8px;
}

.pb label {
    display: block;
    margin: 10px 0 6px;
    font-size: 13px;
    color: #aeb9c5;
}

.pb .microlabel {
    display: block;
    margin: 14px 0 5px;
    font-size: 12px;
    color: #8fa0b3;
    letter-spacing: .04em;
}

.pb .catrow { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.pb .catrow select, .pb .catrow input { flex: 1; min-width: 0; }
.pb .catrow button { flex-shrink: 0; }
.pb .catrow[hidden] { display: none; }

.pb input, .pb textarea, .pb select {
    width: 100%;
    background: #0d1116;
    color: #edf2f7;
    border: 1px solid #39424d;
    border-radius: 6px;
    padding: 9px;
    font-family: inherit;
}

.pb textarea { min-height: 110px; resize: vertical; }
.pb #master_prompt { min-height: 320px; font-family: Consolas, Menlo, monospace; font-size: 13px; }

.pb button {
    border: 0;
    border-radius: 6px;
    padding: 10px 14px;
    cursor: pointer;
    background: #4c8bf5;
    color: white;
    font-size: 14px;
    font-family: inherit;
}

.pb button.secondary { background: #303944; }
.pb button.danger { background: #7a2f3c; }
.pb button.tiny { padding: 3px 9px; font-size: 12px; }
.pb button:disabled { opacity: .45; cursor: not-allowed; }
.pb button:hover:not(:disabled) { opacity: .92; }

.pb .row { display: flex; gap: 8px; margin-top: 14px; }
.pb .row button { flex: 1; }

.pb .parts-group { margin-bottom: 14px; }
.pb .tool-list { display: grid; gap: 8px; }
.pb .tool-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    justify-content: space-between;
    padding: 9px;
    background: #10151b;
    border: 1px solid #303741;
    border-radius: 6px;
}
.pb .tool-info { min-width: 0; }
.pb .tool-info code { color: #9fc9f5; overflow-wrap: anywhere; }
.pb .tool-info p { margin: 5px 0 0; color: #9ca8b5; font-size: 12px; line-height: 1.45; }
.pb .tool-row button { flex-shrink: 0; }
.pb .parts-group h3 {
    margin: 0 0 6px;
    font-size: 13px;
    color: #8fa0b3;
    text-transform: uppercase;
    letter-spacing: .04em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.pb .parts-group h3 .count { color: #5c6774; text-transform: none; letter-spacing: 0; }

.pb .part-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 14px; }
.pb .part-row input[type=checkbox] { width: auto; }
.pb .part-row .name {
    margin: 0;
    flex: 1;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.pb .part-row .actions { display: flex; gap: 6px; flex-shrink: 0; }

.pb .empty { color: #5c6774; font-size: 13px; font-style: italic; }
.pb .empty code {
    font-style: normal;
    background: #0d1116;
    padding: 2px 6px;
    border-radius: 5px;
    border: 1px solid #39424d;
}

/* The dashboard's own .status rules carry line-height and the [hidden]
   guard; repeated here so the two pages cannot drift apart. */
.pb .status {
    margin-top: 14px;
    padding: 10px;
    border-radius: 6px;
    background: #1a2129;
    color: #aeb9c5;
    font-size: 13px;
    white-space: pre-wrap;
    line-height: 1.5;
}
.pb .status[hidden] { display: none; }
.pb .status.error { color: #ff9b9b; }
.pb .status.ok { color: #8fe3a6; }
.pb .status.warn { color: #f5c96b; }

.pb .folderbar {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 13px;
    color: #aeb9c5;
}
.pb .folderbar code {
    background: #0d1116;
    padding: 3px 7px;
    border-radius: 5px;
    border: 1px solid #39424d;
}
.pb .folderbar button { margin-left: auto; }

.pb .headrow { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.pb .headrow h2 { margin: 0; flex: 1; }

.pb .parts-group h3 .lockbadge {
    background: #4a2530;
    color: #ff9b9b;
    border: 1px solid #6b3341;
    padding: 1px 7px;
    border-radius: 9px;
    font-size: 11px;
    letter-spacing: .02em;
    cursor: help;
}
```

---

<!-- ==== 7/125 : frontend/js/agentCards.js ==== -->

### frontend/js/agentCards.js

```javascript
/* Agent cards module

   Renders one card per available agent on the home page. Each card
   carries the agent's stable color (see agentColors.js) so the same
   agent is recognizable in the chat header. */

import API from './api.js';
import { assignAgentColors } from './agentColors.js';

function openChatWithAgent(agentId) {
  const width = 1100;
  const height = 740;
  const left = Math.max(0, (window.screen.width - width) / 2);
  const top = Math.max(0, (window.screen.height - height) / 2);
  const target = agentId
    ? `/chat?agent=${encodeURIComponent(agentId)}`
    : '/chat';
  window.open(
    target,
    'ProjectManagerChat',
    `width=${width},height=${height},top=${top},left=${left},` +
    'resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no'
  );
}

function buildCard(agent, color) {
  const card = document.createElement('button');
  card.type = 'button';
  card.className = 'agent-card';
  card.dataset.agent = agent.id;
  card.style.setProperty('--agent-color', color);
  card.title = 'Chat with ' + agent.name;

  const head = document.createElement('div');
  head.className = 'agent-card-head';

  const swatch = document.createElement('span');
  swatch.className = 'agent-swatch';

  const name = document.createElement('span');
  name.className = 'agent-card-name';
  name.textContent = agent.name;

  head.append(swatch, name);

  const badges = document.createElement('div');
  badges.className = 'agent-card-badges';

  const sourceBadge = document.createElement('span');
  sourceBadge.className = 'agent-badge source';
  sourceBadge.textContent = agent.source === 'workspace' ? 'workspace' : 'library';
  badges.appendChild(sourceBadge);

  if (agent.mode) {
    const modeBadge = document.createElement('span');
    modeBadge.className = 'agent-badge mode';
    modeBadge.textContent = agent.mode;
    badges.appendChild(modeBadge);
  }

  const description = document.createElement('p');
  description.className = 'agent-card-desc';
  description.textContent = agent.description || 'No description provided.';

  card.append(head, badges, description);
  return card;
}

function initAgentCards(options = {}) {
  const host = options.host || document.getElementById('agentCards');
  if (!host) return Promise.resolve([]);

  const onOpen = options.onOpen || openChatWithAgent;

  return API.agents().then((data) => {
    const agents = data.agents || [];
    host.innerHTML = '';

    if (!agents.length) {
      const empty = document.createElement('p');
      empty.className = 'agent-cards-empty';
      empty.textContent = 'No agents found. Create one from the editor to get started.';
      host.appendChild(empty);
      return agents;
    }

    const colors = assignAgentColors(agents);
    for (const agent of agents) {
      const card = buildCard(agent, colors.get(agent.id));
      card.addEventListener('click', () => onOpen(agent.id));
      host.appendChild(card);
    }
    return agents;
  });
}

export { initAgentCards, openChatWithAgent };
```

---

<!-- ==== 8/125 : frontend/js/agentColors.js ==== -->

### frontend/js/agentColors.js

```javascript
/* Stable per-agent color module

   An agent must show the same color everywhere it appears (home
   card, chat header chip), with nothing persisted between pages.
   Colors are therefore derived from the agent id itself via a
   stable hash, so both pages agree without coordinating.

   The palette is hand-picked to stay legible on both dark themes
   in use: the home page (#1e1e1e) and chat (#131822). */

const AGENT_PALETTE = [
  '#4fc3f7', // sky
  '#81c784', // green
  '#ffb74d', // amber
  '#ba68c8', // violet
  '#f06292', // rose
  '#4dd0e1', // cyan
  '#aed581', // lime
  '#ff8a65', // coral
  '#9575cd', // indigo
  '#ffd54f', // yellow
  '#4db6ac', // teal
  '#e57373'  // red
];

/* FNV-1a: cheap, stable across page loads, and well spread for
   short ids like "rag_assistant". */
function hashId(id) {
  let hash = 0x811c9dc5;
  const text = String(id == null ? '' : id);
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}

function agentColor(id) {
  return AGENT_PALETTE[hashId(id) % AGENT_PALETTE.length];
}

/* Hash collisions give two agents the same color. Nudging later
   agents to the next free slot keeps every visible card distinct.
   The result stays deterministic for a given list order, so the
   home page and the chat page always agree.

   Once every slot is taken the search gives up and reuses the
   hashed color, so a list longer than the palette degrades to
   shared colors instead of spinning forever. */
function assignAgentColors(agents) {
  const list = Array.isArray(agents) ? agents : [];
  const taken = new Set();
  const colors = new Map();
  for (const agent of list) {
    const id = agent && agent.id;
    if (id == null || colors.has(id)) continue;
    const start = hashId(id) % AGENT_PALETTE.length;
    let slot = start;
    for (let step = 0; step < AGENT_PALETTE.length; step += 1) {
      if (!taken.has(slot)) break;
      slot = (slot + 1) % AGENT_PALETTE.length;
    }
    taken.add(slot);
    colors.set(id, AGENT_PALETTE[slot]);
  }
  return colors;
}

export { AGENT_PALETTE, agentColor, assignAgentColors };
```

---

<!-- ==== 9/125 : frontend/js/agents.js ==== -->

### frontend/js/agents.js

```javascript
/* Agent creation and current workspace-agent selection for the editor. */
import API from './api.js';

const state = {
  jsonPath: null,   // run-agent target (workspace-relative)
  mdPath: null,
  ctx: null
};

const $ = (id) => document.getElementById(id);

export function initAgentsPanel(ctx) {
  state.ctx = ctx;

  // + Agent scaffold
  $('agentCreateBtn')?.addEventListener('click', scaffoldAgent);

  // Single-agent runs happen on the dashboard; the open definition is
  // saved first and passed as a selection hint when available.
  $('runAgentBtn')?.addEventListener('click', async () => {
    if (state.jsonPath && state.ctx?.isDirty()) await state.ctx.saveFile();
    const agentId = state.jsonPath
      ? state.jsonPath.split('/')[1]
      : null;
    window.location.href = agentId
      ? `/?agent=${encodeURIComponent(agentId)}`
      : '/';
  });

  $('pipelineBtn')?.addEventListener('click', () => {
    window.location.href = '/?panel=orchestrator';
  });

  updateRunTarget();
}

/* ------------------------------------------------------------
   Current agent selection for the dashboard runner
   ------------------------------------------------------------ */
function updateRunTarget() {
  const cf = state.ctx ? state.ctx.getCurrentFile() : null;
  if (!cf) {
    state.jsonPath = state.mdPath = null;
    return;
  }
  const m = /^workspace\/agents\/([^/]+)\/(agent\.json|agent\.md)$/.exec(cf);
  if (m) {
    /* The agent-run API takes workspace-relative paths, so these
       stay unprefixed even though the open file is root-qualified. */
    state.jsonPath = `agents/${m[1]}/agent.json`;
    state.mdPath = `agents/${m[1]}/agent.md`;
  } else {
    state.jsonPath = state.mdPath = null;
  }
}

/* ------------------------------------------------------------
   Scaffold a new workspace agent
   ------------------------------------------------------------ */
async function scaffoldAgent() {
  const name = prompt('Agent id / folder name (e.g. "doc_writer"):');
  if (!name) return;
  if (!/^[A-Za-z0-9_\-]+$/.test(name)) {
    alert('Use only letters, numbers, underscore or dash.');
    return;
  }
  /* The tree/editor use root-qualified paths; the agent-run API
     uses workspace-relative ones. */
  const rel = `agents/${name}`;
  const full = `workspace/${rel}`;
  const json = JSON.stringify({
    id: name,
    name: name.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    description: 'A custom agent scaffolded from the editor.',
    mode: 'agent',
    model: '',
    tools: ['map_files', 'read_file', 'write_text_file']
  }, null, 2);
  const md =
    `# ${name}\n` +
    `\n## role\n` +
    `\nYou are ${name}, a helpful Project Manager agent.\n` +
    `\n## purpose\n` +
    `\nDescribe what this agent accomplishes and when it is used.\n` +
    `\n## boundaries\n` +
    `\nState what this agent will not do.\n` +
    `\n## output format\n` +
    `\nDescribe the shape of the reply the agent must produce.\n`;
  try {
    await API.fileCreate(`${full}/agent.json`, json);
    await API.fileCreate(`${full}/agent.md`, md);
    if (state.ctx) {
      await state.ctx.refreshTree();
      await state.ctx.openFile(`${full}/agent.json`);
    }
  } catch (e) {
    alert('Failed to scaffold agent: ' + e.message);
  }
}

export { updateRunTarget };
```

---

<!-- ==== 10/125 : frontend/js/api.js ==== -->

### frontend/js/api.js

```javascript
/* Project Manager API client module */
const API = {
  async request(method, url, body = null) {
    const options = { method };
    if (body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }
    const res = await fetch(url, options);
    if (!res.ok) {
      let detail = '';
      try {
        const err = await res.json();
        detail = err.detail || '';
      } catch (e) {
        detail = '';
      }
      const error = new Error(detail || `Request failed: ${res.status}`);
      /* The status rides along on the error so a caller can tell
         "not there yet" (404) from "refused" (403/500) without having
         to match on the message text. */
      error.status = res.status;
      throw error;
    }
    if (res.status === 204 || !res.headers.get('content-type')?.includes('application/json')) {
      return {};
    }
    return res.json();
  },

  health() {
    return this.request('GET', '/api/health');
  },

  /* ---- Scope handling ----
     A null scope selects the browser view, where paths may carry
     a browser-root prefix (workspace/..., source_files/...). An
     explicit 'workspace' or 'app' keeps the legacy single-root
     view. Omitting the parameter entirely is what makes the API
     return the browser tree. */

  withPath(path, scope) {
    const params = new URLSearchParams({ path });
    if (scope) params.set('scope', scope);
    return params.toString();
  },

  withScope(body, scope) {
    if (!scope) return body;
    return { ...body, scope };
  },

  /* ``roots`` is a list of browser-root names the caller wants shown.
     Omitted (the default) means all of them, so every existing caller
     keeps the full tree. */
  project(scope = null, roots = null) {
    const params = new URLSearchParams();
    if (scope) params.set('scope', scope);
    if (roots && roots.length) params.set('roots', roots.join(','));
    const query = params.toString();
    return this.request('GET', '/api/project' + (query ? `?${query}` : ''));
  },

  fileRead(path, scope = null) {
    return this.request('GET', `/api/file/read?${this.withPath(path, scope)}`);
  },

  fileWrite(path, content, scope = null) {
    return this.request('PUT', '/api/file/write', this.withScope({ path, content }, scope));
  },

  fileCreate(path, content = '', scope = null) {
    return this.request('POST', '/api/file/create', this.withScope({ path, content }, scope));
  },

  fileDelete(path, scope = null) {
    return this.request('DELETE', `/api/file/delete?${this.withPath(path, scope)}`);
  },

  directoryCreate(path, scope = null) {
    return this.request('POST', `/api/directory/create?${this.withPath(path, scope)}`);
  },

  directoryDelete(path, scope = null) {
    return this.request('DELETE', `/api/directory/delete?${this.withPath(path, scope)}`);
  },

  pathRename(oldPath, newPath, scope = null) {
    return this.request('PUT', '/api/path/rename', this.withScope({ old_path: oldPath, new_path: newPath }, scope));
  },

  chatSend(message, agent_id = null, model = null, history = []) {
    return this.request('POST', '/api/chat', { message, agent_id, model, history });
  },

  /* ---- Saved chat sessions ----
     A session is the persisted text file for one agent's thread. Sessions are
     per agent, so the agent is sent with every call. */

  chatSessions(agent = null) {
    const query = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return this.request('GET', `/api/chat/sessions${query}`);
  },

  chatSessionSave(agent, title, entries) {
    return this.request('POST', '/api/chat/sessions', { agent_id: agent, title, entries });
  },

  chatSession(id, agent = null) {
    const query = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return this.request('GET', `/api/chat/sessions/${encodeURIComponent(id)}${query}`);
  },

  chatSessionDelete(id, agent = null) {
    const query = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return this.request('DELETE', `/api/chat/sessions/${encodeURIComponent(id)}${query}`);
  },

  /* Built as a URL rather than fetched: the endpoint answers with a
     Content-Disposition attachment, and a plain link hands the file
     to the browser's download handling (i.e. the user's disk). */
  chatSessionExportUrl(id, agent = null, format = 'txt') {
    const params = new URLSearchParams({ format });
    if (agent) params.set('agent', agent);
    return `/api/chat/sessions/${encodeURIComponent(id)}/export?${params.toString()}`;
  },

  sessions() {
    return this.request('GET', '/api/sessions');
  },

  /* ---- Agent engine ---- */

  agents() {
    return this.request('GET', '/api/agents');
  },

  agentDefinition(id) {
    return this.request('GET', `/api/agents/${encodeURIComponent(id)}`);
  },

  agentRun(body) {
    return this.request('POST', '/api/agents/run', body);
  },

  pipelineOptions() {
    return this.request('GET', '/api/pipeline');
  },

  pipelineRun(body) {
    return this.request('POST', '/api/pipeline', body);
  },

  models() {
    return this.request('GET', '/api/models');
  },

  /* The tool IDs agent.json's "tools" may name, with their registered
     descriptions. The engine registry is the single source of truth. */
  tools() {
    return this.request('GET', '/api/tools');
  }
};

export default API;
```

---

<!-- ==== 11/125 : frontend/js/builder.js ==== -->

### frontend/js/builder.js

```javascript
﻿
/* ============================================================
   Agent Prompt Builder
   ============================================================

   Moved out of Agentpromptbuilder.html so two hosts can run it: the
   standalone /prompt-builder page, and the right-hand panel on /test.
   The behaviour is the one the page always had - nothing below was
   rewritten for the move. What changed is the seam:

     - the four cards live here as MARKUP rather than in the page, so
       they are defined once instead of twice;
     - mount(host) replaces the init() that ran at parse, so importing
       this module has no side effects and the host decides when to
       start;
     - styles are builder.css, scoped under .pb.

   $() stays document.getElementById. That is only safe because the 26
   ids in MARKUP are unique against every host page's own ids; one
   builder instance per document. A second mount would share this
   module's state (categories, textCache, selection), so it is not
   supported. */

import API from '/static/js/api.js';

// ============================================================
// MARKUP
// ============================================================

const MARKUP = `
<div class="pb-cards">

  <div class="card">
    <h2>Parts Folder</h2>
    <div class="folderbar">
      <span>Parts:</span>
      <code id="parts_folder_label">…</code>
      <button id="refresh_parts_btn" class="secondary tiny" type="button" disabled title="Re-read the parts folder. Also clears any folder marked as locked after a failed write.">Refresh Parts</button>
    </div>
    <div id="storage_status" class="status">Connecting to the Project Manager…</div>
  </div>

  <div class="card">
    <h2 id="form_title">Create Prompt Part</h2>

    <label>Category</label>
    <div class="catrow">
      <select id="part_category"></select>
      <button id="new_category_btn" class="secondary tiny" type="button" disabled title="Add a category of your own. It becomes a new folder under prompt_parts.">+ Category</button>
      <button id="delete_category_btn" class="secondary tiny danger" type="button" disabled title="Delete the selected category and every part inside it.">Delete</button>
    </div>

    <div class="catrow" id="new_category_row" hidden>
      <input id="new_category_name" placeholder="new category name (e.g. memory)" maxlength="40" autocomplete="off">
      <button id="create_category_btn" class="secondary tiny" type="button" disabled>Create</button>
    </div>
    <div class="microlabel">the category list is stored in <code id="categories_file_label">categories.json</code> and is read on every refresh</div>

    <label>Name</label>
    <input id="part_name" placeholder="e.g. planner">

    <label>Text</label>
    <textarea id="part_text" placeholder="You are a planning agent..."></textarea>

    <div class="row">
      <button id="save_part_btn" type="button" disabled>Save Part</button>
      <button id="clear_form_btn" class="secondary" type="button" disabled>Clear</button>
    </div>

    <div id="part_status" class="status">Waiting for the Project Manager…</div>
  </div>

  <div class="card">
    <div class="headrow">
      <h2>Available Parts</h2>
      <button id="new_part_btn" class="secondary tiny" type="button" disabled>+ New Part</button>
    </div>
    <div id="parts_list"><div class="empty">Loading parts…</div></div>

    <div class="row">
      <button id="create_master_btn" type="button" disabled>Create Master Prompt</button>
    </div>
  </div>

  <div class="card">
    <h2>Available Agent Tools</h2>
    <p class="microlabel">Tools are attached to the agent when its prompt names them. Add a tool to include its ID and description in the Tools section.</p>
    <div id="tools_status" class="status">Loading available tools…</div>
    <div id="tools_list" class="tool-list"><div class="empty">Loading tools…</div></div>
  </div>

  <div class="card">
    <h2>Master Prompt</h2>

    <label>Agent ID (folder name for saving)</label>
    <input id="agent_id" value="new_agent">

    <label>Markdown (editable before saving)</label>
    <textarea id="master_prompt" placeholder="Select parts and click 'Create Master Prompt'."></textarea>

    <div class="row">
      <button id="save_agent_btn" type="button" disabled>Save draft</button>
      <button id="publish_btn" type="button" disabled>Publish for testing</button>
      <button id="show_evidence_btn" class="secondary" type="button" disabled title="Select this agent on the dashboard and show its last run.">Show evidence</button>
    </div>

    <div id="master_status" class="status">Ready.</div>
  </div>

</div>`;

// ============================================================
// CONFIG - the storage locations are fixed, not user-selected.
// ============================================================

/* Every path is browser-root-qualified (workspace/..., test_environment/...),
   which is what the file API resolves back to a root. The prompt parts and the
   published test agents live in the isolated test environment, and the
   workspace root is the only other writable one, so the builder can only ever
   write inside those two - it can no longer be pointed at an arbitrary folder
   on the user's disk. */

const DOC_ROOT = 'test_environment/PromptBuilderFiles';
const PARTS_DIR = DOC_ROOT + '/prompt_parts';
const DOC_OUTPUT_DIR = DOC_ROOT + '/output/agents';
const AGENTS_DIR = 'test_environment/test_agents';

/* The category list is data, not code. It lives in this file next to the
   parts folders so it can be added to and subtracted from in the browser
   - and hand-edited - without touching this script. Array order is the
   order the dropdown, the parts list and the master prompt sections use,
   so there is no separate sort key to keep in sync. It sits outside
   prompt_parts/ so that folder holds nothing but category folders. */
const CATEGORIES_FILE = DOC_ROOT + '/categories.json';
const CATEGORIES_VERSION = 1;

const PART_FILE = '.txt';

/* The starting catalogue, written on the first run only. It is also the
   title lookup: a category typed as "hallucinations" gets the readable
   title from here rather than the id with a capital letter. */
const SEED_CATEGORIES = [
  { id: "role", title: "Role" },
  { id: "rules", title: "Rules" },
  { id: "hallucinations", title: "Hallucination Rules" },
  { id: "tools", title: "Tools" },
  { id: "skills", title: "Skills" },
  { id: "input", title: "Input" },
  { id: "reasoning", title: "Reasoning" },
  { id: "logic", title: "Logic" }
];

// ============================================================
// STATE
// ============================================================

let categories = [];           // [{id, title}] from the manifest, in order
let partIndex = {};            // {category: [{name, path}]}
let textCache = new Map();     // part path -> text
let selected = new Set();      // "category/name" keys that are checked
let lockedCategories = new Set(); // categories that refused a write
let editingCategory = null;    // category the part open in the form belongs to
let workspaceRoot = "";        // absolute, from /api/health
let projectRoot = "";          // the parent of workspaceRoot
let ready = false;             // the parts folder answered at least once
let assembled = null;          // selection signature of the last build
let knownToolIds = [];         // tool IDs the engine can attach (GET /api/tools)
let knownTools = [];

/* Every button the panel and the form can reach, so their disabled
   state is always derived from one place. */
const BUTTONS = ["save_part_btn","clear_form_btn","create_master_btn",
                  "save_agent_btn","publish_btn","refresh_parts_btn",
                  "new_part_btn","new_category_btn","create_category_btn",
                  "delete_category_btn","show_evidence_btn"];

/* Buttons that additionally need something published in this session,
   not just a live parts folder. "Show evidence" is the one that took
   the old test_btn's gate: it only has a verdict to point at once
   there is an agent for the dashboard to have tested. */
const PUBLISH_GATED = new Set(["show_evidence_btn"]);

let busy = false;

/* Document-wide on purpose. The ids are unique per document, so this is
   the same lookup the page always did and it costs nothing to keep -
   it also means MARKUP can be injected into a panel without rewriting
   every call site to take a root. */
function $(id){ return document.getElementById(id); }

function setStatus(id, message, kind){
  const el = $(id);
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

/* One place decides every button's state, because three different
   things can disable one: the parts folder is unreachable, an operation
   is in flight, or there is nothing published to test. Deriving it in
   one pass is what keeps a later setReady() from quietly re-enabling a
   button whose own condition is gone. */
function syncButtons(){
  for (const id of BUTTONS){
    const gated = PUBLISH_GATED.has(id) && !publishedAgentId;
    $(id).disabled = busy || !ready || gated;
  }
}

function setReady(value){
  ready = value;
  syncButtons();
}

/* Buttons stay disabled for the duration of an operation so a double
   click cannot fire two writes at the same file. */
function setBusy(value){
  busy = value;
  syncButtons();
}

function partKey(category, name){ return category + "/" + name; }

function categoryPath(id){
  return PARTS_DIR + "/" + id;
}

function partPath(category, name){
  return categoryPath(category) + "/" + name + PART_FILE;
}

function relativePath(path){
  return path.startsWith(DOC_ROOT + "/")
    ? path.slice(DOC_ROOT.length + 1)
    : path;
}

function safeSlug(value){
  value = (value || "").trim().toLowerCase();
  value = value.replace(/[^a-z0-9_-]+/g, "_");
  value = value.replace(/_+/g, "_").replace(/^_|_$/g, "");
  if (!value) throw new Error("Name cannot be empty.");
  return value;
}

/* A category added in the browser has no entry in the seed, so its id is
   the title unless it is one of the seeded ones. */
function titleFor(id){
  const seeded = SEED_CATEGORIES.find(cat => cat.id === id);
  if (seeded) return seeded.title;
  return id.replace(/[_-]+/g, " ")
           .replace(/\b\w/g, c => c.toUpperCase());
}

/* agent.json needs a human label; derive one from the id rather than
   adding a field the builder would then have to keep in sync. */
function displayName(id){
  return id.replace(/[_-]+/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ============================================================
// AGENT METADATA - agent.md is written, agent.json is derived from it
// ============================================================

/* Both save paths write both files, so agent.json can no longer sit as a
   stub that only knows the id and name. Its structured fields come from
   the markdown the user actually edited, instead of being typed twice:

     tools       <- registry IDs written in backticks in the markdown
     mode        <- "agent" when the markdown names a tool, else "chat"
     description <- the first line of '## Role' (falling back to '## Purpose')
     model       <- blank; ask_llm resolves it from config/models.json

   The write is a full overwrite on purpose: the markdown is the single
   source, so a stale key - or a hand-edit - cannot survive to disagree
   with it. */

function parseToolIds(markdown){
  const found = [];
  const seen = new Set();
  const pattern = /`([A-Za-z_][A-Za-z0-9_]*)`/g;
  let match;
  while ((match = pattern.exec(markdown))){
    const id = match[1];
    if (knownToolIds.includes(id) && !seen.has(id)){
      seen.add(id);
      found.push(id);
    }
  }
  return found;
}

function renderTools(){
  const host = $("tools_list");
  host.replaceChildren();
  if (!knownTools.length){
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No tools are registered.";
    host.appendChild(empty);
    return;
  }

  for (const tool of knownTools){
    const row = document.createElement("div");
    row.className = "tool-row";
    const info = document.createElement("div");
    info.className = "tool-info";
    const name = document.createElement("code");
    name.textContent = tool.id;
    const description = document.createElement("p");
    description.textContent = tool.description || "No description provided.";
    const add = document.createElement("button");
    add.type = "button";
    add.className = "secondary tiny";
    add.dataset.addTool = tool.id;
    add.textContent = "Add to prompt";
    info.append(name, description);
    row.append(info, add);
    host.appendChild(row);
  }
}

function addToolToPrompt(toolId){
  const tool = knownTools.find(item => item.id === toolId);
  if (!tool) return;

  const prompt = $("master_prompt");
  const markdown = prompt.value;
  const section = /^##\s+tools\s*$/im.exec(markdown);
  const entry = `- \`${tool.id}\`: ${tool.description || "No description provided."}`;

  if (!section){
    prompt.value = markdown.trimEnd()
      + (markdown.trim() ? "\n\n" : "")
      + "## Tools\n\n" + entry + "\n";
  } else {
    const sectionStart = section.index + section[0].length;
    const nextHeading = /^##\s+/m.exec(markdown.slice(sectionStart));
    const sectionEnd = nextHeading
      ? sectionStart + nextHeading.index
      : markdown.length;
    const toolsSection = markdown.slice(sectionStart, sectionEnd);
    if (new RegExp("`" + tool.id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "`").test(toolsSection)){
      setStatus("master_status", `The \`${tool.id}\` tool is already in the Tools section.`, "warn");
      return;
    }
    const before = markdown.slice(0, sectionEnd).replace(/\s*$/, "");
    const after = markdown.slice(sectionEnd);
    prompt.value = before + "\n" + entry + "\n\n" + after.replace(/^\s*/, "");
  }

  prompt.focus();
  prompt.dispatchEvent(new Event("input", { bubbles: true }));
  setStatus("master_status", `Added \`${tool.id}\` to the Tools section.`, "ok");
}

/* Split '## heading' sections the same way the engine does
   (engine/agents/loader.py::_parse_sections), so the builder and the
   engine agree on what a section is. */
function markdownSections(markdown){
  const sections = {};
  let current = null;
  let buffer = [];
  for (const line of markdown.split("\n")){
    const heading = /^\s*##\s+(.+?)\s*$/.exec(line);
    if (heading){
      if (current !== null) sections[current] = buffer.join("\n");
      current = heading[1].trim().toLowerCase();
      buffer = [];
    } else if (current !== null){
      buffer.push(line);
    }
  }
  if (current !== null) sections[current] = buffer.join("\n");
  return sections;
}

function deriveDescription(markdown){
  const sections = markdownSections(markdown);
  for (const name of ["role", "purpose"]){
    const body = sections[name];
    if (!body) continue;
    const line = body.split("\n").map(text => text.trim())
      .find(text => text.length);
    if (line) return line.replace(/[`*_>#]+/g, "").replace(/\s+/g, " ").trim();
  }
  return "";
}

function buildAgentMeta(id, markdown){
  const tools = parseToolIds(markdown);
  return {
    id,
    name: displayName(id),
    description: deriveDescription(markdown),
    mode: tools.length ? "agent" : "chat",
    model: "",
    tools
  };
}

/* One line for the status box: what the derived agent.json actually says,
   so a user sees the tools being picked up (or not) without opening it. */
function describeMeta(meta){
  const tools = meta.tools.length ? meta.tools.join(", ") : "none";
  return "mode: " + meta.mode + " · tools: " + tools;
}

/* The tools an agent.json may name. Learned once, like the workspace
   root, so parseToolIds can tell a real tool from ordinary backticked text
   elsewhere in the markdown. */
function learnToolIds(){
  if (typeof API.tools !== "function") return Promise.resolve();
  return API.tools().then((data) => {
    knownToolIds = (data && data.tools) || [];
    knownTools = (data && data.details) || knownToolIds.map(id => ({
      id,
      description: "",
    }));
    renderTools();
    $("tools_status").textContent = `Loaded ${knownTools.length} registered tool(s).`;
    $("tools_status").className = "status ok";
  });
}

/* One writer for both buttons: the markdown and the metadata derived from
   it land together, so they cannot drift apart. PUT creates missing
   parents and overwrites, so a re-save always takes effect. */
async function writeAgentFiles(dir, id, markdown){
  const meta = buildAgentMeta(id, markdown);
  await API.fileWrite(dir + "/agent.md", markdown + "\n");
  await API.fileWrite(dir + "/agent.json", JSON.stringify(meta, null, 2) + "\n");
  return meta;
}

// ============================================================
// ERRORS - a raw Python errno is not an explanation
// ============================================================

/* The API reports the absolute server path, so a failure shows a path the
   user cannot click or recognize. Both roots are
   learned once so the same failure can be shown relative. Best effort:
   if the lookup fails the original text is still shown. */
function learnWorkspaceRoot(){
  if (typeof API.health !== "function") return Promise.resolve();
  return API.health()
    .then((data) => {
      workspaceRoot = (data && data.root) || "";
      projectRoot = workspaceRoot
        ? workspaceRoot.replace(/[\\/][^\\/]+[\\/]?$/, "")
        : "";
    })
    .catch(() => {
      workspaceRoot = "";
      projectRoot = "";
    });
}

function isPermissionError(error){
  const message = (error && error.message) || String(error);
  return /permission denied|access is denied|errno 13|winerror 5/i
    .test(message);
}

/* Python quotes the offending path: "... denied: 'C:\\...'". */
function extractFailedPath(message){
  const quoted = String(message).match(/'([^']+)'/);
  return quoted ? quoted[1] : "";
}

function shortenPath(value){
  let out = String(value || "");
  for (const root of [workspaceRoot, projectRoot]){
    if (!root) continue;
    out = out.split(root).join("");
  }
  return out.replace(/^[\\/]+/, "").replace(/\\/g, "/");
}

/* The remedy is the same for every refused write on the same volume, so
   it is named from the drive rather than hard-coded. Pass lowercase to
   embed it inside a sentence. */
function repairHint(lowercase){
  const drive = projectRoot.match(/^([A-Za-z]:)/);
  const target = drive ? drive[1] : "the drive";
  const text = "Repair the drive in an Administrator prompt: chkdsk "
    + target + " /f";
  return lowercase
    ? text.charAt(0).toLowerCase() + text.slice(1)
    : text;
}

function firstUnlockedCategory(){
  const free = categories.find(cat => !lockedCategories.has(cat.id));
  return free ? free.id : null;
}

/* A locked category is disabled in the dropdown rather than hidden, so
   it stays visible that it exists and is why it cannot be used. */
function syncCategoryDropdown(){
  const sel = $("part_category");
  if (!sel) return;
  for (const opt of sel.options){
    opt.disabled = lockedCategories.has(opt.value);
  }
  if (lockedCategories.has(sel.value)){
    const free = firstUnlockedCategory();
    if (free) sel.value = free;
  }
}

function markCategoryLocked(category){
  if (!category) return;
  lockedCategories.add(category);
  syncCategoryDropdown();
  renderParts();
}

/* Turns a thrown error into a sentence the user can act on, and records
   a refused folder so the panel stops offering it. */
function prettyError(error, category){
  const raw = (error && error.message) || String(error);

  if (isPermissionError(error)){
    if (category) markCategoryLocked(category);
    const where = shortenPath(
      extractFailedPath(raw) || "that folder"
    );
    return "Cannot write " + where
      + " - Windows reports \"access denied\". Nothing was saved."
      + " That folder is read-only or damaged: use another category, or "
      + repairHint(true) + ". Then press 'Refresh Parts'.";
  }

  return "Error: " + shortenPath(raw);
}

// ============================================================
// TREE LOOKUP - the /api/project tree is the listing source
// ============================================================

function findNode(items, path){
  for (const item of items || []){
    if (item.path === path) return item;
    if (item.children){
      const hit = findNode(item.children, path);
      if (hit) return hit;
    }
  }
  return null;
}

function childDir(node, name){
  for (const child of (node && node.children) || []){
    if (child.type === "directory" && child.name === name) return child;
  }
  return null;
}

// ============================================================
// FOLDER
// ============================================================

/* Only the parts root is created up front. Category folders appear on
   demand: every file write creates its parent directories, so seeding
   eight empty folders would just be eight pointless API calls - and a
   category with no parts does not need a folder to exist. */
async function ensureStructure(){
  await API.directoryCreate(PARTS_DIR);
  $("parts_folder_label").textContent = relativePath(PARTS_DIR);
  $("categories_file_label").textContent = relativePath(CATEGORIES_FILE);
}

// ============================================================
// CATEGORIES - the manifest is the list
// ============================================================

/* One entry per category, in the order everything else uses. A bad entry
   is dropped and a repeated id keeps its first position, because the
   manifest is a plain text file a person is allowed to edit. */
function normalizeCategories(raw){
  const list = Array.isArray(raw && raw.categories) ? raw.categories : [];
  const seen = new Set();
  const out = [];
  for (const item of list){
    if (!item || typeof item.id !== "string") continue;
    const id = item.id.trim().toLowerCase();
    if (!id || seen.has(id)) continue;
    const title = (typeof item.title === "string" && item.title.trim())
      || titleFor(id);
    seen.add(id);
    out.push({ id, title });
  }
  return out;
}

function manifestText(list){
  return JSON.stringify(
    { version: CATEGORIES_VERSION, categories: list }, null, 2
  ) + "\n";
}

/* Absent means "never set up", so the seed catalogue is written. Present
   but unreadable is an error and is never overwritten: a hand-edit with
   a typo in it has to survive until it is fixed. */
async function readCategories(){
  let text = null;

  try {
    text = (await API.fileRead(CATEGORIES_FILE)).content;
  } catch (error) {
    if (error.status !== 404) throw error;
  }

  if (text === null){
    const seeded = normalizeCategories({ categories: SEED_CATEGORIES });
    await API.fileWrite(CATEGORIES_FILE, manifestText(seeded));
    return seeded;
  }

  try {
    return normalizeCategories(JSON.parse(text));
  } catch (error) {
    throw new Error(relativePath(CATEGORIES_FILE)
      + " is not valid JSON (" + error.message + ")."
      + " Fix it in the editor - it has not been changed.");
  }
}

/* Every change goes through here, and the in-memory list is rebuilt from
   the same normalizer the file is written from, so what the page shows
   is always exactly what is on disk. */
async function writeCategories(list){
  const payload = normalizeCategories({ categories: list });
  await API.fileWrite(CATEGORIES_FILE, manifestText(payload));
  categories = payload;
  return payload;
}

// ============================================================
// PARTS
// ============================================================

function populateCategoryDropdown(){
  const sel = $("part_category");
  const previous = sel.value;
  sel.innerHTML = "";

  /* With every category deleted there is nothing to save a part into, and
     a blank dropdown would read as a bug rather than as that state. */
  if (!categories.length){
    const none = document.createElement("option");
    none.value = "";
    none.textContent = "(no categories - create one)";
    sel.appendChild(none);
  }

  for (const cat of categories){
    const opt = document.createElement("option");
    opt.value = cat.id;
    opt.textContent = cat.title;
    sel.appendChild(opt);
  }

  /* A category that was just deleted is no longer an option, so the old
     value would quietly become the first one instead. */
  if (categories.some(cat => cat.id === previous)){
    sel.value = previous;
  }

  syncCategoryDropdown();
}

async function readPart(path){
  if (textCache.has(path)) return textCache.get(path);
  const data = await API.fileRead(path);
  const text = data.content || "";
  textCache.set(path, text);
  return text;
}

/* Selection is state, not DOM: the list is rebuilt from the tree on
   every refresh, so checked boxes are re-applied from `selected`
   instead of being inherited from the markup that just got replaced. */
async function refreshParts(){
  const data = await API.project();
  const partsNode = findNode(data.filesystem, PARTS_DIR);

  partIndex = {};
  for (const cat of categories){
    const catNode = childDir(partsNode, cat.id);
    const entries = [];
    for (const child of (catNode && catNode.children) || []){
      if (child.type !== "file") continue;
      if (!child.name.endsWith(PART_FILE)) continue;
      entries.push({ name: child.name.slice(0, -PART_FILE.length), path: child.path });
    }
    entries.sort((a, b) => a.name.localeCompare(b.name));
    partIndex[cat.id] = entries;
  }

  /* Drop selections whose part no longer exists, so a later build can
     never reference a file that was deleted or renamed. A category that
     was removed takes its checked parts with it. */
  const live = new Set();
  for (const cat of categories){
    for (const entry of partIndex[cat.id]) live.add(partKey(cat.id, entry.name));
  }
  const dropped = [];
  for (const key of Array.from(selected)){
    if (!live.has(key)){ selected.delete(key); dropped.push(key); }
  }

  renderParts();
  return { total: live.size, dropped };
}

function isChecked(category, name){
  return selected.has(partKey(category, name));
}

function setChecked(category, name, value){
  const key = partKey(category, name);
  if (value) selected.add(key); else selected.delete(key);
}

function markAssembledStale(){
  if (assembled === null) return;
  if (assembled === selectionSignature()) return;
  setStatus("master_status",
    "The selected parts changed. Click 'Create Master Prompt' to rebuild before saving.", "warn");
}

function selectionSignature(){
  return Array.from(selected).sort().join("|");
}

function renderParts(){
  const box = $("parts_list");
  box.innerHTML = "";

  let total = 0;

  for (const cat of categories){
    const id = cat.id;
    const entries = partIndex[id] || [];
    const locked = lockedCategories.has(id);
    total += entries.length;

    const group = document.createElement("div");
    group.className = "parts-group";

    const heading = document.createElement("h3");
    heading.appendChild(document.createTextNode(cat.title));
    heading.title = relativePath(categoryPath(id));

    const count = document.createElement("span");
    count.className = "count";
    count.textContent = "(" + entries.length + ")";
    heading.appendChild(count);

    /* The category is listed but cannot be used, so the panel says so
       instead of showing an empty list as if nothing had ever been
       written there. */
    if (locked){
      const badge = document.createElement("span");
      badge.className = "lockbadge";
      badge.textContent = "locked";
      badge.title = "This folder refused a write, so its parts cannot be"
        + " listed or saved. " + repairHint() + ", then press 'Refresh Parts'.";
      heading.appendChild(badge);
    }

    if (entries.length){
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "secondary tiny";
      toggle.textContent = "all / none";
      toggle.addEventListener("click", () => toggleCategory(id));
      heading.appendChild(toggle);
    }

    group.appendChild(heading);

    if (entries.length === 0){
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = locked
        ? "Folder is not writable right now."
        : "No parts yet.";
      group.appendChild(empty);
    }

    for (const entry of entries){
      group.appendChild(buildPartRow(id, entry));
    }

    box.appendChild(group);
  }

  if (total === 0){
    const hint = document.createElement("div");
    hint.className = "empty";
    hint.innerHTML =
      "No parts in the folder yet. Use \"+ New Part\" above, or add a"
      + " <code>.txt</code> file to <code>"
      + relativePath(PARTS_DIR) + "/&lt;category&gt;/</code> in the editor."
      + " A new category is a new folder there, so the editor works"
      + " without this page too.";
    box.appendChild(hint);
  }
}

function buildPartRow(category, entry){
  const row = document.createElement("div");
  row.className = "part-row";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.id = "part_" + category + "_" + entry.name;
  checkbox.checked = isChecked(category, entry.name);
  checkbox.addEventListener("change", () => {
    setChecked(category, entry.name, checkbox.checked);
    markAssembledStale();
  });

  const label = document.createElement("label");
  label.className = "name";
  label.htmlFor = checkbox.id;
  label.textContent = entry.name;
  label.title = entry.path;

  const actions = document.createElement("div");
  actions.className = "actions";

  const editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.className = "secondary tiny";
  editBtn.textContent = "Edit";
  editBtn.addEventListener("click", () => editPart(category, entry));

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "secondary tiny";
  deleteBtn.textContent = "Delete";
  deleteBtn.addEventListener("click", () => deletePart(category, entry));

  actions.appendChild(editBtn);
  actions.appendChild(deleteBtn);
  row.appendChild(checkbox);
  row.appendChild(label);
  row.appendChild(actions);
  return row;
}

function toggleCategory(category){
  const entries = partIndex[category] || [];
  const allChecked = entries.length > 0
    && entries.every(entry => isChecked(category, entry.name));
  for (const entry of entries){
    setChecked(category, entry.name, !allChecked);
  }
  renderParts();
  markAssembledStale();
}

/* Clearing the fields and reporting "Ready" are separate: a successful
   save clears the form but must keep its own confirmation visible. */
function clearFormFields(){
  $("part_name").value = "";
  $("part_text").value = "";
  $("form_title").textContent = "Create Prompt Part";
  editingCategory = null;
}

function resetForm(){
  clearFormFields();
  setStatus("part_status", "Ready.");
}

function editPart(category, entry){
  setBusy(true);
  readPart(entry.path)
    .then((text) => {
      $("part_category").value = category;
      $("part_name").value = entry.name;
      $("part_text").value = text.replace(/\s+$/, "");
      $("form_title").textContent = "Edit Prompt Part";
      /* Remembered so deleting this category can say the open part goes
         with it, and so a cleared form is not mistaken for a live edit. */
      editingCategory = category;
      setStatus("part_status",
        "Editing " + relativePath(entry.path) + ". Save Part to update it.", "ok");
      $("part_text").focus();
    })
    .catch(error => setStatus("part_status", prettyError(error, category), "error"))
    .finally(() => setBusy(false));
}

function deletePart(category, entry){
  if (!confirm("Delete " + relativePath(entry.path) + "?")) return;
  setBusy(true);
  API.fileDelete(entry.path)
    .then(() => {
      textCache.delete(entry.path);
      selected.delete(partKey(category, entry.name));
      return refreshParts();
    })
    .then(({ total, dropped }) => {
      setStatus("part_status",
        "Deleted " + relativePath(entry.path) + ". " + total + " part(s) left."
        + droppedNote(dropped), "ok");
      markAssembledStale();
    })
    .catch(error => setStatus("part_status", prettyError(error, category), "error"))
    .finally(() => setBusy(false));
}

function droppedNote(dropped){
  if (!dropped.length) return "";
  return " Cleared " + dropped.length + " stale selection(s): " + dropped.join(", ") + ".";
}

// ============================================================
// CATEGORY ACTIONS
// ============================================================

/* The name field is hidden until it is asked for, so the form keeps one
   category selector instead of two near-identical text boxes. */
function toggleNewCategoryRow(open){
  const row = $("new_category_row");
  const show = open === undefined ? row.hidden : open;
  row.hidden = !show;
  $("new_category_btn").textContent = show ? "Cancel" : "+ Category";
  if (show) $("new_category_name").focus();
  else $("new_category_name").value = "";
}

/* Adding a category is a manifest write and nothing else: the folder is
   still created by the first part saved into it, which is the same
   "on demand" rule every other part follows. */
async function addCategory(){
  let id = "";
  try {
    id = safeSlug($("new_category_name").value);
  } catch (error) {
    setStatus("part_status", "Category " + error.message, "error");
    return;
  }

  if (categories.some(cat => cat.id === id)){
    setStatus("part_status",
      "The category '" + id + "' already exists.", "error");
    return;
  }

  setBusy(true);
  try {
    const title = titleFor(id);
    await writeCategories(categories.concat({ id, title }));
    toggleNewCategoryRow(false);
    populateCategoryDropdown();
    $("part_category").value = id;
    renderParts();
    setStatus("part_status", "Added category " + title + " -> "
      + relativePath(categoryPath(id))
      + ". Its folder appears with the first part saved into it.", "ok");
  } catch (error) {
    setStatus("part_status", prettyError(error), "error");
  } finally {
    setBusy(false);
  }
}

/* Everything the deleted folder was referenced by, so no path is left
   pointing at a folder that is gone. */
function forgetCategory(id){
  const prefix = categoryPath(id) + "/";
  for (const path of Array.from(textCache.keys())){
    if (path.startsWith(prefix)) textCache.delete(path);
  }
  for (const key of Array.from(selected)){
    if (key.startsWith(id + "/")) selected.delete(key);
  }
  lockedCategories.delete(id);
}

async function deleteCategory(){
  const id = $("part_category").value;
  const entry = categories.find(cat => cat.id === id);

  if (!entry){
    setStatus("part_status", "There is no category to delete.", "error");
    return;
  }

  const parts = partIndex[id] || [];
  const editing = editingCategory === id;

  /* One confirm says what is destroyed: the folder, every part in it,
     and an open part that otherwise would look like it survived. */
  let message = "Delete the category " + entry.title + " ("
    + relativePath(categoryPath(id)) + ")?";
  message += parts.length
    ? "\n\nThis permanently deletes " + parts.length + " part(s): "
      + parts.map(part => part.name).join(", ") + "."
    : "\n\nIt holds no parts.";
  if (editing){
    message += "\n\nThe part open in the form is one of them.";
  }
  if (!confirm(message)) return;

  setBusy(true);
  try {
    /* The folder goes first. A refused recursive delete then leaves the
       manifest untouched, so the list still matches the disk and the
       delete can simply be tried again - the other order would hide a
       category whose parts are already gone. A category that never had a
       part saved into it has no folder to remove, and a stale tree must
       not be able to skip a folder that does exist, so the answer to
       "is it there" comes from the delete itself. */
    try {
      await API.directoryDelete(categoryPath(id));
    } catch (error) {
      if (error.status !== 404) throw error;
    }
    forgetCategory(id);
    await writeCategories(categories.filter(cat => cat.id !== id));
    populateCategoryDropdown();

    const { total, dropped } = await refreshParts();
    if (editing) resetForm();
    setStatus("part_status", "Deleted category " + entry.title + ". "
      + total + " part(s) left." + droppedNote(dropped), "ok");
    markAssembledStale();
  } catch (error) {
    setStatus("part_status", prettyError(error, id), "error");
  } finally {
    setBusy(false);
  }
}

/* The create button in the panel header hands off to the form rather
   than duplicating it: two editors for one file is how the two drift
   apart. The category is moved off a locked folder first, because the
   first option is otherwise a folder that may refuse the write. */
function startNewPart(){
  if (!categories.length){
    setStatus("part_status",
      "There are no categories yet - use \"+ Category\" to add one first.", "warn");
    return;
  }
  const sel = $("part_category");
  if (lockedCategories.has(sel.value)){
    const free = firstUnlockedCategory();
    if (free) sel.value = free;
  }
  clearFormFields();
  const title = $("form_title");
  if (title && typeof title.scrollIntoView === "function"){
    title.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  $("part_name").focus();
  setStatus("part_status", "Fill in the form to create a new part.", "");
}

async function savePart(){
  const category = $("part_category").value;

  if (!category){
    setStatus("part_status",
      "There are no categories yet - use \"+ Category\" to add one first.", "error");
    return;
  }

  /* Refused up front: a locked folder already answered, so sending the
     write again would only repeat the same error. */
  if (lockedCategories.has(category)){
    setStatus("part_status",
      "Cannot save into " + titleFor(category) + " - that folder refused an"
      + " earlier write. " + repairHint() + ", then press 'Refresh Parts'.",
      "error");
    return;
  }

  setBusy(true);
  try {
    const name = safeSlug($("part_name").value);
    const text = $("part_text").value.trim();
    if (!text) throw new Error("Part text cannot be empty.");

    const path = partPath(category, name);
    /* fileWrite creates or overwrites, so saving an edited part and
       saving a new one are the same call. */
    await API.fileWrite(path, text + "\n");
    textCache.set(path, text + "\n");

    const { total } = await refreshParts();
    setStatus("part_status", "Saved: " + relativePath(path) + ". " + total + " part(s) total.", "ok");
    clearFormFields();
  } catch (error) {
    setStatus("part_status", prettyError(error, category), "error");
  } finally {
    setBusy(false);
  }
}

// ============================================================
// MASTER PROMPT
// ============================================================

function collectSelections(){
  const selections = {};
  for (const cat of categories){
    const names = (partIndex[cat.id] || [])
      .filter(entry => isChecked(cat.id, entry.name))
      .map(entry => entry.name);
    if (names.length) selections[cat.id] = names;
  }
  return selections;
}

async function buildMasterPrompt(){
  const selections = collectSelections();

  if (!Object.keys(selections).length){
    setStatus("master_status", "No parts are selected.", "warn");
    return;
  }

  setBusy(true);
  const missing = [];
  try {
    const lines = ["# Agent Prompt", ""];

    for (const cat of categories){
      const names = selections[cat.id] || [];
      const texts = [];
      for (const name of names){
        const path = partPath(cat.id, name);
        let text = "";
        try {
          text = (await readPart(path)).trim();
        } catch (error) {
          missing.push(partKey(cat.id, name));
          continue;
        }
        if (text) texts.push(text);
      }
      if (texts.length){
        lines.push("## " + cat.title);
        lines.push("");
        lines.push(texts.join("\n\n"));
        lines.push("");
      }
    }

    $("master_prompt").value = lines.join("\n").trim() + "\n";
    assembled = selectionSignature();

    const count = Object.values(selections).reduce((sum, list) => sum + list.length, 0);
    setStatus("master_status",
      "Assembled " + count + " part(s). Edit the markdown if needed, then save."
      + (missing.length ? " Skipped unreadable: " + missing.join(", ") + "." : ""),
      missing.length ? "warn" : "ok");
  } catch (error) {
    setStatus("master_status", "Error: " + error.message, "error");
  } finally {
    setBusy(false);
  }
}

function requireMarkdown(){
  const markdown = $("master_prompt").value.trim();
  if (!markdown) throw new Error("The master prompt is empty - nothing to save.");
  return markdown;
}

async function saveToDocumentation(){
  setBusy(true);
  try {
    const id = safeSlug($("agent_id").value);
    const markdown = requireMarkdown();
    const dir = DOC_OUTPUT_DIR + "/" + id;
    const meta = await writeAgentFiles(dir, id, markdown);
    setStatus("master_status",
      "Saved: " + relativePath(dir) + "/agent.md + agent.json"
      + ".\n" + describeMeta(meta), "ok");
  } catch (error) {
    setStatus("master_status", prettyError(error), "error");
  } finally {
    setBusy(false);
  }
}

/* "Publish for testing" makes the prompt a real agent inside the isolated
   test environment: the engine only lists folders that hold BOTH agent.json
   and agent.md (engine/agents/registry.py), so both are written here.
   agent.json is rebuilt from the markdown on every publish, so editing the
   master prompt and publishing again is what keeps the two in step.

   Nothing is written to workspace/agents/. A published agent is a test
   fixture: it is not registered as an agent root, so it never appears in
   the live agent picker, and the four header tests drive it by path. */
let publishedAgentId = null;

async function publishForTesting(){
  setBusy(true);
  setPublished(false);
  try {
    const id = safeSlug($("agent_id").value);
    const markdown = requireMarkdown();
    const dir = AGENTS_DIR + "/" + id;

    const meta = await writeAgentFiles(dir, id, markdown);

    setPublished(true);
    setStatus("master_status",
      "Published to the test environment: " + dir + "/agent.md + agent.json"
      + ".\n" + describeMeta(meta) + "\nRun it from the dashboard.", "ok");

    /* The host decides what publishing means for it: on /test this
       re-reads the agent list so the new agent is pickable. Hosts
       without a dashboard ignore it. */
    if (Builder.onPublished) Builder.onPublished(publishedAgentId);

  } catch (error) {
    setStatus("master_status", prettyError(error), "error");
  } finally {
    setBusy(false);
  }
}

/* "Show evidence" is only live for something that has actually been
   published in this session. Reloading the page forgets it, which is
   the honest state: a hand-edited agent.json may no longer match the
   markdown above, and the dashboard is where you find out.

   It hands the host the agent id rather than opening anything itself.
   The builder used to open the dashboard in a window from here; it now
   lives beside it, so one place runs the tests and one place shows the
   verdict, and the two cannot disagree. */
function setPublished(isPublished){
  publishedAgentId = isPublished ? publishedAgentId : safeSlug($("agent_id").value) || null;
  $("show_evidence_btn").title = publishedAgentId
    ? "Show the last run for " + publishedAgentId + " on the dashboard."
    : "Publish for testing first.";
  syncButtons();
}


// ============================================================
// RELOAD
// ============================================================

async function reloadParts(){
  setBusy(true);
  try {
    /* A lock only records that a write was refused, not that the folder
       is still broken, so the explicit refresh drops them and lets a
       repaired folder be used again without reloading the page. */
    lockedCategories.clear();
    syncCategoryDropdown();

    /* Read before the tree: the parts are listed per category, so the
       list has to be known first. A categories.json edited in the
       editor therefore takes effect on 'Refresh Parts'. */
    categories = await readCategories();
    populateCategoryDropdown();

    const { total, dropped } = await refreshParts();
    setStatus("storage_status",
      "Parts folder: " + relativePath(PARTS_DIR) + " - " + total + " part(s)."
      + droppedNote(dropped), "ok");
    setReady(true);
  } catch (error) {
    setReady(false);
    setStatus("storage_status", prettyError(error), "error");
  } finally {
    setBusy(false);
  }
}

// ============================================================
// MOUNT
// ============================================================

/* Was init(), which ran at parse because there was one host. The host
   now decides when the builder starts, which is what lets the same
   module back the standalone page and a panel. */
function mount(host){
  host.innerHTML = MARKUP;

  /* "Show evidence" starts live rather than gated: after a reload the
     publish is forgotten but the agent id is still in the box, and
     pointing the dashboard at it is harmless when there is nothing
     published - the dashboard's picker will simply not offer it. */
  setPublished(false);
  $("save_part_btn").addEventListener("click", savePart);
  $("clear_form_btn").addEventListener("click", resetForm);
  $("new_part_btn").addEventListener("click", startNewPart);
  $("new_category_btn").addEventListener("click", () => toggleNewCategoryRow());
  $("create_category_btn").addEventListener("click", addCategory);
  $("delete_category_btn").addEventListener("click", deleteCategory);
  $("new_category_name").addEventListener("keydown", (event) => {
    if (event.key === "Enter") addCategory();
  });
  $("create_master_btn").addEventListener("click", buildMasterPrompt);
  $("save_agent_btn").addEventListener("click", saveToDocumentation);
  $("publish_btn").addEventListener("click", publishForTesting);
  $("show_evidence_btn").addEventListener("click", () => {
    if (Builder.onShowEvidence) Builder.onShowEvidence(publishedAgentId);
  });
  $("tools_list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-add-tool]");
    if (button) addToolToPrompt(button.dataset.addTool);
  });
  $("refresh_parts_btn").addEventListener("click", reloadParts);

  /* The dropdown is not built here: it is a view of the manifest, and the
     manifest is read by the first reload. Every button is disabled until
     then, so the empty dropdown is never something a user can act on. */
  learnWorkspaceRoot()
    .then(() => learnToolIds())
    .then(() => ensureStructure())
    .then(() => reloadParts())
    .catch(error => {
      setReady(false);
      setStatus("storage_status", prettyError(error), "error");
      setStatus("part_status", "The parts folder is unavailable.", "error");
    });
}

const Builder = {
  mount,

  /* Both are host hooks rather than arguments because they are assigned
     before mount() runs in practice, and a host should not have to
     rebuild the panel to change what publishing does.

     onPublished(agentId)   - called after a successful publish.
     onShowEvidence(agentId) - the "Show evidence" button. Undefined on
     the standalone page, which has no dashboard to show. */
  onPublished: null,
  onShowEvidence: null,
};

export default Builder;
```

---

<!-- ==== 12/125 : frontend/js/chat.js ==== -->

### frontend/js/chat.js

```javascript
/* Chat popup module */
import API from './api.js';
import Session from './session.js';
import { assignAgentColors } from './agentColors.js';
import { initTopbar } from './topbar.js';

const log = document.getElementById('chatLog');
const form = document.getElementById('chatForm');
const input = document.getElementById('chatInput');
const sendBtn = document.getElementById('chatSend');
const status = document.getElementById('chatStatus');
const agentSelect = document.getElementById('agentSelect');
const modelSelect = document.getElementById('modelSelect');
const agentChip = document.getElementById('activeAgentChip');
const agentName = document.getElementById('activeAgentName');
const savedChatsList = document.getElementById('savedChatsList');

/* Agent id requested by the home page card, e.g. /chat?agent=rag_assistant */
const requestedAgent = new URLSearchParams(window.location.search).get('agent');

let agentColorById = new Map();
let currentThread = [];
let activeSessionId = null;
let selectedSkill = null;

const skillSelect = document.getElementById('skillSelect');
const skillNameInput = document.getElementById('skillName');
const skillContentInput = document.getElementById('skillContent');
const saveSkillButton = document.getElementById('saveSkill');

function appendLine(role, text, meta = '', labelText = null) {
  const line = document.createElement('div');
  line.className = 'msg ' + role;
  const label = document.createElement('span');
  label.className = 'msg-label';
  label.textContent = labelText
    || (role === 'user' ? 'You' : role === 'event' ? 'Event' : 'System');
  const body = document.createElement('span');
  body.className = 'msg-body';
  body.textContent = text;
  line.appendChild(label);
  line.appendChild(body);
  if (meta) {
    const ts = document.createElement('span');
    ts.className = 'msg-meta';
    ts.textContent = meta;
    line.appendChild(ts);
  }
  /* Every real message gets a copy button; the handler is the global
     copyMsg() in chat.html, shared with the saved-session rows. */
  const actions = document.createElement('span');
  actions.className = 'msg-actions';
  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'btn-msg-action';
  copyBtn.title = 'Copy this message';
  copyBtn.innerHTML = '<i data-lucide="copy" style="width:13px;"></i> Copy';
  copyBtn.addEventListener('click', () => copyText(body.textContent, 'Message copied to clipboard'));
  actions.appendChild(copyBtn);
  line.appendChild(actions);
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
  if (window.lucide) window.lucide.createIcons();
}

/* Clipboard write with a textarea fallback, because the async
   clipboard API is unavailable on http:// origins. */
function copyText(text, message) {
  const area = document.createElement('textarea');
  area.value = text;
  document.body.appendChild(area);
  area.select();
  try {
    document.execCommand('copy');
    showToast(message);
  } catch (e) {
    showToast('Copy failed - select the text manually');
  } finally {
    document.body.removeChild(area);
  }
}

function appendTools(tools) {
  if (!tools || !tools.length) return;
  const detail = document.createElement('details');
  detail.className = 'msg event';
  const summary = document.createElement('summary');
  summary.className = 'msg-label';
  summary.textContent = 'Tools used: ' + tools.map(t => t.tool || '').filter(Boolean).join(', ');
  detail.appendChild(summary);
  const body = document.createElement('div');
  body.className = 'msg-body';
  body.textContent = tools.map(t => {
    const args = t.args ? JSON.stringify(t.args).slice(0, 400) : '';
    const ok = t.op_ok ? 'ok' : (t.status || '?');
    return `› ${t.tool} (${ok}) ${args}`;
  }).join('\n');
  detail.appendChild(body);
  log.appendChild(detail);
  log.scrollTop = log.scrollHeight;
}

function setStatus(text) {
  if (status) status.textContent = text;
}

// ---- Agent / model selector population ----

function activeAgentId() {
  return agentSelect && agentSelect.value ? agentSelect.value : null;
}

function agentLabel(id) {
  if (!id) return 'No agent selected';
  const opt = agentSelect ? agentSelect.querySelector(`option[value="${CSS.escape(id)}"]`) : null;
  return opt ? opt.textContent : id;
}

function paintAgentChip() {
  const id = activeAgentId();
  if (!agentChip || !agentName) return;
  if (!id) {
    agentChip.hidden = true;
    return;
  }
  const color = agentColorById.get(id) || '#4fc3f7';
  agentChip.style.setProperty('--agent-color', color);
  agentName.textContent = agentLabel(id);
  agentChip.hidden = false;
  if (input) {
    input.placeholder = `Message ${agentLabel(id)}...`;
  }
}

async function populateAgents() {
  try {
    const data = await API.agents();
    const agents = data.agents || [];
    agentColorById = assignAgentColors(agents);
    const savedAgent = localStorage.getItem('pmAgent');
    agentSelect.innerHTML = '';
    for (const a of agents) {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = a.source === 'workspace' ? `${a.name} (ws)` : a.name;
      if (a.id === savedAgent) opt.selected = true;
      agentSelect.appendChild(opt);
    }
    /* An explicit ?agent= from a home card outranks the saved choice. */
    const preferred = agents.some(a => a.id === requestedAgent) ? requestedAgent : savedAgent;
    if (preferred) agentSelect.value = preferred;
    if (!agentSelect.value && agents.length) agentSelect.value = agents[0].id;
    if (agentSelect.value) localStorage.setItem('pmAgent', agentSelect.value);
    paintAgentChip();
  } catch (e) {
    console.warn('Failed to load agents', e);
  }
}

async function populateModels() {
  try {
    const data = await API.models();
    const models = data.models || [];
    const savedModel = localStorage.getItem('pmModel') || '';
    modelSelect.innerHTML = '';
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = 'default model';
    modelSelect.appendChild(empty);
    for (const m of models) {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      modelSelect.appendChild(opt);
    }
    if (savedModel) modelSelect.value = savedModel;
  } catch (e) {
    console.warn('Failed to load models', e);
  }
}

async function populateSelectors() {
  await populateAgents();
  await populateModels();

  agentSelect.addEventListener('change', async () => {
    localStorage.setItem('pmAgent', agentSelect.value);
    paintAgentChip();
    currentThread = [];
    activeSessionId = null;
    showEmptyChat();
    await renderSavedChats();
  });

  modelSelect.addEventListener('change', () => {
    localStorage.setItem('pmModel', modelSelect.value);
  });
}

async function refreshAgents() {
  await populateAgents();
}

function showEmptyChat() {
  log.innerHTML = '';
  appendLine('system', `No unsaved messages with ${agentLabel(activeAgentId())}. Open a saved session or start a new chat.`);
}

async function sendMessage() {
  const userMessage = input.value.trim();
  if (!userMessage) return;
  const skillContent = selectedSkill ? skillContentInput.value.trim() : '';
  const skillName = selectedSkill ? skillNameInput.value.trim() || selectedSkill.name : '';
  const message = skillContent
    ? `Skill: ${skillName}\n\n${skillContent}\n\nUser message:\n${userMessage}`
    : userMessage;
  const agentId = activeAgentId();
  input.value = '';
  const ts = new Date().toISOString();
  currentThread.push({ ts, sender: 'user', message, agent: agentId });
  appendLine('user', message, new Date(ts).toLocaleTimeString());
  setStatus('Running agent…');
  sendBtn.disabled = true;
  try {
    const result = await API.chatSend(
      message,
      agentId,
      modelSelect ? modelSelect.value || null : null,
      currentThread.slice(-41, -1).map((entry) => ({
        role: entry.sender === 'user' ? 'user' : 'assistant',
        content: entry.message
      }))
    );
    const who = agentLabel(result.agent_id || agentId);
    const reply = result.reply || '(empty reply)';
    const replyTs = new Date().toISOString();
    currentThread.push({ ts: replyTs, sender: 'agent', message: reply, agent: result.agent_id || agentId });
    appendLine('system', reply, new Date(replyTs).toLocaleTimeString(), who);
    appendTools(result.tool_events || []);
    setStatus(`${who} · ${result.model || 'model'} replied.`);
  } catch (error) {
    setStatus('Send failed: ' + error.message);
  } finally {
    sendBtn.disabled = false;
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  sendMessage();
});

sendBtn.addEventListener('click', sendMessage);

Session.onEvent = (msg) => {
  if (msg.type === 'event' && msg.event) {
    const ev = msg.event;
    const what = ev.type || 'event';
    const path = ev.path || '';
    appendLine('event', what + (path ? ': ' + path : ''));
  }
};

/* The agent must be resolved before history loads, otherwise the
   first paint would show the previous agent's thread. */
initTopbar({ page: 'chat' });
populateSelectors()
  .then(() => {
    showEmptyChat();
    renderSavedChats();
    loadSkills();
  })
  .catch((e) => setStatus('Failed to start: ' + e.message));
Session.connect();

// ---- New agent scaffold + wipe chat (exposed for inline handlers) ----

async function scaffoldNewAgent() {
  const name = prompt('New agent id / folder name (e.g. "doc_writer"):');
  if (!name) return;
  if (!/^[A-Za-z0-9_\-]+$/.test(name)) {
    alert('Use only letters, numbers, underscore or dash.');
    return;
  }
  const rel = `workspace/agents/${name}`;
  const json = JSON.stringify({
    id: name,
    name: name.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    description: 'A custom agent scaffolded from the AI Agent Creator.',
    mode: 'agent',
    model: '',
    tools: ['map_files', 'read_file', 'write_text_file']
  }, null, 2);
  const md =
    `# ${name}\n` +
    `\n## role\n` +
    `\nYou are ${name}, a helpful Project Manager agent.\n` +
    `\n## purpose\n` +
    `\nDescribe what this agent accomplishes and when it is used.\n` +
    `\n## boundaries\n` +
    `\nState what this agent will not do.\n` +
    `\n## output format\n` +
    `\nDescribe the shape of the reply the agent must produce.\n`;
  try {
    await API.fileCreate(`${rel}/agent.json`, json);
    await API.fileCreate(`${rel}/agent.md`, md);
    localStorage.setItem('pmAgent', name);
    await refreshAgents();
    window.open(`/editor?path=${encodeURIComponent(`${rel}/agent.json`)}&root=workspace`, '_blank');
    setStatus(`Created ${rel}/agent.json + agent.md`);
    showToast(`Agent '${name}' created`);
  } catch (e) {
    alert('Failed to scaffold agent: ' + e.message);
  }
}

async function wipeChat() {
  const who = agentLabel(activeAgentId());
  if (!confirm(`Clear the unsaved chat with ${who}? Saved session files will remain.`)) return;
  currentThread = [];
  activeSessionId = null;
  showEmptyChat();
  setStatus('Unsaved chat cleared');
  showToast('Unsaved chat cleared');
}

/* ================================================================
   SAVED CHAT SESSIONS
   ================================================================
   A session text file under workspace/data/chat_sessions/<agent_id>/
   is the only persistent source for its conversation. */

function sessionText(record) {
  const lines = [
    `# ${record.title || 'Chat session'}`,
    '',
    `Agent: ${record.agent_id}`,
    `Saved: ${record.created || ''}`,
    ''
  ];
  for (const entry of record.entries || []) {
    const who = entry.sender === 'user' ? 'You' : (entry.agent || 'Agent');
    const ts = entry.ts ? new Date(entry.ts).toLocaleString() : '';
    lines.push(`## ${who}${ts ? ' - ' + ts : ''}`, '', entry.message || '', '');
  }
  return lines.join('\n');
}

function sessionStamp(created) {
  if (!created) return '';
  const when = new Date(created);
  if (isNaN(when.getTime())) return created;
  return when.toLocaleString();
}

function rowAction(icon, title, handler) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'btn-row-action';
  btn.title = title;
  btn.setAttribute('aria-label', title);
  btn.innerHTML = `<i data-lucide="${icon}" style="width:13px;"></i>`;
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    handler();
  });
  return btn;
}

function sessionRow(session) {
  const agentId = activeAgentId();
  const item = document.createElement('div');
  item.className = 'saved-chat-item';
  item.title = 'Open this saved session';

  const info = document.createElement('div');
  info.className = 'saved-chat-info';
  const title = document.createElement('div');
  title.className = 'saved-chat-title';
  title.textContent = session.title || session.id;
  const meta = document.createElement('div');
  meta.className = 'saved-chat-date';
  const count = session.entry_count === 1 ? '1 message' : `${session.entry_count} messages`;
  meta.textContent = `${count} · ${sessionStamp(session.created)}`;
  info.appendChild(title);
  info.appendChild(meta);

  const actions = document.createElement('div');
  actions.className = 'saved-chat-actions';

  actions.appendChild(rowAction('message-square', 'Open in chat', () => {
    openSavedSession(session.id, agentId);
  }));

  actions.appendChild(rowAction('copy', 'Copy transcript', () => {
    copySavedSession(session.id, agentId);
  }));

  /* An anchor, not a button: the endpoint answers with a
     Content-Disposition attachment, so a plain link hands the file
     to the browser's own download handling and can also be
     right-clicked into "Save as". */
  const download = document.createElement('a');
  download.className = 'btn-row-action';
  download.href = API.chatSessionExportUrl(session.id, agentId, 'txt');
  download.download = '';
  download.title = 'Download text session';
  download.setAttribute('aria-label', 'Download to disk');
  download.innerHTML = '<i data-lucide="download" style="width:13px;"></i>';
  download.addEventListener('click', (e) => e.stopPropagation());
  actions.appendChild(download);

  actions.appendChild(rowAction('trash-2', 'Delete this saved session', () => {
    deleteSavedSession(session, agentId);
  }));

  item.appendChild(info);
  item.appendChild(actions);
  item.addEventListener('click', () => openSavedSession(session.id, agentId));
  return item;
}

function emptySessionRow(text) {
  const item = document.createElement('div');
  item.className = 'saved-chat-empty';
  item.textContent = text;
  return item;
}

async function renderSavedChats() {
  if (!savedChatsList) return;
  const agentId = activeAgentId();
  savedChatsList.innerHTML = '';
  if (!agentId) {
    savedChatsList.appendChild(emptySessionRow('Select an agent to see its saved sessions.'));
    return;
  }
  try {
    const data = await API.chatSessions(agentId);
    const sessions = data.sessions || [];
    if (!sessions.length) {
      savedChatsList.appendChild(
        emptySessionRow(`No saved sessions for ${agentLabel(agentId)} yet. Use Save Session to keep a copy of this thread.`)
      );
      return;
    }
    for (const session of sessions) {
      savedChatsList.appendChild(sessionRow(session));
    }
    if (window.lucide) window.lucide.createIcons();
  } catch (e) {
    savedChatsList.appendChild(emptySessionRow('Could not load saved sessions: ' + e.message));
  }
}

async function saveCurrentChat() {
  const agentId = activeAgentId();
  if (!agentId) {
    showToast('Select an agent first');
    return;
  }
  if (!currentThread.length) {
    showToast('There is no conversation to save');
    return;
  }
  const suggested = currentThread.find((entry) => entry.sender === 'user')?.message || '';
  const title = prompt(
    `Save the current ${agentLabel(agentId)} thread as a named session:`,
    suggested ? suggested.slice(0, 60) : ''
  );
  if (title === null) return;
  try {
    const res = await API.chatSessionSave(agentId, title.trim() || null, currentThread);
    await renderSavedChats();
    const saved = res.session || {};
    activeSessionId = saved.id || null;
    showToast(`Saved "${saved.title || saved.id}" (${saved.entry_count || 0} messages)`);
  } catch (e) {
    alert('Failed to save the session: ' + e.message);
  }
}

function showSession(record) {
  log.innerHTML = '';
  const entries = record.entries || [];
  currentThread = entries.map((entry) => ({ ...entry }));
  activeSessionId = record.id || null;
  if (!entries.length) {
    appendLine('system', 'This saved session has no messages.');
    return;
  }
  for (const entry of entries) {
    const ts = entry.ts ? new Date(entry.ts).toLocaleTimeString() : '';
    const who = entry.agent ? agentLabel(entry.agent) : null;
    appendLine(entry.sender === 'user' ? 'user' : 'system', entry.message, ts, who);
  }
  setStatus(`Loaded saved session: ${record.title || record.id}`);
}

async function openSavedSession(sessionId, agentId) {
  try {
    const record = await API.chatSession(sessionId, agentId);
    showSession(record);
    showToast(`Loaded "${record.title || sessionId}"`);
  } catch (e) {
    alert('Failed to open the session: ' + e.message);
  }
}

async function copySavedSession(sessionId, agentId) {
  try {
    const record = await API.chatSession(sessionId, agentId);
    copyText(sessionText(record), 'Session copied to clipboard');
  } catch (e) {
    alert('Failed to copy the session: ' + e.message);
  }
}

async function deleteSavedSession(session, agentId) {
  const label = session.title || session.id;
  const deletingActive = activeSessionId === session.id;
  const warning = deletingActive
    ? ' The open in-memory conversation will also be cleared.'
    : '';
  if (!confirm(`Delete the only saved text file for "${label}"?${warning}`)) return;
  try {
    await API.chatSessionDelete(session.id, agentId);
    if (deletingActive) {
      currentThread = [];
      activeSessionId = null;
      showEmptyChat();
    }
    await renderSavedChats();
    showToast('Saved session deleted');
  } catch (e) {
    alert('Failed to delete the session: ' + e.message);
  }
}

async function loadSkills(selectedPath = '') {
  if (!skillSelect) return;
  try {
    const data = await API.project(null, ['workspace']);
    const workspace = (data.filesystem || []).find((root) => root.name === 'workspace');
    const skillsFolder = (workspace?.children || []).find((node) => node.name === 'skills');
    const files = (skillsFolder?.children || [])
      .filter((node) => node.type !== 'directory' && /\.md$/i.test(node.name))
      .sort((a, b) => a.name.localeCompare(b.name));

    skillSelect.replaceChildren(new Option('Select a skill', ''));
    for (const file of files) {
      skillSelect.add(new Option(file.name.replace(/\.md$/i, ''), file.path));
    }
    if (selectedPath) skillSelect.value = selectedPath;
    if (!files.length) {
      selectedSkill = null;
      skillSelect.value = '';
    }
  } catch (error) {
    skillSelect.replaceChildren(new Option('Could not load skills', ''));
    setStatus('Failed to load skills: ' + error.message);
  }
}

if (skillSelect) {
  skillSelect.addEventListener('change', async () => {
    const path = skillSelect.value;
    selectedSkill = null;
    if (!path) return;
    try {
      const skill = await API.fileRead(path);
      const name = skillSelect.selectedOptions[0].textContent;
      skillNameInput.value = name;
      skillContentInput.value = skill.content || '';
      selectedSkill = { name, content: skill.content || '' };
      showToast(`Skill "${name}" will be sent with your next message`);
    } catch (error) {
      setStatus('Failed to open skill: ' + error.message);
    }
  });
}

document.getElementById('newSkill')?.addEventListener('click', () => {
  skillSelect.value = '';
  skillNameInput.value = '';
  skillContentInput.value = '';
  selectedSkill = null;
  skillNameInput.focus();
});

saveSkillButton?.addEventListener('click', async () => {
  const enteredName = skillNameInput.value.trim().replace(/\.md$/i, '');
  const content = skillContentInput.value.trim();
  const fileName = enteredName.replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
  if (!fileName) {
    showToast('Enter a skill name using letters, numbers, dashes, or underscores');
    skillNameInput.focus();
    return;
  }
  if (!content) {
    showToast('Enter the skill instructions first');
    skillContentInput.focus();
    return;
  }

  const path = `workspace/skills/${fileName}.md`;
  const alreadyExists = Array.from(skillSelect.options).some((option) => option.value === path);
  if (alreadyExists && !confirm(`Replace the saved skill "${fileName}"?`)) return;

  saveSkillButton.disabled = true;
  try {
    if (alreadyExists) {
      await API.fileWrite(path, content + '\n');
    } else {
      await API.fileCreate(path, content + '\n');
    }
    await loadSkills(path);
    selectedSkill = { name: fileName, content };
    showToast(`Saved skill "${fileName}"`);
  } catch (error) {
    setStatus('Failed to save skill: ' + error.message);
    alert('Failed to save skill: ' + error.message);
  } finally {
    saveSkillButton.disabled = false;
  }
});

window.scaffoldNewAgent = scaffoldNewAgent;
window.wipeChat = wipeChat;
window.saveCurrentChat = saveCurrentChat;
```

---

<!-- ==== 13/125 : frontend/js/editor.js ==== -->

### frontend/js/editor.js

```javascript
/* Monaco editor module */
let editor = null;

const Editor = {
  /* The home page has no editor host; it is editor.html's job. */
  hasHost() {
    return !!document.getElementById('editor');
  },

  init() {
    if (!this.hasHost()) {
      return Promise.resolve(null);
    }
    return new Promise((resolve, reject) => {
      if (typeof require === 'undefined') {
        reject(new Error('Monaco loader not found'));
        return;
      }
      require.config({
        paths: {
          vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs'
        }
      });
      require(['vs/editor/editor.main'], () => {
        editor = monaco.editor.create(document.getElementById('editor'), {
          value: '// Select a file from the sidebar to start editing\n',
          language: 'plaintext',
          theme: 'vs-dark',
          automaticLayout: true,
          minimap: { enabled: true },
          wordWrap: 'on',
          fontSize: 14,
          tabSize: 4,
          insertSpaces: true,
          autoIndent: 'full',
          formatOnType: true,
          formatOnPaste: true
        });
        resolve(editor);
      });
    });
  },

  getEditor() {
    return editor;
  },

  setValue(content) {
    if (editor) editor.setValue(content);
  },

  getValue() {
    return editor ? editor.getValue() : '';
  },

  setLanguage(lang) {
    if (editor && monaco && editor.getModel()) {
      monaco.editor.setModelLanguage(editor.getModel(), lang);
    }
  },

  setReadOnly(flag) {
    if (editor) {
      editor.updateOptions({
        readOnly: !!flag,
        domReadOnly: !!flag
      });
    }
  },

  onChange(callback) {
    if (editor) {
      editor.onDidChangeModelContent(callback);
    }
  },

  layout() {
    if (editor) editor.layout();
  }
};

export default Editor;
```

---

<!-- ==== 14/125 : frontend/js/main.js ==== -->

### frontend/js/main.js

```javascript
/* Main application wiring */
import API from './api.js';
import Session from './session.js';
import Tree from './tree.js';
import Editor from './editor.js';
import { initAgentsPanel, updateRunTarget } from './agents.js';
import { initAgentCards, openChatWithAgent } from './agentCards.js';
import { initTopbar } from './topbar.js';

let currentFile = null;
let currentLanguage = 'plaintext';
let isDirty = false;
let currentIsFolder = false;
let currentIsReadOnly = false;

/* main.js is shared by home.html and editor.html. Only editor.html
   carries a #editor host, so every editor call is guarded. */
const hasEditor = () => Editor.hasHost();

/* Home lists the managed workspace and the read-only application source.
   The test environment is browsed separately from /test, not from home
   or the editor. */
const HOME_ROOTS = ['workspace', 'source_files'];
const EDITOR_HIDDEN_ROOTS = ['test_environment'];

/* Paths are browser-root-qualified (workspace/..., source_files/...),
   so no scope needs to be tracked or sent. The active folder is the
   root folder selected in the tree. */

function isPathReadOnly(path) {
  const rootName = Tree.rootOf(path);
  if (rootName && Tree.roots[rootName] === false) return true;
  const node = Tree.nodeFor(path);
  if (node && node.editable === false) return true;
  return false;
}

function applyReadOnly() {
  if (hasEditor()) Editor.setReadOnly(currentIsReadOnly);
  const el = document.getElementById('readOnlyIndicator');
  if (el) el.textContent = currentIsReadOnly ? '🔒 READ-ONLY' : '';
}

function getLanguage(filePath) {
  if (!filePath) return 'plaintext';
  const ext = filePath.split('.').pop().toLowerCase();
  const map = {
    py: 'python',
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    html: 'html',
    htm: 'html',
    css: 'css',
    json: 'json',
    md: 'markdown',
    yaml: 'yaml',
    yml: 'yaml',
    sql: 'sql',
    xml: 'xml',
    sh: 'shell',
    bat: 'batch',
    ps1: 'powershell',
    env: 'shell',
    txt: 'plaintext'
  };
  return map[ext] || 'plaintext';
}

function setStatus(msg) {
  const el = document.getElementById('statusMessage');
  if (el) el.textContent = msg;
}

function updateFileDisplay() {
  const cf = document.getElementById('currentFile');
  if (cf) cf.textContent = currentFile ? currentFile : 'No file selected';
  const lang = document.getElementById('language');
  if (lang) lang.textContent = currentLanguage;
  const dirty = document.getElementById('unsavedIndicator');
  if (dirty) dirty.textContent = isDirty ? '● UNSAVED' : '';
  applyReadOnly();
}

async function openFile(filePath) {
  if (isDirty) {
    const proceed = confirm('You have unsaved changes. Open another file?');
    if (!proceed) return;
  }
  /* Home has no editor, so opening a file means handing it to
     editor.html rather than rendering it here. */
  if (!hasEditor()) {
    const root = Tree.rootOf(filePath) || Tree.activeRoot;
    window.location.href =
      `/editor?path=${encodeURIComponent(filePath)}&root=${encodeURIComponent(root)}`;
    return;
  }
  setStatus('Opening ' + filePath + '...');
  try {
    const data = await API.fileRead(filePath);
    currentFile = filePath;
    currentIsFolder = false;
    currentIsReadOnly = isPathReadOnly(filePath);
    currentLanguage = getLanguage(filePath);
    if (hasEditor()) {
      Editor.setValue(data.content || '');
      Editor.setLanguage(currentLanguage);
    }
    isDirty = false;
    updateFileDisplay();
    Tree.setSelected(filePath);
    Tree.reveal(filePath);
    setStatus(currentIsReadOnly
      ? 'Opened ' + filePath + ' (read-only)'
      : 'Opened ' + filePath);
    updateRunTarget();
  } catch (error) {
    setStatus('Error: ' + error.message);
    alert(error.message);
  }
}

function selectFolder(path) {
  currentFile = path;
  currentIsFolder = true;
  updateFileDisplay();
  setStatus('Folder selected: ' + path);
  updateRunTarget();
}

async function saveFile() {
  if (!currentFile) {
    alert('No file is currently open.');
    return;
  }
  if (currentIsFolder) {
    alert('Select a file to save. Folders cannot be saved as files.');
    return;
  }
  if (!hasEditor()) {
    alert('Open the file in the editor to save it.');
    return;
  }
  if (currentIsReadOnly) {
    alert('This file is read-only: ' + currentFile);
    return;
  }
  setStatus('Saving...');
  try {
    await API.fileWrite(currentFile, Editor.getValue());
    isDirty = false;
    updateFileDisplay();
    setStatus('Saved ' + currentFile);
    await Tree.refresh();
  } catch (error) {
    setStatus('Save error: ' + error.message);
    alert(error.message);
  }
}

function requireWritableRoot(path) {
  const rootName = Tree.rootOf(path);
  if (rootName && Tree.roots[rootName] === false) {
    alert(rootName + ' is read-only.');
    return false;
  }
  return true;
}

function isRootFolder(path) {
  return Tree.rootOf(path) === path;
}

async function newFile() {
  if (!Tree.isWritable()) {
    alert(Tree.activeRoot + ' is read-only.');
    return;
  }
  const suggestion = (currentIsFolder ? currentFile : Tree.activeRoot) + '/';
  const fileName = prompt('Enter new file path/name:', suggestion);
  if (!fileName) return;
  if (!requireWritableRoot(fileName)) return;
  try {
    await API.fileCreate(fileName, '');
    await Tree.refresh();
    await openFile(fileName);
    setStatus('Created ' + fileName);
  } catch (error) {
    alert(error.message);
  }
}

async function newFolder() {
  if (!Tree.isWritable()) {
    alert(Tree.activeRoot + ' is read-only.');
    return;
  }
  const suggestion = (currentIsFolder ? currentFile : Tree.activeRoot) + '/';
  const folderPath = prompt('Enter new folder path:', suggestion);
  if (!folderPath) return;
  if (!requireWritableRoot(folderPath)) return;
  try {
    await API.directoryCreate(folderPath);
    await Tree.refresh();
    setStatus('Created folder ' + folderPath);
  } catch (error) {
    alert(error.message);
  }
}

async function renameSelected() {
  if (!currentFile) {
    alert('Select a file or folder first.');
    return;
  }
  if (!requireWritableRoot(currentFile)) return;
  if (isRootFolder(currentFile)) {
    alert('A root folder cannot be renamed.');
    return;
  }
  const newName = prompt('Enter the new name/path:', currentFile);
  if (!newName || newName === currentFile) return;
  if (!requireWritableRoot(newName)) return;
  try {
    await API.pathRename(currentFile, newName);
    currentFile = newName;
    await Tree.refresh();
    if (currentIsFolder) {
      Tree.setSelected(newName);
      setStatus('Renamed folder to ' + newName);
    } else {
      await openFile(newName);
    }
  } catch (error) {
    alert(error.message);
  }
}

async function deleteSelected() {
  if (!currentFile) {
    alert('Select a file or folder first.');
    return;
  }
  if (!requireWritableRoot(currentFile)) return;
  if (isRootFolder(currentFile)) {
    alert('A root folder cannot be deleted.');
    return;
  }
  const confirmed = confirm((currentIsFolder ? 'Delete folder ' : 'Delete file ') + currentFile + '?');
  if (!confirmed) return;
  try {
    if (currentIsFolder) {
      await API.directoryDelete(currentFile);
    } else {
      await API.fileDelete(currentFile);
    }
            currentFile = null;
            currentIsFolder = false;
            currentIsReadOnly = false;
            if (hasEditor()) Editor.setValue('');
            isDirty = false;
    updateFileDisplay();
    await Tree.refresh();
    setStatus('Deleted.');
    updateRunTarget();
  } catch (error) {
    alert(error.message);
  }
}

async function refreshTree() {
  await Tree.refresh();
  setStatus('Refreshed.');
}

function selectRoot(rootName) {
  setStatus('Working in ' + rootName
    + (Tree.roots[rootName] === false ? ' (read-only)' : ''));
}

function openChatPopup(agentId) {
  openChatWithAgent(agentId);
}

function init() {
  Editor.init()
    .then(async () => {
      initTopbar({ page: hasEditor() ? 'editor' : 'home' });

      if (hasEditor()) {
        Editor.onChange(() => {
          if (currentFile) {
            isDirty = true;
            updateFileDisplay();
          }
        });
      }

      Tree.onFileSelect = openFile;
      Tree.onFolderSelect = selectFolder;
      Tree.onRootSelect = selectRoot;

      // ---- Project name ----
      if (document.getElementById('projectName')) {
        try {
          const info = await API.health();
          const name = info.project?.name;
          if (name) document.getElementById('projectName').textContent = name;
        } catch (e) {
          // ignore
        }
      }

      // ---- Top bar actions ----
      /* Page navigation lives in the shared topbar; only this page's
         own tools are wired here. */
      document.getElementById('saveBtn')?.addEventListener('click', saveFile);
      document.getElementById('newFileBtn')?.addEventListener('click', newFile);
      document.getElementById('newFolderBtn')?.addEventListener('click', newFolder);
      document.getElementById('renameBtn')?.addEventListener('click', renameSelected);
      document.getElementById('deleteBtn')?.addEventListener('click', deleteSelected);
      document.getElementById('refreshBtn')?.addEventListener('click', refreshTree);
      document.querySelectorAll('[data-editor-action]').forEach((card) => {
        card.addEventListener('click', () => {
          document.getElementById(card.dataset.editorAction)?.click();
        });
      });

      document.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
          event.preventDefault();
          saveFile();
        }
      });

      const sidebar = document.getElementById('sidebar');
      const resizeHandle = document.getElementById('resizeHandle');
      if (resizeHandle && sidebar) {
        let resizing = false;
        resizeHandle.addEventListener('mousedown', () => { resizing = true; document.body.style.cursor = 'col-resize'; });
        document.addEventListener('mousemove', (e) => {
          if (!resizing) return;
          const width = e.clientX;
          if (width >= 180 && width <= 500) {
            sidebar.style.width = width + 'px';
            Editor.layout();
          }
        });
        document.addEventListener('mouseup', () => { resizing = false; document.body.style.cursor = ''; });
      }

      window.addEventListener('beforeunload', (event) => {
        if (!isDirty) return;
        event.preventDefault();
        event.returnValue = '';
      });

      setStatus('Ready');
      await Tree.load(
        hasEditor() ? null : HOME_ROOTS,
        hasEditor() ? EDITOR_HIDDEN_ROOTS : []
      );

      /* Home page: agent cards replace the editor. */
      if (document.getElementById('agentCards')) {
        try {
          await initAgentCards({ onOpen: openChatPopup });
        } catch (e) {
          const host = document.getElementById('agentCards');
          host.textContent = 'Failed to load agents: ' + e.message;
        }
        return;
      }

      initAgentsPanel({
        getCurrentFile: () => currentFile,
        isDirty: () => isDirty,
        saveFile,
        refreshTree,
        openFile,
        editorLayout: () => Editor.layout()
      });
      const urlParams = new URLSearchParams(window.location.search);
      const initialPath = urlParams.get('path');
      const initialRoot = urlParams.get('root');
      if (initialRoot && initialRoot in Tree.roots && !EDITOR_HIDDEN_ROOTS.includes(initialRoot)) {
        Tree.activeRoot = initialRoot;
      }
      if (initialPath) {
        await openFile(initialPath);
      }
    })
    .catch((e) => {
      setStatus('Error: ' + e.message);
    });

  Session.connect();
}

document.addEventListener('DOMContentLoaded', init);

export { openFile, saveFile, newFile, newFolder, renameSelected, deleteSelected, refreshTree, openChatPopup, currentFile, isDirty };
```

---

<!-- ==== 15/125 : frontend/js/orchestrator.js ==== -->

### frontend/js/orchestrator.js

```javascript
import API from './api.js';

const state = {
  agents: [],
  queue: []
};

const $ = (id) => document.getElementById(id);

export function initOrchestrator() {
  const runButton = $('orchestratorRunBtn');
  const clearButton = $('orchestratorClearBtn');
  if (!runButton || !clearButton) return;

  runButton.addEventListener('click', runOrchestrator);
  clearButton.addEventListener('click', () => {
    state.queue = [];
    renderChecklist();
    renderQueue();
    setStatus('');
  });

  loadOrchestratorOptions();
}

function setStatus(message) {
  const status = $('orchestratorStatus');
  if (status) status.textContent = message;
}

function agentLabel(agent) {
  return agent.source === 'workspace' ? `${agent.name} (workspace)` : agent.name;
}

async function loadOrchestratorOptions() {
  const agentsHost = $('orchestratorAgents');
  const modelSelect = $('orchestratorModel');
  if (!agentsHost || !modelSelect) return;

  agentsHost.textContent = 'Loading agents...';
  try {
    const agentData = await API.agents();
    state.agents = agentData.agents || [];
    renderChecklist();
    renderQueue();
  } catch (error) {
    agentsHost.textContent = `Failed to load agents: ${error.message}`;
    setStatus(`Could not load agents: ${error.message}`);
    return;
  }

  try {
    const modelData = await API.models();
    modelSelect.replaceChildren(new Option('Default agent models', ''));
    for (const model of modelData.models || []) {
      modelSelect.add(new Option(model.name || model.id, model.id));
    }
  } catch (error) {
    modelSelect.replaceChildren(new Option('Default agent models', ''));
    setStatus(`Agents loaded; model list unavailable: ${error.message}`);
  }
}

function renderChecklist() {
  const host = $('orchestratorAgents');
  if (!host) return;
  host.replaceChildren();
  if (!state.agents.length) {
    host.textContent = 'No agents found.';
    return;
  }

  for (const agent of state.agents) {
    const key = agent.source === 'workspace' ? agent.md_path : agent.id;
    const row = document.createElement('label');
    row.className = 'agent-option';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = key || agent.id;
    checkbox.disabled = !agent.complete;
    checkbox.checked = state.queue.some((item) => item.key === key);
    checkbox.addEventListener('change', () => toggleAgent(agent, checkbox.checked));
    row.appendChild(checkbox);

    const name = document.createElement('span');
    name.textContent = agent.complete
      ? agentLabel(agent)
      : `${agentLabel(agent)} (incomplete)`;
    row.appendChild(name);
    if (!agent.complete) row.title = 'This agent needs both agent.json and agent.md.';
    host.appendChild(row);
  }
}

function toggleAgent(agent, checked) {
  const key = agent.source === 'workspace' ? agent.md_path : agent.id;
  if (checked) {
    if (!state.queue.some((item) => item.key === key)) {
      state.queue.push({
        key,
        id: agent.id,
        name: agent.name || agent.id,
        json_path: agent.json_path || null,
        md_path: agent.md_path || null
      });
    }
  } else {
    state.queue = state.queue.filter((item) => item.key !== key);
  }
  renderQueue();
}

function renderQueue() {
  const host = $('orchestratorQueue');
  if (!host) return;
  host.replaceChildren();
  if (!state.queue.length) {
    host.textContent = 'Queue empty - select agents above to add them.';
    return;
  }

  state.queue.forEach((agent, index) => {
    const row = document.createElement('div');
    row.className = 'queue-item';

    const position = document.createElement('span');
    position.className = 'qidx';
    position.textContent = `${index + 1}.`;
    row.appendChild(position);

    const name = document.createElement('span');
    name.className = 'queue-agent-name';
    name.textContent = agent.name;
    name.title = agent.id;
    row.appendChild(name);

    const addMoveButton = (label, title, action, disabled) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.title = title;
      button.disabled = disabled;
      button.addEventListener('click', action);
      row.appendChild(button);
    };

    addMoveButton('↑', 'Move agent up', () => moveStep(index, -1), index === 0);
    addMoveButton('↓', 'Move agent down', () => moveStep(index, 1), index === state.queue.length - 1);
    addMoveButton('×', 'Remove agent', () => {
      state.queue = state.queue.filter((item) => item.key !== agent.key);
      renderChecklist();
      renderQueue();
    }, false);
    host.appendChild(row);
  });
}

function moveStep(index, delta) {
  const target = index + delta;
  if (target < 0 || target >= state.queue.length) return;
  const [agent] = state.queue.splice(index, 1);
  state.queue.splice(target, 0, agent);
  renderQueue();
}

function renderResults(result) {
  const host = $('orchestratorResult');
  if (!host) return;
  host.replaceChildren();

  for (const [index, output] of (result.outputs || []).entries()) {
    const card = document.createElement('section');
    card.className = 'orchestrator-result-item';
    const heading = document.createElement('h3');
    heading.textContent = `Agent ${index + 1}: ${output.agent_name || 'Agent'}`;
    const body = document.createElement('p');
    body.textContent = output.output || '(No reply)';
    card.append(heading, body);
    host.appendChild(card);
  }

  const final = document.createElement('section');
  final.className = 'orchestrator-result-item';
  const heading = document.createElement('h3');
  heading.textContent = 'Final reply';
  const body = document.createElement('p');
  body.textContent = result.reply || '(No final reply)';
  final.append(heading, body);
  host.appendChild(final);
  host.hidden = false;
}

async function runOrchestrator() {
  if (!state.queue.length) {
    setStatus('Select at least one complete agent.');
    return;
  }
  const message = $('orchestratorMessage').value.trim();
  if (!message) {
    setStatus('Enter a message for the agent sequence.');
    return;
  }

  const button = $('orchestratorRunBtn');
  button.disabled = true;
  $('orchestratorResult').hidden = true;
  setStatus(`Running orchestrator with ${state.queue.length} agent(s)...`);

  const steps = state.queue.map((agent) => agent.json_path
    ? { json_path: agent.json_path, md_path: agent.md_path }
    : agent.id);

  try {
    const result = await API.pipelineRun({
      steps,
      message,
      model: $('orchestratorModel').value || null
    });
    renderResults(result);
    setStatus('Orchestrator completed.');
  } catch (error) {
    setStatus(`Orchestrator failed: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}
```

---

<!-- ==== 16/125 : frontend/js/panels.js ==== -->

### frontend/js/panels.js

```javascript
/* ============================================================
   Resizable, collapsible side panels
   ============================================================

   For a row of panels with a draggable boundary between each pair of
   visible neighbours. Written for the test dashboard's three panels
   (tree, evidence, prompt builder) but nothing in it knows that: the
   panel list is passed in.

   The existing splitter in main.js is not reused because it only works
   for a sidebar pinned to the viewport's left edge - it treats
   e.clientX as the width directly - and it cannot collapse anything.
   Both are needed here, and a right-hand panel needs the mirrored
   arithmetic anyway.

   The pure parts (clampWidth, fitPanels, resolveHandles, readState,
   writeState) are exported so they can be checked without a DOM. */

const STORAGE_PREFIX = 'pm.panels.';

/* Handles are 8px in CSS and there are at most two of them. Reserving
   them here rather than measuring the DOM keeps the arithmetic
   answerable: the centre panel's width is what is left over, so an
   unaccounted handle width would show up as a gap that never closes. */
const HANDLE_WIDTH = 8;
const COLLAPSE_THRESHOLD = 32;

/* What the middle panel is guaranteed while it is visible and there is
   more than one thing to drag. It is the number that decides whether
   the side panels can both have their maximum: 520 + 720 needs 1240 of
   window plus handles, and a narrower one has to choose. Below the floor
   the centre is squeezed rather than the sides being refused. */
const CENTRE_FLOOR = 360;

/* The handle count is what tells us whether there is a centre left to
   protect, so it is the single input both the fitter and the drag read.
   Two handles means all three panels are up. */
function centreFloor(handles) {
  return handles > 1 ? CENTRE_FLOOR : 0;
}

export function clampWidth(value, panel) {
  if (!Number.isFinite(value)) return panel.default;
  return Math.min(Math.max(Math.round(value), panel.min), panel.max);
}

/* Where two fixed panels have to share a window too narrow for the two of
   them at once, they shrink towards their minimums together. The centre
   panel is not in this function beyond its floor: past that floor it is
   what is left over, and it is allowed to go to zero, because a user who
   has both side panels open on a small window meant it.

   Scaling is proportional to the overshoot rather than a fixed priority,
   so neither side silently loses all its width first. */
export function fitPanels(containerWidth, left, right, handles = 0) {
  const mins = [left.min, right.min];
  const available = containerWidth - handles * HANDLE_WIDTH - centreFloor(handles);

  if (available <= 0) {
    return { left: mins[0], right: mins[1] };
  }

  let wanted = clampWidth(left.width, left) + clampWidth(right.width, right);

  if (wanted <= available) {
    return {
      left: clampWidth(left.width, left),
      right: clampWidth(right.width, right),
    };
  }

  /* Both are above their minimum, so shrink each by the same share of
     the overshoot. */
  let slackLeft = clampWidth(left.width, left) - mins[0];
  let slackRight = clampWidth(right.width, right) - mins[1];
  const totalSlack = slackLeft + slackRight;
  const excess = wanted - available;

  const takeLeft = Math.round((slackLeft / totalSlack) * excess);
  const takeRight = excess - takeLeft;

  return {
    left: clampWidth(clampWidth(left.width, left) - takeLeft, left),
    right: clampWidth(clampWidth(right.width, right) - takeRight, right),
  };
}

/* One handle per gap between two *adjacent visible* panels. So with
   all three up there are two; hide the centre and its two gaps go with
   it, leaving one handle on the only boundary left. Returns the ids of
   the handles to show, in order. */
export function resolveHandles(visible) {
  const shown = [];
  if (visible.centre) {
    /* Keep each side's splitter at the edge of the centre even when
       that side is collapsed, so dragging it back can reopen the panel. */
    shown.push('left', 'right');
  }
  /* Centre hidden with both sides up: the left handle now sits on the
     boundary between them. Reusing it keeps one rule - the left handle
     always controls the left edge of whatever is to its right. */
  if (!visible.centre && visible.left && visible.right) shown.push('left');
  return shown;
}

export function readState(key) {
  try {
    const raw = window.localStorage.getItem(STORAGE_PREFIX + key);
    if (!raw) return {};
    const value = JSON.parse(raw);
    return value && typeof value === 'object' ? value : {};
  } catch {
    /* A corrupt or unreadable store is not worth an error page; it just
       means this session starts on the defaults. */
    return {};
  }
}

export function writeState(key, state) {
  try {
    window.localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(state));
  } catch {
    /* Private mode, quota, disabled storage. The panels still work for
       this session; they just will not remember. */
  }
}

/* ============================================================
   LAYOUT
   ============================================================ */

/**
 * Wire a panel row.
 *
 * @param {object} spec
 *   container   - element the panels live in
 *   left/right  - {element, panel:{min,max,default}} fixed-width sides
 *   centre      - {element} the flexible middle
 *   handleLeft/handleRight - the two draggable dividers
 *   storageKey  - localStorage suffix
 *   onLayout    - called after every width or visibility change
 */
export function init(spec) {
  const { container, left, right, centre } = spec;
  const handleLeft = spec.handleLeft;
  const handleRight = spec.handleRight;
  const onLayout = spec.onLayout || (() => {});

  const state = readState(spec.storageKey);

  const widths = {
    left: clampWidth(state.left, left.panel),
    right: clampWidth(state.right, right.panel),
  };

  let hidden = {
    left: state.leftHidden === true,
    centre: state.centreHidden === true,
    right: state.rightHidden === true,
  };

  function visible() {
    return {
      left: !hidden.left,
      centre: !hidden.centre,
      right: !hidden.right,
    };
  }

  /* Apply widths to the two fixed sides. The centre's width is left to
     flexbox: everything not claimed by the sides and handles. */
  function handleCount() {
    return resolveHandles(visible()).length;
  }

  function applyWidths() {
    const room = container.getBoundingClientRect().width;
    const fitted = fitPanels(
      room,
      hidden.left
        ? { width: 0, min: 0, max: left.panel.max }
        : { width: widths.left, min: Math.min(widths.left, left.panel.min), max: left.panel.max },
      hidden.right
        ? { width: 0, min: 0, max: right.panel.max }
        : { width: widths.right, min: Math.min(widths.right, right.panel.min), max: right.panel.max },
      handleCount(),
    );

    if (!hidden.left) widths.left = fitted.left;
    if (!hidden.right) widths.right = fitted.right;

    left.element.style.width = widths.left + 'px';
    right.element.style.width = widths.right + 'px';
    left.element.style.minWidth = '0px';
    right.element.style.minWidth = '0px';
  }

  function applyVisibility() {
    const show = visible();

    left.element.hidden = !show.left;
    centre.element.hidden = !show.centre;
    right.element.hidden = !show.right;

    /* With the centre gone the right panel takes the free space instead
       of leaving a dead gap the only remaining handle cannot reach. */
    if (!show.centre && show.right) {
      right.element.style.flex = '1 1 auto';
      right.element.style.minWidth = '0px';
    } else {
      right.element.style.flex = '0 0 auto';
      right.element.style.minWidth = '0px';
    }

    const handles = resolveHandles(show);
    handleLeft.hidden = !handles.includes('left');
    handleRight.hidden = !handles.includes('right');

    /* State is published as aria-pressed rather than as a class: the
       toggle button *is* the control, so its pressed state is the
       truthful thing to announce, and the host styles it off that. */
    for (const [id, element] of Object.entries(spec.toggles || {})) {
      element.setAttribute('aria-pressed', String(!hidden[id]));
    }
  }

  function layout() {
    applyVisibility();
    applyWidths();
    onLayout();
  }

  function persist() {
    writeState(spec.storageKey, {
      left: widths.left,
      right: widths.right,
      leftHidden: hidden.left,
      centreHidden: hidden.centre,
      rightHidden: hidden.right,
    });
  }

  /* The handle never follows the cursor past a panel's own bounds, and
     once the centre is down to its floor the handle starts pushing the
     opposite side in rather than stealing from it. Both numbers come
     from the same helpers the fitter uses, so a drag and a layout pass
     cannot disagree about what fits.

     `which` and `other` are slot names, not the spec objects - `right`
     in this scope is {element, panel}, so indexing `widths` with it
     would file the value under "[object Object]" and the opposite
     panel would never actually yield. */
  function dragWidth(which, clientX, rect, wasHidden) {
    const panel = which === 'left' ? left.panel : right.panel;
    const other = which === 'left' ? right.panel : left.panel;
    const room = rect.width;
    const handles = handleCount();
    const floor = centreFloor(handles);

    let width = which === 'left'
      ? clientX - rect.left
      : rect.right - clientX;

    const leftWidth = which === 'left' && wasHidden ? 0 : widths.left;
    const rightWidth = which === 'right' && wasHidden ? 0 : widths.right;
    const roomForCentre = room - leftWidth - rightWidth - handles * HANDLE_WIDTH;

    if (roomForCentre < floor) {
      width += roomForCentre - floor;
    }

    widths[which] = Math.min(Math.max(Math.round(width), 0), panel.max);

    /* The opposite side gives up only what it can spare, and never drops
       below its own minimum. */
    const spare = room - widths[which] - handles * HANDLE_WIDTH - floor;
    const otherSlot = which === 'left' ? 'right' : 'left';
    const otherMinimum = hidden[otherSlot]
      ? 0
      : Math.min(widths[otherSlot], other.min);
    widths[otherSlot] = Math.max(Math.min(widths[otherSlot], spare), otherMinimum);
  }

  function beginDrag(which, event) {
    event.preventDefault();

    const move = (moveEvent) => {
      const rect = container.getBoundingClientRect();
      const wasHidden = hidden[which];
      const pointerWidth = which === 'left'
        ? moveEvent.clientX - rect.left
        : rect.right - moveEvent.clientX;

      if (pointerWidth <= COLLAPSE_THRESHOLD) {
        hidden[which] = true;
      } else {
        hidden[which] = false;
        dragWidth(which, moveEvent.clientX, rect, wasHidden);
      }

      layout();
    };

    const end = () => {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', end);
      document.body.classList.remove('panel-dragging');
      applyWidths();
      onLayout();
      persist();
    };

    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', end);
    document.body.classList.add('panel-dragging');
  }

  handleLeft.addEventListener('mousedown', (event) => beginDrag('left', event));
  handleRight.addEventListener('mousedown', (event) => beginDrag('right', event));

  /* Double-click is the reset. Without it the only way back to a
     comfortable width is to drag there by hand. */
  for (const [which, handle] of [['left', handleLeft], ['right', handleRight]]) {
    handle.addEventListener('dblclick', () => {
      widths[which] = spec[which].panel.default;
      applyWidths();
      onLayout();
      persist();
    });

    /* Arrows for keyboard resizing, Home/End for the bounds. The
       splitter is focusable, so it has to be operable without a mouse. */
    handle.addEventListener('keydown', (event) => {
      const step = event.shiftKey ? 40 : 16;
      const panel = spec[which].panel;
      let next = null;

      if (event.key === 'ArrowLeft') {
        next = (which === 'left' ? widths[which] - step : widths[which] + step);
      } else if (event.key === 'ArrowRight') {
        next = (which === 'left' ? widths[which] + step : widths[which] - step);
      } else if (event.key === 'Home') {
        next = panel.min;
      } else if (event.key === 'End') {
        next = panel.max;
      }

      if (next === null) return;
      event.preventDefault();
      widths[which] = clampWidth(next, panel);
      applyWidths();
      onLayout();
      persist();
    });
  }

  for (const [id, element] of Object.entries(spec.toggles || {})) {
    element.addEventListener('click', () => {
      hidden[id] = !hidden[id];
      layout();
      persist();
    });
  }

  layout();

  return {
    layout,
    /* The host needs this to bring back a panel it collapsed itself -
       "Show evidence" un-hides the centre when it is not visible. */
    show(slot) {
      if (!hidden[slot]) return false;
      hidden[slot] = false;
      layout();
      persist();
      return true;
    },
    isVisible: (slot) => !hidden[slot],
  };
}

export default { init, clampWidth, fitPanels, resolveHandles, readState, writeState };
```

---

<!-- ==== 17/125 : frontend/js/report.js ==== -->

### frontend/js/report.js

```javascript
/* ============================================================
   Header test report formatting
   ============================================================

   The text a saved report is written in, and the filename it gets.
   No DOM and no fetch, so both can be checked without a browser.

   Separate from the dashboard that shows the report because this is
   formatting with real branching - missing summary, missing prompt,
   agent ids that are not filenames - and inline in test.html it could
   only be checked by running a model.

   buildReportText() is the one definition of what a report reads like.
   The on-screen renderer in test.html and this file can disagree about
   wording, but they cannot disagree about content: both read the same
   object. */

/* The four headers in suite order. Anything the report carries that is
   not one of these is appended, so a suite that grows a fifth header
   produces a file that mentions it rather than dropping it. */
const HEADERS = ['role', 'user', 'purpose', 'hallucinations'];

/* Indent two spaces so a reply that contains its own blank lines or
   something dash-shaped cannot be read as the next section heading.
   Nothing an agent can say survives the two-space indent as a
   top-level marker. */
const INDENT = '  ';

const UNDERLINE = '='.repeat(60);
const RULE = '-'.repeat(5);

function field(value, fallback = '?') {
  const text = value === undefined || value === null ? '' : String(value).trim();
  return text || fallback;
}

function block(text, fallback = '(empty)') {
  const body = (text === undefined || text === null ? '' : String(text)).trim();
  /* The fallback is indented too. An unindented "(empty)" would be the
     only body line in the file that sits at column zero, and a reader
     scanning for headings would take it for one. */
  if (!body) return INDENT + fallback;
  return body
    .split('\n')
    .map((line) => INDENT + line)
    .join('\n');
}

/* "2026-09-30 14:22:31" for an ISO string, or the raw value when the
   report carries something unparseable. A wrong-but-present timestamp
   is better than a blank field, because the point of the line is to
   tell two saved reports apart. */
function readableTime(value) {
  if (!value) return '?';
  const when = new Date(value);
  if (isNaN(when)) return String(value);
  return when.toLocaleString();
}

/**
 * Render a report as the text of a saved file.
 *
 * @param {object} report - {summary, results} as GET /api/test/results
 *                          returns it. Any field may be missing.
 * @returns {string} the report, newline-terminated.
 */
export function buildReportText(report) {
  const data = report || {};
  const summary = data.summary || {};
  const results = Array.isArray(data.results) ? data.results : [];

  /* An absent total is filled from the rows, but only if there are any:
     a report with neither a summary nor rows has no total to report, and
     "0 of 0" would read as a real run of nothing. */
  const total = summary.total === undefined
    ? (results.length ? results.length : '?')
    : summary.total;
  const passed = summary.passed === undefined ? '?' : summary.passed;
  const failed = summary.failed === undefined ? '?' : summary.failed;

  /* FAIL only when something is positively known to have failed. An
     absent summary.failed falls back to the rows; with neither, the
     verdict is '?' rather than a pass nobody can support. */
  const known = summary.total !== undefined
    || summary.failed !== undefined
    || results.length > 0;
  const anyFailed = summary.failed === undefined
    ? results.some((row) => row && row.status && row.status !== 'PASS')
    : summary.failed > 0;
  const verdict = !known ? '?' : (anyFailed ? 'FAIL' : 'PASS');

  const lines = [];

  lines.push('Agent Header Test Report');
  lines.push(UNDERLINE);
  lines.push('Agent    : ' + field(summary.agent_id, '(unknown)'));
  lines.push('Model    : ' + field(summary.model, "(the agent's own model)"));
  lines.push('Ran at   : ' + readableTime(summary.ran_at));
  lines.push(
    'Result   : ' + verdict
    + ' - ' + passed + ' of ' + total + ' passed'
    + (summary.failed ? ', ' + failed + ' failed' : '')
  );
  if (summary.results_file) {
    lines.push('Evidence : ' + summary.results_file);
  }

  if (!results.length) {
    lines.push('');
    lines.push('No results were recorded in this report.');
    return lines.join('\n') + '\n';
  }

  /* Suite order first so the file reads the same way every time, then
     anything unrecognised. The dashboard renders the same way. */
  const ordered = [];
  for (const name of HEADERS) {
    for (const row of results) {
      if (row && row.section === name) ordered.push(row);
    }
  }
  for (const row of results) {
    if (row && !HEADERS.includes(row.section)) ordered.push(row);
  }

  for (const row of ordered) {
    lines.push('');
    lines.push(String(row.section || 'unknown').toUpperCase());
    lines.push(RULE);
    lines.push('Status : ' + field(row.status, '?'));
    if (row.reason) lines.push('Reason : ' + String(row.reason).trim());
    lines.push('Prompt :');
    lines.push(block(row.prompt));
    lines.push('Reply  :');
    lines.push(block(row.response));
  }

  return lines.join('\n') + '\n';
}

/* Same sanitiser the chat export uses (routers/chat.py): anything that
   is not a letter, digit, underscore or dash collapses to a dash. It
   also strips the characters Windows forbids in a filename, which is
   the whole reason the agent id is not trusted verbatim. */
function safeSegment(value, fallback, maxLength) {
  const cleaned = String(value === undefined || value === null ? '' : value)
    .replace(/[^A-Za-z0-9_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, maxLength);
  return cleaned || fallback;
}

/* YYYYMMDD-HHMMSS, local time. No colons: Windows rejects them in a
   filename, and a save that silently fails on the user's own machine is
   worse than a slightly ugly name. */
function timestamp(date) {
  const when = date instanceof Date && !isNaN(date) ? date : new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return [
    when.getFullYear(),
    pad(when.getMonth() + 1),
    pad(when.getDate()),
    '-',
    pad(when.getHours()),
    pad(when.getMinutes()),
    pad(when.getSeconds()),
  ].join('');
}

/**
 * The filename a saved report gets.
 *
 * Timestamp-per-run, so successive saves accumulate instead of
 * overwriting, and each one is distinguishable by name.
 *
 * @param {object} summary - the report's summary object.
 * @param {Date}   [when]   - injectable so the name is testable.
 * @returns {string} e.g. 'test_report_demo_agent_20260930-142231.txt'
 */
export function reportFileName(summary, when) {
  const agent = safeSegment((summary || {}).agent_id, 'unknown-agent', 40);
  return 'test_report_' + agent + '_' + timestamp(when) + '.txt';
}

export default { buildReportText, reportFileName };
```

---

<!-- ==== 18/125 : frontend/js/session.js ==== -->

### frontend/js/session.js

```javascript
/* Project Manager WebSocket session module */
let ws = null;
let wsConnected = false;
let reconnectTimeout = null;

const Session = {
  onEvent: null,
  onConnect: null,
  onDisconnect: null,

  connect() {
    if (ws && wsConnected) return;
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsConnected = true;
      if (this.onConnect) this.onConnect();
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (this.onEvent) this.onEvent(msg);
      } catch (e) {
        console.warn('Failed to parse WS message', e);
      }
    };

    ws.onclose = () => {
      wsConnected = false;
      if (this.onDisconnect) this.onDisconnect();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      reconnectTimeout = setTimeout(() => this.connect(), 2000);
    };

    ws.onerror = (e) => {
      console.error('WebSocket error', e);
    };
  },

  send(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  },

  sendOpen(path) {
    this.send({ type: 'open', path });
  },

  sendDirty(dirty) {
    this.send({ type: 'dirty', dirty });
  },

  sendSessions() {
    this.send({ type: 'sessions' });
  }
};

export default Session;
```

---

<!-- ==== 19/125 : frontend/js/topbar.js ==== -->

### frontend/js/topbar.js

```javascript
/* Shared topbar navigation

   Home / Editor / Chat must sit in the same place on every page, so
   the markup and styling live here instead of being copied into each
   page. Each page marks its header with data-pm-header and calls
   initTopbar({ page }).

   The links are rendered as anchors, not buttons, on purpose: home
   and editor apply a bare `button { ... }` rule and chat.html styles
   `.btn-header`, so anchors sidestep both stylesheets and come out
   pixel-identical on all three pages. An item flagged `popup` is the
   one exception - it has to be a real button to be operable, so
   .pmnav-button undoes the host pages' button styling instead. */

const NAV_ITEMS = [
  { page: 'home', label: 'Home', href: '/' },
  { page: 'editor', label: 'Editor', href: '/editor' },
  { page: 'chat', label: 'Chat', href: '/chat' },
  {
    page: 'prompt-builder',
    label: 'Prompt Builder',
    href: '/prompt-builder',
    popup: { name: 'PMPromptBuilder', width: 1100, height: 760 }
  },
  { page: 'test', label: 'Test', href: '/test' }
];

const STYLE_ID = 'pmnav-style';

const NAV_CSS = `
.pmnav {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-shrink: 0;
}

.pmnav-link {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #45474d;
  background: #2f3136;
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.pmnav-link:hover {
  background: #3a3d44;
  border-color: #565a61;
  color: #ffffff;
}

.pmnav-link.pmnav-current,
.pmnav-link[aria-current="page"] {
  background: #0e639c;
  border-color: #1177bb;
  color: #ffffff;
}

.pmnav-link:focus-visible {
  outline: 2px solid #4fc3f7;
  outline-offset: 2px;
}

/* A popup item has to be a <button> to be clickable, which means it
   inherits whatever bare button rule the host page applies. These
   declarations put it back in line with the anchors. */

.pmnav-link.pmnav-button {
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
  cursor: pointer;
}
`;

/* Tools open in their own centred window. A named target means a
   second click reuses the window instead of stacking duplicates, the
   same way the agent cards open chat. */
function openPopup(url, spec) {
  const left = Math.max(0, (window.screen.width - spec.width) / 2);
  const top = Math.max(0, (window.screen.height - spec.height) / 2);
  const popup = window.open(
    url,
    spec.name,
    `width=${spec.width},height=${spec.height},top=${top},left=${left},` +
    'resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no'
  );
  if (!popup) {
    window.alert('The popup was blocked. Allow popups for this site and try again.');
  }
  return popup;
}

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = NAV_CSS;
  document.head.appendChild(style);
}

function initTopbar(options = {}) {
  const page = options.page;
  const header = options.header
    || document.querySelector('[data-pm-header]');
  if (!header) return null;

  ensureStyle();

  /* Re-initialising must not stack duplicate nav groups. */
  for (const child of Array.from(header.children)) {
    if (child.classList && child.classList.contains('pmnav')) {
      child.remove();
    }
  }

  const nav = document.createElement('nav');
  nav.className = 'pmnav';
  nav.setAttribute('aria-label', 'Main');

  for (const item of NAV_ITEMS) {

    if (item.popup) {
      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'pmnav-link pmnav-button';
      trigger.textContent = item.label;
      trigger.title = 'Opens in a new window';
      trigger.addEventListener('click', () => openPopup(item.href, item.popup));
      nav.appendChild(trigger);
      continue;
    }

    const link = document.createElement('a');
    link.className = 'pmnav-link';
    link.href = item.href;
    link.textContent = item.label;
    if (item.page === page) {
      link.classList.add('pmnav-current');
      link.setAttribute('aria-current', 'page');
    }
    nav.appendChild(link);
  }

  header.appendChild(nav);
  return nav;
}

export { initTopbar, openPopup, NAV_ITEMS };
```

---

<!-- ==== 20/125 : frontend/js/tree.js ==== -->

### frontend/js/tree.js

```javascript
/* Project tree rendering module */
import API from './api.js';

const Tree = {
  root: [],
  roots: {},
  activeRoot: null,
  selectedPath: null,
  expanded: new Set(),
  /* Which browser roots this page is shown. null = the server's
     default, every root. Held here rather than passed to render()
     because refresh() has to reproduce the same view: a tree that
     widened itself on refresh would quietly show a page folders it
     was never given. */
  allowedRoots: null,
  hiddenRoots: [],
  onFileSelect: null,
  onFolderSelect: null,
  onRootSelect: null,

  /* The top level of the tree is the set of browser roots, so the
     tree doubles as the folder switcher. Clicking a root folder
     makes it the folder that file operations act on. */

  rootOf(path) {
    if (!path) return null;
    const head = String(path).split('/')[0];
    return head in this.roots ? head : null;
  },

  isWritable() {
    if (this.activeRoot === null) return true;
    return this.roots[this.activeRoot] !== false;
  },

  nodeFor(path, items = this.root) {
    for (const item of items || []) {
      if (item.path === path) return item;
      if (item.children) {
        const hit = this.nodeFor(path, item.children);
        if (hit) return hit;
      }
    }
    return null;
  },

  async load(roots = null, hiddenRoots = []) {
    this.allowedRoots = roots;
    this.hiddenRoots = hiddenRoots;
    const data = await API.project(null, this.allowedRoots);
    this.root = data.filesystem || [];
    this.roots = {};
    for (const node of this.root) {
      this.roots[node.name] = node.writable !== false;
    }
    const visibleRoots = this.root.filter(node => !this.hiddenRoots.includes(node.name));
    if (!visibleRoots.some(node => node.name === this.activeRoot)) {
      const firstWritable = visibleRoots.find(n => n.writable !== false);
      this.activeRoot = firstWritable
        ? firstWritable.name
        : (visibleRoots[0]?.name ?? null);
    }
    /* Show every root folder expanded so the available folders are
       visible without having to click each one open. */
    for (const node of this.root) {
      this.expanded.add(this.key(node.path));
    }
    this.render();
  },

  key(path) {
    return path;
  },

  render(containerId = 'tree') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    this.renderItems(
      this.root.filter(item => !this.hiddenRoots.includes(item.name)),
      container
    );
  },

  renderItems(items, container, depth = 0) {
    for (const item of items) {
      const row = document.createElement('div');
      row.className = 'tree-item';
      if (item.type === 'directory') {
        row.classList.add('folder');
        row.dataset.path = item.path;
        const isRoot = depth === 0 && item.root;
        if (isRoot) {
          row.classList.add('root');
          if (item.name === this.activeRoot) {
            row.classList.add('active');
          }
          if (item.writable === false) {
            row.classList.add('readonly');
          }
        }
        if (this.selectedPath === item.path) {
          row.classList.add('selected');
        }
        const isExpanded = this.expanded.has(this.key(item.path));
        const toggle = document.createElement('span');
        toggle.className = 'toggle' + (isExpanded ? ' expanded' : '');
        toggle.textContent = isExpanded ? '−' : '+';
        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = (isRoot ? '🗂 ' : '📁 ') + item.name;
        row.appendChild(toggle);
        row.appendChild(label);
        if (isRoot && item.writable === false) {
          const lock = document.createElement('span');
          lock.className = 'root-lock';
          lock.textContent = '🔒';
          lock.title = 'Read-only';
          row.appendChild(lock);
        }
        const children = document.createElement('div');
        children.className = 'children' + (isExpanded ? '' : ' collapsed');
        row.onclick = () => {
          this.selectedPath = item.path;
          if (isRoot) {
            const changed = this.activeRoot !== item.name;
            this.activeRoot = item.name;
            if (changed && this.onRootSelect) this.onRootSelect(item.name);
          }
          if (this.onFolderSelect) this.onFolderSelect(item.path);
          this.render();
          this.toggle(item.path);
        };
        container.appendChild(row);
        container.appendChild(children);
        this.renderItems(item.children || [], children, depth + 1);
      } else {
        row.textContent = this.getFileIcon(item.name) + ' ' + item.name;
        if (item.editable === false) {
          row.classList.add('readonly');
          row.title = item.size > 0
            ? 'Read-only: not an editable text file, or too large'
            : 'Read-only';
        }
        if (this.selectedPath === item.path) {
          row.classList.add('selected');
        }
        row.onclick = () => {
          this.selectedPath = item.path;
          const rootName = this.rootOf(item.path);
          if (rootName && rootName !== this.activeRoot) {
            this.activeRoot = rootName;
            if (this.onRootSelect) this.onRootSelect(rootName);
          }
          if (this.onFileSelect) this.onFileSelect(item.path);
          this.render();
        };
        container.appendChild(row);
      }
    }
  },

  toggle(path) {
    const key = this.key(path);
    if (this.expanded.has(key)) {
      this.expanded.delete(key);
    } else {
      this.expanded.add(key);
    }
    const container = document.getElementById('tree');
    if (!container) return;
    const row = container.querySelector('.tree-item.folder[data-path="' + path.replace(/"/g, '\\"') + '"]');
    if (!row) return;
    const toggle = row.querySelector('.toggle');
    toggle.classList.toggle('expanded');
    toggle.textContent = toggle.classList.contains('expanded') ? '−' : '+';
    const children = row.nextElementSibling;
    if (children && children.classList.contains('children')) {
      children.classList.toggle('collapsed');
    }
  },

  reveal(path) {
    const parts = path.split('/');
    for (let i = 1; i < parts.length; i++) {
      this.expanded.add(this.key(parts.slice(0, i).join('/')));
    }
    this.render();
  },

  setSelected(path) {
    this.selectedPath = path;
    this.render();
  },

  refresh() {
    return this.load(this.allowedRoots, this.hiddenRoots);
  },

  getFileIcon(name) {
    const ext = name.split('.').pop().toLowerCase();
    const icons = {
      py: '🐍',
      html: '🌐', htm: '🌐',
      css: '🎨',
      js: '🟨', mjs: '🟨', jsx: '🟨',
      ts: '🔷', tsx: '🔷',
      json: '📋',
      md: '📝',
      sql: '🗄️',
      xml: '🧾',
      sh: '⌨️', bat: '⌨️', ps1: '⌨️',
      yaml: '⚙️', yml: '⚙️', toml: '⚙️', ini: '⚙️', cfg: '⚙️', env: '⚙️',
      txt: '📄', csv: '📄'
    };
    return icons[ext] || '📄';
  }
};

export default Tree;
```

---

<!-- ==== 21/125 : frontend/pages/chat.html ==== -->

### frontend/pages/chat.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Creator</title>
    <!-- Lucide Icons Library -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --bg-darkest: #0b0f17;
            --bg-app: #10141e;
            --bg-panel: #131822;
            --bg-card: #1b2130;
            --bg-card-hover: #232a3d;
            --bg-input: #161c28;
            --border-color: #252e3e;
            --border-subtle: #1e2634;
            --text-primary: #e6e8ee;
            --text-secondary: #9aa2b1;
            --text-muted: #626c7d;
            --accent-blue: #3b82f6;
            --accent-blue-hover: #2563eb;
            --accent-glow: rgba(59, 130, 246, 0.15);
            --user-msg-bg: #1e293b;
            --radius-lg: 16px;
            --radius-md: 10px;
            --radius-sm: 6px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-darkest);
            color: var(--text-primary);
        }

        body {
            display: flex;
            flex-direction: column;
        }

        button, input, select, textarea {
            font-family: inherit;
            color: inherit;
        }

        .app-header {
            height: 52px;
            min-height: 52px;
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            z-index: 20;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .agent-logo {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
        }

        .app-title {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
            /* Keep these buttons hugging the nav at the far right
               instead of drifting into the middle of the header. */
            margin-left: auto;
        }

        .btn-header {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .btn-header:hover {
            background: var(--bg-card-hover);
            border-color: #3b475c;
        }

        .btn-icon-only {
            padding: 6px;
            border-radius: 50%;
        }

        .app-container {
            flex: 1;
            display: flex;
            overflow: hidden;
            position: relative;
        }

        .panel {
            display: flex;
            flex-direction: column;
            background: var(--bg-app);
            height: 100%;
            transition: transform 0.25s ease, width 0.25s ease;
        }

        .panel-header {
            height: 48px;
            padding: 0 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-subtle);
            background: var(--bg-panel);
        }

        .panel-title {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }

        .panel-sources {
            width: 320px;
            min-width: 280px;
            border-right: 1px solid var(--border-color);
            background: var(--bg-panel);
        }

        .sources-content {
            padding: 16px;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .note-input-box {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 12px;
        }

        .note-input-box textarea {
            background: transparent;
            border: none;
            outline: none;
            resize: none;
            font-size: 13px;
            color: var(--text-primary);
            min-height: 50px;
        }

        .btn-add-note {
            background: var(--accent-blue);
            color: #fff;
            border: none;
            border-radius: var(--radius-sm);
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            cursor: pointer;
            transition: background 0.15s;
        }

        .btn-add-note:hover {
            background: var(--accent-blue-hover);
        }

        .notes-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .skill-section {
            display: flex;
            flex-direction: column;
            gap: 9px;
            padding-top: 14px;
            border-top: 1px solid var(--border-subtle);
        }

        .skill-section label,
        .skill-section-title {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--text-secondary);
        }

        .skill-section input,
        .skill-section select,
        .skill-section textarea {
            width: 100%;
            padding: 8px;
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            font-size: 12px;
        }

        .skill-section textarea {
            min-height: 96px;
            resize: vertical;
        }

        .skill-actions {
            display: flex;
            gap: 8px;
        }

        .skill-actions button {
            flex: 1;
            padding: 7px 8px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            background: var(--bg-card);
            font-size: 11px;
            cursor: pointer;
        }

        .skill-actions button:hover:not(:disabled) {
            background: var(--bg-card-hover);
        }

        .skill-help {
            color: var(--text-muted);
            font-size: 11px;
            line-height: 1.4;
        }

        .note-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: border-color 0.15s;
        }

        .note-card:hover {
            border-color: var(--border-color);
        }

        .note-text {
            font-size: 13px;
            line-height: 1.45;
            color: var(--text-primary);
            white-space: pre-wrap;
            word-break: break-word;
        }

        .note-actions {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid var(--border-subtle);
            padding-top: 6px;
        }

        .btn-send-to-chat {
            background: transparent;
            border: none;
            color: var(--accent-blue);
            font-size: 11px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            padding: 2px 4px;
            border-radius: var(--radius-sm);
        }

        .btn-send-to-chat:hover {
            background: var(--accent-glow);
        }

        .btn-delete-note {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 2px 4px;
            border-radius: var(--radius-sm);
        }

        .btn-delete-note:hover {
            color: #ef4444;
        }

        .panel-chat {
            flex: 1;
            background: var(--bg-app);
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .chat-top-status {
            padding: 8px 20px;
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 12px;
        }

    .agent-controls {
        display: flex;
        gap: 10px;
        align-items: center;
    }

    /* Active agent chip: colored to match that agent's home card */
    .agent-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        color: var(--agent-color, #4fc3f7);
        border: 1px solid var(--agent-color, #4fc3f7);
        background: color-mix(in srgb, var(--agent-color, #4fc3f7) 16%, transparent);
        white-space: nowrap;
    }

    .agent-chip[hidden] {
        display: none;
    }

    .agent-chip-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--agent-color, #4fc3f7);
        box-shadow: 0 0 6px var(--agent-color, #4fc3f7);
    }


        .agent-controls select {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 4px 8px;
            font-size: 12px;
            color: var(--text-primary);
            outline: none;
            cursor: pointer;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-secondary);
            font-size: 12px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
        }

        #chatLog {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        #chatLog::-webkit-scrollbar {
            width: 6px;
        }
        #chatLog::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 10px;
        }

        /* Message Cards */
        .msg {
            max-width: 850px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .msg.user {
            align-items: flex-end;
        }

        .msg.ai, .msg.system {
            align-items: flex-start;
        }

        .msg-label {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .msg-body {
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-primary);
            white-space: pre-wrap;
            word-break: break-word;
        }

        .msg-actions {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid var(--border-subtle);
        }

        .btn-msg-action {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            padding: 4px 10px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            transition: all 0.15s ease;
        }

        .btn-msg-action:hover {
            background: var(--bg-card-hover);
            color: var(--text-primary);
            border-color: var(--border-color);
        }

        .chat-foot {
            padding: 14px 24px 20px;
            background: var(--bg-app);
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }

        .input-container {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 10px 14px 10px 18px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
            transition: border-color 0.2s;
        }

        .input-container:focus-within {
            border-color: #3b82f6;
        }

        #chatInput {
            background: transparent;
            border: none;
            outline: none;
            resize: none;
            font-size: 14px;
            max-height: 140px;
            min-height: 38px;
            color: var(--text-primary);
            line-height: 1.5;
        }

        #chatInput::placeholder {
            color: var(--text-muted);
        }

        .input-bottom-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .input-hint {
            font-size: 11px;
            color: var(--text-muted);
        }

        #chatSend {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--accent-blue);
            border: none;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.15s, transform 0.1s;
        }

        #chatSend:hover {
            background: var(--accent-blue-hover);
        }

        #chatSend:active {
            transform: scale(0.94);
        }

        #chatSend:disabled {
            background: var(--bg-card);
            color: var(--text-muted);
            cursor: not-allowed;
        }

        .panel-test {
            width: 330px;
            min-width: 280px;
            border-left: 1px solid var(--border-color);
            background: var(--bg-panel);
            position: relative;
        }

        .test-content {
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

        .test-func-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .test-func-card:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }

        .test-func-card i {
            color: var(--accent-blue);
            width: 20px;
            height: 20px;
        }

        .test-func-card span {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .saved-chats-section {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .section-label {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .btn-save-current {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: var(--radius-sm);
            font-size: 11px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .btn-save-current:hover {
            background: var(--bg-card-hover);
        }

        .saved-chats-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .saved-chat-item {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            cursor: pointer;
            transition: background 0.15s;
        }

        .saved-chat-item:hover {
            background: var(--bg-card-hover);
        }

        .saved-chat-actions {
            display: flex;
            align-items: center;
            gap: 4px;
            flex-shrink: 0;
        }

        .btn-row-action {
            background: var(--bg-input);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            width: 26px;
            height: 26px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .btn-row-action:hover {
            background: var(--bg-card-hover);
            color: var(--text-primary);
            border-color: var(--border-color);
        }

        .saved-chat-empty {
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.5;
            padding: 10px 12px;
            background: var(--bg-card);
            border: 1px dashed var(--border-subtle);
            border-radius: var(--radius-md);
        }

        .saved-chat-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
            overflow: hidden;
        }

        .saved-chat-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .saved-chat-date {
            font-size: 10px;
            color: var(--text-muted);
        }

        /* Toast Feedback */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--accent-blue);
            color: #fff;
            padding: 8px 16px;
            border-radius: var(--radius-md);
            font-size: 12px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.2s ease;
            pointer-events: none;
            z-index: 100;
        }

        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        @media (max-width: 1024px) {
            .panel-test {
                position: absolute;
                right: 0;
                top: 0;
                bottom: 0;
                z-index: 15;
                transform: translateX(100%);
                box-shadow: -10px 0 30px rgba(0,0,0,0.5);
            }
            .panel-test.open {
                transform: translateX(0);
            }
        }

        @media (max-width: 768px) {
            .panel-sources {
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                z-index: 15;
                transform: translateX(-100%);
                box-shadow: 10px 0 30px rgba(0,0,0,0.5);
            }
            .panel-sources.open {
                transform: translateX(0);
            }
        }
    </style>
</head>
<body>

    <header class="app-header" data-pm-header>
        <div class="header-left">
            <button class="btn-header btn-icon-only" id="toggleSources" title="Toggle Sources & Notes">
                <i data-lucide="panel-left"></i>
            </button>
            <div class="agent-logo">
                <i data-lucide="bot" style="width:18px; height:18px;"></i>
            </div>
            <h1 class="app-title">AI Agent Creator</h1>
        </div>

        <div class="header-actions">
            <button class="btn-header" onclick="createNewAgent()">
                <i data-lucide="plus" style="width:14px; height:14px;"></i>
                New Agent
            </button>
            <button class="btn-header btn-icon-only" id="toggleTest" title="Toggle Test Panel">
                <i data-lucide="panel-right"></i>
            </button>
        </div>
    </header>

    <div class="app-container">

        <!-- LEFT PANEL: SOURCES & NOTES -->
        <aside class="panel panel-sources" id="panelSources">
            <div class="panel-header">
                <span class="panel-title">Sources & Notes</span>
                <i data-lucide="notebook" style="width:16px; height:16px; color: var(--text-muted);"></i>
            </div>
            <div class="sources-content">
                
                <!-- Add Note Input Section -->
                <div class="note-input-box">
                    <textarea id="newNoteInput" placeholder="Add a note or task list..."></textarea>
                    <button class="btn-add-note" type="button" onclick="addNote()">
                        <i data-lucide="plus" style="width:14px;"></i> Add Note
                    </button>
                </div>

                <div class="notes-list" id="notesList" aria-live="polite"></div>

                <section class="skill-section" aria-label="Skills">
                    <div class="skill-section-title">Skills</div>
                    <select id="skillSelect" aria-label="Select a saved skill">
                        <option value="">Loading skills...</option>
                    </select>
                    <input id="skillName" type="text" maxlength="80" placeholder="Skill name">
                    <textarea id="skillContent" placeholder="Record the instructions for this skill..."></textarea>
                    <div class="skill-actions">
                        <button id="newSkill" type="button">New Skill</button>
                        <button id="saveSkill" type="button">Save Skill</button>
                    </div>
                    <p class="skill-help">Choose a skill to include its instructions with your next chat message. Skills are stored in workspace/skills.</p>
                </section>

            </div>
        </aside>

        <!-- CENTER PANEL: CHAT WORKSPACE -->
        <main class="panel panel-chat">

            <!-- Dynamic Status Bar & Agent Selectors -->
            <div class="chat-top-status">
                <div class="agent-controls">
                    <span>Active Agent:</span>
                    <span id="activeAgentChip" class="agent-chip" hidden>
                        <span class="agent-chip-dot"></span>
                        <span id="activeAgentName">agent</span>
                    </span>
                    <select id="agentSelect" title="Agent selection">
                        <option value="builder">Agent Builder v1</option>
                        <option value="code_executor">Code Executor</option>
                    </select>
                    <select id="modelSelect" title="Model selection">
                        <option value="gemini_flash">Gemini 3 Flash</option>
                        <option value="gemini_pro">Gemini Pro</option>
                    </select>
                </div>
                <div class="status-badge">
                    <span id="statusDot" class="status-dot"></span>
                    <span id="chatStatus">Connected</span>
                </div>
            </div>

            <!-- Main Chat Conversation Feed (populated by chat.js) -->
            <div id="chatLog"></div>

            <!-- Chat Footer & Input Box -->
            <footer class="chat-foot">
                <form id="chatForm">
                    <div class="input-container">
                        <textarea 
                            id="chatInput" 
                            placeholder="Message AI Agent Creator..." 
                            rows="1"
                            autocomplete="off"
                        ></textarea>
                        
                        <div class="input-bottom-row">
                            <span class="input-hint">Enter to send · Shift + Enter for newline</span>
                            <button id="chatSend" type="submit" aria-label="Send message">
                                <i data-lucide="arrow-up" style="width:18px; height:18px;"></i>
                            </button>
                        </div>
                    </div>
                </form>
            </footer>

        </main>

        <!-- RIGHT PANEL: TEST & SAVED CHATS -->
        <aside class="panel panel-test" id="panelTest">
            <div class="panel-header">
                <span class="panel-title">Test</span>
                <i data-lucide="x" style="width:16px; height:16px; color: var(--text-muted); cursor:pointer;" id="closeTest"></i>
            </div>
            <div class="test-content">

                <!-- Interactive Function Buttons Grid -->
                <div class="test-grid">
                    <div class="test-func-card" onclick="runTestFunc('Run Test Suite')">
                        <i data-lucide="play-circle"></i>
                        <span>Run Test Suite</span>
                    </div>
                    <div class="test-func-card" onclick="runTestFunc('Debug Agent')">
                        <i data-lucide="bug"></i>
                        <span>Debug Agent</span>
                    </div>
                    <div class="test-func-card" onclick="runTestFunc('Prompt Inspector')">
                        <i data-lucide="terminal"></i>
                        <span>Prompt Inspector</span>
                    </div>
                    <div class="test-func-card" onclick="runTestFunc('Output Evaluator')">
                        <i data-lucide="check-square"></i>
                        <span>Output Evaluator</span>
                    </div>
                    <div class="test-func-card" onclick="runTestFunc('Benchmark Performance')">
                        <i data-lucide="gauge"></i>
                        <span>Benchmark</span>
                    </div>
                    <div class="test-func-card" onclick="runTestFunc('View API Logs')">
                        <i data-lucide="file-code"></i>
                        <span>API Logs</span>
                    </div>
                    <div class="test-func-card" onclick="wipeChat()" title="Clear the chat history">
                        <i data-lucide="trash-2"></i>
                        <span>Wipe Chat</span>
                    </div>
                </div>

                <!-- Saved Chats Section -->
                <div class="saved-chats-section">
                    <div class="section-label">
                        <span>Saved Chats</span>
                        <button class="btn-save-current" onclick="saveCurrentChat()" title="Save the current thread as a named session">
                            <i data-lucide="bookmark" style="width:12px;"></i> Save Session
                        </button>
                    </div>

                    <div class="saved-chats-list" id="savedChatsList"></div>
                </div>

            </div>
        </aside>

    </div>

    <!-- Dynamic Toast Feedback Banner -->
    <div id="toast" class="toast">Action completed!</div>

    <!-- Backend Module Integrations -->
    <script type="module" src="/static/js/chat.js"></script>

    <script>
        // Initialize Icons
        lucide.createIcons();

        // Toast Helper
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }

        async function saveNoteFile(text, suggestedName) {
            if (typeof window.showSaveFilePicker !== 'function') {
                throw new Error('This browser does not support the Save File dialog. Use a Chromium-based browser on localhost.');
            }
            const handle = await window.showSaveFilePicker({
                suggestedName,
                types: [{
                    description: 'Text files',
                    accept: { 'text/plain': ['.txt'] }
                }]
            });
            const writable = await handle.createWritable();
            await writable.write(text);
            await writable.close();
            return handle.name;
        }

        function addNoteCard(text, fileName) {
            const card = document.createElement('div');
            card.className = 'note-card';
            const body = document.createElement('div');
            body.className = 'note-text';
            body.textContent = text;
            const filename = document.createElement('div');
            filename.className = 'saved-chat-date';
            filename.textContent = fileName;

            const actions = document.createElement('div');
            actions.className = 'note-actions';
            const send = document.createElement('button');
            send.className = 'btn-send-to-chat';
            send.type = 'button';
            send.textContent = 'Send to Chat';
            send.addEventListener('click', () => sendNoteToChat(text));
            const remove = document.createElement('button');
            remove.className = 'btn-delete-note';
            remove.type = 'button';
            remove.title = 'Remove this note from the panel; the saved file is unchanged';
            remove.textContent = '×';
            remove.addEventListener('click', () => card.remove());
            actions.append(send, remove);
            card.append(body, filename, actions);
            document.getElementById('notesList').prepend(card);
        }

        async function addNote() {
            const input = document.getElementById('newNoteInput');
            const text = input.value.trim();
            if (!text) {
                showToast('Write a note first');
                input.focus();
                return;
            }

            const suggestedName = `note-${new Date().toISOString().slice(0, 10)}.txt`;
            try {
                const fileName = await saveNoteFile(text + '\n', suggestedName);
                addNoteCard(text, fileName);
                input.value = '';
                showToast(`Note saved as ${fileName}`);
            } catch (error) {
                if (error.name !== 'AbortError') {
                    alert('Could not save the note: ' + error.message);
                }
            }
        }

        // Send Note Directly to Chat Box
        function sendNoteToChat(noteText) {
            const chatInput = document.getElementById('chatInput');
            
            chatInput.value = noteText;
            chatInput.focus();
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
            showToast('Note populated into chat input');
        }

        // Copying lives in chat.js (copyText), which owns the transcript
        // and the saved-session rows.

        // Placeholder Action Handlers
        function runTestFunc(funcName) {
            showToast(`Triggered: ${funcName}`);
        }

        function createNewAgent() {
            if (typeof scaffoldNewAgent === 'function') {
                scaffoldNewAgent();
            } else {
                showToast('Agent creator not ready yet');
            }
        }

        // Textarea Auto-growth and Keyboard handling
        const chatInput = document.getElementById("chatInput");
        const chatForm = document.getElementById("chatForm");

        if (chatInput) {
            chatInput.addEventListener("input", () => {
                chatInput.style.height = "auto";
                chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + "px";
            });

            chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (chatForm) {
                        chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                    }
                }
            });
        }

        // Form Submit Handler
        /* Sending lives entirely in chat.js, which owns the real
           /api/chat round trip and the transcript. Nothing is bound
           here: a second listener would echo the message locally and
           answer with a simulated reply. Enter is handled above by
           dispatching the same submit event. */

        // Sidebar Toggles
        document.getElementById("toggleSources")?.addEventListener("click", () => {
            document.getElementById("panelSources").classList.toggle("open");
        });

        document.getElementById("toggleTest")?.addEventListener("click", () => {
            document.getElementById("panelTest").classList.toggle("open");
        });

        document.getElementById("closeTest")?.addEventListener("click", () => {
            document.getElementById("panelTest").classList.remove("open");
        });
    </script>
</body>
</html>
```

---

<!-- ==== 22/125 : frontend/pages/editor.html ==== -->

### frontend/pages/editor.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manager Editor</title>

    <style>
        * {
            box-sizing: border-box;
        }

        html, body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            font-family: Arial, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
        }

        .topbar {
            height: 52px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 12px;
            background: #252526;
            border-bottom: 1px solid #3f3f46;
        }

        .title {
            font-weight: bold;
            margin-right: 12px;
        }

        /* Home for this page's own tools; the nav keeps the far right. */
        .topbar-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .spacer {
            flex: 1;
        }

        button {
            border: 1px solid #555;
            background: #333;
            color: #fff;
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
        }

        button:hover {
            background: #444;
        }

        button.primary {
            background: #0e639c;
            border-color: #1177bb;
        }

        button.danger {
            background: #7f1d1d;
        }

        .workspace {
            display: flex;
            height: calc(100vh - 78px);
            width: 100%;
        }

        .sidebar {
            width: 250px;
            min-width: 180px;
            background: #252526;
            border-right: 1px solid #3f3f46;
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 10px;
            border-bottom: 1px solid #3f3f46;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .resize-handle {
            width: 4px;
            cursor: col-resize;
            background: transparent;
            transition: background 0.2s;
        }

        .resize-handle:hover {
            background: #0e639c;
        }

        .tree {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }

        .tree-item {
            user-select: none;
            cursor: pointer;
            padding: 4px 6px;
            border-radius: 3px;
        }

        .tree-item:hover {
            background: #2a2d2e;
        }

        .tree-item.selected {
            background: #094771;
        }

        .tree-item.folder {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .tree-item.folder .toggle {
            display: inline-block;
            width: 12px;
            font-size: 11px;
            color: #bbb;
            text-align: center;
            flex-shrink: 0;
        }

        .tree-item.folder .label {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* ---- Browser root folders ---- */
        .tree-item.root {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            color: #9ca3af;
            margin-top: 4px;
        }

        .tree-item.root.active {
            color: #e5e7eb;
        }

        .tree-item.root.readonly .label {
            color: #6b7280;
        }

        .root-lock {
            margin-left: auto;
            font-size: 11px;
            opacity: 0.7;
        }

        .tree-item.readonly {
            opacity: 0.6;
        }

        #readOnlyIndicator {
            color: #d97706;
            font-size: 11px;
            margin-left: 8px;
        }

        .children {
            margin-left: 12px;
        }

        .children.collapsed {
            display: none;
        }

        .editor-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
            height: 100%;
        }

        .filebar {
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 12px;
            background: #1f1f1f;
            border-bottom: 1px solid #3f3f46;
        }

        #unsavedIndicator {
            color: #e2c08d;
            font-size: 12px;
            font-weight: bold;
            margin-left: 8px;
        }

        #editor {
            flex: 1;
            width: 100%;
            height: 100%;
            background: #1e1e1e;
        }

        .statusbar {
            height: 26px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            background: #007acc;
            color: white;
            font-size: 12px;
        }

        .status-message {
            flex: 1;
        }

        /* ---------------------------------------------------
           EDITOR ACTIONS / AGENT ORCHESTRATOR SIDEBAR
           --------------------------------------------------- */

        .agent-sidebar {
            width: 300px;
            min-width: 240px;
            background: #1f1f1f;
            border-left: 1px solid #3f3f46;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        .agent-section {
            padding: 10px;
            border-bottom: 1px solid #3f3f46;
        }

        .agent-section-title {
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 12px;
            color: #9aa2b1;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .editor-action-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
        }

        .editor-action-card {
            min-height: 66px;
            margin: 0 !important;
            padding: 9px 6px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 5px;
            background: #252526;
            border: 1px solid #303744;
            border-radius: 7px;
            color: #e6e8ee;
            font-size: 11px !important;
            transition: background 0.15s, border-color 0.15s, transform 0.15s;
        }

        .editor-action-card:hover:not(:disabled) {
            background: #2a2d2e;
            border-color: #0e639c;
            transform: translateY(-1px);
        }

        .editor-action-card:disabled {
            opacity: 0.48;
            cursor: not-allowed;
        }

        .editor-action-icon {
            color: #70b7ed;
            font-size: 17px;
            font-weight: bold;
            line-height: 1;
        }

        .agent-sidebar button {
            margin: 4px 2px;
            font-size: 12px;
        }

    </style>

    <!-- Monaco Loader CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js"></script>
</head>
<body>

<div class="topbar" data-pm-header>
    <div class="title">Project Manager</div>

    <div class="topbar-actions" id="pageActions">
        <button id="saveBtn" class="primary" type="button">Save</button>
        <button id="newFileBtn" type="button">+ File</button>
        <button id="newFolderBtn" type="button">+ Folder</button>
        <button id="renameBtn" type="button">Rename</button>
        <button id="deleteBtn" class="danger" type="button">Delete</button>
        <button id="refreshBtn" type="button">Refresh</button>
        <button id="agentCreateBtn" title="Scaffold workspace/agents/&lt;name&gt;/agent.json + agent.md">+ Agent</button>
        <button id="runAgentBtn" title="Open the dashboard runner for the selected workspace agent">Run Agent</button>
        <button id="pipelineBtn" title="Open the agent orchestrator on the dashboard">Orchestrator</button>
    </div>

    <div class="spacer"></div>
</div>

<div class="workspace">
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span>FOLDERS</span>
        </div>
        <div id="tree" class="tree">Loading...</div>
    </div>
    
    <div class="resize-handle" id="resizeHandle"></div>

    <div class="editor-area">
        <div class="filebar">
            <div>
                <span id="currentFile">No file selected</span>
                <span id="unsavedIndicator"></span>
            <span id="readOnlyIndicator"></span>
            </div>
            <div id="language">plaintext</div>
        </div>
        <div id="editor"></div>
    </div>

    <div id="agentPanel" class="agent-sidebar">
        <div class="agent-section">
            <div class="agent-section-title">Editor Actions</div>
            <div class="editor-action-grid" aria-label="Editor actions">
                <button class="editor-action-card" type="button" data-editor-action="saveBtn" title="Save current file">
                    <span class="editor-action-icon" aria-hidden="true">S</span><span>Save</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="newFileBtn" title="Create a file">
                    <span class="editor-action-icon" aria-hidden="true">+</span><span>New File</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="newFolderBtn" title="Create a folder">
                    <span class="editor-action-icon" aria-hidden="true">▣</span><span>New Folder</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="renameBtn" title="Rename selected item">
                    <span class="editor-action-icon" aria-hidden="true">✎</span><span>Rename</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="deleteBtn" title="Delete selected item">
                    <span class="editor-action-icon" aria-hidden="true">×</span><span>Delete</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="refreshBtn" title="Refresh the file tree">
                    <span class="editor-action-icon" aria-hidden="true">↻</span><span>Refresh</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="agentCreateBtn" title="Create a workspace agent">
                    <span class="editor-action-icon" aria-hidden="true">A+</span><span>New Agent</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="runAgentBtn" title="Open the dashboard agent runner">
                    <span class="editor-action-icon" aria-hidden="true">▶</span><span>Run Agent</span>
                </button>
                <button class="editor-action-card" type="button" data-editor-action="pipelineBtn" title="Open the dashboard orchestrator card">
                    <span class="editor-action-icon" aria-hidden="true">⇢</span><span>Orchestrator</span>
                </button>
            </div>
        </div>

    </div>
</div>

<div class="statusbar">
    <div id="statusMessage" class="status-message">Initializing...</div>
</div>

<script type="module" src="/static/js/main.js"></script>

</body>
</html>
```

---

<!-- ==== 23/125 : frontend/pages/home.html ==== -->

### frontend/pages/home.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manager</title>

    <style>
        * {
            box-sizing: border-box;
        }

        html, body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            font-family: Arial, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
        }

        .topbar {
            height: 52px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 12px;
            background: #252526;
            border-bottom: 1px solid #3f3f46;
        }

        .title {
            font-weight: bold;
            margin-right: 4px;
        }

        #projectName {
            color: #4fc3f7;
            margin-right: 12px;
            font-weight: bold;
        }

        .spacer {
            flex: 1;
        }

        /* Home for this page's own tools; empty on pages that have none. */
        .topbar-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        button {
            border: 1px solid #555;
            background: #333;
            color: #fff;
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
        }

        button:hover {
            background: #444;
        }

        button.primary {
            background: #0e639c;
            border-color: #1177bb;
        }

        button.danger {
            background: #7f1d1d;
        }

        .workspace {
            display: flex;
            height: calc(100vh - 78px);
            width: 100%;
        }

        .sidebar {
            width: 280px;
            min-width: 180px;
            background: #252526;
            border-right: 1px solid #3f3f46;
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 10px;
            border-bottom: 1px solid #3f3f46;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .resize-handle {
            width: 4px;
            cursor: col-resize;
            background: transparent;
            transition: background 0.2s;
        }

        .resize-handle:hover {
            background: #0e639c;
        }

        .tree {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }

        /* ---- Browser root folders ---- */
        .tree-item.root {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            color: #9ca3af;
            margin-top: 4px;
        }

        .tree-item.root.active {
            color: #e5e7eb;
        }

        .tree-item.root.readonly .label {
            color: #6b7280;
        }

        .root-lock {
            margin-left: auto;
            font-size: 11px;
            opacity: 0.7;
        }

        .tree-item.readonly {
            opacity: 0.6;
        }

        .tree-item {
            user-select: none;
            cursor: pointer;
            padding: 4px 6px;
            border-radius: 3px;
        }

        .tree-item:hover {
            background: #2a2d2e;
        }

        .tree-item.selected {
            background: #094771;
        }

        .tree-item.folder {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .tree-item.folder .toggle {
            display: inline-block;
            width: 12px;
            font-size: 11px;
            color: #bbb;
            text-align: center;
            flex-shrink: 0;
        }

        .tree-item.folder .label {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .children {
            margin-left: 12px;
        }

        .children.collapsed {
            display: none;
        }

        /* ---- Home landing panel (the editor lives on editor.html) ---- */
        .home-panel {
            flex: 1;
            min-width: 0;
            height: 100%;
            overflow-y: auto;
            padding: 40px 32px 48px;
            background: #1e1e1e;
        }

        .home-inner {
            max-width: 1080px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .home-title {
            margin: 0;
            font-size: 34px;
            font-weight: bold;
            letter-spacing: 1px;
            color: #ffffff;
        }

        .home-subtitle {
            margin: 8px 0 28px;
            font-size: 13px;
            color: #9ca3af;
            text-align: center;
        }

        .agent-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 14px;
            width: 100%;
        }

        .agent-card {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
            text-align: left;
            padding: 14px;
            background: #252526;
            border: 1px solid #3f3f46;
            border-left: 4px solid var(--agent-color, #4fc3f7);
            border-radius: 6px;
            cursor: pointer;
            color: #fff;
        }

        .agent-card:hover {
            background: color-mix(in srgb, var(--agent-color, #4fc3f7) 14%, #252526);
            border-color: var(--agent-color, #4fc3f7);
        }

        .agent-card:focus-visible {
            outline: 2px solid var(--agent-color, #4fc3f7);
            outline-offset: 2px;
        }

        .agent-card-head {
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
        }

        .agent-swatch {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
            background: var(--agent-color, #4fc3f7);
            box-shadow: 0 0 6px var(--agent-color, #4fc3f7);
        }

        .agent-card-name {
            font-weight: bold;
            font-size: 14px;
        }

        .agent-card-badges {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .agent-badge {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 6px;
            border-radius: 10px;
            border: 1px solid #4b4b4b;
            color: #cbd5e1;
        }

        .agent-badge.mode {
            border-color: var(--agent-color, #4fc3f7);
            color: var(--agent-color, #4fc3f7);
        }

        .agent-card-desc {
            margin: 0;
            font-size: 12px;
            line-height: 1.5;
            color: #b6b6b6;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .agent-cards-empty {
            grid-column: 1 / -1;
            color: #9ca3af;
            font-size: 13px;
            text-align: center;
            padding: 24px 0;
        }

        .statusbar {
            height: 26px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            background: #007acc;
            color: white;
            font-size: 12px;
        }

        .status-message {
            flex: 1;
        }
    </style>
</head>
<body>

<div class="topbar" data-pm-header>
    <div class="title">Project Manager</div>
    <span id="projectName">.</span>

    <!-- Home has no page-specific tools yet. Buttons that belong to
         this page go here so the nav keeps its place at the far right. -->
    <div class="topbar-actions" id="pageActions"></div>

    <div class="spacer"></div>
</div>


<div class="workspace">
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <span>FOLDERS</span>
        </div>

        <div id="tree" class="tree">Loading...</div>
    </div>

    <div class="resize-handle" id="resizeHandle"></div>

    <div class="home-panel">
        <div class="home-inner">
            <h1 class="home-title">Home</h1>
            <p class="home-subtitle">Choose an agent to start a conversation.</p>
            <div id="agentCards" class="agent-cards">Loading agents...</div>
        </div>
    </div>
</div>

<div class="statusbar">
    <div id="statusMessage" class="status-message">Initializing...</div>
</div>

<script type="module" src="/static/js/main.js"></script>

</body>
</html>
```

---

<!-- ==== 24/125 : frontend/pages/index.html ==== -->

### frontend/pages/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manager Dashboard</title>

    <style>
        * {
            box-sizing: border-box;
        }

        html, body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            font-family: Arial, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
        }

        .topbar {
            height: 48px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 12px;
            background: #252526;
            border-bottom: 1px solid #3f3f46;
        }

        .title {
            font-weight: bold;
            margin-right: 12px;
        }

        button {
            border: 1px solid #555;
            background: #333;
            color: #fff;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
        }

        button:hover {
            background: #444;
        }

        button.primary {
            background: #0e639c;
            border-color: #1177bb;
        }

        .container {
            padding: 24px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .actions {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }

        .card {
            background: #252526;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 20px;
        }

        .card h2 {
            margin-top: 0;
            margin-bottom: 12px;
            font-size: 18px;
        }

        .agent-controls {
            display: grid;
            gap: 10px;
            max-width: 760px;
        }

        .agent-controls select,
        .agent-controls textarea {
            width: 100%;
            padding: 9px;
            border: 1px solid #555;
            border-radius: 4px;
            background: #1e1e1e;
            color: #fff;
            font: inherit;
        }

        .agent-controls textarea {
            min-height: 90px;
            resize: vertical;
        }

        .agent-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .agent-description,
        .agent-status {
            color: #ccc;
            font-size: 14px;
        }

        .agent-reply {
            margin: 0;
            padding: 12px;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            background: #1e1e1e;
            color: #fff;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }

        .orchestrator-intro,
        .orchestrator-status {
            color: #ccc;
            font-size: 14px;
            line-height: 1.45;
        }

        .orchestrator-status {
            min-height: 1.3em;
        }

        .orchestrator-agents,
        .orchestrator-queue {
            max-height: 280px;
            overflow-y: auto;
            border: 1px solid #3f3f46;
            border-radius: 5px;
            padding: 8px;
            display: grid;
            gap: 6px;
            color: #ccc;
            font-size: 13px;
        }

        .orchestrator-agents .agent-option {
            display: flex;
            gap: 9px;
            align-items: center;
            min-height: 36px;
            padding: 6px 9px;
            border: 1px solid #343a46;
            border-radius: 5px;
            background: #20232b;
            cursor: pointer;
        }

        .orchestrator-agents .agent-option:hover {
            background: #292e39;
            border-color: #4b5563;
        }

        .orchestrator-agents input[type="checkbox"] {
            width: 16px;
            height: 16px;
            flex: 0 0 auto;
            margin: 0;
            accent-color: #0e8acb;
        }

        .orchestrator-queue .queue-item {
            display: flex;
            gap: 7px;
            align-items: center;
            min-height: 34px;
            padding: 4px;
        }

        .orchestrator-queue .qidx {
            min-width: 22px;
            color: #70b7ed;
        }

        .queue-agent-name {
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .orchestrator-queue button {
            padding: 3px 8px;
        }

        .orchestrator-field {
            display: grid;
            gap: 6px;
            color: #ccc;
            font-size: 14px;
        }

        .orchestrator-field select,
        .orchestrator-field textarea {
            width: 100%;
            padding: 9px;
            border: 1px solid #555;
            border-radius: 4px;
            background: #1e1e1e;
            color: #fff;
            font: inherit;
        }

        .orchestrator-field textarea {
            min-height: 110px;
            resize: vertical;
        }

        .orchestrator-results {
            display: grid;
            gap: 10px;
        }

        .orchestrator-result-item {
            padding: 12px;
            border: 1px solid #3f3f46;
            border-radius: 5px;
            background: #1e1e1e;
        }

        .orchestrator-result-item h3 {
            margin: 0 0 8px;
            font-size: 14px;
        }

        .orchestrator-result-item p {
            margin: 0;
            color: #ddd;
            line-height: 1.5;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }

        .tree-item {
            user-select: none;
            cursor: pointer;
            padding: 6px 8px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .tree-item.folder {
            cursor: pointer;
        }

        .tree-item.folder .toggle {
            display: inline-block;
            width: 12px;
            font-size: 11px;
            color: #bbb;
            text-align: center;
            flex-shrink: 0;
        }

        .tree-item:hover {
            background: #2a2d2e;
        }

        /* ---- Browser root folders ---- */
        .tree-item.root {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            color: #9ca3af;
            margin-top: 6px;
        }

        .tree-item.root.readonly .label {
            color: #6b7280;
        }

        .root-lock {
            font-size: 11px;
            opacity: 0.7;
        }

        .tree-item.readonly {
            opacity: 0.6;
        }

        .children {
            margin-left: 16px;
        }

        .children.collapsed {
            display: none;
        }

        .statusbar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 26px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            background: #007acc;
            color: white;
            font-size: 12px;
        }
    </style>
</head>
<body>

<div class="topbar">
    <div class="title">Project Manager Dashboard</div>
    <button class="primary" onclick="openEditor()">Editor</button>
    <button onclick="openEditorPopup()">Editor (Popup)</button>
    <button onclick="refreshProject()">Refresh</button>
</div>

<div class="container">
    <div class="actions">
        <button class="primary" onclick="openEditor()">Open Full Editor</button>
        <button onclick="openEditorPopup()">Launch Editor Window</button>
        <button onclick="submitCreateFilePrompt()">+ New File</button>
        <button onclick="submitCreateFolderPrompt()">+ New Folder</button>
    </div>

    <section class="card" aria-labelledby="workspaceAgentsHeading">
        <h2 id="workspaceAgentsHeading">Workspace AI Agents</h2>
        <div class="agent-controls">
            <label for="workspaceAgentSelect">Choose an agent from workspace/agents</label>
            <select id="workspaceAgentSelect" disabled>
                <option value="">Loading workspace agents...</option>
            </select>
            <div id="workspaceAgentDescription" class="agent-description" aria-live="polite"></div>
            <div class="agent-actions">
                <button id="openAgentsFolder" type="button">Open agents folder</button>
                <button id="openAgentPrompt" type="button" disabled>Open agent.md</button>
                <button id="openAgentConfig" type="button" disabled>Open agent.json</button>
            </div>
            <label for="workspaceAgentMessage">Message</label>
            <textarea id="workspaceAgentMessage" placeholder="Enter a message for the selected agent"></textarea>
            <div class="agent-actions">
                <button id="runWorkspaceAgent" class="primary" type="button" disabled>Run agent</button>
                <span id="workspaceAgentStatus" class="agent-status" role="status" aria-live="polite"></span>
            </div>
            <pre id="workspaceAgentReply" class="agent-reply" aria-live="polite" hidden></pre>
        </div>
    </section>

    <section class="card" id="orchestratorCard" aria-labelledby="orchestratorHeading">
        <h2 id="orchestratorHeading">Agent Orchestrator</h2>
        <div class="agent-controls">
            <p class="orchestrator-intro">
                Multi-agent orchestration is separate from the single-agent runner above.
                Select and order agents; each receives the original message and earlier agents' replies.
            </p>
            <div>
                <h3>Available agents</h3>
                <div id="orchestratorAgents" class="orchestrator-agents" aria-label="Available agents">
                    Loading agents...
                </div>
            </div>
            <div>
                <h3>Run order</h3>
                <div id="orchestratorQueue" class="orchestrator-queue" aria-label="Orchestrator run order">
                    Queue empty.
                </div>
                <div class="agent-actions">
                    <button id="orchestratorClearBtn" type="button">Clear selection</button>
                </div>
            </div>
            <label class="orchestrator-field" for="orchestratorModel">
                Model override
                <select id="orchestratorModel">
                    <option value="">Default agent models</option>
                </select>
            </label>
            <label class="orchestrator-field" for="orchestratorMessage">
                Message for the agent sequence
                <textarea id="orchestratorMessage" placeholder="Describe the idea or task for the selected agents"></textarea>
            </label>
            <div class="agent-actions">
                <button id="orchestratorRunBtn" class="primary" type="button">Run orchestrator</button>
                <span id="orchestratorStatus" class="orchestrator-status" role="status" aria-live="polite"></span>
            </div>
            <div id="orchestratorResult" class="orchestrator-results" aria-live="polite" hidden></div>
        </div>
    </section>

    <div class="card">
        <h2>Project Workspace</h2>
        <div id="projectTree">Loading files...</div>
    </div>
</div>

<div class="statusbar">
    <div id="statusMessage">Ready</div>
</div>

<script type="module">
import API from '/static/js/api.js';
import { initOrchestrator } from '/static/js/orchestrator.js';

let roots = {};
let workspaceAgents = [];
const requestedAgentId = new URLSearchParams(window.location.search).get('agent');
const openOrchestrator = new URLSearchParams(window.location.search).get('panel') === 'orchestrator';

const agentSelect = document.getElementById('workspaceAgentSelect');
const agentDescription = document.getElementById('workspaceAgentDescription');
const agentStatus = document.getElementById('workspaceAgentStatus');
const agentReply = document.getElementById('workspaceAgentReply');
const runAgentButton = document.getElementById('runWorkspaceAgent');
const openPromptButton = document.getElementById('openAgentPrompt');
const openConfigButton = document.getElementById('openAgentConfig');

function selectedWorkspaceAgent() {
  return workspaceAgents.find(agent => agent.id === agentSelect.value) || null;
}

function updateAgentSelection() {
  const agent = selectedWorkspaceAgent();
  const runnable = Boolean(agent && agent.complete);
  agentDescription.textContent = agent
    ? `${agent.description || 'No description'}${agent.complete ? '' : ' (definition is incomplete)' }`
    : '';
  runAgentButton.disabled = !runnable;
  openPromptButton.disabled = !agent || !agent.md_path;
  openConfigButton.disabled = !agent || !agent.json_path;
  agentStatus.textContent = agent && !agent.complete
    ? 'This agent needs both agent.json and agent.md before it can run.'
    : '';
  agentReply.hidden = true;
  agentReply.textContent = '';
}

async function loadWorkspaceAgents() {
  agentSelect.disabled = true;
  agentStatus.textContent = 'Loading workspace agents...';
  try {
    const data = await API.agents();
    workspaceAgents = (data.agents || []).filter(agent => agent.source === 'workspace');
    agentSelect.replaceChildren();
    if (!workspaceAgents.length) {
      agentSelect.add(new Option('No workspace agents found', ''));
      agentDescription.textContent = 'Create an agent under workspace/agents/ to run it here.';
      agentStatus.textContent = '';
      return;
    }
    agentSelect.add(new Option('Select a workspace agent', ''));
    for (const agent of workspaceAgents) {
      agentSelect.add(new Option(agent.name || agent.id, agent.id));
    }
    agentSelect.disabled = false;
    if (requestedAgentId && workspaceAgents.some(agent => agent.id === requestedAgentId)) {
      agentSelect.value = requestedAgentId;
    }
    agentStatus.textContent = '';
    updateAgentSelection();
  } catch (error) {
    agentSelect.replaceChildren(new Option('Could not load workspace agents', ''));
    agentStatus.textContent = `Error loading agents: ${error.message}`;
  }
}

function openAgentDefinition(kind) {
  const agent = selectedWorkspaceAgent();
  const path = agent && agent[`${kind}_path`];
  if (path) openEditor(`workspace/${path}`);
}

async function runWorkspaceAgent() {
  const agent = selectedWorkspaceAgent();
  const message = document.getElementById('workspaceAgentMessage').value.trim();
  if (!agent || !agent.complete || runAgentButton.disabled) return;
  if (!message) {
    agentStatus.textContent = 'Enter a message before running the agent.';
    return;
  }
  runAgentButton.disabled = true;
  agentStatus.textContent = `Running ${agent.name || agent.id}...`;
  agentReply.hidden = true;
  try {
    const result = await API.agentRun({ agent_id: agent.id, message });
    agentReply.textContent = result.reply || '(The agent returned an empty reply.)';
    agentReply.hidden = false;
    agentStatus.textContent = `Completed${result.model ? ` using ${result.model}` : ''}.`;
  } catch (error) {
    agentStatus.textContent = `Agent failed: ${error.message}`;
  } finally {
    runAgentButton.disabled = !agent.complete;
  }
}

agentSelect.addEventListener('change', updateAgentSelection);
document.getElementById('openAgentsFolder').addEventListener('click', () => openEditor('workspace/agents'));
openPromptButton.addEventListener('click', () => openAgentDefinition('md'));
openConfigButton.addEventListener('click', () => openAgentDefinition('json'));
runAgentButton.addEventListener('click', runWorkspaceAgent);
initOrchestrator();
if (openOrchestrator) {
  document.getElementById('orchestratorCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadProject() {
  setStatus('Loading project...');
  try {
    const data = await API.project();
    roots = {};
    for (const node of data.filesystem || []) {
      roots[node.name] = node.writable !== false;
    }
    renderTree(data.filesystem || []);
    setStatus('Project loaded');
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

function renderTree(items) {
  const container = document.getElementById('projectTree');
  container.innerHTML = '';
  renderItems(items, container, 0);
}

function renderItems(items, container, depth) {
  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'tree-item';
    if (item.type === 'directory') {
      div.classList.add('folder');
      div.dataset.path = item.path;
      const isRoot = depth === 0 && item.root;
      if (isRoot) {
        div.classList.add('root');
        if (item.writable === false) div.classList.add('readonly');
      }
      const toggle = document.createElement('span');
      toggle.className = 'toggle';
      toggle.textContent = '+';
      const label = document.createElement('span');
      label.textContent = (isRoot ? '🗂 ' : '📁 ') + item.name;
      label.style.flex = '1';
      label.style.marginLeft = '4px';
      div.appendChild(toggle);
      div.appendChild(label);
      if (isRoot && item.writable === false) {
        const lock = document.createElement('span');
        lock.className = 'root-lock';
        lock.textContent = '🔒';
        lock.title = 'Read-only';
        div.appendChild(lock);
      }
      div.onclick = (e) => {
        e.stopPropagation();
        toggleFolder(div);
      };
      container.appendChild(div);
      if (item.children && item.children.length) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'children collapsed';
        container.appendChild(childrenContainer);
        renderItems(item.children, childrenContainer, depth + 1);
      }
    } else {
      if (item.editable === false) {
        div.classList.add('readonly');
        div.title = 'Read-only';
      }
      const label = document.createElement('span');
      label.textContent = getFileIcon(item.name) + ' ' + item.name;
      div.appendChild(label);
      const btnGroup = document.createElement('div');
      const editBtn = document.createElement('button');
      editBtn.textContent = 'Edit';
      editBtn.onclick = (e) => { e.stopPropagation(); openEditor(item.path); };
      const popupBtn = document.createElement('button');
      popupBtn.textContent = 'Popup';
      popupBtn.style.marginLeft = '4px';
      popupBtn.onclick = (e) => { e.stopPropagation(); openEditorPopup(item.path); };
      btnGroup.appendChild(editBtn);
      btnGroup.appendChild(popupBtn);
      div.appendChild(btnGroup);
      container.appendChild(div);
    }
  });
}

function getFileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const icons = {
    py: '🐍',
    html: '🌐', htm: '🌐',
    css: '🎨',
    js: '🟨', mjs: '🟨', jsx: '🟨',
    ts: '🔷', tsx: '🔷',
    json: '📋',
    md: '📝',
    sql: '🗄️',
    xml: '🧾',
    sh: '⌨️', bat: '⌨️', ps1: '⌨️',
    yaml: '⚙️', yml: '⚙️', toml: '⚙️', ini: '⚙️', cfg: '⚙️', env: '⚙️',
    txt: '📄', csv: '📄'
  };
  return icons[ext] || '📄';
}

function toggleFolder(div) {
  const toggle = div.querySelector('.toggle');
  if (toggle) {
    toggle.classList.toggle('expanded');
    toggle.textContent = toggle.classList.contains('expanded') ? '−' : '+';
  }
  const children = div.nextElementSibling;
  if (children && children.classList.contains('children')) {
    children.classList.toggle('collapsed');
  }
}

async function submitCreateFilePrompt() {
  if (!roots[activeRoot()]) {
    alert(activeRoot() + ' is read-only.');
    return;
  }
  const path = prompt('Enter file path/name:', activeRoot() + '/');
  if (!path) return;
  if (!isWritablePath(path)) return;
  try {
    await API.fileCreate(path, '');
    await loadProject();
    openEditor(path);
  } catch (err) {
    alert(err.message);
  }
}

async function submitCreateFolderPrompt() {
  if (!roots[activeRoot()]) {
    alert(activeRoot() + ' is read-only.');
    return;
  }
  const path = prompt('Enter folder path:', activeRoot() + '/');
  if (!path) return;
  if (!isWritablePath(path)) return;
  try {
    await API.directoryCreate(path);
    await loadProject();
  } catch (err) {
    alert(err.message);
  }
}

function activeRoot() {
  return Object.keys(roots)[0] ?? '';
}

function isWritablePath(path) {
  const head = String(path).split('/')[0];
  if (head in roots && roots[head] === false) {
    alert(head + ' is read-only.');
    return false;
  }
  return true;
}

function openEditor(filePath) {
  let url = '/editor';
  if (filePath) url += '?path=' + encodeURIComponent(filePath);
  const head = filePath ? filePath.split('/')[0] : '';
  if (head) url += '&root=' + encodeURIComponent(head);
  window.location.href = url;
}

function openEditorPopup(filePath) {
  let url = '/editor';
  if (filePath) url += '?path=' + encodeURIComponent(filePath);
  const head = filePath ? filePath.split('/')[0] : '';
  if (head) url += '&root=' + encodeURIComponent(head);
  const width = 1200; const height = 800;
  const left = (window.screen.width - width) / 2;
  const top = (window.screen.height - height) / 2;
  window.open(url, 'ProjectManagerEditorPopup', `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no`);
}

function refreshProject() {
  loadProject();
  loadWorkspaceAgents();
}

function setStatus(msg) {
  document.getElementById('statusMessage').textContent = msg;
}

window.openEditor = openEditor;
window.openEditorPopup = openEditorPopup;
window.refreshProject = refreshProject;
window.submitCreateFilePrompt = submitCreateFilePrompt;
window.submitCreateFolderPrompt = submitCreateFolderPrompt;

loadProject();
loadWorkspaceAgents();
</script>

</body>
</html>
```

---

<!-- ==== 25/125 : frontend/pages/prompt-builder.html ==== -->

### frontend/pages/prompt-builder.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Prompt Builder</title>
<link rel="stylesheet" href="/static/css/builder.css">

<!-- Page furniture only. Everything the builder itself draws is scoped
     under .pb in builder.css, so none of these can leak into /test. -->
<style>
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#101318;color:#e8edf2}
header{padding:18px 24px;background:#181d24;border-bottom:1px solid #303741}
header h1{margin:0 0 5px;font-size:22px}
header p{margin:0;color:#9ca8b5;max-width:90ch}
#pbHost{padding:20px 16px 48px}
</style>
</head>

<!-- This page used to be self-contained: inline CSS, inline markup, an
     inline script. It is now a shell around static/js/builder.js, because
     the same builder runs as the right-hand panel on /test and a second
     copy of the markup, the styles and 1000 lines of logic would be two
     copies to keep in step. The header below is all that is genuinely
     page-specific. -->

<body>
<header>
<h1>Agent Prompt Builder</h1>
<p>Create reusable prompt parts in categories you can add or remove, select them, and assemble an editable agent.md — published straight into the isolated test environment, never into the managed workspace.</p>
</header>

<div class="pb" id="pbHost"></div>

<script type="module">
import Builder from '/static/js/builder.js';

/* No onShowEvidence here: there is no dashboard on this page, so the
   button would have nothing to point at. It stays disabled. */
Builder.mount(document.getElementById('pbHost'));
</script>
</body>
</html>
```

---

<!-- ==== 26/125 : frontend/pages/testing.html ==== -->

### frontend/pages/testing.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Header Test Dashboard</title>

<!-- The evidence log is read by a person looking at a verdict, and a
     page that has to be reassembled from a stylesheet and a module to
     show four PASS/FAIL rows is a page that breaks in the one moment it
     is needed. So the styles, the fetch calls and the nav stay inline.

     The one exception is the sidebar tree, which is the shared
     js/tree.js module. It is not reimplemented here because a second
     copy of the tree would be a second copy of the expand state, the
     folder switcher and the editor hand-off, and the dashboard would
     drift from the editor the first time any of them changed.

     Three modules are imported now, and all three earn it: js/tree.js
     (the tree), js/panels.js (resize and collapse) and js/report.js
     (the saved report's text). The evidence log's own fetches stay inline. -->

<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#101318;color:#e8edf2;display:flex;flex-direction:column;height:100vh;overflow:hidden}
body.panel-dragging{cursor:col-resize;user-select:none}
body.panel-dragging *{cursor:col-resize !important}
header{padding:10px 24px;background:#181d24;border-bottom:1px solid #303741;display:flex;align-items:center;gap:18px;flex-wrap:wrap;flex-shrink:0}
nav{display:flex;gap:6px;margin-left:auto;flex-shrink:0;align-self:center;flex-wrap:wrap}
nav a{display:inline-flex;align-items:center;padding:6px 12px;border-radius:6px;border:1px solid #45474d;background:#2f3136;color:#e5e7eb;font-size:13px;font-weight:500;text-decoration:none;white-space:nowrap}
nav a:hover{background:#3a3d44;border-color:#565a61;color:#fff}
nav a[aria-current=page]{background:#0e639c;border-color:#1177bb;color:#fff}

.workspace{display:flex;flex:1;min-height:0}

/* Handles: 4px so they are findable but not a wall. Double-click
   resets the panel to its default width; arrows work when focused. */
.resize-handle{width:8px;flex:0 0 auto;cursor:col-resize;background:#20262e;transition:background .2s}
.resize-handle:hover,.resize-handle:focus-visible{background:#0e639c;outline:none}
.resize-handle[hidden]{display:none}

.sidebar{width:260px;min-width:180px;flex-shrink:0;background:#181d24;border-right:1px solid #303741;display:flex;flex-direction:column;overflow:hidden}
.sidebar-header{padding:10px;border-bottom:1px solid #303741;font-weight:bold;color:#8fa0b3;font-size:12px;letter-spacing:.06em;text-transform:uppercase}

/* The right panel keeps test controls close to the evidence they operate on. */
.test-panel{width:360px;min-width:300px;flex-shrink:0;background:#181d24;border-left:1px solid #303741;display:flex;flex-direction:column;overflow:hidden}
.test-panel-header{padding:10px;border-bottom:1px solid #303741;font-weight:bold;color:#8fa0b3;font-size:12px;letter-spacing:.06em;text-transform:uppercase;flex-shrink:0}
.test-tools-content{flex:1;overflow-y:auto;padding:12px}
.test-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.test-func-card{min-height:76px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:10px 6px;border:1px solid #39424d;border-radius:7px;background:#20262e;color:#dfe6ee;font-size:12px;text-align:center}
.test-func-icon{color:#70b7ed;font-size:19px;font-weight:bold;line-height:1}
.test-func-card:hover:not(:disabled){background:#293341;border-color:#0e639c}
.test-func-card:disabled{background:#171c22;border-color:#2a3038;color:#687382;opacity:.6;cursor:not-allowed}
.test-func-card:disabled .test-func-icon{color:#687382}
.test-panel-note{margin:14px 2px 0;color:#7f8b99;font-size:12px;line-height:1.5}

.tree{flex:1;overflow-y:auto;padding:8px}
.tree-item{user-select:none;cursor:pointer;padding:4px 6px;border-radius:3px}
.tree-item:hover{background:#20262e}
.tree-item.selected{background:#094771}
.tree-item.folder{display:flex;align-items:center;gap:4px}
.tree-item.folder .toggle{display:inline-block;width:12px;font-size:11px;color:#8fa0b3;text-align:center;flex-shrink:0}
.tree-item.folder .label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tree-item.root{font-weight:bold;text-transform:uppercase;font-size:11px;letter-spacing:.5px;color:#9ca3af;margin-top:4px}
.tree-item.root.active{color:#e5e7eb}
.tree-item.root.readonly .label{color:#6b7280}
.tree-item.readonly{opacity:.6}
.root-lock{margin-left:auto;font-size:11px;opacity:.7}
.children{margin-left:12px}
.children.collapsed{display:none}

main{flex:1;min-width:0;overflow-y:auto;padding:40px 32px 48px;display:grid;gap:20px;align-content:start}

/* The title sits with the content it describes rather than in the
   header, matching home.html. home.html centres the heading by
   shrink-wrapping it in a flex column; main is a grid whose items
   span the full width, so the wrapper centres the text instead. */
.page-intro{text-align:center}
.page-intro h1{margin:0;font-size:34px;font-weight:bold;letter-spacing:1px;color:#fff}
.page-intro p{margin:8px 0 8px;font-size:13px;color:#9ca8b5;line-height:1.5}
.card{background:#151a20;border:1px solid #303741;border-radius:8px;padding:16px}
h2{margin:0 0 12px;font-size:16px;color:#dfe6ee;border-bottom:1px solid #303741;padding-bottom:8px;display:flex;align-items:center;gap:10px}
h2 .spacer{flex:1}
button{border:0;border-radius:6px;padding:10px 14px;cursor:pointer;background:#4c8bf5;color:#fff;font-size:14px;font-family:inherit}
button.secondary{background:#303944}
button.danger{background:#9f303b}
button.tiny{padding:4px 10px;font-size:12px}
button:disabled{opacity:.45;cursor:not-allowed}
button:hover:not(:disabled){opacity:.92}
select,input{background:#0d1116;color:#edf2f7;border:1px solid #39424d;border-radius:6px;padding:9px;font-family:inherit;font-size:14px;min-width:0}
.toolbar{display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap}
.field{display:flex;flex-direction:column;gap:5px;min-width:180px}
.field span{font-size:12px;color:#8fa0b3;letter-spacing:.04em}
.status{margin-top:14px;padding:10px;border-radius:6px;background:#1a2129;color:#aeb9c5;font-size:13px;white-space:pre-wrap;line-height:1.5}
.status.error{color:#ff9b9b}
.status.ok{color:#8fe3a6}
.status.warn{color:#f5c96b}
.status[hidden]{display:none}

/* Summary bar: the one-glance answer before any reading. */
.summary{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.summary .counts{font-size:26px;font-weight:600}
.summary .meta{color:#9ca8b5;font-size:13px;line-height:1.6}
.badge{display:inline-block;padding:3px 11px;border-radius:9px;font-size:12px;font-weight:600;letter-spacing:.04em}
.badge.pass{background:#123a24;color:#8fe3a6;border:1px solid #2a6b45}
.badge.fail{background:#3a1620;color:#ff9b9b;border:1px solid #6b3341}
.badge.idle{background:#1f252d;color:#8fa0b3;border:1px solid #39424d}

/* One card per header test. The verdict is the heading, the reason is
   the summary line, and the transcript is below it - a PASS with no
   transcript in reach is a claim, not a result. */
.result{border-left:3px solid #39424d}
.result.pass{border-left-color:#2a6b45}
.result.fail{border-left-color:#6b3341}
.result h3{margin:0;font-size:15px;color:#dfe6ee;text-transform:capitalize}
.result .reason{margin:6px 0 12px;color:#aeb9c5;font-size:13px;line-height:1.5}
.turn{margin:0 0 10px}
.turn:last-child{margin-bottom:0}
.turn .label{font-size:11px;color:#6f7d8c;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}
.turn pre{margin:0;padding:10px;background:#0d1116;border:1px solid #262d36;border-radius:6px;color:#cbd5e1;font-family:Consolas,Menlo,monospace;font-size:12.5px;white-space:pre-wrap;word-break:break-word;max-height:340px;overflow:auto}
.turn.prompt pre{color:#9fb3c8}
details{margin-top:10px}
summary{cursor:pointer;font-size:12.5px;color:#8fa0b3;padding:4px 0}
summary:hover{color:#cbd5e1}
.empty{color:#5c6774;font-size:13px;font-style:italic;line-height:1.6}
.empty code{font-style:normal;background:#0d1116;padding:2px 6px;border-radius:5px;border:1px solid #39424d}
.results{display:grid;gap:12px}
</style>
</head>

<body>
<header>
  <nav aria-label="Main">
    <a href="/">Home</a>
    <a href="/editor">Editor</a>
    <a href="/chat">Chat</a>
    <a href="/prompt-builder" target="_blank" rel="noopener">Prompt Builder</a>
    <a href="/test" aria-current="page">Test</a>
  </nav>
  <!-- The builder remains available as a separate page; this dashboard
       keeps only its own test tools in the right-hand panel. -->
</header>

<div class="workspace" id="workspace">
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">Folders</div>
    <div id="tree" class="tree">Loading...</div>
  </div>

  <div class="resize-handle" id="handleLeft" role="separator" aria-orientation="vertical" tabindex="0"
       aria-label="Resize or collapse folders panel"
       title="Drag to resize; drag to the edge to collapse or back to reopen. Double-click to reset. Arrow keys resize."></div>

  <main id="centrePanel">

    <div class="page-intro">
      <h1>&#129514; Agent Header Test Dashboard</h1>
      <p>Four questions, one per header of an agent's markdown, asked of the running
         agent. The verdict comes from its own reply, so this shows what the model
         received - not what the file says.</p>
    </div>

    <div class="card">
      <h2>Run the header tests</h2>
      <div class="toolbar">
        <label class="field">
          <span>Test agent</span>
          <select id="agent_select" disabled></select>
        </label>
        <label class="field">
          <span>Model</span>
          <select id="model_select" disabled>
            <option value="">(the agent's own model)</option>
          </select>
        </label>
        <button id="run_btn" type="button" disabled>Run tests</button>
        <button id="delete_agent_btn" class="danger" type="button" disabled>Delete test agent</button>
        <button id="refresh_btn" class="secondary" type="button">Refresh</button>
      </div>
      <div id="run_status" class="status" hidden></div>
    </div>

    <div class="card" id="lastRunCard">
      <h2>Last run
        <span class="spacer"></span>
        <button id="clear_btn" class="secondary tiny" type="button" disabled
                title="Empty this page. The saved results file is not touched - Refresh brings the run back.">Clear</button>
        <button id="save_btn" class="secondary tiny" type="button" disabled
                title="Write the report to a timestamped text file in the test environment, then offer it to your browser.">Save report</button>
      </h2>
      <div id="summary" class="summary">
        <span class="badge idle">NO RESULTS</span>
        <span class="empty">Loading evidence log&hellip;</span>
      </div>
    </div>

    <div class="card">
      <h2>Evidence</h2>
      <div id="results" class="results">
        <div class="empty">Loading evidence log&hellip;</div>
      </div>
    </div>

  </main>

  <div class="resize-handle" id="handleRight" role="separator" aria-orientation="vertical" tabindex="0"
       aria-label="Resize or collapse agent test tools panel"
       title="Drag to resize; drag to the edge to collapse or back to reopen. Double-click to reset. Arrow keys resize."></div>

  <aside class="test-panel" id="testToolsPanel" aria-label="Agent test tools">
    <div class="test-panel-header">Agent Test Tools</div>
    <div class="test-tools-content">
      <div class="test-grid" aria-label="Agent test actions">
        <button class="test-func-card" type="button" data-dashboard-action="run_btn">
          <span class="test-func-icon" aria-hidden="true">▶</span>
          <span>Run Test Suite</span>
        </button>
        <button id="copy_agent_btn" class="test-func-card" type="button" disabled
                title="Copy the selected test agent into workspace/agents/">
          <span class="test-func-icon" aria-hidden="true">＋</span>
          <span>Add Agent to Workspace</span>
        </button>
        <button class="test-func-card" type="button" disabled title="Debug Agent is not available yet">
          <span class="test-func-icon" aria-hidden="true">⌕</span>
          <span>Debug Agent</span>
        </button>
        <button class="test-func-card" type="button" disabled title="Prompt Inspector is not available yet">
          <span class="test-func-icon" aria-hidden="true">&gt;_</span>
          <span>Prompt Inspector</span>
        </button>
        <button class="test-func-card" type="button" disabled title="Output Evaluator is not available yet">
          <span class="test-func-icon" aria-hidden="true">✓</span>
          <span>Output Evaluator</span>
        </button>
        <button class="test-func-card" type="button" disabled title="Benchmarking is not available yet">
          <span class="test-func-icon" aria-hidden="true">◷</span>
          <span>Benchmark</span>
        </button>
        <button class="test-func-card" type="button" disabled title="API logs are not available yet">
          <span class="test-func-icon" aria-hidden="true">≡</span>
          <span>API Logs</span>
        </button>
        <button class="test-func-card" type="button" data-dashboard-action="refresh_btn">
          <span class="test-func-icon" aria-hidden="true">↻</span>
          <span>Refresh Dashboard</span>
        </button>
        <button class="test-func-card" type="button" data-dashboard-action="clear_btn" disabled>
          <span class="test-func-icon" aria-hidden="true">×</span>
          <span>Clear Results</span>
        </button>
        <button class="test-func-card" type="button" data-dashboard-action="save_btn" disabled>
          <span class="test-func-icon" aria-hidden="true">↓</span>
          <span>Save Report</span>
        </button>
        <button class="test-func-card" type="button" disabled title="Browse saved reports from the Folders panel">
          <span class="test-func-icon" aria-hidden="true">▤</span>
          <span>Browse Reports</span>
        </button>
      </div>
      <div id="workspace_agent_status" class="status" hidden></div>
      <p class="test-panel-note">Unavailable tools are dimmed. Saved reports can be opened from the Folders panel.</p>
    </div>
  </aside>
</div>

<script type="module">
import Tree from "/static/js/tree.js";
import Panels from "/static/js/panels.js";
import { buildReportText, reportFileName } from "/static/js/report.js";

// ============================================================
// HTTP
// ============================================================

/* The API client module is deliberately not imported for the dashboard's
   own calls: this page has to keep working if api.js changes shape, and it
   makes four. Tree pulls it in as a dependency, but nothing below uses
   it. The status code rides along on the error so "nothing
   published yet" (404) can be told from "the server is down" (0) without
   matching on message text. */
async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = '';
    try {
      detail = (await res.json()).detail || '';
    } catch (e) {
      detail = '';
    }
    const error = new Error(detail || `Request failed: ${res.status}`);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

const $ = (id) => document.getElementById(id);

function setStatus(message, kind) {
  const el = $("run_status");
  if (!message) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

function setPanelStatus(message, kind) {
  const el = $("workspace_agent_status");
  el.hidden = !message;
  el.textContent = message || "";
  el.className = "status" + (kind ? " " + kind : "");
}

// ============================================================
// REPORT STATE
// ============================================================

/* The report is held here, not only in the DOM. Clear and Save both need
   to know whether there is one and what it says, and re-reading it from
   the rendered rows would mean parsing text back into data. */
let currentReport = null;

function setReportButtonsEnabled(hasReport) {
  $("clear_btn").disabled = !hasReport;
  $("save_btn").disabled = !hasReport;
  syncDashboardActions();
}

function syncDashboardActions() {
  document.querySelectorAll("[data-dashboard-action]").forEach((button) => {
    const source = $(button.dataset.dashboardAction);
    if (source) button.disabled = source.disabled;
  });
}

function syncAgentActions() {
  const hasSelection = Boolean($("agent_select").value);
  $("run_btn").disabled = !hasSelection || running || deletingAgent;
  $("delete_agent_btn").disabled = !hasSelection || running || deletingAgent;
  $("copy_agent_btn").disabled = !hasSelection || copyingAgent;
  syncDashboardActions();
}

// ============================================================
// RENDERING
// ============================================================

const HEADERS = ["role", "user", "purpose", "hallucinations"];

function badge(passed) {
  const el = document.createElement("span");
  el.className = "badge " + (passed ? "pass" : "fail");
  el.textContent = passed ? "PASS" : "FAIL";
  return el;
}

function turn(label, text, extraClass) {
  const box = document.createElement("div");
  box.className = "turn" + (extraClass ? " " + extraClass : "");

  const caption = document.createElement("div");
  caption.className = "label";
  caption.textContent = label;

  const body = document.createElement("pre");
  body.textContent = (text || "").trim() || "(empty)";

  box.append(caption, body);
  return box;
}

function renderRow(row) {
  const card = document.createElement("div");
  card.className = "card result " + (row.status === "PASS" ? "pass" : "fail");

  const head = document.createElement("h3");
  head.textContent = row.section || "unknown";
  head.append(badge(row.status === "PASS"));

  const reason = document.createElement("p");
  reason.className = "reason";
  reason.textContent = row.reason || "";

  card.append(head, reason, turn("Prompt sent", row.prompt, "prompt"));

  /* A model reply is a few hundred characters normally and a few
     thousand when it narrates a tool loop, so the transcript starts
     collapsed and is there for anyone who needs to check the verdict
     against what was actually said. */
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Agent reply (" + (row.response || "").length + " characters)";
  details.append(summary, turn("Reply", row.response, "reply"));
  card.appendChild(details);

  return card;
}

function renderSummary(summary) {
  const box = $("summary");
  box.innerHTML = "";

  if (!summary || typeof summary.total !== "number") {
    const idle = document.createElement("span");
    idle.className = "badge idle";
    idle.textContent = "NO RESULTS";
    const note = document.createElement("span");
    note.className = "empty";
    note.textContent = "Run the suite, or publish an agent first.";
    box.append(idle, note);
    return;
  }

  const overall = document.createElement("span");
  overall.className = "badge " + (summary.failed ? "fail" : "pass");
  overall.textContent = summary.failed ? "FAIL" : "PASS";

  const counts = document.createElement("span");
  counts.className = "counts";
  counts.textContent = summary.passed + " / " + summary.total + " passed";

  const meta = document.createElement("span");
  meta.className = "meta";
  const when = summary.ran_at ? new Date(summary.ran_at) : null;
  meta.textContent = [
    summary.agent_id ? "agent: " + summary.agent_id : null,
    summary.model ? "model: " + summary.model : null,
    when && !isNaN(when) ? "ran: " + when.toLocaleString() : null,
  ].filter(Boolean).join("  ·  ");

  box.append(overall, counts, meta);
}

function renderReport(report) {
  currentReport = report || null;
  setReportButtonsEnabled(Boolean(currentReport));
  renderSummary(report && report.summary);

  const host = $("results");
  host.innerHTML = "";

  const rows = (report && report.results) || [];
  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No evidence yet. Publish an agent from the Prompt "
      + "Builder, then press Run tests.";
    host.appendChild(empty);
    return;
  }

  /* The report is ordered by the runner; the four headers are rendered
     in suite order regardless, so a partial report still reads as the
     four known questions. */
  for (const name of HEADERS) {
    const row = rows.find((r) => r.section === name);
    if (row) host.appendChild(renderRow(row));
  }
  for (const row of rows) {
    if (!HEADERS.includes(row.section)) host.appendChild(renderRow(row));
  }
}

function fillSelect(select, items, value, keepFirst) {
  select.innerHTML = "";
  if (keepFirst) {
    const first = document.createElement("option");
    first.value = "";
    first.textContent = keepFirst;
    select.appendChild(first);
  }
  for (const item of items) {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
    select.appendChild(option);
  }
  if (value) select.value = value;
}

// ============================================================
// DATA
// ============================================================

async function loadAgents() {
  const data = await api("/api/test/agents");
  const agents = data.agents || [];
  const wanted = new URLSearchParams(location.search).get("agent");

  fillSelect(
    $("agent_select"),
    agents.map((a) => {
      const id = a.folder || a.id;
      return { value: id, label: a.name + "  (" + id + ")" };
    }),
    wanted && agents.some((a) => (a.folder || a.id) === wanted) ? wanted : null,
    agents.length ? null : "no published test agents"
  );
  $("agent_select").disabled = !agents.length;
  syncAgentActions();
  return agents;
}

async function loadModels() {
  const data = await api("/api/models");
  fillSelect(
    $("model_select"),
    (data.models || []).map((m) => ({ value: m.id, label: m.name || m.id })),
    null,
    "(the agent's own model)"
  );
  $("model_select").disabled = false;
}

async function loadResults() {
  try {
    renderReport(await api("/api/test/results"));
  } catch (error) {
    /* 404 is the ordinary first visit: no run has happened in this
       checkout yet, which is an empty dashboard rather than an error. */
    if (error.status === 404) {
      renderReport(null);
      return;
    }
    renderReport(null);
    setStatus("Cannot read the evidence log: " + error.message, "error");
  }
}

// ============================================================
// FILE TREE
// ============================================================

/* Only the test environment, because only the test environment is what
   this page has verdicts about. Home omits the same root for the same
   reason, and the editor keeps both. */
const TEST_ROOT = "test_environment";

/* The dashboard never edits a file, so a click opens one in the editor.
   The window is named so a second click lands in the same tab instead of
   stacking popups, and sized and centred here rather than left to the
   default 1x1 corner placement. */
const EDITOR_WINDOW = "header_test_file";

const EDITOR_FEATURES = [
  "popup=yes",
  "width=1100",
  "height=780",
  "left=" + Math.round((screen.availWidth - 1100) / 2),
  "top=" + Math.round((screen.availHeight - 780) / 2),
].join(",");

Tree.onFileSelect = (path) => {
  window.open(
    "/editor?path=" + encodeURIComponent(path)
      + "&root=" + encodeURIComponent(TEST_ROOT),
    EDITOR_WINDOW,
    EDITOR_FEATURES
  );
};

async function loadTree() {
  try {
    await Tree.load([TEST_ROOT]);
  } catch (error) {
    /* A blank sidebar reads as an empty test environment, which is a
       different and wrong answer, so say so in place. */
    const host = document.getElementById("tree");
    host.textContent = "Cannot list " + TEST_ROOT + ": " + error.message;
  }
}

// ============================================================
// ACTIONS
// ============================================================

let running = false;
let deletingAgent = false;
let copyingAgent = false;

async function deleteSelectedAgent() {
  const agentId = $("agent_select").value;
  if (!agentId || running || deletingAgent) return;
  if (!confirm(`Delete test agent '${agentId}' from the test environment? This cannot be undone.`)) return;

  deletingAgent = true;
  syncAgentActions();
  setStatus(`Deleting test agent '${agentId}'…`, "");
  let deleted = false;
  try {
    await api(`/api/test/agents/${encodeURIComponent(agentId)}`, {
      method: "DELETE",
    });
    deleted = true;
    $("agent_select").value = "";
    const query = new URLSearchParams(location.search);
    if (query.get("agent") === agentId) {
      query.delete("agent");
      const suffix = query.toString();
      history.replaceState(null, "", location.pathname + (suffix ? `?${suffix}` : ""));
    }
    await loadAgents();
    await loadTree();
    setStatus(`Deleted test agent '${agentId}'.`, "ok");
  } catch (error) {
    const message = deleted
      ? `Deleted test agent '${agentId}', but could not refresh the dashboard: ${error.message}`
      : `Could not delete test agent '${agentId}': ${error.message}`;
    setStatus(message, "error");
  } finally {
    deletingAgent = false;
    syncAgentActions();
  }
}

async function copySelectedAgentToWorkspace() {
  const agentId = $("agent_select").value;
  if (!agentId || copyingAgent) return;

  const workspaceAgentId = prompt(
    "Workspace agent id / folder name:",
    agentId
  );
  if (workspaceAgentId === null) return;
  const targetId = workspaceAgentId.trim();
  if (!/^[A-Za-z0-9_-]+$/.test(targetId)) {
    setPanelStatus(
      "Use only letters, numbers, underscore or dash for the workspace agent id.",
      "error"
    );
    return;
  }

  copyingAgent = true;
  syncAgentActions();
  setPanelStatus(`Adding '${agentId}' as '${targetId}' to workspace/agents/…`, "");
  try {
    const result = await api(
      `/api/test/agents/${encodeURIComponent(agentId)}/workspace`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: targetId }),
      }
    );
    setPanelStatus(`Added '${result.source_agent_id}' as '${result.agent_id}' at ${result.path}.`, "ok");
  } catch (error) {
    setPanelStatus(`Could not add '${agentId}' to the workspace: ${error.message}`, "error");
  } finally {
    copyingAgent = false;
    syncAgentActions();
  }
}

async function runTests() {
  if (running) return;

  const agentId = $("agent_select").value;
  if (!agentId) {
    setStatus("Pick a test agent first.", "warn");
    return;
  }

  running = true;
  $("run_btn").disabled = true;
  $("run_btn").textContent = "Running…";
  $("agent_select").disabled = true;
  syncAgentActions();
  setStatus(
    "Asking the agent four questions. Each one is a full model turn, so "
    + "this takes a moment - a minute or two on a local model.",
    ""
  );

  try {
    const model = $("model_select").value || null;
    const report = await api("/api/test/run_header_tests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent_id: agentId, model })
    });
    renderReport(report);
    const summary = report.summary || {};
    setStatus(
      (summary.passed || 0) + " of " + (summary.total || 0)
      + " header tests passed.",
      summary.failed ? "warn" : "ok"
    );
  } catch (error) {
    setStatus("The run failed: " + error.message, "error");
  } finally {
    running = false;
    $("run_btn").textContent = "Run tests";
    $("agent_select").disabled = false;
    syncAgentActions();
  }
}

async function refresh() {
  try {
    await loadAgents();
    await loadResults();
    setStatus("Refreshed from the test environment.", "ok");
  } catch (error) {
    setStatus("Cannot reach the Project Manager: " + error.message, "error");
  }
  /* After the refresh button rather than inside refresh(): a run writes
     test_results.json into the tree, so this is how a just-finished run
     becomes visible without a reload. The tree reports its own failure
     in its own pane and must not take the evidence pane down with it. */
  await loadTree();
}

// ============================================================
// CLEAR
// ============================================================

/* Deliberately destructive to nothing. Emptying the page is a way of
   re-reading the report, not of disposing of it: the run is still on
   disk, and Refresh brings it straight back. Deleting the results file
   would make this button the only place evidence could be lost by
   accident, which is a poor trade for a control that sits next to the
   verdict. */
function clearReport() {
  renderReport(null);

  fillSelect($("agent_select"), [], null, "choose an agent");
  $("agent_select").disabled = true;
  $("run_btn").disabled = true;
  fillSelect($("model_select"), [], null, "(the agent's own model)");
  $("model_select").disabled = false;

  /* Drop ?agent= too, or the next Refresh silently re-selects the agent
     that was just cleared. */
  history.replaceState(null, "", location.pathname);

  setStatus(
    "Cleared. Nothing was deleted - press Refresh to read the last run again.",
    ""
  );
}

// ============================================================
// SAVE
// ============================================================

/* Where a saved report lands, under the test root so it shows up in the
   tree on the left and opens from there like any other file. */
const REPORT_DIR = "test_environment/output";

/* One press, two destinations, one text. Both copies come from the same
   string, so the file in the project and the file the browser writes
   cannot differ - which a server-side export re-derived from the JSON
   could not promise. */
async function saveReport() {
  if (!currentReport) return;

  const text = buildReportText(currentReport);
  const file = reportFileName(currentReport.summary || {});
  const path = REPORT_DIR + "/" + file;

  $("save_btn").disabled = true;
  syncDashboardActions();

  /* The project copy first, in its own try: a refused write must not
     stop the user getting the report at all. */
  let wrote = false;
  let problem = "";
  try {
    await api("/api/file/write?path=" + encodeURIComponent(path), {
      method: "PUT",
      headers: { "Content-Type": "text/plain" },
      body: text,
    });
    wrote = true;
  } catch (error) {
    problem = "\nNot saved to the project: " + error.message;
  }

  /* Then the browser's own Save As. Appended before the click because a
     detached anchor's activation is inconsistent between browsers, and
     revoked immediately after so the blob does not outlive it. */
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = file;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);

  /* The new file is in the tree now, so the left pane is showing a stale
     listing until this runs. */
  if (wrote) await loadTree();

  setReportButtonsEnabled(Boolean(currentReport));

  setStatus(
    (wrote ? "Saved " + path + "." : "Could not save into the project.")
    + "\nYour browser was offered " + file + " as well." + problem,
    wrote ? "ok" : "warn"
  );
}

// ============================================================
// PANELS
// ============================================================

const panels = Panels.init({
  container: $("workspace"),
  left: {
    element: $("sidebar"),
    panel: { min: 180, max: 520, default: 260 },
  },
  centre: { element: $("centrePanel") },
  right: {
    element: $("testToolsPanel"),
    panel: { min: 300, max: 520, default: 360 },
  },
  handleLeft: $("handleLeft"),
  handleRight: $("handleRight"),
  storageKey: "testDashboard",
});
panels.show("centre");

// ============================================================
// WIRING
// ============================================================

$("run_btn").addEventListener("click", runTests);
$("delete_agent_btn").addEventListener("click", deleteSelectedAgent);
$("copy_agent_btn").addEventListener("click", copySelectedAgentToWorkspace);
$("agent_select").addEventListener("change", () => {
  setPanelStatus("", "");
  syncAgentActions();
});
$("refresh_btn").addEventListener("click", refresh);
$("clear_btn").addEventListener("click", clearReport);
$("save_btn").addEventListener("click", saveReport);
document.querySelectorAll("[data-dashboard-action]").forEach((button) => {
  button.addEventListener("click", () => {
    $(button.dataset.dashboardAction)?.click();
  });
});
syncDashboardActions();

/* The agents and the models are independent of the evidence, so a
   failure in one does not blank the other two. */
(async function init() {
  try {
    await loadModels();
  } catch (error) {
    /* The model list is a convenience; the suite resolves a model on
       its own, so this is not worth an error banner. */
  }
  /* refresh() loads the tree too, and the first call is how the tree
     gets loaded at all -- no separate tree load here. */
  await refresh();
})();
</script>
</body>
</html>
```

---

<!-- ==== 27/125 : headless_app/bridge/__init__.py ==== -->

### headless_app/bridge/__init__.py

```python
"""bridge - Project Manager connection layer for the headless engine."""

from bridge.client import (
    ProjectManagerBridge,
    AsyncProjectManagerBridge,
)

__all__ = [
    "ProjectManagerBridge",
    "AsyncProjectManagerBridge",
]
```

---

<!-- ==== 28/125 : headless_app/bridge/client.py ==== -->

### headless_app/bridge/client.py

```python
"""
bridge/client.py
================

Project Manager bridge clients for the headless engine.

The bridge is the *interface* the headless agents use to reach the running
Project Manager. Every file operation goes through the Project Manager
server (or its direct in-process filesystem authority) - the bridge never
touches the project filesystem itself unless a direct provider is used.

Two transports:

    ProjectManagerBridge       - synchronous HTTP (+ sync WebSocket subscribe)
    AsyncProjectManagerBridge  - async/await HTTP (+ async WebSocket subscribe)

Both implement the provider surface the file tools expect:

    workspace_root (str)    .relpath(path) -> posix relative (or raises)
    .list_tree() -> nested  .read(rel) -> str    .write(rel, content)
    .create(rel, content)   .delete(rel)         .exists(rel) -> bool

Plus Project Manager conveniences: health(), project(), sessions(),
rename(), create_directory(), delete_directory(), open(), subscribe().

The server responses follow the Project Manager contract:

    GET  /api/health          -> {"status", "project", "root"}
    GET  /api/project         -> {"scope", "project", "root", "filesystem"}
    GET  /api/file/read       -> {"path", "content", "scope"}
    PUT  /api/file/write      -> {"status": "saved", "path", "scope"}
    POST /api/file/create     -> {"status": "created", "path", "scope"}
    DELETE /api/file/delete   -> {"status": "deleted", "path", "scope"}
    DELETE /api/directory/delete -> {"status": "deleted", ...}
    POST /api/directory/create   -> {"status": "created", ...}
    PUT  /api/path/rename     -> {"status": "renamed", ...}
    WS   /api/ws              -> {"type": "event", "event": {...}} frames
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, AsyncIterator, Callable

import httpx
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as ws_connect


# ============================================================
# BASE URL DETECTION
# ============================================================

def _default_base_url() -> str:
    """
    Best-effort default: localhost on the standard Project Manager port.
    """

    import os

    return os.environ.get(
        "PROJECT_MANAGER_BASE_URL",
        "http://127.0.0.1:8000",
    )


def _apply_project_root(
    path: str,
    project_root: str = "",
) -> str:
    """
    Normalize a project-relative path into the API path form.
    """

    path = path.replace("\\", "/").strip("/")

    return path


# ============================================================
# SHARED RESPONSE MACHINERY
# ============================================================

def _raise_for_error(
    response: httpx.Response,
) -> None:
    """
    Turn a non-2xx response into a useful Python error.
    """

    if response.is_success:
        return

    detail = ""

    try:

        detail = response.json().get(
            "detail",
            "",
        )

    except Exception:
        pass

    message = detail or f"Project Manager error (HTTP {response.status_code})."

    raise RuntimeError(
        message
    )


def _decode_message(message: Any) -> dict[str, Any]:
    """
    Turn a raw WebSocket message into a dict (bytes or str payload).
    """

    import json

    if isinstance(message, bytes):
        return json.loads(
            message.decode(
                "utf-8"
            )
        )

    try:

        return json.loads(
            message
        )

    except Exception:

        return {
            "type": "message",
            "data": message,
        }


# ============================================================
# PATH HELPERS (shared by both clients)
# ============================================================

def _normalize(raw: str) -> str:
    return str(raw).replace("\\", "/").strip("/")


def _relpath(root: Path, path: str) -> str:
    """Translate an absolute-or-relative path into a posix relative path that
    stays inside the Project Manager workspace root. The root itself maps to
    "". Raises ValueError when the path would escape the root."""
    raw = str(path).strip()
    if not raw:
        return ""
    if raw in (".", "/", "\\"):
        return ""

    root = root.resolve()

    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Path '{raw}' is outside the Project Manager workspace root "
                f"({root})."
            )
        return "" if rel == Path(".") else rel.as_posix()

    joined = (root / _normalize(raw)).resolve()
    try:
        rel = joined.relative_to(root)
    except ValueError:
        raise ValueError(
            f"Path '{raw}' is outside the Project Manager workspace root "
            f"({root})."
        )
    as_posix = rel.as_posix()
    return "" if as_posix == "." else as_posix


# ============================================================
# SYNC CLIENT
# ============================================================

class ProjectManagerBridge:
    """Synchronous HTTP bridge to the Project Manager server.

    Implements the provider surface used by the headless file tools and the
    Project Manager operations exposed by the original Python client.
    """

    #: how long a project tree snapshot is trusted (list/exists lookups)
    _TREE_TTL = 2.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout
        self.scope = "workspace"

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

        self._root: str | None = None
        self._tree_cache: tuple[float, list] = (0.0, [])

    # ========================================================
    # PROVIDER SURFACE
    # ========================================================

    @property
    def workspace_root(self) -> str:
        """The Project Manager workspace root (from /api/health)."""
        if self._root is None:
            health = self.health()
            self._root = str((health or {}).get("root", ""))
        if not self._root:
            raise RuntimeError(
                "Project Manager did not report a workspace root."
            )
        return self._root

    def relpath(self, path: str) -> str:
        return _relpath(Path(self.workspace_root), path)

    def _fresh_tree(self) -> list:
        now = time.monotonic()
        if now - self._tree_cache[0] < self._TREE_TTL:
            return self._tree_cache[1]
        tree: list = (self.tree() or {}).get("filesystem") or []
        self._tree_cache = (now, tree)
        return tree

    def list_tree(self) -> list:
        """Nested project tree ([{name, path, type, children?, size?}...])."""
        return self._fresh_tree()

    def read(self, rel: str) -> str:
        """Read a workspace text file; returns the content."""
        return self.open(rel)["content"]

    def write(self, rel: str, content: str) -> dict[str, Any]:
        return self.save(rel, content)

    def create(self, rel: str, content: str) -> dict[str, Any]:
        return self.create_file(rel, content)

    def delete(self, rel: str) -> dict[str, Any]:
        return self.delete_file(rel)

    def exists(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").strip("/")
        for entry in self._flatten_paths():
            if entry == rel:
                return True
        return False

    def _flatten_paths(self) -> list[str]:
        paths: list[str] = []

        def walk(entries):
            for entry in entries or []:
                rel = entry.get("path", "")
                if rel:
                    paths.append(rel)
                walk(entry.get("children") or [])

        walk(self._fresh_tree())
        return paths

    # ========================================================
    # GET HELPERS
    # ========================================================

    def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # PROJECT OPERATIONS
    # ========================================================

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def project(self) -> dict[str, Any]:
        return self._get("/api/project", scope=self.scope)

    def tree(self) -> dict[str, Any]:
        return self.project()

    def sessions(self) -> dict[str, Any]:
        return self._get("/api/sessions")

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def read_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    def open(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Open a project file and return its contents.
        """

        return self.read_file(path, scope=scope)

    def write_file(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Save file content. Alias for write_file().
        """

        return self.write_file(path, content, scope=scope)

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    def delete_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    # ========================================================
    # DIRECTORY OPERATIONS
    # ========================================================

    def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope or self.scope,
            },
        )

    def delete_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    # ========================================================
    # RENAME / MOVE OPERATIONS
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope or self.scope,
            },
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def subscribe(
        self,
        *,
        timeout: float | None = None,
    ):
        """
        Open a WebSocket and yield Project Manager frames as they arrive.

        Frames keep the server contract: {"type": "event", "event": {...}}
        for project changes, {"type": "hello", ...} and
        {"type": "sessions", ...} for session state.
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        import websockets.sync.client as ws_sync

        with ws_sync.connect(
            ws_url,
            timeout=timeout,
        ) as socket:

            while True:

                message = socket.recv()

                if message is None:
                    break

                yield _decode_message(message)

    def expose(
        self,
    ) -> dict[str, Any]:
        """Self-description: which Project Manager endpoints the bridge uses."""
        return {
            "base_url": self.base_url,
            "workspace_root": self.workspace_root,
            "scope": self.scope,
        }

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ProjectManagerBridge":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ============================================================
# ASYNC CLIENT
# ============================================================

class AsyncProjectManagerBridge:
    """Asynchronous HTTP + WebSocket bridge to the Project Manager.

    Provides the same operations as ProjectManagerBridge with async/await,
    plus subscribe() for real-time project events.
    """

    _TREE_TTL = 2.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout
        self.scope = "workspace"

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

        self._root: str | None = None
        self._tree_cache: tuple[float, list] = (0.0, [])

    # ========================================================
    # PROVIDER SURFACE (async)
    # ========================================================

    @property
    async def workspace_root(self) -> str:
        if self._root is None:
            health = await self.health()
            self._root = str((health or {}).get("root", ""))
        if not self._root:
            raise RuntimeError(
                "Project Manager did not report a workspace root."
            )
        return self._root

    def relpath(self, path: str) -> str:
        root = self._root or "."
        return _relpath(Path(root), path)

    async def _fresh_tree(self) -> list:
        now = time.monotonic()
        if now - self._tree_cache[0] < self._TREE_TTL:
            return self._tree_cache[1]
        payload = await self.tree()
        tree: list = (payload or {}).get("filesystem") or []
        self._tree_cache = (now, tree)
        return tree

    async def list_tree(self) -> list:
        return await self._fresh_tree()

    async def read(self, rel: str) -> str:
        return (await self.open(rel))["content"]

    async def write(self, rel: str, content: str) -> dict[str, Any]:
        return await self.save(rel, content)

    async def create(self, rel: str, content: str) -> dict[str, Any]:
        return await self.create_file(rel, content)

    async def delete(self, rel: str) -> dict[str, Any]:
        return await self.delete_file(rel)

    async def exists(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").strip("/")
        for path in await self._flatten_paths():
            if path == rel:
                return True
        return False

    async def _flatten_paths(self) -> list[str]:
        paths: list[str] = []

        def walk(entries):
            for entry in entries or []:
                rel = entry.get("path", "")
                if rel:
                    paths.append(rel)
                walk(entry.get("children") or [])

        walk(await self._fresh_tree())
        return paths

    # ========================================================
    # ASYNC HELPERS
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # OPERATIONS (ASYNC)
    # ========================================================

    async def health(self) -> dict[str, Any]:
        return await self._get("/api/health")

    async def project(self) -> dict[str, Any]:
        return await self._get("/api/project", scope=self.scope)

    async def tree(self) -> dict[str, Any]:
        return await self.project()

    async def sessions(self) -> dict[str, Any]:
        return await self._get("/api/sessions")

    async def read_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def open(
        self,
        path: str,
        scope: str | None = None,
    ):
        return await self.read_file(path, scope=scope)

    async def write_file(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    async def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ):
        return await self.write_file(path, content, scope=scope)

    async def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope or self.scope,
            },
        )

    async def delete_file(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope or self.scope,
            },
        )

    async def delete_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope or self.scope,
        )

    async def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        return await self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope or self.scope,
            },
        )

    # ========================================================
    # REAL-TIME SUBSCRIPTION
    # ========================================================

    async def subscribe(
        self,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Open a WebSocket and yield Project Manager event frames.

        Example:
            >>> async for frame in client.subscribe():
            ...     if frame.get("type") == "event":
            ...         event = frame["event"]
            ...         if event["type"] == "saved":
            ...             print("Saved", event["path"])
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        async with ws_connect(
            ws_url
        ) as socket:

            async for message in socket:

                yield _decode_message(
                    message
                )

    async def expose(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "workspace_root": await self.workspace_root,
            "scope": self.scope,
        }

    async def close(self) -> None:
        await self._http.aclose()


__all__ = [
    "ProjectManagerBridge",
    "AsyncProjectManagerBridge",
    "_default_base_url",
]
```

---

<!-- ==== 29/125 : headless_app/bridge/providers.py ==== -->

### headless_app/bridge/providers.py

```python
"""
bridge/providers.py
===================

In-process Project Manager filesystem authority.

Used when the agent engine is mounted INSIDE a running Project Manager
server (the agent-backed /api/chat router). In that case a separate HTTP
loop-back bridge is unnecessary, so this provider drives the SAME
parameters.filesystem module the Project Manager itself uses - keeping the
Project Manager as the single filesystem owner even in-process.

It implements the provider surface the headless file tools expect, exactly
like the HTTP ProjectManagerBridge does:

    workspace_root (str)    .relpath(path) -> posix relative (or raises)
    .list_tree() -> nested  .read(rel) -> str    .write(rel, content)
    .create(rel, content)   .delete(rel)         .exists(rel) -> bool
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bridge.client import _relpath


class DirectProjectIO:
    """
    Filesystem provider backed directly by the Project Manager's
    parameters.filesystem authority.

    Requires the Project Manager server modules to be importable
    (``from parameters import filesystem``).
    """

    def __init__(self) -> None:
        from parameters import filesystem

        self._filesystem = filesystem
        self._root = Path(filesystem.PROJECT_ROOT)
        self.scope = "workspace"

    # --------------------------------------------------------
    # PROVIDER SURFACE
    # --------------------------------------------------------

    @property
    def workspace_root(self) -> str:
        return str(self._root)

    def relpath(self, path: str) -> str:
        return _relpath(self._root, path)

    def list_tree(self) -> list:
        return self._filesystem.read_filesystem()

    def read(self, rel: str) -> str:
        return self._filesystem.read_file(rel)

    def write(self, rel: str, content: str) -> dict[str, Any]:
        self._filesystem.write_file(rel, content)
        return {"status": "saved", "path": rel, "scope": self.scope}

    def create(self, rel: str, content: str) -> dict[str, Any]:
        self._filesystem.create_file(rel, content)
        return {"status": "created", "path": rel, "scope": self.scope}

    def create_directory(self, rel: str) -> dict[str, Any]:
        self._filesystem.create_directory(rel)
        return {"status": "created", "path": rel, "scope": self.scope}

    def delete(self, rel: str) -> dict[str, Any]:
        self._filesystem.delete_path(rel)
        return {"status": "deleted", "path": rel, "scope": self.scope}

    def exists(self, rel: str) -> bool:
        target = (self._root / rel.replace("\\", "/").strip("/")).resolve()
        try:
            target.relative_to(self._root.resolve())
        except ValueError:
            return False
        return target.exists()

    # --------------------------------------------------------
    # PROJECT MANAGER CONVENIENCES
    # --------------------------------------------------------

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "project": self._filesystem.read_project_info(),
            "root": str(self._root),
        }

    def tree(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "project": self._filesystem.read_project_info(),
            "root": str(self._root),
            "filesystem": self._filesystem.read_filesystem(),
        }

    def project(self) -> dict[str, Any]:
        return self.tree()

    def sessions(self) -> list:
        return []

    def expose(self) -> dict[str, Any]:
        return {
            "mode": "direct",
            "workspace_root": self.workspace_root,
            "scope": self.scope,
        }


__all__ = ["DirectProjectIO"]
```

---

<!-- ==== 30/125 : headless_app/bridge/routers/__init__.py ==== -->

### headless_app/bridge/routers/__init__.py

```python
"""bridge.routers - drop-in FastAPI routers for the Project Manager."""
```

---

<!-- ==== 31/125 : headless_app/bridge/routers/agents.py ==== -->

### headless_app/bridge/routers/agents.py

```python
"""
bridge/routers/agents.py
========================

Agent registry, run, and pipeline endpoints for the Project Manager.

Turns the Project Manager into an agent workspace: browse every agent
(library + workspace), run one agent from its ``agent.json``/``agent.md``
files, or cascade many agents one after another (each later step receives
every earlier step's reply) through ``/api/pipeline``.

    GET  /api/agents
        -> library agents (engine/agent_library/) plus workspace agents
           discovered under <workspace>/agents/<name>/agent.json.

    GET  /api/agents/{agent_id}
        -> {"source", "meta", "sections"} for one agent (workspace first,
           library fallback), so the editor can open/read its definition.

    POST /api/agents/run
        {"json_path", "md_path" | "agent_id", "message", "model"?}
        -> builds the agent (workspace-relative paths resolved through the
           Project Manager filesystem), runs it, records chat entries, and
           returns {"reply", "agent_id", "name", "model", "tool_events"}.

    GET /api/pipeline
        -> default step chain from config/pipeline.json plus every selectable
           step candidate (library + workspace agents).

    POST /api/pipeline
        {"steps": [id | {"json_path", "md_path"}], "message", "model"?}
        -> run_pipeline: cascade the ordered steps, feed-forward every
           earlier step's reply into the next; each step's stdout line is
           "Agent N (<id>) completed. Tools used: <tools>".

    GET /api/models
        -> models listed in config/models.json, for the frontend picker.

All file tool calls run in-process through DirectProjectIO, so
parameters.filesystem remains the single filesystem authority.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .errors import project_manager_error
from .chat import MAX_MESSAGE_LENGTH, _mirror_pm_log


# ------------------------------------------------------------
# Headless engine bootstrap
# ------------------------------------------------------------

def _ensure_headless_on_path() -> None:
    here = Path(__file__).resolve()
    if here.name == "agents.py" and here.parent.name == "routers":
        candidate = here.parents[3] / "headless_app"
    else:
        candidate = here.parents[2]
    candidate = candidate.resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


_ensure_headless_on_path()

from engine.agents.factory import (  # noqa: E402
    build_agent,
    build_agent_from_definition,
)
from engine.agents.loader import AgentNotFoundError  # noqa: E402
from engine.agents.registry import list_agents  # noqa: E402
from engine.pipeline import load_pipeline, run_pipeline  # noqa: E402
from tools.chatlog import append_chat  # noqa: E402

try:
    from bridge.providers import DirectProjectIO  # noqa: E402
except Exception:
    DirectProjectIO = None  # type: ignore[assignment]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class AgentRunRequest(BaseModel):

    message: str

    agent_id: str | None = None

    json_path: str | None = None

    md_path: str | None = None

    model: str | None = None


class PipelineRunRequest(BaseModel):

    steps: list = []

    message: str

    model: str | None = None


# ============================================================
# PROJECT MANAGER FILESYSTEM AUTHORITY
# ============================================================

_workspace_root: Any = None


def _pm_filesystem():
    """parameters.filesystem when running inside the Project Manager."""
    try:
        from parameters import filesystem
        return filesystem
    except Exception:
        return None


def _workspace() -> Path | None:
    global _workspace_root
    if _workspace_root is not None:
        return _workspace_root
    filesystem = _pm_filesystem()
    if filesystem is None:
        _workspace_root = None
        return None
    _workspace_root = filesystem.PROJECT_ROOT
    return _workspace_root


def _resolve(relative_path: str) -> Path:
    """Safe absolute path for a workspace-relative agent file path."""
    filesystem = _pm_filesystem()
    if filesystem is None:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            return candidate
        raise ValueError(
            "Running outside the Project Manager - a workspace-relative "
            "path cannot be resolved."
        )
    return filesystem.resolve_project_path(relative_path)


def _provider() -> Any:
    if DirectProjectIO is None:
        raise RuntimeError(
            "DirectProjectIO is unavailable - the agent router must run "
            "inside the Project Manager server."
        )
    return DirectProjectIO()


# ============================================================
# WORKSPACE AGENT DISCOVERY
# ============================================================

def _workspace_agents() -> list[dict]:
    """Scan <workspace>/agents/*/agent.json for runnable agent definitions."""
    workspace = _workspace()
    if workspace is None:
        return []

    discovered: list[dict] = []
    base = workspace / "agents"
    if not base.is_dir():
        return discovered

    for agent_dir in sorted(base.iterdir()):
        if not agent_dir.is_dir() or agent_dir.name.startswith(("_", ".")):
            continue
        json_file = agent_dir / "agent.json"
        md_file = agent_dir / "agent.md"
        if not json_file.exists() or not md_file.exists():
            continue
        try:
            meta = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        rel_dir = f"agents/{agent_dir.name}"
        discovered.append({
            "id": meta.get("id") or agent_dir.name,
            "name": meta.get("name") or agent_dir.name,
            "description": meta.get("description", ""),
            "mode": meta.get("mode", "chat"),
            "model": meta.get("model", "") or "",
            "tools": meta.get("tools", []),
            "source": "workspace",
            "json_path": f"{rel_dir}/agent.json",
            "md_path": f"{rel_dir}/agent.md",
            "dir": rel_dir,
        })

    return discovered


def _all_agents() -> list[dict]:
    library = [dict(a, source="library") for a in list_agents()]
    return library + _workspace_agents()


# ============================================================
# CHAT LOG RECORDING
# ============================================================

def _record_entries(user_message: str, reply: str) -> list[dict]:
    user_entry = append_chat("user", user_message)
    reply_entry = append_chat("agent", reply)
    _mirror_pm_log(user_entry)
    _mirror_pm_log(reply_entry)
    return [user_entry, reply_entry]


def _validated_message(message: str) -> str:
    text = message.strip()
    if not text:
        raise project_manager_error(ValueError("Chat message cannot be empty."))
    if len(text) > MAX_MESSAGE_LENGTH:
        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )
    return text


# ============================================================
# LIST AGENTS
# ============================================================

@router.get("/api/agents")
def list_all_agents(
    request: Request,
):
    """
    Return every runnable agent: library (engine/agent_library/) and
    workspace (workspace/agents/<name>/) definitions.

    Workspace agents include json_path/md_path so the frontend can run or
    open them directly.
    """

    try:

        return {
            "agents": _all_agents(),
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# GET ONE AGENT DEFINITION
# ============================================================

@router.get("/api/agents/{agent_id}")
def get_agent_definition(
    request: Request,
    agent_id: str,
):
    """
    Return one agent's metadata + markdown sections. Workspace agents
    (agents/<id>/) win over library agents with the same id.
    """

    from engine.agents.loader import load_definition

    workspace = _workspace()
    ws_dir = (workspace / "agents" / agent_id) if workspace is not None else None

    if ws_dir is not None and (ws_dir / "agent.json").exists():
        try:
            meta = json.loads(
                (ws_dir / "agent.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise project_manager_error(
                ValueError(f"Agent config unreadable: {ws_dir / 'agent.json'} ({exc})")
            )
        md_file = ws_dir / "agent.md"
        md_text = md_file.read_text(encoding="utf-8")
        from engine.agents.loader import _parse_sections, _clean_body
        raw = _parse_sections(md_text)
        sections = {name: _clean_body(body) for name, body in raw.items()}
        return {
            "source": "workspace",
            "meta": meta,
            "sections": sections,
            "json_path": f"agents/{agent_id}/agent.json",
            "md_path": f"agents/{agent_id}/agent.md",
        }

    try:
        definition = load_definition(agent_id)
        return {
            "source": "library",
            "meta": definition["meta"],
            "sections": definition["sections"],
        }
    except Exception as error:
        raise project_manager_error(
            ValueError(f"Agent not found: {agent_id} ({error})")
        )


# ============================================================
# RUN ONE AGENT (from agent.json / agent.md or a library id)
# ============================================================

@router.post("/api/agents/run")
def run_single_agent(
    request: Request,
    payload: AgentRunRequest,
):
    """
    Build and run one agent, then log the exchange.

    Body:
        message:   the user's instruction (required).
        json_path/md_path:
                   workspace-relative paths to agent.json + agent.md
                   (e.g. "agents/demo/agent.json"). When given, the agent
                   is built from those files; otherwise agent_id is used.
        agent_id:  library agent to run when json_path is not given.
        model:     optional model override.
    """

    message = _validated_message(payload.message)

    try:

        if payload.json_path and payload.md_path:
            json_file = _resolve(str(payload.json_path))
            md_file = _resolve(str(payload.md_path))
            agent = build_agent_from_definition(
                str(json_file),
                str(md_file),
                model=payload.model,
                bridge=_provider(),
            )
            agent_id = str(agent.profile.id)
        elif payload.agent_id:
            agent_id = payload.agent_id
            agent = build_agent(
                agent_id,
                model=payload.model,
                bridge=_provider(),
            )
        else:
            raise project_manager_error(
                ValueError(
                    "Provide json_path + md_path, or an agent_id, to run."
                )
            )

        reply = agent.think(message)

        entries = _record_entries(message, reply)

        return {
            "status": "ok",
            "reply": reply,
            "agent_id": agent_id,
            "name": agent.profile.name,
            "description": agent.profile.description,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entry": entries[0],
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# PIPELINE OPTIONS
# ============================================================

@router.get("/api/pipeline")
def pipeline_options(
    request: Request,
):
    """
    Return the default step chain (config/pipeline.json) plus every
    selectable step candidate (library + workspace agents).

    The frontend starts with an empty selection and lets the user build an
    ordered, reorderable cascade from these candidates.
    """

    try:

        return {
            "default_steps": load_pipeline(),
            "candidates": _all_agents(),
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# RUN PIPELINE (multi-agent cascade)
# ============================================================

@router.post("/api/pipeline")
def run_agent_pipeline(
    request: Request,
    payload: PipelineRunRequest,
):
    """
    Cascade many agents one after another.

    Body:
        steps:   ordered list. Each element is either a library agent id
                 (str) or a dict with workspace-relative json_path + md_path
                 (workspace agent). Every later step receives the original
                 message plus all earlier steps' replies as its input.
        message: the original user request.
        model:   optional model override for every step.

    Returns {"reply", "outputs": [{agent_id, agent_name, output, tools_used}],
    "tool_events"} and logs the exchange.
    """

    message = _validated_message(payload.message)
    steps = list(payload.steps or [])

    if not steps:

        raise project_manager_error(
            ValueError("Pipeline requires at least one step.")
        )

    try:

        normalized: list = []
        for step in steps:
            if isinstance(step, dict):
                if not (step.get("json_path") and step.get("md_path")):
                    raise project_manager_error(
                        ValueError(
                            "Pipeline step dicts need json_path + md_path: "
                            f"{step!r}"
                        )
                    )
                normalized.append({
                    "json_path": str(_resolve(str(step["json_path"]))),
                    "md_path": str(_resolve(str(step["md_path"]))),
                })
            else:
                normalized.append(str(step))

        result = run_pipeline(
            message,
            model=payload.model,
            steps=normalized,
            bridge=_provider(),
        )

        _record_entries(message, result["reply"])

        return {
            "status": "ok",
            "reply": result["reply"],
            "outputs": result["outputs"],
            "tool_events": result["tool_events"],
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# MODELS
# ============================================================

@router.get("/api/models")
def list_models(
    request: Request,
):
    """
    Return the models in config/models.json for the frontend picker.
    Run refresh_models to re-scan installed Ollama models.
    """

    from engine.core import llm

    model_file = llm.CONFIG_DIR / "models.json"

    try:

        if model_file.exists():
            data = json.loads(model_file.read_text(encoding="utf-8"))
            models = data.get("models") or []
        else:
            models = []

        return {
            "models": [
                {
                    "id": m.get("id", ""),
                    "name": m.get("name", m.get("id", "")),
                    "source": m.get("source", "ollama"),
                }
                for m in models
            ],
        }

    except Exception as error:

        raise project_manager_error(error)
```

---

<!-- ==== 32/125 : headless_app/bridge/routers/chat.py ==== -->

### headless_app/bridge/routers/chat.py

```python
"""
bridge/routers/chat.py
======================

Agent-backed Project Manager chat router (drop-in replacement).

The Project Manager keeps a stub chat surface: ``POST /api/chat`` logs a
message and ``GET /api/chat`` fetches history. This router swaps the stub
handler for the agentCreator engine, so the Project Manager becomes a fully
agent-driven server:

    POST /api/chat  {"message": str, "agent_id": str?, "model": str?}
        -> builds the requested agent (headless engine),
        -> runs agent.think(message),
        -> records user turn + reply into the headless chat log
           (data/chatlog/chat.log, which search_chat_logs reads) AND
           mirrors both entries into the Project Manager's own
           workspace/data/chat.log, and
        -> returns {"status", "reply", "agent_id", "model", "tool_events"}.

    GET /api/chat  ?limit=
        -> most recent headless chat log entries.

In-process file tools run through DirectProjectIO, so the Project Manager's
parameters.filesystem stays the single filesystem authority.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .errors import project_manager_error


# ------------------------------------------------------------
# Headless engine bootstrap (works from the server app or when imported
# from the headless bridge package).
# ------------------------------------------------------------

def _ensure_headless_on_path() -> None:
    here = Path(__file__).resolve()
    if here.name == "chat.py" and here.parent.name == "routers":
        candidate = here.parents[3] / "headless_app"
    else:
        candidate = here.parents[2]
    candidate = candidate.resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


_ensure_headless_on_path()

from engine.agents.factory import build_agent  # noqa: E402
from engine.agents.loader import AgentNotFoundError  # noqa: E402
from engine.agents.registry import list_agents  # noqa: E402
from tools.chatlog import append_chat, read_history  # noqa: E402

try:
    from bridge.providers import DirectProjectIO  # noqa: E402
except Exception:
    DirectProjectIO = None  # type: ignore[assignment]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatMessage(BaseModel):

    message: str

    agent_id: str | None = None

    model: str | None = None


# ============================================================
# CHAT LOG HELPERS
# ============================================================

MAX_MESSAGE_LENGTH = 2000

DEFAULT_LIMIT = 50

MAX_LIMIT = 500

_provider_cache: Any = None


def _provider() -> Any:
    """The active filesystem authority (in-process Project Manager)."""
    global _provider_cache
    if _provider_cache is None:
        if DirectProjectIO is None:
            raise RuntimeError(
                "DirectProjectIO is unavailable - the agent-backed chat "
                "router must run inside the Project Manager server."
            )
        _provider_cache = DirectProjectIO()
    return _provider_cache


def _default_agent_id() -> str | None:
    agents = list_agents()
    if not agents:
        return None
    return agents[0]["id"]


def _mirror_pm_log(entry: dict) -> None:
    """Mirror one chat entry into the Project Manager's own chat.log."""
    try:
        from parameters import filesystem

        log_path = filesystem.resolve_project_path("data/chat.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # fail-safe: never break the chat response over a log write


def _record_entries(user_message: str, reply: str) -> list[dict]:
    """Persist user + reply to the headless chat log; mirror to PM's log."""
    user_entry = append_chat("user", user_message)
    reply_entry = append_chat("agent", reply)
    _mirror_pm_log(user_entry)
    _mirror_pm_log(reply_entry)
    return [user_entry, reply_entry]


# ============================================================
# SEND MESSAGE
# ============================================================

@router.post("/api/chat")
def send_chat_message(
    request: Request,
    payload: ChatMessage,
):
    """
    Send a message to the agent engine and return its reply.

    Body:
        message (str):   the user's message (required, non-empty, max 2000).
        agent_id (str):  agent to use; defaults to the first registered.
        model (str):     optional model override.
    """

    message = payload.message.strip()

    if not message:

        raise project_manager_error(
            ValueError(
                "Chat message cannot be empty."
            )
        )

    if len(message) > MAX_MESSAGE_LENGTH:

        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )

    agent_id = payload.agent_id or _default_agent_id()

    if not agent_id:

        raise project_manager_error(
            RuntimeError(
                "No agents are registered in engine/agent_library/."
            )
        )

    try:

        agent = build_agent(
            agent_id,
            model=payload.model,
            bridge=_provider(),
        )

        reply = agent.think(message)

        entries = _record_entries(message, reply)

        return {
            "status": "ok",
            "reply": reply,
            "agent_id": agent_id,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entry": entries[0],
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(
                f"Agent not found: {agent_id} ({error})"
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# FETCH HISTORY
# ============================================================

@router.get("/api/chat")
def get_chat_history(
    request: Request,
    limit: int = DEFAULT_LIMIT,
):
    """
    Return the most recent chat entries.

    Query params:
        limit:
            Maximum number of entries to return.
    """

    try:

        return {
            "entries": read_history(limit),
        }

    except Exception as error:

        raise project_manager_error(
            error
        )


if __name__ == "__main__":
    print(__doc__)
```

---

<!-- ==== 33/125 : headless_app/bridge/tools_adapter.py ==== -->

### headless_app/bridge/tools_adapter.py

```python
"""
bridge/tools_adapter.py
=======================

Maps the headless agent tools to their Project Manager HTTP surface and
binds a bridge to the tool registry.

The tools themselves live in tools/project_tools.py and branch on the
configured provider; this module is the wiring point that turns a bridge
(or direct provider) into the active filesystem authority for all agents
built afterwards.

TOOL_ENDPOINT_MAP documents, for each tool id, the Project Manager endpoint
the tool ultimately drives when a bridge is connected.
"""

from __future__ import annotations

from typing import Any

import tools.registry as _registry

#: Tool id -> Project Manager endpoint backing it (informational).
TOOL_ENDPOINT_MAP: dict[str, str] = {
    "map_files": "GET /api/project (filesystem tree)",
    "read_file": "GET /api/file/read",
    "write_text_file": "PUT /api/file/write | POST /api/file/create",
    "delete_files": "DELETE /api/file/delete",
    "create_directory": "POST /api/directory/create",
    "search_workspace": "(local or Project Manager filesystem)",
    "get_current_date": "(local)",
    "tell_me_the_date_and_time": "(local)",
    "search_chat_logs": "get data/chatlog/chat.log (local store)",
}


def bind_tools(bridge: Any) -> Any:
    """Point the tool registry's file tools at a Project Manager provider.

    Pass either a ProjectManagerBridge (HTTP) or a DirectProjectIO
    (in-process filesystem authority). Returns the same provider for
    convenience, so callers can chain it.

    All agents built AFTER this call route their file tools through the
    provider until configure(None) is called again.
    """
    _registry.configure(bridge)
    print(
        f"[tools_adapter] file tools bound to Project Manager "
        f"(root={getattr(bridge, 'workspace_root', '?')})"
    )
    return bridge


def unbind_tools() -> None:
    """Return the file tools to the local-disk backend."""
    _registry.configure(None)


def describe_tools() -> dict[str, str]:
    """Return the tool-id -> endpoint map for documentation/debugging."""
    return dict(TOOL_ENDPOINT_MAP)


__all__ = [
    "bind_tools",
    "unbind_tools",
    "describe_tools",
    "TOOL_ENDPOINT_MAP",
]
```

---

<!-- ==== 34/125 : headless_app/config/models.json ==== -->

### headless_app/config/models.json

```json
{
  "models": [
    {
      "id": "llama3.1:8b",
      "name": "llama3.1:8b",
      "source": "ollama",
      "size": 4920753328
    },
    {
      "id": "nomic-embed-text:latest",
      "name": "nomic-embed-text:latest",
      "source": "ollama",
      "size": 274302450
    },
    {
      "id": "qwen2.5-coder:latest",
      "name": "qwen2.5-coder:latest",
      "source": "ollama",
      "size": 4683087561
    },
    {
      "id": "gemma4:e2b",
      "name": "gemma4:e2b",
      "source": "ollama",
      "size": 7162405886
    }
  ]
}
```

---

<!-- ==== 35/125 : headless_app/config/pipeline.json ==== -->

### headless_app/config/pipeline.json

```json
{
  "name": "module-generation",
  "description": "One idea -> a working drop-in custom module. Step 1 drafts the feature plan, Step 2 turns it into a blueprint grounded on the skills reference, Step 3 writes the .py module file.",
  "steps": [
    "feature_planner_agent",
    "execute_engineer_agent",
    "module_builder_agent"
  ]
}
```

---

<!-- ==== 36/125 : headless_app/engine/__init__.py ==== -->

### headless_app/engine/__init__.py

```python
(empty file — 0 bytes)
```

---

<!-- ==== 37/125 : headless_app/engine/agent_library/Builder/agent.json ==== -->

### headless_app/engine/agent_library/Builder/agent.json

```json
{
  "id": "module_builder_agent",
  "name": "Module Builder Agent",
  "description": "Step 3: Confirms the target save location, then compiles Step 2 blueprints into complete 3-phase drop-in Python modules.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "tools": [
    "map_files",
    "read_file",
    "write_text_file"
  ]
}
```

---

<!-- ==== 38/125 : headless_app/engine/agent_library/Builder/agent.md ==== -->

### headless_app/engine/agent_library/Builder/agent.md

````markdown
# Module Builder Agent

## role
You are the **Module Builder Agent** (Step 3 of the agentCreator Module Development Pipeline). Your role is to take a Stage 2 Technical Implementation Blueprint provided directly in the user's message and compile it into a single, complete, production-ready Python custom module file.

## purpose
To convert technical blueprints into runnable Python custom module code (`<module_name>.py`) that communicates with the rest of the agentCreator application through the interface framework (`UI_MANIFEST` + `register_routes(app)` FastAPI endpoints + `server.paths` path authority + `InterfaceDispatcher` wiring).

## tools
You have access to exactly **THREE tools** and MUST ONLY use these tools:
1. `read_file`: Reads text and document file contents from disk.
2. `write_text_file`: Writes text files directly to a specified directory on disk.
3. `map_files`: Inspects directory structures and lists file trees on disk.

**Tool Rule**: You MUST ONLY use `read_file`, `write_text_file`, and `map_files`. Do NOT attempt to execute or call any other tools outside of these three.

## do_not_hallucinate
- **Strict Route Encapsulation**: EVERY route decorator (`@app.get(...)`, `@app.post(...)`) MUST be placed INSIDE the top-level `def register_routes(app: FastAPI):` function definition. NEVER write `@app.get` or `@app.post` at the root level of the file, because `app` is only passed to `register_routes(app)` at runtime.
- **Strict Grounding**: Do NOT fabricate or invent non-existent UI action types, ungrounded schema keys, or fake framework decorators. Only use the 4 supported agentCreator UI action patterns (`prompt_input`, `dropdown_menu`, `open_modal`, `qa_survey`) and standard FastAPI decorators (`@app.get`, `@app.post`).
- **No Incomplete / Imaginary Code**: Never invent imaginary function calls, fake imports, or unverified backend helper methods. Always import path storage authority from `server.paths` (`DATA_DIR`, `EXPORTS_DIR`, `RECORDS_DIR`, `RAG_DB_DIR`).
- **No Hallucinated Tool Calls**: Never output fake tool JSON schemas or imaginary function names like `execute_plan()`. When using your tools, emit valid calls for `read_file`, `write_text_file`, or `map_files` only.

## input_contract
- You accept the **Stage 2 Technical Implementation Blueprint** passed directly as text in the conversation message.
- Output the complete Python custom module code in a single markdown code block. Do NOT ask save questions or emit pre-script chatter.

## workflow
Compile the incoming Stage 2 blueprint into a single Python script file organized into three explicit code phases:

### Phase 1: UI Phase (`UI_MANIFEST` Declaration)
- Declare the top-level `UI_MANIFEST` dictionary matching the module ID and header button action specifications (`prompt_input`, `dropdown_menu`, `open_modal`, `qa_survey`).

### Phase 2: Logic & Server Endpoints Phase (`register_routes` + Real-Time Logging)
- Define `register_routes(app: FastAPI)` to mount ALL GET and POST route handlers INSIDE this function.
- **Real-Time Terminal Execution Logging**: Include descriptive `print(f"[{module_id}] ...")` statements at key execution points inside every endpoint to stream execution logic live to the terminal console.
- Import storage paths directly from `server.paths` (`EXPORTS_DIR`, `DATA_DIR`, `RECORDS_DIR`, `RAG_DB_DIR`).
- Return standard JSON response contracts: `{"status": "success", "message": "...", "indicate_success": True}`.

### Phase 3: Variable Map & Extension Architecture
- Include a structured docstring block mapping all global imports, path authorities, data payload keys, and output files.
- Provide explicit extension hook functions (`_extension_pre_process_hook` and `_extension_post_process_hook`) for future feature additions.

## boundaries
- **Code Only**: Output ONLY the Python script inside a single markdown code block. No preambles or file save questions.
- **All Routes Enclosed**: All FastAPI route handlers must be defined inside `def register_routes(app: FastAPI):`.
- **Strict agentCreator Contracts**: Use exact schema keys (`components`, `target_endpoint`, `indicate_success`, `status`, `message`).
- **No Incomplete Placeholders**: Produce complete, syntactically valid, runnable Python code without unindented blocks or `TODO` gaps.
- **Path Authority**: Always import storage locations from `server.paths`. Never hardcode relative string paths or drive letters.

## output_format
Output strictly the Python code block:

```python
"""
Drop-in Custom Module: <module_name>.py
Generated by: Module Builder Agent (Step 3)
"""

from datetime import datetime
import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from server.paths import DATA_DIR, EXPORTS_DIR, RECORDS_DIR

# ==============================================================================
# PHASE 1: UI PHASE (UI_MANIFEST Declaration)
# ==============================================================================
UI_MANIFEST = {
    "module_id": "<module_name>",
    "buttons": [
        {
            "id": "btn-<module_name>",
            "label": "💬 <Label>",
            "target": "header",
            "action": "open_modal",
            "schema_endpoint": "/api/<module_name>/schema",
            "title": "<Title>"
        }
    ]
}

# ==============================================================================
# PHASE 2: LOGIC & SERVER ENDPOINTS PHASE (register_routes + Real-Time Logging)
# ==============================================================================
def register_routes(app: FastAPI):
    """Registers FastAPI endpoints with real-time terminal execution logging."""

    @app.get("/api/<module_name>/schema")
    def get_schema():
        print("[<module_name>] GET /api/<module_name>/schema -> Serving modal schema.")
        return {
            "title": "<Modal Title>",
            "target_endpoint": "/api/<module_name>/execute",
            "components": [
                {"type": "input", "name": "user_message", "label": "Message", "placeholder": "Type here..."},
                {"type": "button", "label": "Submit", "action": "submit"}
            ]
        }

    @app.post("/api/<module_name>/execute")
    async def execute_action(payload: dict):
        print(f"[<module_name>] POST /api/<module_name>/execute -> Payload: {payload}")

        # Extension Hook execution
        payload = _extension_pre_process_hook(payload)

        user_message = payload.get("user_message", "").strip()

        response = {
            "status": "success",
            "message": f"Successfully processed message: '{user_message}'",
            "indicate_success": True
        }

        _extension_post_process_hook(None, response)
        return response

# ==============================================================================
# PHASE 3: VARIABLE ARCHITECTURE MAP & EXTENSION HOOKS
# ==============================================================================
"""
--- MODULE ARCHITECTURE & VARIABLE MAP ---
• Global Imports / Path Authority:
  - EXPORTS_DIR: Resolved path for saved JSON export records.
• Data Objects & Keys:
  - payload.user_message (str): Primary input key.

--- EXTENSION HOOKS & FUTURE CAPABILITIES ---
To add extra features to this module:
1. Insert custom data transformation inside `_extension_pre_process_hook()`.
2. Add external webhook triggers inside `_extension_post_process_hook()`.
"""

def _extension_pre_process_hook(data: dict) -> dict:
    """Extension Point: Pre-process incoming payload before endpoint execution."""
    return data

def _extension_post_process_hook(record_path: Path, result: dict) -> None:
    """Extension Point: Post-process after file persistence."""
    pass
````

---

<!-- ==== 39/125 : headless_app/engine/agent_library/Enginner/agent.json ==== -->

### headless_app/engine/agent_library/Enginner/agent.json

```json
{
  "id": "execute_engineer_agent",
  "name": "Execute Engineer Agent",
  "description": "Step 2: Uses read_file to inspect ux_module_designer_skills.md and translates Step 1 functional plans into section-by-section pseudo-code and agentCreator Python blueprints.",
  "mode": "agent",
  "model": "qwen2.5-coder:latest",
  "tools": [
    "read_file"
  ]
}
```

---

<!-- ==== 40/125 : headless_app/engine/agent_library/Enginner/agent.md ==== -->

### headless_app/engine/agent_library/Enginner/agent.md

````markdown
# Execute Engineer Agent

## role
You are the **Execute Engineer Agent** (Step 2). Your role is to take the functional feature list from Step 1 and translate it into structured pseudo-code and Python implementation blueprints grounded strictly in the agentCreator skills reference.

## purpose
To bridge functional requirements and code by applying the implementation patterns defined in `skills/ux_module_designer_skills.md`.

## input_contract
Accepts the **Feature Plan** document from Step 1. The Feature Plan for the CURRENT task is always included in your incoming message - never ask for it or wait for it.

## skills
Reference `skills/ux_module_designer_skills.md` for:
1. `UI_MANIFEST` button declarations.
2. Action button logic (`prompt_input`, `dropdown_menu`, `open_modal`, `qa_survey`).
3. Endpoint registration via `register_routes(app)`.
4. Standard status response contracts (`status`, `message`, `indicate_success`).
5. Storage path authority using `server.paths`.

## workflow
0. **Load the Skills Reference ONCE**: call the `read_file` tool on `skills/ux_module_designer_skills.md` by default, and read exactly ONE TIME. If the result of that read is already in the conversation (any earlier `read_file` result message with tool "read_file" and path `ux_module_designer_skills.md`), do NOT call it again - that file never changes during your turn. Ground every decision on what that file actually contains. Never guess or invent patterns not present in it.
1. Map the functional requirements from Step 1 to skills in `ux_module_designer_skills.md`.
2. Write step-by-step pseudo-code explaining the UI and server endpoint logic.
3. Provide concrete Python code examples for `UI_MANIFEST` and `register_routes(app)`.

## boundaries
- **Strict Grounding**: Do NOT invent unsupported UI action types or non-existent framework decorators.
- **Dynamic Scoping**: Adapt logic dynamically to whatever module ID and fields are passed in the plan.
- **No Stalling**: The Step 1 Feature Plan IS included in your message. Never ask for it, never repeat that you are waiting for it, and never ask the user to provide it - act on it immediately. If a detail is missing, state the one missing field in a single line and move on.

## output_format
### 1. Executive Summary
- **Module ID**: `<module_name>`
- **UI Action Type**: [`prompt_input` | `dropdown_menu` | `open_modal` | `qa_survey`]

### 2. UI Manifest Specification
**Pseudo-Code:**
```text
[Step-by-step logic for UI_MANIFEST declaration]
```
**Python Implementation:**
```python
UI_MANIFEST = { ... }
```

### 3. Backend Route Handlers (`register_routes`)
**Pseudo-Code:**
```text
[Step-by-step logic for FastAPI GET/POST endpoints]
```
**Python Implementation:**
```python
def register_routes(app: FastAPI):
    ...
```

### 4. Path & Core Wiring Integration
**Pseudo-Code & Python Examples for `server.paths` storage.**
````

---

<!-- ==== 41/125 : headless_app/engine/agent_library/Planner/agent.json ==== -->

### headless_app/engine/agent_library/Planner/agent.json

```json
{
  "id": "feature_planner_agent",
  "name": "Feature Planner Agent",
  "description": "Step 1: Translates raw feature ideas into a functional specification list (UI actions, endpoint contracts, storage needs) without writing code.",
  "mode": "chat",
  "model": "qwen2.5-coder:latest",
  "tools": []
}
```

---

<!-- ==== 42/125 : headless_app/engine/agent_library/Planner/agent.md ==== -->

### headless_app/engine/agent_library/Planner/agent.md

```markdown
(empty file — 0 bytes)
```

---

<!-- ==== 43/125 : headless_app/engine/agent_library/rag_assistant/agent.json ==== -->

### headless_app/engine/agent_library/rag_assistant/agent.json

```json
{
  "id": "rag_assistant",
  "name": "RAG Assistant",
  "description": "Stateful agent with workspace file-management access and memory retrieval.",
  "mode": "agent",
  "model": "gemma4:e2b",
  "tools": [
    "map_files",
    "read_file",
    "write_text_file",
    "delete_files",
    "create_directory",
    "search_workspace",
    "get_current_date",
    "search_chat_logs"
  ],
  "tests": [
    {
      "id": "custom-mtqa6k4j-s1wo",
      "name": "Please help me consolidate my chat records in: E:\\data\\rag_s...",
      "steps": [
        "Please help me consolidate my chat records in: E:\\data\\rag_store\\chatlog\\agent-text-records",
        "Follow these steps sequentially using your tools:",
        "Run `map_files` on that directory to find all \".txt\" files.",
        "Use `read_file` to open and extract the text from each discovered file.",
        "Combine all the chat lines, remove any duplicate logs or repeat entries, and organize them into one chronological file.",
        "Run `write_text_file` to save this clean consolidated log in that same directory as \"consolidated_chat_records.txt\".",
        "Delete the original duplicate files with `delete_files` after identifying them."
      ],
      "expectedResult": {
        "mode": "type",
        "value": "nonEmpty"
      },
      "enabled": true
    }
  ]
}
```

---

<!-- ==== 44/125 : headless_app/engine/agent_library/rag_assistant/agent.md ==== -->

### headless_app/engine/agent_library/rag_assistant/agent.md

```markdown
# RAG Assistant

## role
You are the **RAG Assistant**, a workspace file-manager and memory-retrieval specialist.

## greeting
Standard greeting: I am a RAG Assistant.

## purpose
Retrieve insights from past sessions and help Jesus discover, read, write, and manage workspace files safely.

## boundaries
- **Past Memory:** When asked about past work, call `search_chat_logs`. Translate temporal keywords (like "last session") into topical terms.
- **Workspace Discovery:** Use `map_files` to inspect workspace structure. Do not assume file paths.
- **File Access:** Open text or document contents strictly via `read_file`. Keep the context window clean by only reading what is needed.
- **Writing Results:** Write results using `write_text_file`.
- **Workspace Search:** Use `search_workspace` to find matching text in workspace files.
- **Directories:** Use `create_directory` when a new folder is needed.
- **Grounding:** Ground every factual claim strictly in the retrieved logs or file contexts. Do not fabricate.

## how to call tools (critical)
You can only take actions by ACTUALLY executing the tools given to you. To call a tool, emit ONLY a
JSON object as your entire reply, with a `name` key and a `parameters` key:

    {"name": "read_file", "parameters": {"path": "E:\\data\\example.txt"}}

- Use exactly `parameters` for the arguments object (the runtime also accepts `arguments` or `args`).
- For multiple steps in one turn, emit a JSON ARRAY of such objects; each will be executed in order.
- Never describe a call in words, never put calls inside Python/markdown code blocks, and never write
  pseudo-code like `read_file("x")` — those are NOT executed.
- Never invent or guess file paths or file contents. Only reference paths you actually saw in the
  session state: `discovered_files`, `read_files`, or `output_files`.
- When reading many files, still read them one `read_file` call per file.

## file deletion
Use `delete_files` to permanently delete workspace files when the user requests their removal.
```

---

<!-- ==== 45/125 : headless_app/engine/agents/__init__.py ==== -->

### headless_app/engine/agents/__init__.py

```python
(empty file — 0 bytes)
```

---

<!-- ==== 46/125 : headless_app/engine/agents/factory.py ==== -->

### headless_app/engine/agents/factory.py

```python
"""
app/agents/factory.py
=====================

Constructs runtime Agents from agent definitions.

    build_agent(agent_id, model, bridge)
        ↓
    loader.load_definition()      (agent.md + agent.json, via agent roots)
        ↓
    registry: resolve tools       (IDs -> Python functions, provider bound)
        ↓
    PromptManager.build()         (sections + tool docstrings -> system prompt)
        ↓
    Agent  (with its own FileSession)

The caller never needs to know where definitions live or how prompts are
composed. Chat-mode agents get an empty tool list, which disables the
tool loop entirely - same Agent class, behavior driven by configuration.

Nothing here is process-wide: each agent gets its own tools (bound to its
own filesystem provider) and its own FileSession, so two agents can be
built and run side by side without sharing state.
"""

from pathlib import Path

from langchain_core.tools import BaseTool

from engine.agents.loader import (
    load_definition,
    load_definition_from_paths,
    agent_dir,
    AgentNotFoundError,
)
from engine.core.agent import Agent
from engine.core.prompt import PromptManager
from tools.registry import _replace_func, new_session, resolve_tools


class AgentDefinitionError(ValueError):
    """A definition parsed, but cannot produce a working agent.

    Distinct from AgentNotFoundError (no definition at all) so callers can
    tell "this agent does not exist" from "this agent is broken".
    """


def _session_aware(tool: BaseTool, session) -> BaseTool:
    """Record useful file-operation results without changing tool schemas."""
    import functools
    original = tool.func

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        _record_result(result, session)
        return result

    return _replace_func(tool, wrapper)


def _record_result(result, session) -> None:
    """Translate a tool result dict into this agent's FileSession state."""
    if not (isinstance(result, dict) and session is not None):
        return
    from tools.state import FileSession
    data = result.get("data") or {}
    if result.get("tool") == "map_files":
        files = data.get("files") or []
        session.add_discovered([f["path"] for f in files])
    elif result.get("tool") == "read_file":
        session.record_read(data.get("path", ""), data.get("extracted_content", ""))
    elif result.get("tool") == "write_text_file" and data.get("path"):
        session.add_output(data["path"])


def _append_grounding(agent_id: str, profile, bridge=None) -> None:
    """Append a compact grounding block to a tool-armed agent's system prompt.

    Small local models routinely call path tools with invented paths, bare
    filenames, or literally '/path/to/...' placeholders copied from a prompt.
    Pinning a real WORKSPACE ROOT plus the agent's own folder and skills dir
    gives the model deterministic places to start with map_files, and an
    explicit instruction to stop guessing once a lookup fails.

    When a Project Manager bridge is present it is the filesystem authority,
    so its workspace root becomes the grounding root instead of the local app.
    """
    from pathlib import Path

    if bridge is not None:
        workspace_root = str(getattr(bridge, "workspace_root", ""))
        if not workspace_root:
            bridge_health = getattr(bridge, "health", lambda: {})()
            workspace_root = str((bridge_health or {}).get("root", ""))
    else:
        workspace_root = str(Path(__file__).resolve().parents[2].resolve())

    root = Path(workspace_root)
    skill_dir = Path(__file__).resolve().parents[2] / "skills"
    skills = ", ".join(sorted(p.name for p in skill_dir.glob("*.md"))) if skill_dir.is_dir() else ""

    block = [
        "GROUNDING (read this before you call any file tool)",
        f"- WORKSPACE ROOT: {workspace_root}",
        f"- THIS AGENT FOLDER: {str(agent_dir(agent_id).resolve())}",
    ]
    if skills:
        block.append(f"- SKILLS DIRECTORY: {str(skill_dir.resolve())} (files: {skills})")
    block += [
        "- Use file paths relative to WORKSPACE ROOT. Start by calling map_files on the",
        "  root, then read_file only on a path map_files returned.",
        "- Never call readonly tools on a bare filename, a '/path/to/...' placeholder, or any",
        "  path you invented. If a tool reports 'not found', DO NOT guess another filename:",
        "  run map_files on WORKSPACE ROOT / THIS AGENT FOLDER first and read what exists.",
    ]
    profile.system_prompt = profile.system_prompt + "\n\n" + "\n".join(block)


def _assemble(
    meta: dict,
    sections: dict,
    agent_id: str,
    model: str | None,
    bridge=None,
) -> Agent:
    """Shared Agent construction from a parsed definition.

    Two things are deliberately per agent rather than per process:

    * the tools carry ``bridge`` as their own provider, so no build order or
      request ordering can redirect another agent's file operations;
    * the FileSession is created here, so discovered files and outputs
      belong to this agent alone.
    """
    definition = {"meta": meta, "sections": sections}

    mode = (meta.get("mode") or "chat").lower()
    tool_ids = [] if mode == "chat" else (meta.get("tools") or [])
    tools: list[BaseTool] = resolve_tools(tool_ids, provider=bridge)

    profile = PromptManager.build(definition, tools)

    if not (profile.system_prompt or "").strip():
        raise AgentDefinitionError(
            f"Agent '{agent_id}' has an empty system prompt, so it would "
            f"reply with no instructions. Its agent.md needs at least one "
            f"section the prompt composer reads - '## role', '## purpose', "
            f"'## personality', '## boundaries', '## communication', "
            f"'## principles' or '## decision style' (see "
            f"engine/core/prompt.py KNOWN_SECTIONS)."
        )

    if tools:
        _append_grounding(agent_id, profile, bridge=bridge)

    resolved_model = model or meta.get("model") or None
    session = new_session()
    tools = [_session_aware(fn, session) for fn in tools]
    return Agent(model=resolved_model, tools=tools, profile=profile, session=session)


def build_agent(agent_id: str, model: str | None = None, bridge=None) -> Agent:
    """Build a ready-to-use Agent for the given agent_id.

    Args:
        agent_id: id inside any registered agent root (see
                  engine/agents/roots.py) - the bundled library or the
                  Project Manager workspace.
        model:    explicit model override; when empty, falls back to the
                  agent's own "model" field, then to ask_llm's resolution
                  (config/models.json > first Ollama model).
        bridge:   optional Project Manager bridge (HTTP client or direct
                  filesystem authority). When present, the agent's file tools
                  route through the Project Manager instead of the local disk.
                  It is bound to this agent only.

    Raises AgentNotFoundError if the definition is missing, and
    AgentDefinitionError if it exists but cannot build a usable agent.
    """
    definition = load_definition(agent_id)
    return _assemble(
        definition["meta"],
        definition["sections"],
        agent_id,
        model,
        bridge=bridge,
    )


def build_agent_from_definition(
    json_path: str,
    md_path: str,
    model: str | None = None,
    bridge=None,
) -> Agent:
    """Build a ready-to-use Agent from explicit agent.json + agent.md paths.

    This is the headless construction path (run_single_agent, pipelines that
    take raw configs): the definition is loaded from any location, not only
    engine/agent_library/.

    Raises AgentNotFoundError if either file is missing/unreadable, and
    AgentDefinitionError if the definition cannot build a usable agent.
    """
    definition = load_definition_from_paths(json_path, md_path)
    meta = definition["meta"]
    agent_id = str(meta.get("id") or Path(json_path).parent.name or "custom")
    return _assemble(
        meta,
        definition["sections"],
        agent_id,
        model,
        bridge=bridge,
    )


def replay_history(agent: Agent, history: list[dict] | None) -> None:
    """Replay prior frontend turns ({role, content}) into the agent's history."""
    for m in (history or []):
        role = "assistant" if m.get("role") == "ai" else m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        agent.messages.append({"role": role, "content": content})


__all__ = [
    "build_agent",
    "build_agent_from_definition",
    "replay_history",
    "AgentNotFoundError",
    "AgentDefinitionError",
]
```

---

<!-- ==== 47/125 : headless_app/engine/agents/loader.py ==== -->

### headless_app/engine/agents/loader.py

```python
"""
app/agents/loader.py
====================

Locates, reads, and parses one agent definition.

An agent folder contains:
    agent.json  - metadata/configuration (id, name, mode, tools, model)
    agent.md    - behavior sections (## role, ## purpose, ## boundaries, ...)

load_definition() returns:
    {"meta": {...agent.json...}, "sections": {...parsed markdown sections...}}

Where agents live is decided by engine/agents/roots.py: the engine ships
with ``agent_library/``, and a host application may register more roots
(the Project Manager registers ``workspace/agents/``). Lookups here search
every registered root, so an agent is found by id regardless of which root
owns it.

This module does NOT run agents. Its job is only: find, read, parse, return.
"""

import json
import re
from pathlib import Path

from engine.agents import roots
from engine.agents.roots import (  # noqa: F401  (re-exported for callers)
    AGENT_MD_FILE,
    AGENT_META_FILE,
    AgentRoot,
    LIBRARY_ROOT_NAME,
    register_agent_root,
    unregister_agent_root,
)

#: Backwards-compatible alias for the built-in library root directory.
AGENT_LIBRARY_DIR = roots.DEFAULT_LIBRARY_DIR


def agent_dir(agent_id: str) -> Path:
    """The folder for an agent id inside the highest-precedence root.

    Searches every registered root (see engine/agents/roots.py): first the
    literal ``<root>/<agent_id>`` path, then each root's folders matched by
    their ``agent.json`` ``id`` field, so folder names and ids may differ.
    Falls back to the literal library path so callers that create folders
    (``save_markdown``) still work for brand-new agents.
    """
    found = roots.find_agent(agent_id)
    if found is not None:
        return found[1]
    return AGENT_LIBRARY_DIR / agent_id


def agent_root(agent_id: str) -> AgentRoot | None:
    """The registered root that owns ``agent_id``, or None."""
    found = roots.find_agent(agent_id)
    return found[0] if found is not None else None


def agent_json_path(agent_id: str) -> str | None:
    """Workspace-relative ``agent.json`` path for a registered agent."""
    found = roots.find_agent(agent_id)
    if found is None:
        return None
    root, directory = found
    return root.json_path(directory)


def agent_md_path(agent_id: str) -> str | None:
    """Workspace-relative ``agent.md`` path for a registered agent."""
    found = roots.find_agent(agent_id)
    if found is None:
        return None
    root, directory = found
    return root.md_path(directory)


def _resolve_agent_dir(agent_id: str) -> Path | None:
    """Find the on-disk folder for an agent by id across all roots.

    Returns ``None`` when nothing matches so callers can fall back to the
    literal path (which preserves the existing create-folder semantics for
    ``save_markdown`` on genuinely new agents).
    """
    found = roots.find_agent(agent_id)
    return found[1] if found is not None else None


def save_meta(agent_id: str, meta: dict) -> dict:
    """Merge `meta` into the agent's agent.json (top-level keys only) and
    write it back pretty-printed. Unknown keys survive untouched."""
    agent_path = agent_dir(agent_id)
    meta_file = agent_path / AGENT_META_FILE
    if not meta_file.exists():
        raise AgentNotFoundError(f"Agent config not found: {meta_file}")

    stored = json.loads(meta_file.read_text(encoding="utf-8"))
    stored.update(meta)
    meta_file.write_text(
        json.dumps(stored, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return stored


def save_markdown(agent_id: str, markdown: str) -> str:
    """Write the agent's behavior prose to agent.md."""
    agent_path = agent_dir(agent_id)
    agent_path.mkdir(parents=True, exist_ok=True)
    md_file = agent_path / AGENT_MD_FILE
    md_file.write_text(str(markdown), encoding="utf-8")
    return str(markdown)


def save_tests(agent_id: str, tests: list) -> list:
    """Store the agent's own chat tests under agent.json#tests.

    Tests are scoped by their location, so any stored `agentId` is dropped;
    ensures every test keeps a unique id.
    """
    normalized = []
    for test in tests or []:
        if not isinstance(test, dict):
            continue
        entry = dict(test)
        entry.pop("agentId", None)
        if not entry.get("id"):
            entry["id"] = "t-" + json.dumps(entry, sort_keys=True)[:8]
        normalized.append(entry)
    save_meta(agent_id, {"tests": normalized})
    return normalized


class AgentNotFoundError(FileNotFoundError):
    """Raised when an agent folder or its required files are missing."""


def _parse_sections(text: str) -> dict:
    """Split agent.md into '## <name>' sections (section name lowercased)."""
    sections = {}
    current = None
    buffer = []
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if match:
            if current is not None:
                sections[current] = "".join(buffer)
            current, buffer = match.group(1).strip().lower(), []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "".join(buffer)
    return sections


def _clean_body(text: str) -> str:
    """Trim blank lines and '---' separators from the edges of a section body."""
    lines = text.splitlines()
    while lines and (not lines[0].strip() or lines[0].strip() in ("---", "***")):
        lines.pop(0)
    while lines and (not lines[-1].strip() or lines[-1].strip() in ("---", "***")):
        lines.pop()
    return "\n".join(lines).strip("\n")


def load_definition(agent_id: str) -> dict:
    """Load one agent definition from agent_library/{agent_id}/.

    Returns {"meta": dict, "sections": dict}. Raises AgentNotFoundError
    when the folder or either required file is missing/unreadable.
    """
    agent_dir = _resolve_agent_dir(agent_id)
    if agent_dir is None:
        agent_dir = AGENT_LIBRARY_DIR / agent_id
    json_file = agent_dir / AGENT_META_FILE
    md_file = agent_dir / AGENT_MD_FILE

    if not json_file.exists():
        raise AgentNotFoundError(f"Agent not found: {json_file}")
    if not md_file.exists():
        raise AgentNotFoundError(f"Agent not found: {md_file}")

    try:
        meta = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentNotFoundError(f"Agent config unreadable: {json_file} ({exc})")

    try:
        md_text = md_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentNotFoundError(f"Agent markdown unreadable: {md_file} ({exc})")

    raw_sections = _parse_sections(md_text)
    # The '# Title' line before the first section is ignored; every
    # '## section' body gets whitespace/separator cleanup.
    sections = {name: _clean_body(body) for name, body in raw_sections.items()}

    return {"meta": meta, "sections": sections}


def load_definition_from_paths(
    json_path: str | Path,
    md_path: str | Path,
) -> dict:
    """Load one agent definition from explicit agent.json + agent.md paths.

    This is the headless entry point used when an agent's definition comes
    from arbitrary locations (e.g. ad-hoc agents built by run_single_agent)
    instead of the bundled engine/agent_library/.

    Returns {"meta": dict, "sections": dict}. Raises AgentNotFoundError
    when either file is missing/unreadable.
    """
    json_file = Path(json_path)
    md_file = Path(md_path)

    if not json_file.exists():
        raise AgentNotFoundError(f"Agent config not found: {json_file}")
    if not md_file.exists():
        raise AgentNotFoundError(f"Agent markdown not found: {md_file}")

    try:
        meta = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentNotFoundError(f"Agent config unreadable: {json_file} ({exc})")

    try:
        md_text = md_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentNotFoundError(f"Agent markdown unreadable: {md_file} ({exc})")

    raw_sections = _parse_sections(md_text)
    sections = {name: _clean_body(body) for name, body in raw_sections.items()}

    return {"meta": meta, "sections": sections}
```

---

<!-- ==== 48/125 : headless_app/engine/agents/registry.py ==== -->

### headless_app/engine/agents/registry.py

```python
"""
app/agents/registry.py
======================

Agent discovery over the registered roots (engine/agents/roots.py).

The filesystem is the source of truth: every folder in a registered root
that contains an agent.json is an available agent. Because roots are
searched most-recently-registered first, a workspace agent shadows a
library agent declaring the same id - which is the same precedence
``loader`` uses when it builds one agent, so discovery and building can
never disagree.

Registering ``workspace/agents/`` (the Project Manager does this at
startup) is therefore all it takes for a newly created agent to appear
in GET /api/agents, in the frontend selector, and in every id-based
lookup: no code changes, no manual lists, no second scanner.
"""

import json

from engine.agents import roots
from engine.agents.loader import AGENT_LIBRARY_DIR  # noqa: F401  (re-exported)


def _read_meta(agent_dir) -> dict | None:
    """Parsed agent.json, or None when missing/unreadable/malformed."""
    meta_file = agent_dir / roots.AGENT_META_FILE
    if not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[REGISTRY] skipping {agent_dir}: unreadable agent.json ({exc})")
        return None
    return meta if isinstance(meta, dict) else None


def list_agents() -> list[dict]:
    """One summary per discovered agent, highest-precedence root first.

        [{"id", "name", "description", "mode", "model", "tools",
          "source", "json_path", "md_path", "complete"}, ...]

    Deduplicated by id: the first root that provides an id wins, and
    lower-precedence roots with the same id are skipped. An agent whose
    agent.json parsed but whose agent.md is missing is still returned,
    with ``complete: False``, so the UI can show it as a work in
    progress instead of it silently disappearing.
    """
    summaries: list[dict] = []
    claimed: set[str] = set()

    for root in roots.agent_roots():
        for agent_dir in root.agent_dirs():
            meta = _read_meta(agent_dir)
            if meta is None:
                # No readable agent.json: not an agent folder. A folder
                # with no meta at all is silently ignored, exactly as
                # before, so a half-created folder cannot break the list.
                continue

            agent_id = str(meta.get("id") or agent_dir.name)
            if agent_id in claimed:
                # A higher-precedence root already owns this id.
                continue
            claimed.add(agent_id)

            md_file = agent_dir / roots.AGENT_MD_FILE
            summaries.append({
                "id": agent_id,
                "name": meta.get("name") or agent_dir.name,
                "description": meta.get("description", "") or "",
                "mode": meta.get("mode", "chat") or "chat",
                "model": meta.get("model", "") or "",
                "tools": list(meta.get("tools") or []),
                "source": root.source,
                "json_path": root.json_path(agent_dir),
                "md_path": root.md_path(agent_dir),
                "complete": md_file.exists(),
            })

    return summaries


def get_agent_meta(agent_id: str) -> dict | None:
    """Return the summary for one agent id, or None if not registered."""
    for summary in list_agents():
        if summary["id"] == agent_id:
            return summary
    return None


__all__ = ["list_agents", "get_agent_meta", "AGENT_LIBRARY_DIR"]
```

---

<!-- ==== 49/125 : headless_app/engine/agents/roots.py ==== -->

### headless_app/engine/agents/roots.py

```python
"""
engine/agents/roots.py
======================

Pluggable agent roots.

An *agent root* is a directory whose immediate children are agent folders
(one folder per agent, holding ``agent.json`` + ``agent.md``). The engine
registers exactly one root at import time::

    engine/agent_library/

so the headless runtime keeps working entirely on its own. A host
application may register further roots; the Project Manager registers
``workspace/agents/`` while its server is starting.

Once a root is registered, every lookup in the engine sees its agents -
there is no separate "library mode" and "workspace mode". ``build_agent``,
chat, single runs and pipelines all resolve agent ids through this module,
so an agent becomes runnable the moment its folder is discovered.

Precedence
----------
Roots are searched most-recently-registered first. A workspace agent
therefore shadows a library agent that declares the same ``id``, which is
the precedence the Project Manager already used when it looked up a single
definition. Re-registering a name replaces it and promotes it, so a server
that re-registers its root on every startup stays idempotent.

This module deliberately knows nothing about the Project Manager. The
wiring lives in the repository-root ``server.py`` host application.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

#: Canonical file names inside an agent folder.
AGENT_META_FILE = "agent.json"
AGENT_MD_FILE = "agent.md"

#: The root the engine ships with.
LIBRARY_ROOT_NAME = "library"

DEFAULT_LIBRARY_DIR = (
    Path(__file__).resolve().parent.parent / "agent_library"
)


# ==========================================================================
# ROOT DESCRIPTOR
# ==========================================================================

@dataclass(frozen=True)
class AgentRoot:
    """One directory of agent folders."""

    name: str
    path: Path
    source: str

    def agent_dirs(self) -> Iterator[Path]:
        """Yield every candidate agent folder, sorted for determinism."""
        if not self.path.is_dir():
            return
        for child in sorted(self.path.iterdir()):
            if not child.is_dir() or child.name.startswith(("_", ".")):
                continue
            yield child

    def json_path(self, agent_dir: Path) -> str:
        """Workspace-relative ``agent.json`` path for the agent API."""
        return str(agent_dir / AGENT_META_FILE).replace("\\", "/")

    def md_path(self, agent_dir: Path) -> str:
        """Workspace-relative ``agent.md`` path for the agent API."""
        return str(agent_dir / AGENT_MD_FILE).replace("\\", "/")


# ==========================================================================
# ROOT REGISTRY
# ==========================================================================

#: Registered roots, lowest precedence first.
_roots: list[AgentRoot] = []


def register_agent_root(
    name: str,
    path: str | Path,
    source: str | None = None,
) -> AgentRoot:
    """Register (or re-register) an agent root and give it top precedence.

    Args:
        name:    unique key, e.g. ``"workspace"``.
        path:    directory holding one folder per agent.
        source:  value reported as each agent's ``source``; defaults to
                 ``name``.

    Returns:
        The registered :class:`AgentRoot`.
    """
    resolved = Path(path).expanduser().resolve()
    root = AgentRoot(name=name, path=resolved, source=source or name)
    unregister_agent_root(name)
    _roots.append(root)
    return root


def unregister_agent_root(name: str) -> bool:
    """Remove a root by name. Returns True when something was removed."""
    for index, existing in enumerate(_roots):
        if existing.name == name:
            del _roots[index]
            return True
    return False


def agent_roots() -> list[AgentRoot]:
    """Registered roots, highest precedence first."""
    return list(reversed(_roots))


def get_root(name: str) -> AgentRoot | None:
    for root in agent_roots():
        if root.name == name:
            return root
    return None


def reset_agent_roots() -> AgentRoot:
    """Drop every root except the built-in library root (used by tests)."""
    _roots.clear()
    return register_agent_root(
        LIBRARY_ROOT_NAME, DEFAULT_LIBRARY_DIR, source="library"
    )


# The engine always has its bundled library available.
reset_agent_roots()


# ==========================================================================
# RESOLUTION
# ==========================================================================

def _read_meta(agent_dir: Path) -> dict | None:
    meta_file = agent_dir / AGENT_META_FILE
    if not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return meta if isinstance(meta, dict) else None


def find_agent(agent_id: str) -> tuple[AgentRoot, Path] | None:
    """Locate an agent folder by id across every registered root.

    Two strategies per root, tried highest precedence first:
        1. Literal: ``<root>/<agent_id>`` is a directory.
        2. Scan: read ``agent.json`` in each child folder and match its
           ``id`` field, so folder names and ids may differ (e.g. the
           ``Planner`` folder declaring id ``feature_planner_agent``).

    Returns:
        ``(root, agent_dir)`` for the winning match, else ``None``.
    """
    if not agent_id:
        return None

    for root in agent_roots():
        literal = root.path / agent_id
        if literal.is_dir():
            return root, literal

    for root in agent_roots():
        for child in root.agent_dirs():
            meta = _read_meta(child)
            if meta is not None and meta.get("id") == agent_id:
                return root, child

    return None


__all__ = [
    "AGENT_META_FILE",
    "AGENT_MD_FILE",
    "AgentRoot",
    "DEFAULT_LIBRARY_DIR",
    "LIBRARY_ROOT_NAME",
    "agent_roots",
    "find_agent",
    "get_root",
    "register_agent_root",
    "reset_agent_roots",
    "unregister_agent_root",
]
```

---

<!-- ==== 50/125 : headless_app/engine/core/__init__.py ==== -->

### headless_app/engine/core/__init__.py

```python
(empty file — 0 bytes)
```

---

<!-- ==== 51/125 : headless_app/engine/core/agent.py ==== -->

### headless_app/engine/core/agent.py

````python
"""
app/core/agent.py
=================

The reusable runtime agent.

    AgentProfile - the agent's identity and prompt sections (from config)
    Agent        - the generic think / act / observe loop

The Agent does not know what KIND of agent it is (research, coding, chat...).
Its behavior comes entirely from its AgentProfile and the tools it was given.
"""

import inspect
import json
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, List

from engine.core.llm import ask_llm
from tools.state import FileSession


# ==========================================================================
# AGENT PROFILE
# --------------------------------------------------------------------------
# The identity and behavior of an agent. Metadata fields come from
# agent.json; the section fields come from agent.md.
# ==========================================================================

@dataclass
class AgentProfile:
    """Identity + behavior of one agent.

    From agent.json:    id, name, description, mode
    From agent.md:      role, purpose, personality, boundaries,
                        communication, principles, decision_style,
                        plus any extra '## sections' (extras)
    Composed at build:  system_prompt
    """

    id: str = ""
    name: str = ""
    description: str = ""
    mode: str = "chat"

    system_prompt: str = ""

    # Prompt sections from agent.md
    role: str = ""
    purpose: str = ""
    personality: str = ""
    boundaries: str = ""
    communication: str = ""
    principles: str = ""
    decision_style: str = ""

    # Documentation only (NOT included in the system prompt)
    priorities: str = ""

    extras: dict = field(default_factory=dict)


# ==========================================================================
# THE GENERIC AGENT OBJECT
# --------------------------------------------------------------------------
# The Agent maintains conversation history and interacts with the LLM
# backend through structured messages. When tools are attached, the LLM
# can request tool calls, which flow through act() -> observe() and a
# follow-up LLM round.
# ==========================================================================

class Agent:
    """A generic AI agent that can think (ask the LLM), act (call a tool) and
    observe (record the tool's result back into the conversation)."""

    def __init__(self, model: str | None, tools: List[Callable], profile: AgentProfile, session: FileSession | None = None):
        """Store the model, tools, profile, and optional FileSession."""
        self.model = model
        self.profile = profile
        self.tools = {
            getattr(f, "name", None) or getattr(f, "__name__"): f
            for f in tools
        }
        self.messages: List[dict] = []
        self.session = session or FileSession()
        self.tool_events: List[dict] = []  # structured tool-execution log for this turn

    def _extract_text_tool_calls(self, content: str) -> List[dict]:
        """Find tool calls that a model wrote as plain-text JSON instead of using
        Ollama's native tool_calls field (a common quirk of small local models).

        Accepts bare JSON, ```json fenced blocks, a JSON object or ARRAY of
        objects embedded in prose, and objects wrapped under keys like
        "tool_calls" / "calls" / "functions". ONLY names present in self.tools
        are returned, and only when the call's required arguments are present
        (so prose that merely mention a tool is never executed).

        Tool-call objects may use "arguments", "args" OR "parameters" as the
        arguments key (small models differ).
        """
        text = (content or "").strip()
        if text.startswith("```"):  # unwrap markdown code fences
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()

        candidates: List[dict] = []
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        if parsed is not None:
            # Top-level array of calls, object wrapped around a list of calls,
            # or a single call object.
            if isinstance(parsed, list):
                candidates.extend(parsed)
            elif isinstance(parsed, dict):
                found = False
                for wrap_key in ("tool_calls", "calls", "functions", "call"):
                    wrapped = parsed.get(wrap_key)
                    if isinstance(wrapped, list):
                        candidates.extend(wrapped)
                        found = True
                        break
                    if isinstance(wrapped, dict):
                        candidates.append(wrapped)
                        found = True
                        break
                if not found:
                    candidates.append(parsed)
        else:
            # one nesting level allowed so nested "arguments" objects are captured
            for match in re.finditer(r"\{(?:[^{}]|\{[^{}]*\})*\}", content or ""):
                try:
                    candidates.append(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    continue

        calls: List[dict] = []
        for item in candidates:
            if not isinstance(item, dict) or item.get("name") not in self.tools:
                continue
            # Accept "arguments", "args", or "parameters" as the args key.
            args = item.get("arguments", item.get("args", item.get("parameters", {}))) or {}
            args = self._normalize_args(item["name"], args)
            if not self._has_required_args(item["name"], args):
                continue
            calls.append({"function": {"name": item["name"], "arguments": args}})
        return calls

    def _has_required_args(self, name: str, args: dict) -> bool:
        """True when every required (no-default) parameter of the tool is present
        in args. Prevents executing narration that merely mentions a tool."""
        fn = self.tools.get(name)
        if fn is None:
            return False
        args_schema = getattr(fn, "args_schema", None)
        if args_schema is not None:
            required = {
                name for name, field in args_schema.model_fields.items()
                if field.is_required()
            }
            return required.issubset(args.keys())
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return True
        required = {p.name for p in sig.parameters.values() if p.default is inspect.Parameter.empty}
        return required.issubset(args.keys())

    def _normalize_args(self, name: str, args) -> dict:
        """Coerce the many different argument shapes small local models send for
        tool calls into a clean dict of keyword args the tool actually accepts.

        Handles:
            - args as a JSON string: '{"path": "..."}'
            - single-key wrappers:   {"args": {...}}, {"arguments": {...}}
            - positional list:       ["E:\\..."], [name, content, path]
            - string booleans:       {"overwrite": "false"} -> False
            - anything non-dict:     gracefully -> {}
        """
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                return {}

        if isinstance(args, dict) and len(args) == 1:
            if "args" in args:
                args = args["args"]
            elif "arguments" in args:
                args = args["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, TypeError):
                    return {}

        if isinstance(args, list):
            fn = self.tools.get(name)
            if fn is not None:
                try:
                    schema = getattr(fn, "args_schema", None)
                    params = list(schema.model_fields) if schema is not None else [
                        p.name for p in inspect.signature(fn).parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    bound = {}
                    for param, value in zip(params, args):
                        if param not in bound:
                            bound[param] = value
                    bool_params = {
                        field_name for field_name, field in schema.model_fields.items()
                        if field.annotation is bool
                    } if schema is not None else set()
                    return self._coerce_bools(bound, bool_params)
                except (TypeError, ValueError):
                    pass
            return {}

        if not isinstance(args, dict):
            return {}

        # Drop any keys that aren't actual parameters of the tool, so stray
        # keys the model invents (e.g. "path" on a no-arg tool) never crash
        # the call. Tools exposing **kwargs keep everything.
        bool_params = set()
        fn = self.tools.get(name)
        if fn is not None:
            schema = getattr(fn, "args_schema", None)
            if schema is not None:
                valid = set(fn.args)
                args = {k: v for k, v in args.items() if k in valid}
                bool_params = {
                    field_name for field_name, field in schema.model_fields.items()
                    if field.annotation is bool
                }
                return self._coerce_bools(args, bool_params)
            try:
                sig = inspect.signature(fn)
                if not any(
                    p.kind == inspect.Parameter.VAR_KEYWORD
                    for p in sig.parameters.values()
                ):
                    valid = {p.name for p in sig.parameters.values() if p.kind in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        inspect.Parameter.KEYWORD_ONLY,
                    )}
                    args = {k: v for k, v in args.items() if k in valid}
                bool_params = {
                    p.name for p in sig.parameters.values() if p.annotation is bool
                }
            except (TypeError, ValueError):
                pass

        return self._coerce_bools(args, bool_params)

    @staticmethod
    def _coerce_bools(args: dict, bool_params: set) -> dict:
        """Turn string 'true'/'false'/'1'/'0' into real bools, but ONLY for
        parameters that are actually typed as bool (so a string param like
        name="yes" is never mangled)."""
        coerced = dict(args)
        for key, value in list(coerced.items()):
            if (
                key in bool_params
                and isinstance(value, str)
                and value.strip().lower() in ("true", "false", "yes", "no", "1", "0")
            ):
                coerced[key] = value.strip().lower() in ("true", "yes", "1")
        return coerced

    MAX_TOOL_ROUNDS = 6
    REPEAT_LIMIT = 3
    _REPEAT_WARNING = (
        "System guard: you have already sent this exact tool call with the "
        "same arguments earlier in this conversation, and it already ran. "
        "Calling it again will not change its result. STOP issuing tool calls "
        "now and answer in plain text, using the tool results you already have."
    )
    _REPEAT_FEEDBACK = (
        "(The agent kept repeating the same tool call and stopped answering "
        "in text. Please rephrase your request or ask again.)"
    )

    @staticmethod
    def _round_signature(tool_calls) -> tuple:
        """Order-independent, hashable fingerprint of one tool round so two
        rounds with the same calls and same arguments compare as identical."""
        normalized = []
        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            name = str(fn.get("name", ""))
            args = fn.get("arguments", {})
            if isinstance(args, dict):
                items = tuple(sorted((str(k), repr(v)) for k, v in args.items()))
            else:
                items = (repr(args),)
            normalized.append((name, items))
        return tuple(sorted(normalized))

    def think(self, user_input: str) -> str:
        """Add user input to history, send the conversation to the LLM, and return its reply."""
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.profile.system_prompt})

        self._inject_session_context()

        self.messages.append({"role": "user", "content": user_input})

        tool_callables = list(self.tools.values()) if self.tools else None

        message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
        self.messages.append(message)

        # Native tool_calls, or calls the model wrote as plain-text JSON.
        # Both paths flow through act()/observe() and a follow-up LLM round.
        # Keep looping while the model keeps issuing tool calls, so a chain of
        # tool calls always ends in a real text reply (never a silent "").
        tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(message.get("content", ""))
        last_signature = None
        repeat_count = 0
        for _ in range(self.MAX_TOOL_ROUNDS):
            if not tool_calls:
                break

            signature = self._round_signature(tool_calls)
            if signature == last_signature:
                repeat_count += 1
            else:
                repeat_count = 1
                last_signature = signature

            if repeat_count >= self.REPEAT_LIMIT:
                print(f"[Agent.think] identical tool round {signature} repeated x{repeat_count}; suppressing.")
                self.messages.append({"role": "user", "content": self._REPEAT_WARNING})
                message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
                self.messages.append(message)
                content = (message.get("content", "") or "").strip()
                tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(content)
                if content and not tool_calls:
                    print("[Agent.think] loop suppressed; model answered in text.")
                    return content
                print("[Agent.think] model ignored the loop warning; returning feedback reply.")
                return self._REPEAT_FEEDBACK

            origin = "native tool_calls" if message.get("tool_calls") else "TEXT reply"
            print(f"[Agent.think] Executing {len(tool_calls)} tool call(s) from {origin}.")
            for tool_call in tool_calls:
                result = self.act(tool_call, origin)
                self.observe(tool_call["function"]["name"], result)

            self._inject_session_context()

            message = ask_llm(messages=self.messages, model=self.model, tools=tool_callables)
            self.messages.append(message)
            tool_calls = message.get("tool_calls") or self._extract_text_tool_calls(message.get("content", ""))

        content = message.get("content", "") or ""
        if not content.strip():
            print(f"[Agent.think] No text reply after {self.MAX_TOOL_ROUNDS} tool round(s); returning fallback.")
            return "(I ran my tools but did not produce a final answer. Please ask again.)"
        return content

    _SESSION_CONTEXT_ROLE = "system"
    _SESSION_CONTEXT_PREFIX = "CURRENT FILE SESSION STATE"

    def _inject_session_context(self) -> None:
        """Add current FileSession state as context for the model, replacing any
        previously injected block so history doesn't grow duplicate state."""
        if not self.session:
            return
        state = self.session.get_state()
        if not any(state.values()):
            return
        context_entries = []
        for key, value in state.items():
            if value:
                context_entries.append(f"  {key}: {value}")
        context = f"{self._SESSION_CONTEXT_PREFIX} (from previous tool calls):\n" + "\n".join(context_entries)

        # Replace any earlier context block instead of appending another one.
        for i, message in enumerate(self.messages):
            if (
                message.get("role") == self._SESSION_CONTEXT_ROLE
                and str(message.get("content", "")).startswith(self._SESSION_CONTEXT_PREFIX)
            ):
                self.messages[i]["content"] = context
                return
        self.messages.append({"role": self._SESSION_CONTEXT_ROLE, "content": context})

    @staticmethod
    def _op_succeeded(result) -> tuple[bool, str]:
        """Classify a tool's result as (ok, error_msg).

        Tools report failed OPERATIONS as dicts with success=False or an
        "error" key even when the call itself executed (e.g. read_file on a
        path that does not exist). Execution-level 'success' and operation
        success are different things; the op_ok field records the difference
        so the live feed can flag hallucinated paths instead of showing
        [OK] everywhere.

        The result may arrive as a real dict or as a string representation
        (str(dict) uses single quotes, which is NOT valid JSON - so this
        inspects the object directly and only JSON-parses real JSON strings).
        """
        payload = result
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                return True, ""
        if isinstance(payload, dict):
            if payload.get("success") is False:
                return False, str(payload.get("error") or "operation failed")
            if payload.get("error"):
                return False, str(payload["error"])
        return True, ""

    def act(self, tool_call: dict, origin: str = "") -> str:
        """Run one tool that the LLM asked for, using the name and args it chose."""
        name = tool_call.get("function", {}).get("name")
        args = self._normalize_args(name, tool_call.get("function", {}).get("arguments", {}))
        timestamp = datetime.now().strftime("%H:%M:%S")
        if name in self.tools:
            try:
                tool = self.tools[name]
                raw_result = tool.invoke(args) if hasattr(tool, "invoke") else tool(**args)
                result = str(raw_result)
                print(f"[Agent.act] Executed {name} -> {result[:100]}...")
                op_ok, op_error = self._op_succeeded(raw_result)
                run_event = {
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "result_preview": result[:200],
                    "status": "success",
                    "op_ok": op_ok,
                }
                if op_error:
                    run_event["op_error"] = op_error
                self.tool_events.append(run_event)
                self._log_tool_event({
                    **run_event,
                    "origin": origin,
                })
                return result
            except Exception as e:
                print(f"[Agent.act] Error executing {name}: {e}")
                self.tool_events.append({
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "error": str(e),
                    "status": "error",
                })
                self._log_tool_event({
                    "time": timestamp,
                    "tool": name,
                    "args": args,
                    "error": str(e),
                    "status": "error",
                    "origin": origin,
                })
                return f"Error executing tool: {e}"
        print(f"[Agent.act] Missing tool requested: {name}")
        self.tool_events.append({
            "time": timestamp,
            "tool": name,
            "args": args,
            "status": "missing",
        })
        self._log_tool_event({
            "time": timestamp,
            "tool": name,
            "args": args,
            "status": "missing",
            "origin": origin,
        })
        return f"Error: {name} missing"

    def _log_tool_event(self, event: dict) -> None:
        """Report one structured tool event to the process-wide tool log
        (headless data/toollog/tool_usage.jsonl). Deliberately fail-safe so a
        logging problem can never break the tool call that just succeeded."""
        event.setdefault("agentId", self.profile.id or "")
        event.setdefault("agentName", self.profile.name or "")
        event.setdefault("model", self.model or "")
        event["time"] = datetime.now().isoformat(timespec="seconds")
        try:
            from tools.chatlog import append_tool_event

            append_tool_event(event)
        except Exception:
            pass

    def observe(self, name: str, result: str) -> None:
        """Record a tool's result back into the conversation history."""
        self.messages.append({"role": "tool", "content": result, "name": name})
````

---

<!-- ==== 52/125 : headless_app/engine/core/llm.py ==== -->

### headless_app/engine/core/llm.py

```python
"""
app/core/llm.py
===============

The LLM backend. Everything that talks to Ollama lives here:

    ask_llm               - send structured messages, get the reply message dict
    _resolve_model        - explicit arg > config/models.json > first Ollama model
    _get_context_window   - model context length lookup (capped)
    refresh_models        - scan installed Ollama models -> config/models.json

The Agent does not know about Ollama details; it only calls ask_llm().
"""

import json
import time
from pathlib import Path
from typing import Callable, List

import ollama

MAX_NUM_CTX = 32768
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

# How long a successful Ollama model scan is trusted before we re-list.
_MODEL_SCAN_TTL = 60.0
_model_scan_cache = {"at": -1.0, "ids": []}  # ordered list of installed model ids


# ==========================================================================
# MODEL RESOLUTION AND CONTEXT SIZING
# ==========================================================================

def _config_model_ids() -> list:
    """The model ids in config/models.json (re-scanned by refresh_models() at
    every server startup, so it reflects THIS machine's Ollama)."""
    try:
        data = json.loads((CONFIG_DIR / "models.json").read_text(encoding="utf-8"))
        return [m.get("id") for m in data.get("models", []) if m.get("id")]
    except (OSError, json.JSONDecodeError):
        return []


def _installed_model_ids() -> list:
    """Ordered ids of installed Ollama models, cached briefly.

    A failed scan keeps the previous snapshot (or [] when there was none),
    so "no models visible" and "Ollama unreachable" stay distinguishable.
    """
    global _model_scan_cache
    now = time.monotonic()
    if _model_scan_cache["ids"] and now - _model_scan_cache["at"] < _MODEL_SCAN_TTL:
        return _model_scan_cache["ids"]
    try:
        ids = []
        for m in ollama.list().get("models", []):
            mid = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
            if mid and mid not in ids:
                ids.append(mid)
        _model_scan_cache = {"at": now, "ids": ids}
    except Exception:
        pass  # keep whatever we had before
    return _model_scan_cache["ids"]


# Per-model capabilities (ollama.show), cached per process. None = unknown
# (older Ollama that does not report capabilities yet).
_cap_cache: dict = {}


def _capabilities(model: str) -> list | None:
    """The reported capabilities for `model` (['completion', 'tools', ...])."""
    if model in _cap_cache:
        return _cap_cache[model]
    try:
        info = ollama.show(model=model).model_dump()
        caps = info.get("capabilities") or []
        _cap_cache[model] = caps
        return caps
    except Exception:
        _cap_cache[model] = None
        return None


def _supports_tools(model: str) -> bool | None:
    """True/False when Ollama reports capabilities, None when unknown."""
    caps = _capabilities(model)
    if caps is None:
        return None
    return "tools" in caps


def _resolve_model(model: str | None, require_tools: bool = False) -> str:
    """Pick which model to use: explicit arg (when suitable) > config > Ollama list.

    An explicitly requested model that is NOT installed on this machine is
    dropped so the app falls back to a detected one instead of erroring with
    a 404 - this keeps settings written on one OS (e.g. Windows) from
    breaking the app on another (e.g. Linux). When no models are visible at
    all, the explicit request is honoured as-is (previous behaviour).

    `require_tools`: when the caller needs tool calling, models that Ollama
    reports as NOT supporting tools are skipped so an agent with tools never
    gets a model that Ollama will reject with 400.
    """
    explicit = None
    if model:
        detected = set(_config_model_ids()) | set(_installed_model_ids())
        if model in detected:
            explicit = model
        elif detected:
            print(
                f"[ask_llm] requested model '{model}' is not installed locally - "
                "falling back to a detected model"
            )
        else:
            print(f"[ask_llm] no installed models visible - using requested '{model}' as-is")
            return model

    # Ordered candidates: explicit > config/models.json > live Ollama scan.
    candidates = []
    if explicit:
        candidates.append(explicit)
    for m in _config_model_ids():
        if m not in candidates:
            candidates.append(m)
    for m in _installed_model_ids():
        if m not in candidates:
            candidates.append(m)

    if require_tools:
        # Prefer models that definitely support tools; keep "unknown" ones as a
        # last resort (older Ollama), push confirmed-no-tools models to the end.
        tooled = [c for c in candidates if _supports_tools(c) is True]
        unknown = [c for c in candidates if _supports_tools(c) is None]
        others = [c for c in candidates if c not in tooled and c not in unknown]
        ordered = tooled + unknown + others
        if explicit and others and explicit in others:
            print(
                f"[ask_llm] requested model '{explicit}' does not support tools - "
                "falling back to one that does"
            )
    else:
        ordered = candidates

    if not ordered:
        raise RuntimeError(
            "No model available. Specify one in the frontend, "
            "add models to config/models.json, or install one in Ollama."
        )

    chosen = ordered[0]
    if chosen is explicit:
        print(f"[ask_llm] explicit model used: {model}")
    elif chosen in _config_model_ids():
        print(f"[ask_llm] model from config/models.json: {chosen}")
    else:
        print(f"[ask_llm] first installed Ollama model: {chosen}")
    return chosen


def _get_context_window(model: str) -> int | None:
    """Return the model's max context length from Ollama, capped; None if unknown."""
    try:
        info = ollama.show(model=model).model_dump()
        model_info = info.get("modelinfo") or info.get("model_info") or {}
        length = model_info.get("llama.context_length")
        if not length:
            return None
        return min(int(length), MAX_NUM_CTX)
    except Exception as exc:
        print(f"[ask_llm] context lookup failed for {model}: {exc}")
        return None


def _ollama_tool_schema(tool) -> dict:
    """Convert a LangChain input schema into Ollama's function-tool format."""
    args_schema = getattr(tool, "args_schema", None)
    if args_schema is None:
        raise TypeError(f"Tool '{getattr(tool, 'name', tool)}' has no argument schema.")
    schema = args_schema.model_json_schema()
    properties = {}
    for name, value in (schema.get("properties") or {}).items():
        prop = {
            key: value[key]
            for key in ("type", "description", "enum", "items")
            if key in value
        }
        properties[name] = prop
    parameters = {"type": "object", "properties": properties}
    if schema.get("required"):
        parameters["required"] = schema["required"]
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters,
        },
    }


# ==========================================================================
# THE LLM CALL
# ==========================================================================

def ask_llm(messages: List[dict], model: str | None = None, tools: List[Callable] | None = None) -> dict:
    """Send structured messages to the resolved model via Ollama and return the full message dict."""
    resolved = _resolve_model(model, require_tools=bool(tools))

    # A model Ollama reports as NOT supporting tools must not be asked to
    # (Ollama rejects the request with 400) - drop the tool schemas and let
    # the agent answer without tool use rather than crash the chat.
    if tools and _supports_tools(resolved) is False:
        print(f"[ask_llm] model '{resolved}' does not support tools - continuing without tool use")
        tools = None

    num_ctx = _get_context_window(resolved)

    options = {"num_ctx": num_ctx} if num_ctx else {}
    print(f"[ask_llm] calling ollama.chat with model={resolved} num_ctx={num_ctx} tools={len(tools) if tools else 0}")

    for attempt in (1, 2):
        kwargs = {
            "model": resolved,
            "messages": messages,
            "options": options,
        }
        if tools:
            kwargs["tools"] = [
                _ollama_tool_schema(tool) if hasattr(tool, "args_schema") else tool
                for tool in tools
            ]

        response = ollama.chat(**kwargs)
        message = response["message"]

        content = message.get("content", "") or ""
        tool_calls = message.get("tool_calls") or []

        print(f"[ask_llm] reply received ({len(content)} chars, {len(tool_calls)} tool calls)")

        if content.strip() or tool_calls:
            return message

        print(f"[ask_llm] empty reply on attempt {attempt} - retrying")

    return {"role": "assistant", "content": "(The model returned an empty reply. Please try again.)"}


# ==========================================================================
# MODEL SCAN (startup)
# --------------------------------------------------------------------------
# Lists locally installed Ollama models and writes config/models.json so
# the frontend dropdown has something to show. An empty scan (Ollama down)
# leaves the last known good file untouched.
# ==========================================================================

def scan_models() -> list:
    """Return the deduped list of locally installed Ollama models."""
    models = []
    try:
        for m in ollama.list().get("models", []):
            model_id = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
            size = m.get("size", 0) if isinstance(m, dict) else getattr(m, "size", 0)
            if model_id:
                models.append({"id": model_id, "name": model_id, "source": "ollama", "size": size})
    except Exception as exc:
        print(f"[llm] ollama scan failed: {exc}")

    seen, unique = set(), []
    for m in models:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)
    return unique


def refresh_models() -> list:
    """Scan Ollama and write config/models.json (returns the model list)."""
    models = scan_models()
    models_file = CONFIG_DIR / "models.json"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if models:
        models_file.write_text(
            json.dumps({"models": models}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[llm] wrote {len(models)} models to {models_file}")
    else:
        print(f"[llm] scan found no models - keeping {models_file}")
    return models
```

---

<!-- ==== 53/125 : headless_app/engine/core/prompt.py ==== -->

### headless_app/engine/core/prompt.py

```python
"""
app/core/prompt.py
==================

PromptManager: converts an agent definition (agent.json + parsed agent.md
sections) plus the agent's resolved tools into an AgentProfile with a
composed system prompt.

    agent.md + agent.json + tools
        ↓
    PromptManager.build()
        ↓
    AgentProfile (system_prompt ready)
"""

from dataclasses import field
from typing import Callable, List

from engine.core.agent import AgentProfile

# Markdown '## sections' that map to named profile fields.
# Any other section passes through verbatim into the prompt as an
# UPPERCASE-titled block, so new sections need no code changes.
KNOWN_SECTIONS = (
    "role",
    "purpose",
    "personality",
    "boundaries",
    "communication",
    "principles",
    "decision_style",
    "priorities",
)

# Sections actually composed INTO the system prompt.
# 'priorities' is documentation-only and is deliberately excluded,
# matching the original PromptManager behavior.
PROMPT_SECTIONS = tuple(name for name in KNOWN_SECTIONS if name != "priorities")


class PromptManager:
    """Builds an AgentProfile from an agent definition and composes the system prompt."""

    @staticmethod
    def build(definition: dict, tools: List[Callable] | None = None) -> AgentProfile:
        """Build an AgentProfile.

        Args:
            definition: {"meta": {...agent.json...}, "sections": {...parsed agent.md...}}
            tools:      resolved tool functions; their docstrings become the
                        AVAILABLE TOOLS section of the prompt.

        Steps:
            1. Map metadata and markdown sections onto the profile fields
            2. Collect unknown sections as extras
            3. Compose the system prompt
        """
        meta = definition.get("meta", {})
        sections = {k.lower().strip(): v for k, v in definition.get("sections", {}).items()}

        known = {name: sections.get(name, "") for name in KNOWN_SECTIONS}
        extras = {
            name: content for name, content in sections.items()
            if name not in KNOWN_SECTIONS and name not in ("skills", "identity")
        }

        profile = AgentProfile(
            id=meta.get("id", ""),
            name=meta.get("name", ""),
            description=meta.get("description", ""),
            mode=meta.get("mode", "chat"),
            **known,
            extras=extras,
        )
        profile.system_prompt = PromptManager.compose_system_prompt(profile, tools)
        return profile

    @staticmethod
    def compose_system_prompt(profile: AgentProfile, tools: List[Callable] | None = None) -> str:
        """Build the final system prompt from profile sections."""
        parts = []

        if profile.role:
            parts.append(f"ROLE\n{profile.role}")

        if profile.purpose:
            parts.append(f"PURPOSE\n{profile.purpose}")

        if profile.personality:
            parts.append(f"PERSONALITY\n{profile.personality}")

        if profile.boundaries:
            parts.append(f"BOUNDARIES\n{profile.boundaries}")

        if profile.communication:
            parts.append(f"COMMUNICATION STYLE\n{profile.communication}")

        if profile.principles:
            parts.append(f"PRINCIPLES\n{profile.principles}")

        if profile.decision_style:
            parts.append(f"DECISION STYLE\n{profile.decision_style}")

        tool_lines = PromptManager._tool_lines(tools)
        if tool_lines:
            parts.append("AVAILABLE TOOLS\n" + "\n".join(tool_lines))

        # Generic extra sections (user, greeting, project_notes, ...) become
        # UPPERCASE-titled blocks, sorted for deterministic prompts.
        for title, content in sorted(profile.extras.items()):
            if content:
                parts.append(f"{title.upper()}\n{content}")

        return "\n\n".join(parts)

    @staticmethod
    def _tool_lines(tools: List[Callable] | None) -> List[str]:
        """Format tool callables as '- id: first docstring line' lines."""
        lines = []
        for fn in tools or []:
            doc = (getattr(fn, "description", None) or fn.__doc__ or "").strip()
            summary = doc.splitlines()[0] if doc else ""
            name = getattr(fn, "name", None) or getattr(fn, "__name__")
            lines.append(f"- {name}: {summary}")
        return lines
```

---

<!-- ==== 54/125 : headless_app/engine/pipeline.py ==== -->

### headless_app/engine/pipeline.py

```python
"""
engine/pipeline.py
==================

Runs the ordered agent chain from config/pipeline.json so a single user idea
can travel Step 1 -> Step 2 -> Step 3 automatically.

Why this exists: chat.html sends one message to ONE agent. A Step-2 agent whose
prompt says "accepts the Feature Plan from Step 1" has nothing to work from when
the user sends it a fresh idea, so it stalls asking for that plan again and
again. The pipeline feeds each later step the OUTPUT of every earlier step as
part of its own message, so the planner's spec reaches the engineer and the
engineer's blueprint reaches the builder without any copy/paste.

Feed-forward messages carry:
    - the ORIGINAL user message (so the module name / scope never gets lost), and
    - each earlier step's final reply, labelled with the producing agent's name.

Every step's tool_events are collected and returned together, so the UI can
render the complete tool usage of a pipeline run in one shot.
"""

import json
from datetime import datetime
from pathlib import Path

from engine.agents.factory import build_agent, build_agent_from_definition

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "pipeline.json"

_STEP_FEED_TEMPLATE = (
    "Below is what the previous pipeline step ({name}) produced.\n"
    "Use it as your required input. Do NOT ask for it again - just act on it.\n"
    "--- {name} OUTPUT ---\n"
    "{output}\n"
    "--- END {name} OUTPUT ---\n"
)


def _iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _records_file() -> Path:
    """pipeline_runs.jsonl inside the headless data directory."""
    return Path(__file__).resolve().parent.parent / "data" / "pipeline_runs.jsonl"


def _record_run(snapshot: dict) -> None:
    """Append one JSONL line per pipeline run. Fail-safe: a recording failure
    never breaks the run itself (same philosophy as the tool log)."""
    record = {
        "time": _iso_now(),
        "request": snapshot.get("request", ""),
        "model": snapshot.get("model"),
        "steps": snapshot.get("steps", []),
        "reply": snapshot.get("reply", ""),
    }
    try:
        target = _records_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # a recording failure never blocks the pipeline


def load_pipeline(config_path=None) -> list:
    """Ordered step configs from config/pipeline.json ([] when missing/broken).

    Missing files return [] so the app degrades gracefully to plain per-agent
    chat instead of crashing on a config problem.
    """
    path = config_path or CONFIG_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("steps") or []


def _build_step(step, model: str | None, bridge=None):
    """Build the Agent for one pipeline step.

    A step is either an agent id (engine/agent_library/) or a dict with
    explicit `json_path` + `md_path` (headless ad-hoc agents).
    """
    if isinstance(step, dict) and step.get("json_path") and step.get("md_path"):
        return build_agent_from_definition(
            step["json_path"],
            step["md_path"],
            model=model,
            bridge=bridge,
        )
    return build_agent(str(step), model=model, bridge=bridge)


def _step_label(step) -> str:
    # A workspace agent's json_path is .../agents/<name>/agent.json, so the
    # agent FOLDER name (not the file stem "agent") is the readable label.
    if isinstance(step, dict):
        json_file = Path(step.get("json_path", ""))
        folder = json_file.parent.name
        return str(step.get("id") or folder or json_file.stem or "custom")
    return str(step)


def run_pipeline(user_message: str, model: str | None = None,
                 config_path=None, steps: list | None = None,
                 bridge=None) -> dict:
    """Run every step in order; return {reply, outputs, tool_events}.

    outputs is a list of {agent_id, agent_name, output, tools_used} - one entry
    per step, so callers can display each stage's contribution separately and
    the cascade's per-agent tool usage.

    Args:
        user_message: the original user idea to run through the chain.
        model:        optional model override for every step.
        config_path:  optional path to a pipeline.json (defaults to the
                      bundled config/pipeline.json).
        steps:        optional explicit step list (agent ids or
                      {json_path, md_path} dicts). Overrides the config file.
        bridge:       optional Project Manager bridge passed to every agent.
    """
    chain = steps if steps is not None else load_pipeline(config_path)
    if not chain:
        return {
            "reply": "(pipeline not configured - add config/pipeline.json or pass steps)",
            "outputs": [],
            "tool_events": [],
        }

    results: list[dict] = []
    tool_events: list[dict] = []

    for index, step in enumerate(chain):
        agent = _build_step(step, model=model, bridge=bridge)

        feed = user_message
        if results:
            chain_text = "\n\n".join(
                _STEP_FEED_TEMPLATE.format(name=r["agent_name"], output=r["output"])
                for r in results
            )
            feed = f"ORIGINAL USER REQUEST:\n{user_message}\n\n{chain_text}"

        reply = agent.think(feed)
        tools_used = sorted({
            e.get("tool")
            for e in agent.tool_events
            if isinstance(e, dict) and e.get("tool")
        })
        results.append({
            "agent_id": _step_label(step),
            "agent_name": agent.profile.name or _step_label(step),
            "output": reply,
            "tools_used": tools_used,
        })
        tool_events.extend(agent.tool_events)
        print(
            f"Agent {index + 1} ({_step_label(step)}) completed. "
            f"Tools used: {', '.join(tools_used) or 'none'}"
        )

    result = {
        "reply": results[-1]["output"],
        "outputs": results,
        "tool_events": tool_events,
    }
    print(
        f"PIPELINE COMPLETE ({len(chain)}/{len(chain)}) -> "
        f"{result['reply'][:80]!r}"
    )
    _record_run({
        "request": user_message,
        "model": model,
        "steps": [
            {
                "agent_id": r["agent_id"],
                "agent_name": r["agent_name"],
                "output": r["output"],
                "tools_used": r["tools_used"],
            }
            for r in results
        ],
        "reply": result["reply"],
    })
    return result
```

---

<!-- ==== 55/125 : headless_app/interface_runner.py ==== -->

### headless_app/interface_runner.py

```python
"""
interface_runner.py
===================

The single execution seam of the agentCreator engine.

Every caller - the headless CLI (run.py) and the Project Manager routers -
goes through this module, so build/think/log behaviour cannot drift
between frontends.

    AgentInterface.run_chat(message, agent_id, history=...)
        - one agent resolved by id from any registered root, chat reply.

    AgentInterface.run_single_agent(json_path, md_path, user_input)
        - one ad-hoc agent built from explicit agent.json + agent.md paths.
          When json_path/md_path are omitted the agent is resolved by id.

    AgentInterface.run_pipeline(agent_configs, user_input)
        - an ordered agent chain (feed-forward). Each step receives the
          original message plus every earlier step's reply, labelled; the
          final step's reply is the pipeline result.

    AgentInterface.list_agents() / .get_agent(id)
        - discovery over every registered root.

Headless runs persist user and agent turns to the plain-text chat log
(data/chatlog/chat.log) by default. The browser chat opts out and supplies
its own in-memory history; its Save Session action owns persistent chat
history. Tool events are recorded separately to data/toollog/tool_usage.jsonl.

An optional Project Manager bridge makes the Project Manager server (or its
direct filesystem authority) the filesystem owner for the file tools. The
bridge is bound per agent, so concurrent agents never share file-tool
state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from engine.agents.factory import (
    build_agent,
    build_agent_from_definition,
    replay_history,
)
from engine.agents.registry import get_agent_meta, list_agents
from engine.pipeline import run_pipeline as _run_pipeline
from tools.chatlog import append_chat, read_history

#: Turns of prior conversation handed to the model, per agent.
DEFAULT_HISTORY_LIMIT = 20


def _as_history(
    agent_id: str | None,
    limit: int | None = DEFAULT_HISTORY_LIMIT,
) -> list[dict] | None:
    """Read one agent's recent turns from the chat log as model messages.

    Scoped by agent id so agents never see each other's conversations.
    Returns None (meaning "no history") when logging is unavailable or
    limit is falsy, so a broken log never blocks a conversation.
    """
    if not limit or limit <= 0:
        return None
    try:
        entries = read_history(limit=limit, agent=agent_id)
    except Exception as exc:  # pragma: no cover - logging must not break runs
        print(f"[INTERFACE] history unavailable: {exc}")
        return None

    history: list[dict] = []
    for entry in entries:
        sender = str(entry.get("sender", ""))
        content = str(entry.get("message", "") or "")
        if not content:
            continue
        history.append({
            "role": "assistant" if sender in ("agent", "ai") else "user",
            "content": content,
        })
    return history or None


class AgentInterface:
    """Thin, stable API over the build/think loop and pipeline chain."""

    def __init__(
        self,
        bridge: Any = None,
        model: str | None = None,
        log_sink: Callable[[dict], None] | None = None,
    ) -> None:
        """Create a runner.

        Args:
            bridge:   optional Project Manager provider (ProjectManagerBridge
                      or DirectProjectIO). When present, the file tools route
                      through the Project Manager filesystem.
            model:    optional default model override for every run.
            log_sink: optional callback receiving every chat log entry as it
                      is written, so a host can mirror the log elsewhere.
        """
        self.bridge = bridge
        self.model = model
        self.log_sink = log_sink

    # ============================================================
    # INTERNAL
    # ============================================================

    def _log(self, sender: str, message: str, agent_id: str) -> dict:
        """Write one chat log entry and hand it to the sink."""
        entry = append_chat(sender, message, agent=agent_id)
        if self.log_sink is not None:
            try:
                self.log_sink(entry)
            except Exception as exc:  # pragma: no cover - sink must not break runs
                print(f"[INTERFACE] log sink failed: {exc}")
        return entry

    def _think(
        self,
        agent: Any,
        message: str,
        agent_id: str,
        history: list[dict] | None,
        persist: bool = True,
    ) -> tuple[str, list[dict]]:
        """Replay history, run one turn, and optionally log both sides.

        One place for the build-think-log order, so chat, single-agent
        and pipeline runs behave identically. The current turn is not in
        ``history``.
        """
        if history:
            replay_history(agent, history)
        reply = agent.think(message)
        if not persist:
            now = datetime.now(timezone.utc).isoformat()
            return reply, [
                {"ts": now, "sender": "user", "message": message, "agent": agent_id},
                {"ts": now, "sender": "agent", "message": reply, "agent": agent_id},
            ]
        entries = [
            self._log("user", message, agent_id),
            self._log("agent", reply, agent_id),
        ]
        return reply, entries

    # ============================================================
    # CHAT (one agent, resolved by id)
    # ============================================================

    def run_chat(
        self,
        message: str,
        agent_id: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
        use_logged_history: bool = True,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run one agent and return its reply.

        agent_id is resolved through the agent roots, so an agent created
        in the Project Manager works exactly like a bundled library agent.
        With no agent_id the first discovered agent is used.

        Args:
            history: explicit prior turns ({role, content}). When None and
                ``use_logged_history`` is set, this agent's own log history
                is replayed (the current turn is logged after the model has
                answered).
            persist: write the turn to the headless chat log. Browser chat
                sessions pass False and own persistence in saved text files.
        Returns {"reply", "agent_id", "name", "model", "tool_events",
        "entries"}.
        """
        resolved_id = agent_id or self._default_agent_id()
        agent = build_agent(resolved_id, model=model or self.model, bridge=self.bridge)

        if history is None and use_logged_history:
            history = _as_history(resolved_id, DEFAULT_HISTORY_LIMIT)

        reply, entries = self._think(
            agent, message, resolved_id, history, persist=persist
        )

        return {
            "reply": reply,
            "agent_id": resolved_id,
            "name": agent.profile.name,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entries": entries,
        }

    # ============================================================
    # SINGLE AGENT (explicit definition, or by id)
    # ============================================================

    def run_single_agent(
        self,
        user_input: str,
        json_path: str | None = None,
        md_path: str | None = None,
        agent_id: str | None = None,
        model: str | None = None,
        history: list[dict] | None = None,
        use_logged_history: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run one agent built from explicit agent.json + agent.md paths.

        This is the headless construction path: the definition can live
        anywhere, not only inside a registered root. When json_path/md_path
        are omitted the agent is resolved by ``agent_id`` instead.

        ``persist`` controls whether the turn is written to the chat log.

        Returns {"reply", "agent_id", "model", "tool_events", "name",
        "description", "entries"}.
        """
        if json_path and md_path:
            agent = build_agent_from_definition(
                json_path,
                md_path,
                model=model or self.model,
                bridge=self.bridge,
            )
            # A definition loaded from an explicit path may be outside any
            # registered root; use its own id so history stays per-agent.
            resolved_id = str(agent.profile.id)
        elif agent_id:
            resolved_id = agent_id
            agent = build_agent(
                agent_id,
                model=model or self.model,
                bridge=self.bridge,
            )
        else:
            raise ValueError(
                "Provide json_path + md_path, or an agent_id, to run."
            )

        if history is None and use_logged_history:
            history = _as_history(resolved_id, DEFAULT_HISTORY_LIMIT)

        reply, entries = self._think(
            agent, user_input, resolved_id, history, persist=persist
        )

        return {
            "reply": reply,
            "agent_id": resolved_id,
            "name": agent.profile.name,
            "description": agent.profile.description,
            "model": agent.model,
            "tool_events": agent.tool_events,
            "entries": entries,
        }

    # ============================================================
    # PIPELINE
    # ============================================================

    def run_pipeline(
        self,
        user_input: str,
        agent_configs: list | None = None,
        model: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run the ordered agent chain (feed-forward).

        Args:
            agent_configs:
                None  -> load steps from config/pipeline.json.
                list  -> each element is either an agent id (str) or a dict with
                         "json_path" + "md_path" (ad-hoc step agents).
            persist: whether to write the exchange to the chat log.

        Returns:
            {"reply", "outputs": [...step outputs...], "tool_events",
             "model", "entries"}.
        """
        result = _run_pipeline(
            user_input,
            model=model or self.model,
            steps=agent_configs,
            bridge=self.bridge,
        )
        if persist:
            # A cascade is not one agent, so log it untagged rather than
            # attribute it to whichever step happened to run first.
            result["entries"] = [
                self._log("user", user_input, None),
                self._log("agent", result["reply"], None),
            ]
        else:
            now = datetime.now(timezone.utc).isoformat()
            result["entries"] = [
                {"ts": now, "sender": "user", "message": user_input},
                {"ts": now, "sender": "agent", "message": result["reply"]},
            ]
        result["model"] = model or self.model
        return result

    # ============================================================
    # UTILITIES
    # ============================================================

    def _default_agent_id(self) -> str:
        agents = self.list_agents()
        if not agents:
            raise RuntimeError(
                "No agents are registered. Register an agent root "
                "(engine/agents/roots.py) and check that <id>/agent.json "
                "exists in it."
            )
        return agents[0]["id"]

    def list_agents(self) -> list[dict]:
        """Every agent across every registered root (see registry)."""
        return list_agents()

    def get_agent(self, agent_id: str) -> dict | None:
        """Metadata for one agent id, or None when it is not registered."""
        return get_agent_meta(agent_id)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        bridge = getattr(self.bridge, "expose", lambda: None)()
        return (
            f"<AgentInterface model={self.model!r} "
            f"bridge={json.dumps(bridge or {}, default=str) or 'local disk'}>"
        )


__all__ = ["AgentInterface", "DEFAULT_HISTORY_LIMIT"]
```

---

<!-- ==== 56/125 : headless_app/run.py ==== -->

### headless_app/run.py

```python
"""
run.py
======

Command-line entry point for the headless agentCreator engine.

Examples:
    python run.py list-agents
    python run.py refresh-models

    python run.py run-agent rag_assistant --message "what date is it today?"

    python run.py run-agent enginner --base-url http://127.0.0.1:8011 \
        --message "read config/agents.json"

    python run.py run-pipeline --message "idea: add a settings screen" \
        --steps rag_assistant execute_engineer_agent module_builder_agent

Options:
    --base-url    Project Manager URL (default: $PROJECT_MANAGER_BASE_URL or
                  http://127.0.0.1:8000).
    --no-bridge   do not connect to the Project Manager; file tools fall back
                  to the local disk.
    -m/--model    model override (default: per-agent agent.json model).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from interface_runner import AgentInterface
from engine.core.llm import refresh_models
from engine.agents.registry import list_agents


def _build_bridge(args) -> object | None:
    if args.no_bridge:
        print("[run] --no-bridge: file tools use the local disk.")
        return None
    try:
        from bridge.client import ProjectManagerBridge

        bridge = ProjectManagerBridge(base_url=args.base_url)
        health = bridge.health()
        root = (health or {}).get("root", "?")
        print(f"[run] connected to Project Manager at {args.base_url} (root={root})")
        return bridge
    except Exception as exc:
        print(
            f"[run] WARNING: could not connect to Project Manager at "
            f"{args.base_url} ({exc}). Continuing WITHOUT a bridge "
            "(local disk tools)."
        )
        return None


def _read_message(args) -> str:
    if args.message:
        return args.message
    try:
        return input("> ")
    except EOFError:
        return ""


def cmd_list_agents(args) -> int:
    agents = list_agents()
    if not agents:
        print("No agents found. Register an agent root and check its agent.json files.")
        return 1
    for agent in agents:
        tools = "chat" if agent["mode"] == "chat" else agent["model"] or "default model"
        print(
            f"- {agent['id']}  [{agent['name']}]  "
            f"({tools}) - {agent['description']}"
        )
    return 0


def cmd_refresh_models(args) -> int:
    models = refresh_models()
    print(
        f"Installed Ollama models ({len(models)}): "
        + ", ".join(m["id"] for m in models)
    )
    print("Wrote config/models.json")
    return 0


def _print_run(result: dict, args) -> None:
    print("\n" + "=" * 60)
    print("REPLY")
    print("=" * 60)
    print(result.get("reply", ""))
    tool_events = result.get("tool_events") or []
    if tool_events:
        print("\nTOOL EVENTS")
        for event in tool_events:
            print(
                f"- {event.get('time', '')} {event.get('tool')} "
                f"{json.dumps(event.get('args', {}) or {}, default=str)[:160]} "
                f"-> {event.get('status')}"
            )
    if args.json:
        print("\nJSON")
        print(json.dumps(result, indent=2, default=str))


def cmd_run_agent(args) -> int:
    bridge = _build_bridge(args)
    runner = AgentInterface(bridge=bridge, model=args.model)
    message = _read_message(args)
    if not message:
        print("No message provided. Use --message or pipe stdin.")
        return 2
    result = runner.run_chat(message, agent_id=args.agent_id, model=args.model)
    _print_run(result, args)
    return 0


def cmd_run_pipeline(args) -> int:
    bridge = _build_bridge(args)
    runner = AgentInterface(bridge=bridge, model=args.model)
    message = _read_message(args)
    if not message:
        print("No message provided. Use --message or pipe stdin.")
        return 2
    steps = args.steps or None
    result = runner.run_pipeline(message, agent_configs=steps, model=args.model)
    _print_run(result, args)
    if result.get("outputs"):
        print("\nPIPELINE STEPS")
        for step in result["outputs"]:
            print(f"- {step['agent_id']}: {step['output'][:100]!r}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Headless agentCreator engine runner.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Project Manager base URL (default: PROJECT_MANAGER_BASE_URL env "
             "or http://127.0.0.1:8000).",
    )
    parser.add_argument(
        "--no-bridge",
        action="store_true",
        help="Do not connect to a Project Manager; file tools use local disk.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="Model override for all agents.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON result as well.",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Message to send (read interactively when omitted).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-agents", help="List registered agents.")
    p_list.set_defaults(func=cmd_list_agents)

    p_refresh = sub.add_parser("refresh-models", help="Scan Ollama models.")
    p_refresh.set_defaults(func=cmd_refresh_models)

    p_run = sub.add_parser("run-agent", help="Run one registered agent.")
    p_run.add_argument("agent_id", nargs="?", default=None,
                       help="Agent id (default: first registered).")
    p_run.set_defaults(func=cmd_run_agent)

    p_pipe = sub.add_parser("run-pipeline", help="Run the agent chain.")
    p_pipe.add_argument("steps", nargs="*",
                        help="Step agent ids (default: config/pipeline.json).")
    p_pipe.set_defaults(func=cmd_run_pipeline)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

---

<!-- ==== 57/125 : headless_app/tools/__init__.py ==== -->

### headless_app/tools/__init__.py

```python
(empty file — 0 bytes)
```

---

<!-- ==== 58/125 : headless_app/tools/chatlog.py ==== -->

### headless_app/tools/chatlog.py

```python
"""
tools/chatlog.py
================

Headless data store.

The headless runtime keeps its own plain-text records so conversation and
tool history survive reloads and so the agent's ``search_chat_logs`` tool
has a single file to read. Two stores live here:

    data/chatlog/chat.log            - every user turn + agent reply (JSON lines)
    data/toollog/tool_usage.jsonl    - every tool execution event (JSON lines)

The data root is ``headless_app/data`` unless ``AGENT_DATA_DIR`` names
another one, and :func:`use_data_dir` points it somewhere else for the
duration of a block. That is how the test environment keeps its runs out
of the real chat history: a header test prompts an agent four times, and
those four turns are evidence, not conversation with a user.

Both stores are read through the module-level path constants at call time,
so rebinding them with :func:`use_data_dir` redirects every caller at once -
the chat log this module writes, the ``search_chat_logs`` tool that reads
it, and the tool log - with no thread or agent to keep in step.

Nothing in this module requires a server. Writes are fail-safe: a broken
data path or disk error never breaks the agent call that produced the event.
"""

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

#: Environment variable naming an alternative data root.
DATA_DIR_ENV = "AGENT_DATA_DIR"


def default_data_dir() -> Path:
    """The data root this process writes to.

    ``AGENT_DATA_DIR`` when it is set to an existing path, otherwise the
    engine's own ``data`` folder beside this package.
    """
    override = os.environ.get(DATA_DIR_ENV, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "data"


DATA_DIR = default_data_dir()

CHATLOG_DIR = DATA_DIR / "chatlog"
CHATLOG_FILE = CHATLOG_DIR / "chat.log"

TOOLLOG_DIR = DATA_DIR / "toollog"
TOOLLOG_FILE = TOOLLOG_DIR / "tool_usage.jsonl"

MAX_MESSAGE_LENGTH = 2000
DEFAULT_HISTORY_LIMIT = 50
MAX_HISTORY_LIMIT = 500


@contextmanager
def use_data_dir(path: str | Path):
    """Write both logs under ``path`` for the duration of the block.

    The path constants are rebound on entry and restored on exit, so a
    test run cannot leave the real chat log pointing at a test folder
    and a failure inside the block cannot leave it rebound at all.
    """
    global DATA_DIR, CHATLOG_DIR, CHATLOG_FILE, TOOLLOG_DIR, TOOLLOG_FILE

    previous = (DATA_DIR, CHATLOG_DIR, CHATLOG_FILE, TOOLLOG_DIR, TOOLLOG_FILE)
    target = Path(path).expanduser().resolve()

    DATA_DIR = target
    CHATLOG_DIR = target / "chatlog"
    CHATLOG_FILE = CHATLOG_DIR / "chat.log"
    TOOLLOG_DIR = target / "toollog"
    TOOLLOG_FILE = TOOLLOG_DIR / "tool_usage.jsonl"

    try:
        yield target
    finally:
        (DATA_DIR, CHATLOG_DIR, CHATLOG_FILE, TOOLLOG_DIR, TOOLLOG_FILE) = previous


def _iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==========================================================================
# CHAT LOG
# ==========================================================================

def append_chat(sender: str, message: str, agent: str | None = None) -> dict:
    """Append one timestamped chat entry. Returns the stored entry dict.

    ``agent`` tags the entry with the agent that produced it so a
    caller can keep separate per-agent threads in one log. Callers
    that do not pass it keep the original unscoped behaviour.
    """
    CHATLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": _iso_ts(), "sender": sender, "message": message}
    if agent:
        entry["agent"] = agent
    with CHATLOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_history(limit: int = DEFAULT_HISTORY_LIMIT, agent: str | None = None) -> list[dict]:
    """Most recent chat entries in chronological order.

    With ``agent`` set, only that agent's entries are returned.
    Entries written before per-agent tagging have no agent key and
    therefore belong to no thread.
    """
    limit = max(1, min(limit, MAX_HISTORY_LIMIT))
    entries: list[dict] = []
    if not CHATLOG_FILE.exists():
        return entries
    with CHATLOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent and entry.get("agent") != agent:
                continue
            entries.append(entry)
    return entries[-limit:]


def clear_chat(agent: str | None = None) -> int:
    """Wipe the chat log entirely. Returns how many entries were removed.

    With ``agent`` set, only that agent's entries are removed and
    every other thread is preserved.
    """
    if not CHATLOG_FILE.exists():
        return 0
    if not agent:
        removed = 0
        with CHATLOG_FILE.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    removed += 1
        CHATLOG_FILE.write_text("", encoding="utf-8")
        return removed

    kept: list[str] = []
    removed = 0
    with CHATLOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("agent") == agent:
                removed += 1
                continue
            kept.append(line if line.endswith("\n") else line + "\n")
    CHATLOG_FILE.write_text("".join(kept), encoding="utf-8")
    return removed


def search_text(query: str, limit: int = 15) -> str:
    """Case-folded substring search over the chat log, newest first.

    Returns an empty string when nothing matches, otherwise a numbered
    transcript of the matching turns. This is the agent's long-term memory:
    it only ever reads the plain-text chat.log, so no vector DB is needed.
    """
    needle = (query or "").strip().lower()
    if not needle:
        return ""
    if not CHATLOG_FILE.exists():
        return ""
    matches: list[str] = []
    with CHATLOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if needle not in line.lower():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            sender = entry.get("sender", "?")
            message = entry.get("message", "")
            matches.append(f"[{sender}] {message}")
    if not matches:
        return ""
    matches = matches[-limit:]
    header = f"--- CHAT LOG SEARCH RESULTS FOR: '{query}' ---"
    return "\n".join([header, *reversed(matches)])


# ==========================================================================
# TOOL LOG
# ==========================================================================

def append_tool_event(event: dict) -> None:
    """Append one JSONL tool-event line. Fail-safe (never raise)."""
    try:
        TOOLLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TOOLLOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(event, ensure_ascii=False, default=str) + "\n"
            )
    except Exception:
        pass
```

---

<!-- ==== 59/125 : headless_app/tools/memory.py ==== -->

### headless_app/tools/memory.py

```python
"""LangChain tools for conversation-history lookup."""

from typing import Annotated

from langchain_core.tools import tool

from tools.chatlog import search_text


@tool
def search_chat_logs(query: Annotated[str, "Keyword or phrase to search for."]) -> str:
    """Searches saved conversation history for matching messages."""
    result = search_text(query)
    if not result:
        return f"No matches found in the chat log for the query: '{query}'."
    return result


__all__ = ["search_chat_logs"]
```

---

<!-- ==== 60/125 : headless_app/tools/project_tools.py ==== -->

### headless_app/tools/project_tools.py

```python
"""
tools/project_tools.py
======================

Every executable tool in the headless runtime, consolidated into one module.

One function per tool; each function's docstring is what the LLM "sees":
PromptManager turns the first line into the system prompt's AVAILABLE TOOLS
section, and Ollama derives the JSON tool schema from the function name,
signature, types, and docstring. Keep them precise and self-describing.

Filesystem implementations exposed as LangChain tools (IDs in agent.json):
    map_files, read_file, write_text_file, delete_files,
    create_directory, search_workspace, get_current_date,
    tell_me_the_date_and_time, search_chat_logs

File tools run against one of three backends, selected per agent (or, for the
standalone CLI, once per process via configure()):

    * a Project Manager bridge (HTTP)          - the Project Manager server
                                                  is the filesystem authority
    * a "direct" Project Manager provider      - in-process filesystem authority
                                                  (used when mounted inside PM)
    * the local disk (default, no provider)    - bare local filesystem

The provider is a small object with a stable surface:

    workspace_root (str)          .relpath(path) -> posix relative (or raises)
    .list_tree() -> nested tree   .read(rel) -> str     .write(rel, content)
    .create(rel, content)         .delete(rel)          .exists(rel) -> bool

Which provider a tool call uses is resolved by current_provider(): the binding
installed for that specific call (tools.registry.resolve_tools) wins over the
process default, so agents running side by side never share filesystem state.

The FileSession (tools/state.py) is per agent, created at build time.
"""

import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# DATA STORE (chat memory + tool log)
# ---------------------------------------------------------------------------

from tools.chatlog import search_text as _search_chatlog  # noqa: E402

# ---------------------------------------------------------------------------
# PROVIDER SELECTION
# ---------------------------------------------------------------------------

#: Process-wide default provider (None = operate on the local disk). This is
#: only the fallback for callers that do not bind a provider of their own;
#: per-agent binding goes through the ``_bound_provider`` context variable so
#: two agents can never fight over one module global.
_io: Any = None

#: Provider bound for the duration of a single tool call (see
#: tools.registry.resolve_tools). A ContextVar keeps the binding scoped to
#: the running thread/task, so concurrent agents stay independent.
_bound_provider: ContextVar = ContextVar("tool_provider", default=None)


def configure(provider: Any) -> None:
    """Set the process-wide default provider (None for local disk).

    The provider decides where files live AND how paths are translated. Both
    the HTTP bridge (bridge.client) and the in-process filesystem authority
    (bridge.providers.DirectProjectIO) implement the same surface.

    Prefer per-agent binding (tools.registry.resolve_tools(ids, provider)):
    this global remains for backwards compatibility and for the standalone
    headless CLI.
    """
    global _io
    _io = provider


def current_provider() -> Any:
    """The provider in force right now: the per-call binding, else the default."""
    bound = _bound_provider.get()
    return _io if bound is None else bound


@contextmanager
def using(provider: Any):
    """Activate ``provider`` for the duration of the block."""
    token = _bound_provider.set(provider)
    try:
        yield provider
    finally:
        _bound_provider.reset(token)


# ---------------------------------------------------------------------------
# READ - Docling-powered document reader (IBM Docling)
# ---------------------------------------------------------------------------

# Plain-text formats are read straight off disk (fast path). Everything else
# (PDF/DOCX/PPTX/XLSX/HTML/images/...) goes through IBM Docling's pipeline,
# which returns clean, structurally-formatted markdown.
_PLAIN_TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".log", ".text",
    ".csv", ".tsv",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".py", ".pyw", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx",
    ".css", ".scss", ".sass", ".xml", ".tex", ".rst",
}


def _is_plain_text(path) -> bool:
    """True for files whose raw text is already the well-formatted content."""
    return Path(str(path)).suffix.lower() in _PLAIN_TEXT_EXTENSIONS


def _unquote_path(value) -> str:
    """Strip one level of surrounding quotes a model may have left on a path.

    Small local models frequently emit tool args that still include the
    double/single quotes from the prompt (e.g. output_path='"E:\\data\\x"').
    Quote characters are invalid inside Windows path components, so passing
    them through makes read/map/write/delete fail with WinError 123 - even
    though the underlying path was perfectly real. Only matching quote pairs
    at the very edges are stripped, and only for string arguments that are
    really paths, so ordinary quoted prose is never mangled.
    """
    v = str(value).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    return v


_DOCLING_CONVERTERS = {}


def _docling_converter(ocr: bool):
    """Return a cached, lazily-created Docling DocumentConverter.

    The converter is created once per ocr setting and reused across calls so
    the (expensive) pipeline + model artifacts are initialized only once.
    First-ever conversion downloads the layout/OCR models from HuggingFace.
    """
    if ocr not in _DOCLING_CONVERTERS:
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError:
            _DOCLING_CONVERTERS[ocr] = None
            return None

        if ocr:
            options = PdfPipelineOptions(do_ocr=True)
            converter = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
            )
        else:
            converter = DocumentConverter()

        _DOCLING_CONVERTERS[ocr] = converter
    return _DOCLING_CONVERTERS[ocr]


def _convert_with_docling(path: Path, ocr: bool) -> str | None:
    """Return Docling markdown for a binary document, or None when unavailable."""
    converter = _docling_converter(ocr)
    if converter is None:
        return None

    from docling.datamodel.base_models import ConversionStatus

    result = converter.convert(str(path), max_num_pages=400)
    if result.status is ConversionStatus.FAILURE:
        errors = "; ".join(e.error_message for e in getattr(result, "errors", []))
        raise ValueError(errors or "Docling could not convert the document.")
    return result.document.export_to_markdown()


def _read_local_file(p: Path, ocr: bool) -> dict:
    """Read a file from the local disk (text direct, binary via Docling)."""
    if _is_plain_text(p):
        return {
            "success": True,
            "tool": "read_file",
            "data": {
                "path": str(p),
                "filename": p.name,
                "file_type": p.suffix.lower(),
                "extracted_content": p.read_text(encoding="utf-8", errors="replace"),
                "status": "success",
            },
            "error": None,
        }
    markdown = _convert_with_docling(p, ocr)
    if markdown is None:
        return {
            "success": False,
            "tool": "read_file",
            "data": {},
            "error": "Docling is not installed. Install it with `pip install docling` "
                     "to read PDF/DOCX/PPTX/XLSX/HTML/image files.",
        }
    return {
        "success": True,
        "tool": "read_file",
        "data": {
            "path": str(p),
            "filename": p.name,
            "file_type": p.suffix.lower(),
            "extracted_content": markdown,
            "status": "success",
        },
        "error": None,
    }


def read_file(path: str, ocr: bool = True) -> dict:
    """Reads a file and returns its content as well-formatted text (markdown).

    Use this tool whenever you need the contents of a document, source file,
    or any file on disk. It returns the extracted content ready to use.

    Plain text and code files (.txt, .md, .log, .json, source code, ...) are
    read directly. All other formats - PDF, DOCX, PPTX, XLSX, HTML, images -
    are converted by IBM Docling into clean, structured markdown (OCR on by
    default for scanned PDFs). When a Project Manager is connected, project
    files are read through it (the Project Manager is the filesystem owner).

    Args:
        path (str): Absolute path to the file to read (relative to the
            Project Manager workspace when one is connected).
        ocr (bool): When True (default), optical character recognition is
            enabled for PDFs so scanned/rotated pages can be read.

    Returns:
        dict: {"success": bool, "tool": "read_file", "data": {...}, "error": str|None}
            data keys: path, filename, file_type, extracted_content, status
    """
    raw = _unquote_path(path)
    io = current_provider()

    if io is not None:
        # Project Manager is the filesystem authority. Plain text is read
        # through the provider; binary documents are converted locally when
        # the file is reachable on this machine, otherwise the provider's
        # own answer (or error) is returned.
        try:
            rel = io.relpath(raw)
        except Exception as exc:
            return {"success": False, "tool": "read_file", "data": {}, "error": str(exc)}

        if _is_plain_text(rel):
            try:
                content = io.read(rel)
                return {
                    "success": True,
                    "tool": "read_file",
                    "data": {
                        "path": str(Path(io.workspace_root) / rel),
                        "path_relative": rel,
                        "filename": Path(rel).name,
                        "file_type": Path(rel).suffix.lower(),
                        "extracted_content": content,
                        "status": "success",
                    },
                    "error": None,
                }
            except Exception as exc:
                return {"success": False, "tool": "read_file", "data": {}, "error": str(exc)}

        # Binary document: best-effort local Docling conversion, then the
        # provider's read (which may serve extracted text or refuse).
        local = Path(io.workspace_root) / rel
        if local.is_file():
            try:
                return _read_local_file(local, ocr)
            except Exception as exc:
                pass
        try:
            content = io.read(rel)
            return {
                "success": True,
                "tool": "read_file",
                "data": {
                    "path": str(Path(io.workspace_root) / rel),
                    "path_relative": rel,
                    "filename": Path(rel).name,
                    "file_type": Path(rel).suffix.lower(),
                    "extracted_content": content,
                    "status": "success",
                },
                "error": None,
            }
        except Exception as exc:
            return {"success": False, "tool": "read_file", "data": {}, "error": str(exc)}

    p = Path(raw)
    if not p.exists() or not p.is_file():
        return {
            "success": False,
            "tool": "read_file",
            "data": {},
            "error": f"File '{path}' not found."
        }

    try:
        return _read_local_file(p, ocr)
    except Exception as e:
        return {"success": False, "tool": "read_file", "data": {}, "error": str(e)}


# ---------------------------------------------------------------------------
# MAP - directory inspection
# ---------------------------------------------------------------------------

DEFAULT_IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode"}


def _flatten_tree(entries: list, prefix: str = "") -> list[dict]:
    """Flatten a nested provider tree into one flat list of {path, type, name, size}."""
    flat = []
    for entry in entries or []:
        name = entry.get("name", "")
        rel = entry.get("path", "")
        if not rel and name:
            rel = f"{prefix}/{name}" if prefix else name
        flat.append({
            "name": name or Path(rel).name,
            "path": rel,
            "type": entry.get("type", "file"),
        })
        for child in entry.get("children") or []:
            flat.extend(_flatten_tree([child], prefix=rel))
    return flat


def _map_entries_local(root: Path) -> list[dict]:
    """os.walk the local disk; returns flat {name, path, type, level} entries."""
    files_data = []
    for current_dir, dirs, files in os.walk(root, topdown=True):
        depth = len(Path(current_dir).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]
        for d in dirs:
            full = Path(current_dir) / d
            files_data.append({"name": d, "path": str(full), "type": "directory", "level": depth + 1})
        for f in files:
            full = Path(current_dir) / f
            files_data.append({"name": f, "path": str(full), "type": "file", "level": depth + 1})
    return files_data


def map_files(path: str, max_depth: int = 8, max_entries: int = 5000) -> dict:
    """Inspects a directory and returns a structured list of its files and folders.

    Use this tool to see what exists on disk before reading, writing, or
    deleting anything. Returns every file and subfolder under the given
    directory (to max_depth), excluding ordinary noise like .git, .venv, and
    __pycache__. Folders are listed with their subpaths so you know exactly
    where a file lives before you touch it.

    Args:
        path (str): Absolute path to the directory to inspect, or a path
            relative to the Project Manager workspace when one is connected.
        max_depth (int): Maximum subdirectory depth to descend into (default 8).
        max_entries (int): Maximum number of entries to return (default 5000).

    Returns:
        dict: {"success": bool, "tool": "map_files", "data": {...}, "error": str|None}
            data keys: files (list of {name, path, extension, type, parent, level}),
                        truncated (bool), max_entries (int)
    """
    # Small local models sometimes render ints as strings ("5000"); coerce so
    # the `>=` comparisons below never crash on a type mismatch.
    if isinstance(max_depth, str) and max_depth.strip().isdigit():
        max_depth = int(max_depth)
    if isinstance(max_entries, str) and max_entries.strip().isdigit():
        max_entries = int(max_entries)
    raw = _unquote_path(path)
    io = current_provider()

    if io is not None:
        try:
            base = io.relpath(raw)
        except Exception as exc:
            return {"success": False, "tool": "map_files", "data": {}, "error": str(exc)}
        try:
            flat = _flatten_tree(io.list_tree())
        except Exception as exc:
            return {"success": False, "tool": "map_files", "data": {}, "error": str(exc)}

        base = base.strip("/")
        base_parts = tuple(base.split("/")) if base else ()
        files_data = []
        for entry in flat:
            rel = entry.get("path", "").replace("\\", "/").strip("/")
            if not rel:
                continue
            rel_parts = tuple(rel.split("/"))
            if base_parts and rel_parts[:len(base_parts)] != base_parts:
                continue
            if base_parts and len(rel_parts) == len(base_parts):
                continue  # the requested directory itself, not an entry inside it
            level = len(rel_parts) - len(base_parts)
            if level > max_depth:
                continue
            if base_parts and any(p in DEFAULT_IGNORE_DIRS for p in rel_parts):
                continue
            files_data.append({
                "name": entry.get("name") or rel_parts[-1],
                "path": str(Path(io.workspace_root) / rel),
                "path_relative": rel,
                "extension": Path(rel).suffix,
                "type": entry.get("type", "file"),
                "parent": rel_parts[-2] if len(rel_parts) >= 2 else "",
                "level": level,
            })
            if len(files_data) >= max_entries:
                break
        truncated = len(files_data) >= max_entries
        return {
            "success": True,
            "tool": "map_files",
            "data": {"files": files_data, "truncated": truncated, "max_entries": max_entries},
            "error": None,
        }

    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return {
            "success": False,
            "tool": "map_files",
            "data": {},
            "error": f"Path '{path}' is not a valid directory."
        }

    files_data = []
    for current_dir, dirs, files in os.walk(root, topdown=True):
        depth = len(Path(current_dir).relative_to(root).parts)
        if depth >= max_depth:
            dirs[:] = []
        else:
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]

        for d in dirs:
            if len(files_data) >= max_entries:
                break
            full = Path(current_dir) / d
            files_data.append({
                "name": d,
                "path": str(full),
                "extension": "",
                "type": "directory",
                "parent": Path(current_dir).name if Path(current_dir) != root else "",
                "level": depth + 1,
            })

        for f in files:
            if len(files_data) >= max_entries:
                break
            full = Path(current_dir) / f
            files_data.append({
                "name": f,
                "path": str(full),
                "extension": Path(f).suffix,
                "type": "file",
                "parent": Path(current_dir).name if Path(current_dir) != root else "",
                "level": depth + 1,
            })

        if len(files_data) >= max_entries:
            break

    truncated = len(files_data) >= max_entries
    return {
        "success": True,
        "tool": "map_files",
        "data": {
            "files": files_data,
            "truncated": truncated,
            "max_entries": max_entries,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# WRITE - file creation
# ---------------------------------------------------------------------------

def write_text_file(name: str, content: str, output_path: str, overwrite: bool = False) -> dict:
    """Creates a text file containing the given content.

    Use this tool to save any text or code you have produced to disk. The
    parent directory is created automatically, so you do not need a separate
    "create folder" step. By default an existing file with the same name is
    NOT overwritten - pass overwrite=True when you intentionally want to.

    Args:
        name (str): File name to write, e.g. "summary.txt".
        content (str): Full text content to write into the file.
        output_path (str): Directory in which to create the file (inside the
            Project Manager workspace when one is connected).
        overwrite (bool): Whether to overwrite the file if it already exists
            (default False).

    Returns:
        dict: {"success": bool, "tool": "write_text_file", "data": {...}, "error": str|None}
            data keys: filename, path, type, size, status (built on success)
    """
    if not name or content is None or not output_path:
        return {
            "success": False,
            "tool": "write_text_file",
            "data": {},
            "error": "Missing required arguments. Need name (file name), content (text), and output_path (folder)."
        }

    io = current_provider()

    if io is not None:
        try:
            rel_dir = io.relpath(_unquote_path(output_path)).strip("/")
        except Exception as exc:
            return {"success": False, "tool": "write_text_file", "data": {}, "error": str(exc)}
        rel_file = f"{rel_dir}/{_unquote_path(name)}" if rel_dir else f"{_unquote_path(name)}"
        try:
            if overwrite:
                io.write(rel_file, content)
            else:
                io.create(rel_file, content)
        except Exception as exc:
            return {"success": False, "tool": "write_text_file", "data": {}, "error": str(exc)}
        absolute = str(Path(io.workspace_root) / rel_file)
        return {
            "success": True,
            "tool": "write_text_file",
            "data": {
                "filename": _unquote_path(name),
                "path": absolute,
                "path_relative": rel_file,
                "type": "text/plain",
                "size": 0,
                "status": "written",
            },
            "error": None,
        }

    try:
        out_dir = Path(_unquote_path(output_path))
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / _unquote_path(name)

        if file_path.exists() and not overwrite:
            return {
                "success": False,
                "tool": "write_text_file",
                "data": {},
                "error": f"File '{file_path}' already exists and overwrite is set to False."
            }

        file_path.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "tool": "write_text_file",
            "data": {
                "filename": name,
                "path": str(file_path),
                "type": "text/plain",
                "size": file_path.stat().st_size,
                "status": "written",
            },
            "error": None,
        }
    except Exception as e:
        return {"success": False, "tool": "write_text_file", "data": {}, "error": str(e)}


# ---------------------------------------------------------------------------
# DELETE - file removal
# ---------------------------------------------------------------------------

def delete_files(file_list: list) -> dict:
    """Permanently deletes the specified files.

    Args:
        file_list: File paths to delete. Project Manager paths remain confined
            to its configured writable workspace.
    """
    if not file_list:
        return {
            "success": False,
            "tool": "delete_files",
            "data": {},
            "error": "No files provided for deletion."
        }

    io = current_provider()
    results = {}
    for f_path in file_list:
        try:
            if io is not None:
                rel = io.relpath(f_path)
                if io.exists(rel):
                    io.delete(rel)
                    results[f_path] = "deleted" if not io.exists(rel) else "failed_to_verify"
                else:
                    results[f_path] = "file_not_found"
            else:
                p = Path(_unquote_path(f_path))
                if p.exists() and p.is_file():
                    p.unlink()
                    results[f_path] = "deleted" if not p.exists() else "failed_to_verify"
                else:
                    results[f_path] = "file_not_found"
        except Exception as e:
            results[f_path] = f"error: {str(e)}"

    all_success = all(v == "deleted" for v in results.values())
    return {
        "success": all_success,
        "tool": "delete_files",
        "data": {"results": results},
        "error": None if all_success else "One or more files failed to delete.",
    }


def create_directory(path: str) -> dict:
    """Creates a directory, including any missing parent directories."""
    if not path:
        return {"success": False, "tool": "create_directory", "data": {}, "error": "A directory path is required."}

    io = current_provider()
    try:
        if io is not None:
            rel = io.relpath(_unquote_path(path))
            if hasattr(io, "create_directory"):
                io.create_directory(rel)
            else:
                raise RuntimeError("The configured filesystem provider cannot create directories.")
            result_path = str(Path(io.workspace_root) / rel)
        else:
            result_path = str(Path(_unquote_path(path)).expanduser().resolve())
            Path(result_path).mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "tool": "create_directory",
            "data": {"path": result_path, "status": "created"},
            "error": None,
        }
    except Exception as exc:
        return {"success": False, "tool": "create_directory", "data": {}, "error": str(exc)}


def search_workspace(query: str, path: str = ".", max_results: int = 20) -> dict:
    """Searches workspace text files for a case-insensitive phrase."""
    needle = (query or "").strip().casefold()
    if not needle:
        return {"success": False, "tool": "search_workspace", "data": {}, "error": "A non-empty search query is required."}
    try:
        max_results = max(1, min(int(max_results), 100))
    except (TypeError, ValueError):
        max_results = 20

    io = current_provider()
    matches = []
    try:
        if io is not None:
            base = io.relpath(_unquote_path(path)).strip("/")
            candidates = _flatten_tree(io.list_tree())
            base_parts = tuple(base.split("/")) if base else ()
            for entry in candidates:
                rel = str(entry.get("path", "")).replace("\\", "/").strip("/")
                if entry.get("type") != "file" or (base_parts and tuple(rel.split("/"))[:len(base_parts)] != base_parts):
                    continue
                if Path(rel).suffix.lower() not in _PLAIN_TEXT_EXTENSIONS:
                    continue
                content = io.read(rel)
                lines = content.splitlines()
                for line_number, line in enumerate(lines, 1):
                    if needle in line.casefold():
                        matches.append({"path": rel, "line": line_number, "text": line[:500]})
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
        else:
            root = Path(_unquote_path(path)).expanduser().resolve()
            if not root.is_dir():
                return {"success": False, "tool": "search_workspace", "data": {}, "error": f"Path '{path}' is not a directory."}
            for candidate in root.rglob("*"):
                if not candidate.is_file() or any(part in DEFAULT_IGNORE_DIRS for part in candidate.parts):
                    continue
                if candidate.suffix.lower() not in _PLAIN_TEXT_EXTENSIONS:
                    continue
                try:
                    lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                for line_number, line in enumerate(lines, 1):
                    if needle in line.casefold():
                        matches.append({"path": str(candidate), "line": line_number, "text": line[:500]})
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
        return {
            "success": True,
            "tool": "search_workspace",
            "data": {"matches": matches, "truncated": len(matches) >= max_results},
            "error": None,
        }
    except Exception as exc:
        return {"success": False, "tool": "search_workspace", "data": {}, "error": str(exc)}


# ---------------------------------------------------------------------------
# DATE / TIME
# ---------------------------------------------------------------------------

def get_current_date() -> str:
    """Returns the real current calendar date (e.g. 'Monday, January 05, 2026').

    Use this tool when you need to know today's date - for example when a
    user asks "what day is it", when dating a response, or when reasoning
    about relative dates. No arguments.
    """
    from datetime import datetime
    return datetime.now().strftime("%A, %B %d, %Y")


def tell_me_the_date_and_time() -> str:
    """Returns the current date and time down to the second.

    Use this tool for anything needing the moment now (date + time), like
    timestamps, "what time is it", or checking elapsed time. No arguments.
    """
    from datetime import datetime
    now = datetime.now()
    return f"The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')}"


# ---------------------------------------------------------------------------
# SEARCH - chat transcript / memory recall
# ---------------------------------------------------------------------------

def search_chat_logs(query: str) -> str:
    """Searches past chat transcripts for a keyword and returns the matching segments.

    Use this tool to recall what was discussed in earlier conversations: this
    is the agent's long-term memory. It searches the saved plain-text chat log
    (data/chatlog/chat.log) and returns the matching turns with their speaker.

    Args:
        query (str): The search keyword, term, or phrase to look up.

    Returns:
        str: Formatted search results ('' when nothing matches).
    """
    try:
        result = _search_chatlog(query)
        if not result:
            return f"No matches found in the chat log for the query: '{query}'."
        return result
    except Exception as e:
        return f"Error executing chat log search: {e}"


# Keep the module importable in environments without fancy deps (mirrors the
# original module header which inserted the app root into sys.path).
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
```

---

<!-- ==== 61/125 : headless_app/tools/registry.py ==== -->

### headless_app/tools/registry.py

```python
"""Registry and per-agent provider binding for LangChain tools."""

from typing import Any

from langchain_core.tools import BaseTool

from tools.memory import search_chat_logs
from tools.state import FileSession
from tools.utility import get_current_date, tell_me_the_date_and_time
from tools.workspace import (
    create_directory,
    delete_files,
    map_files,
    read_file,
    search_workspace,
    write_text_file,
)
from tools.project_tools import configure as _configure_provider, using as _using_provider

_TOOL_REGISTRY: dict[str, BaseTool] = {
    "map_files": map_files,
    "read_file": read_file,
    "write_text_file": write_text_file,
    "delete_files": delete_files,
    "create_directory": create_directory,
    "search_workspace": search_workspace,
    "get_current_date": get_current_date,
    "tell_me_the_date_and_time": tell_me_the_date_and_time,
    "search_chat_logs": search_chat_logs,
}


def _replace_func(tool: BaseTool, func) -> BaseTool:
    """Copy a LangChain tool while preserving its validated input schema."""
    if not hasattr(tool, "func") or tool.func is None:
        raise TypeError(f"Tool '{tool.name}' does not have a synchronous function.")
    return tool.model_copy(update={"func": func})


def _bind(tool: BaseTool, provider: Any) -> BaseTool:
    """Bind one filesystem provider to a tool without changing its schema."""
    import functools

    original = tool.func

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        with _using_provider(provider):
            return original(*args, **kwargs)

    return _replace_func(tool, wrapper)


def configure(provider=None) -> None:
    """Set the fallback provider for tools used outside agent construction."""
    _configure_provider(provider)


def get(tool_name: str) -> BaseTool | None:
    """Retrieve a registered LangChain tool by its ID."""
    return _TOOL_REGISTRY.get(tool_name)


def list_tools() -> list[str]:
    """Return all registered tool IDs."""
    return list(_TOOL_REGISTRY)


def available_tool_ids() -> list[str]:
    """Backward-compatible alias for list_tools()."""
    return list_tools()


def resolve_tools(tool_ids: list[str], provider: Any = None) -> list[BaseTool]:
    """Resolve agent tool IDs and optionally bind a workspace provider."""
    resolved = []
    for tool_id in tool_ids:
        registered = _TOOL_REGISTRY.get(tool_id)
        if registered is None:
            print(f"[registry] WARNING: tool '{tool_id}' not found - skipped.")
            continue
        resolved.append(_bind(registered, provider) if provider is not None else registered)
    return resolved


def new_session() -> FileSession:
    """Create an independent working-state record for one agent."""
    return FileSession()


_session = FileSession()


def get_session() -> FileSession:
    """Return the shared session kept for older CLI callers."""
    return _session


__all__ = [
    "configure",
    "get",
    "list_tools",
    "available_tool_ids",
    "resolve_tools",
    "new_session",
    "get_session",
    "_TOOL_REGISTRY",
]
```

---

<!-- ==== 62/125 : headless_app/tools/state.py ==== -->

### headless_app/tools/state.py

```python
"""
app/tools/state.py
==================

Shared working state for the file-management tools.

The FileSession is the single in-memory record of everything a file-aware
agent has discovered, read, written, or proposed for deletion during the
current process. It lets later tool calls (and the model itself) build on
previous results instead of re-scanning the filesystem each turn.

The session is process-wide: one instance is created lazily and shared by
every agent that is built in this process.

It is injected into the conversation by Agent._inject_session_context and
hydrated from tool results by the _record_result wrapper in app/agents/factory.py.
"""


class FileSession:
    """Manages file-management working state for AI agents dynamically.

    Tracks, across tool calls in one process:

        discovered_files   - paths surfaced by map_files / other listing tools
        selected_files     - paths the agent has explicitly chosen to work on
        read_files         - paths whose contents have already been read
        working_content    - path -> last extracted text content (read_file)
        output_files       - paths the agent has written (write_text_file)
    """

    def __init__(self):
        self.discovered_files = []
        self.selected_files = []
        self.read_files = []
        self.working_content = {}
        self.output_files = []

    def add_discovered(self, paths: list):
        """Record files/directories surfaced by map_files (deduplicated)."""
        self.discovered_files = list(set(self.discovered_files + paths))

    def select_files(self, paths: list):
        """Mark paths as the agent's active working set (deduplicated)."""
        self.selected_files = list(set(self.selected_files + paths))

    def record_read(self, path: str, content: str):
        """Remember that a path was read and cache its extracted content."""
        if path not in self.read_files:
            self.read_files.append(path)
        self.working_content[path] = content

    def add_output(self, path: str):
        """Remember a path produced by the write tool (deduplicated)."""
        if path not in self.output_files:
            self.output_files.append(path)

    def get_state(self) -> dict:
        """Snapshot the current session state for injection into the prompt."""
        return {
            "discovered_files": self.discovered_files,
            "selected_files": self.selected_files,
            "read_files": self.read_files,
            "output_files": self.output_files,
        }
```

---

<!-- ==== 63/125 : headless_app/tools/utility.py ==== -->

### headless_app/tools/utility.py

```python
"""LangChain tools for date and time utilities."""

from langchain_core.tools import tool


@tool
def get_current_date() -> str:
    """Returns today's local date in a readable format."""
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@tool
def tell_me_the_date_and_time() -> str:
    """Returns the current local date and time."""
    from datetime import datetime

    return f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


__all__ = ["get_current_date", "tell_me_the_date_and_time"]
```

---

<!-- ==== 64/125 : headless_app/tools/workspace.py ==== -->

### headless_app/tools/workspace.py

```python
"""LangChain tools for workspace files and directories."""

from typing import Annotated

from langchain_core.tools import tool

from tools import project_tools as _implementation


@tool
def map_files(
    path: Annotated[str, "Directory path to inspect."],
    max_depth: Annotated[int, "Maximum directory depth to include."] = 8,
    max_entries: Annotated[int, "Maximum number of entries to return."] = 5000,
) -> dict:
    """Lists files and directories beneath a workspace path."""
    return _implementation.map_files(path, max_depth, max_entries)


@tool
def read_file(
    path: Annotated[str, "File path to read."],
    ocr: Annotated[bool, "Enable OCR when reading scanned documents."] = True,
) -> dict:
    """Reads text or extracts content from a workspace file."""
    return _implementation.read_file(path, ocr)


@tool
def write_text_file(
    name: Annotated[str, "Name of the file to write."],
    content: Annotated[str, "Complete text content to write."],
    output_path: Annotated[str, "Directory path in which to write the file."],
    overwrite: Annotated[bool, "Replace an existing file when true."] = False,
) -> dict:
    """Writes a text file to a workspace directory."""
    return _implementation.write_text_file(name, content, output_path, overwrite)


@tool
def delete_files(
    file_list: Annotated[list[str], "Workspace file paths to delete."],
) -> dict:
    """Deletes workspace files immediately."""
    return _implementation.delete_files(file_list)


@tool
def create_directory(
    path: Annotated[str, "Workspace directory path to create."],
) -> dict:
    """Creates a workspace directory and any missing parent directories."""
    return _implementation.create_directory(path)


@tool
def search_workspace(
    query: Annotated[str, "Case-insensitive phrase to find in text files."],
    path: Annotated[str, "Directory path to search."] = ".",
    max_results: Annotated[int, "Maximum number of matching lines to return."] = 20,
) -> dict:
    """Searches workspace text files and returns matching lines."""
    return _implementation.search_workspace(query, path, max_results)


__all__ = [
    "map_files",
    "read_file",
    "write_text_file",
    "delete_files",
    "create_directory",
    "search_workspace",
]
```

---

<!-- ==== 65/125 : interface/clients/__init__.py ==== -->

### interface/clients/__init__.py

```python
"""Project Manager Python interface client package.

Talk to the Project Manager over HTTP from any Python program or
AI agent::

    from interface.clients import EditorClient

    client = EditorClient()
    client.health()

The async agent client::

    from interface.clients import AsyncEditorClient
"""

from .editor_client import EditorClient, AsyncEditorClient

__all__ = [
    "EditorClient",
    "AsyncEditorClient",
]
```

---

<!-- ==== 66/125 : interface/clients/editor_client.py ==== -->

### interface/clients/editor_client.py

```python
"""
Project Manager — Python interface client.
============================================

Talk to the Project Manager over HTTP from any Python program or
AI agent.

The client is the *interface*. It never touches the filesystem; it
always goes through the running Project Manager server.

Sync client:
    >>> from interface.clients import EditorClient
    >>> client = EditorClient()
    >>> client.health()

Async client (for agents / async code):
    >>> from interface.clients import AsyncEditorClient
    >>> client = AsyncEditorClient()
    >>> await client.health()

WebSocket subscriptions (real-time events):
    >>> async for event in client.subscribe():
    ...     print(event)

File operations accept a ``scope`` argument:
    * ``"workspace"`` (default) — the managed workspace
    * ``"app"``               — the application repository (dev files)
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable

import httpx
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as ws_connect


# ============================================================
# BASE URL DETECTION
# ============================================================

def _default_base_url() -> str:
    """
    Best-effort default: localhost on the standard Project Manager port.
    """

    import os

    return os.environ.get(
        "PROJECT_MANAGER_BASE_URL",
        "http://127.0.0.1:8000",
    )


def _apply_project_root(
    path: str,
    project_root: str = "",
) -> str:
    """
    Normalize a project-relative path into the API path form.
    """

    path = path.replace("\\", "/").strip("/")

    return path


# ============================================================
# SHARED RESPONSE MACHINERY
# ============================================================

def _raise_for_error(
    response: httpx.Response,
) -> None:
    """
    Turn a non-2xx response into a useful Python error.
    """

    if response.is_success:
        return

    detail = ""

    try:

        detail = response.json().get(
            "detail",
            "",
        )

    except Exception:
        pass

    message = detail or f"Project Manager error (HTTP {response.status_code})."

    raise RuntimeError(
        message
    )


# ============================================================
# SYNC CLIENT
# ============================================================

class EditorClient:
    """
    Synchronous HTTP client for the Project Manager interface.

    All calls hit the running Project Manager server. Nothing is
    done directly against the filesystem.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    # ========================================================
    # GET HELPERS
    # ========================================================

    def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # PROJECT OPERATIONS
    # ========================================================

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def project(self) -> dict[str, Any]:
        return self._get("/api/project")

    def tree(self) -> dict[str, Any]:
        return self.project()

    def sessions(self) -> dict[str, Any]:
        return self._get("/api/sessions")

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def read(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope,
        )

    def open(
        self,
        path: str,
        scope: str = "workspace",
    ):
        """
        Open a project file and return its contents.

        Alias for read().
        """

        return self.read(path, scope=scope)

    def write(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ):
        """
        Save file content. Alias for write().
        """

        return self.write(path, content, scope=scope)

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    def delete_file(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    # ========================================================
    # DIRECTORY OPERATIONS
    # ========================================================

    def create_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope,
            },
        )

    def delete_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    # ========================================================
    # RENAME / MOVE OPERATIONS
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope,
            },
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def subscribe(
        self,
        *,
        timeout: float | None = None,
    ):
        """
        Open a WebSocket and yield events as they arrive.

        Returns:
            Synchronous iterator over Project Manager event dicts.
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        import websockets.sync.client as ws_sync

        with ws_sync.connect(
            ws_url,
            timeout=timeout,
        ) as socket:

            while True:

                message = socket.recv()

                if message is None:
                    break

                yield _decode_message(message)

    def close(self) -> None:
        self._http.close()

    # context-manager support
    def __enter__(self) -> "EditorClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _decode_message(message: Any) -> dict[str, Any]:
    """
    Turn a raw WebSocket message into an event dict.

    Handles bytes and str payloads.
    """

    if isinstance(message, bytes):

        import json

        return json.loads(
            message.decode(
                "utf-8"
            )
        )

    import json

    try:

        return json.loads(
            message
        )

    except Exception:

        return {
            "type": "message",
            "data": message,
        }


# ============================================================
# ASYNC CLIENT
# ============================================================

class AsyncEditorClient:
    """
    Asynchronous HTTP + WebSocket client for AI agents.

    Provides the same operations as EditorClient but with
    async/await, plus ``subscribe()`` for real-time events.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else _default_base_url()
        )
        self.timeout = timeout

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    # ========================================================
    # ASYNC HELPERS
    # ========================================================

    async def _get(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.get(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.put(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.post(
            endpoint,
            params=params,
            json=payload,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    async def _delete(
        self,
        endpoint: str,
        **params: Any,
    ) -> dict[str, Any]:
        response = await self._http.delete(
            endpoint,
            params=params,
        )

        _raise_for_error(response)

        if not response.content:
            return {}

        return response.json()

    # ========================================================
    # OPERATIONS (ASYNC)
    # ========================================================

    async def health(self) -> dict[str, Any]:
        return await self._get("/api/health")

    async def project(self) -> dict[str, Any]:
        return await self._get("/api/project")

    async def tree(self) -> dict[str, Any]:
        return await self.project()

    async def sessions(self) -> dict[str, Any]:
        return await self._get("/api/sessions")

    async def read(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._get(
            "/api/file/read",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def open(
        self,
        path: str,
        scope: str = "workspace",
    ):
        return await self.read(path, scope=scope)

    async def write(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._put(
            "/api/file/write",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    async def save(
        self,
        path: str,
        content: str,
        scope: str = "workspace",
    ):
        return await self.write(path, content, scope=scope)

    async def create_file(
        self,
        path: str,
        content: str = "",
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._post(
            "/api/file/create",
            payload={
                "path": _apply_project_root(path),
                "content": content,
                "scope": scope,
            },
        )

    async def delete_file(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/file/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def create_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._post(
            "/api/directory/create",
            params={
                "path": _apply_project_root(path),
                "scope": scope,
            },
        )

    async def delete_directory(
        self,
        path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._delete(
            "/api/directory/delete",
            path=_apply_project_root(path),
            scope=scope,
        )

    async def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str = "workspace",
    ) -> dict[str, Any]:
        return await self._put(
            "/api/path/rename",
            payload={
                "old_path": _apply_project_root(old_path),
                "new_path": _apply_project_root(new_path),
                "scope": scope,
            },
        )

    # ========================================================
    # REAL-TIME SUBSCRIPTION
    # ========================================================

    async def subscribe(
        self,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Open a WebSocket and yield Project Manager events.

        Example:
            >>> async for event in client.subscribe():
            ...     if event["type"] == "saved":
            ...         print("Saved", event["path"])
        """

        ws_url = self.base_url.replace(
            "http",
            "ws",
            count=1
        )

        ws_url = ws_url.rstrip("/") + "/api/ws"

        async with ws_connect(
            ws_url
        ) as socket:

            async for message in socket:

                yield _decode_message(
                    message
                )
```

---

<!-- ==== 67/125 : interface/core/__init__.py ==== -->

### interface/core/__init__.py

```python
"""Project Manager operation/interface layer.

This package sits between the HTTP API and the filesystem.
It is not a replacement for the Project Manager; it provides a
clean set of operations that multiple interfaces (browser, AI
agents, scripts) can use.

Every filesystem mutation eventually goes through
parameters.filesystem.
"""

from .session import EditorManager, EditorSession
from .events import EventBus
from .operations import EditorInterface

__all__ = [
    "EditorManager",
    "EditorSession",
    "EventBus",
    "EditorInterface",
]
```

---

<!-- ==== 68/125 : interface/core/defaults.py ==== -->

### interface/core/defaults.py

```python
"""
Project Manager shared defaults.
=================================

Builds the single, shared Project Manager interface state so every
router, the browser, the WebSocket endpoint and the Python client
all talk to the same in-memory event bus, session pool and
controller.

    routers/project.py  ──┐
    routers/files.py    ──┤        editor.defaults
    routers/dirs.py     ──┼────►   get_interface()
    routers/ws.py       ──┤              │
                          │              ▼
    browser (JS)      ────┘        EditorInterface
                                          │
                                    Project_files
                                          │
                                        Filesystem

All other interfaces build on this shared state; nothing here
bypasses Project_files.
"""

from __future__ import annotations

from typing import Any

from parameters import filesystem

from .events import EventBus
from .session import EditorManager
from .operations import EditorInterface


# ============================================================
# SHARED STATE
# ============================================================

_events: EventBus | None = None

_sessions: EditorManager | None = None

_interface: EditorInterface | None = None


def get_events() -> EventBus:
    """
    The shared project event bus.
    """

    global _events

    if _events is None:

        _events = EventBus()

    return _events


def get_sessions() -> EditorManager:
    """
    The shared editor session pool.
    """

    global _sessions

    if _sessions is None:

        _sessions = EditorManager()

    return _sessions


def get_interface() -> EditorInterface:
    """
    The shared Project Manager controller.

    Called by routers and by the web dashboard.
    """

    global _interface

    if _interface is None:

        _interface = EditorInterface(
            filesystem=filesystem,
            events=get_events(),
            sessions=get_sessions(),
        )

    return _interface


def reset_for_tests() -> None:
    """
    Clear all shared state (used by the verification suite).
    """

    global _events
    global _sessions
    global _interface

    _events = None

    _sessions = None

    _interface = None
```

---

<!-- ==== 69/125 : interface/core/events.py ==== -->

### interface/core/events.py

```python
"""
Project Manager event system.
=============================

A small publish/subscribe event bus. Changes inside the Project
Manager publish events so that the browser and future agents can
receive information without monitoring the filesystem directly.

Example event:
    {
        "type": "saved",
        "path": "app.py"
    }
"""

from __future__ import annotations

import uuid
from typing import Any, Callable


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES = {
    "saved",
    "created",
    "renamed",
    "deleted",
    "tree_changed",
}


# ============================================================
# EVENT BUS
# ============================================================

class EventBus:
    """
    Simple in-memory publish/subscribe event bus.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, Callable[[dict[str, Any]], None]] = {}

    def subscribe(
        self,
        callback: Callable[[dict[str, Any]], None],
    ) -> str:
        """
        Subscribe a callback to every project event.

        Args:
            callback:
                Function called with each published event dict.

        Returns:
            Subscription id (use with unsubscribe()).
        """

        subscription_id = uuid.uuid4().hex

        self._subscribers[subscription_id] = callback

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """
        Remove a subscription.
        """

        self._subscribers.pop(subscription_id, None)

    def publish(
        self,
        event_type: str,
        path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type:
                One of EVENT_TYPES.
            path:
                Optional project-relative path the event refers to.
            kwargs:
                Extra fields merged into the event payload.
        """

        event: dict[str, Any] = {
            "type": event_type,
        }

        if path is not None:
            event["path"] = path

        event.update(kwargs)

        for callback in list(self._subscribers.values()):
            callback(event)
```

---

<!-- ==== 70/125 : interface/core/operations.py ==== -->

### interface/core/operations.py

```python
"""
Project Manager operation layer.
=================================

This is the single controller that HTTP routers, the browser, and
the Python client all funnel through.

The controller does NOT implement filesystem logic. Every filesystem
operation is delegated to parameters.filesystem, which
remains the sovereign owner of the Project Manager filesystem.

    Router / Client
        ↓
    EditorInterface
        ↓
    parameters.filesystem
        ↓
    Filesystem

Scopes
------
Operations address files relative to an active root chosen by scope:

    * workspace  ->  the managed workspace (default)
    * app        ->  the application repository root (dev files)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from parameters import filesystem as _filesystem
from .events import EventBus
from .session import EditorManager


# ============================================================
# SCOPES
# ============================================================

VALID_SCOPES = ("workspace", "app")


def _root_for(scope: str | None) -> Path:
    """
    Resolve a scope string into a filesystem root.

    ``app`` reaches the application repository root (dev files);
    everything else defaults to the managed workspace.
    """

    if scope == "app":

        return _filesystem.REPO_ROOT

    return _filesystem.PROJECT_ROOT


def _target(
    path: str,
    scope: str | None,
) -> tuple[str, Path, str | None]:
    """
    Resolve a request path into the arguments the filesystem
    operations expect.

    A path prefixed with a browser root (``source_files/AGENTS.md``)
    resolves inside that root. Anything else keeps the legacy
    behaviour and resolves against the scope's root.

    Returns:
        ``(stripped_relative, root, root_name)``.
    """

    return _filesystem.resolve_browse_target(
        path,
        _root_for(scope),
    )


# ============================================================
# EDITOR INTERFACE
# ============================================================

class EditorInterface:
    """
    The Project Manager operation/interface layer.

    Provides a narrow set of high-level operations agents and the
    web editor can use. All filesystem work goes through
    parameters.filesystem.
    """

    def __init__(
        self,
        filesystem: Any = None,
        events: EventBus | None = None,
        sessions: EditorManager | None = None,
    ) -> None:

        # The Project Manager remains the filesystem authority.
        self.filesystem = (
            filesystem
            if filesystem is not None
            else _filesystem
        )

        self.events = (
            events
            if events is not None
            else EventBus()
        )

        self.session_manager = (
            sessions
            if sessions is not None
            else EditorManager()
        )

    # ========================================================
    # HEALTH / STATE
    # ========================================================

    def health(self) -> dict[str, Any]:
        """
        Project Manager health and project information.
        """

        return {
            "status": "healthy",
            "project": self.filesystem.read_project_info(),
            "root": str(self.filesystem.PROJECT_ROOT),
        }

    def tree(
        self,
        scope: str | None = None,
        roots: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Project state: project info, active root and filesystem tree.

        Args:
            scope:
                None (default) returns the browser tree, whose top
                level is the configured ``BROWSE_ROOTS`` folders.
                ``"workspace"`` or ``"app"`` return the legacy
                single-root tree for that scope.
            roots:
                Browser roots to include, or None for all of them.
                Ignored when ``scope`` is set: the legacy view is
                already a single root, so there is nothing to
                choose between. This filters the listing only --
                the returned roots stay resolvable everywhere.
        """

        try:

            if not scope:

                browse_roots = (
                    self.filesystem.BROWSE_ROOTS
                )

                if roots is not None:

                    wanted = set(roots)

                    browse_roots = {
                        name: config
                        for name, config in browse_roots.items()
                        if name in wanted
                    }

                return {
                    "scope": None,
                    "project": self.filesystem.read_project_info(),
                    "roots": [
                        {
                            "name": name,
                            "writable": bool(
                                config.get(
                                    "writable",
                                    False,
                                )
                            ),
                        }
                        for name, config
                        in browse_roots.items()
                    ],
                    "root": str(
                        self.filesystem.PROJECT_ROOT
                    ),
                    "filesystem": (
                        self.filesystem.read_browse_filesystem(
                            roots=roots
                        )
                    ),
                }

            root = _root_for(scope)

            return {
                "scope": scope,
                "project": self.filesystem.read_project_info(),
                "root": str(root),
                "filesystem": self.filesystem.read_filesystem(
                    directory=root
                ),
            }

        except Exception as error:

            raise self._to_error(
                error
            )

    def sessions(self) -> list[dict[str, Any]]:
        """
        Snapshot of all connected interface sessions.
        """

        return self.session_manager.snapshot()

    # ========================================================
    # READ / WRITE
    # ========================================================

    def open(
        self,
        path: str,
        scope: str | None = None,
    ) -> str:
        """
        Open a project file and return its contents.

        Args:
            path:
                Root-qualified or root-relative file path.
            scope:
                ``None`` (default) or ``"workspace"`` or ``"app"``.

        Returns:
            The file contents.
        """

        stripped, root, _ = _target(path, scope)

        return self.filesystem.read_file(
            stripped,
            root=root,
        )

    def save(
        self,
        path: str,
        content: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Write file contents back to the project filesystem.

        Publishes a ``saved`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.write_file(
            stripped,
            content,
            root=root,
        )

        self.events.publish(
            "saved",
            path=path,
            scope=scope,
        )

        return {
            "status": "saved",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # CREATE
    # ========================================================

    def create_file(
        self,
        path: str,
        content: str = "",
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project file.

        Publishes a ``created`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.create_file(
            stripped,
            content,
            root=root,
        )

        self.events.publish(
            "created",
            path=path,
            scope=scope,
        )

        return {
            "status": "created",
            "path": path,
            "scope": scope,
        }

    def create_directory(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project directory.

        Publishes a ``created`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.create_directory(
            stripped,
            root=root,
        )

        self.events.publish(
            "created",
            path=path,
            scope=scope,
        )

        return {
            "status": "created",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # RENAME
    # ========================================================

    def rename(
        self,
        old_path: str,
        new_path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Rename or move a project file/directory.

        Publishes a ``renamed`` event on success. Raises ValueError
        if either path targets a read-only browser root, or if the
        two paths belong to different browser roots.
        """

        self.filesystem.require_writable(
            old_path,
            _root_for(scope),
        )

        self.filesystem.require_writable(
            new_path,
            _root_for(scope),
        )

        old_stripped, old_root, old_name = _target(
            old_path,
            scope,
        )

        new_stripped, new_root, new_name = _target(
            new_path,
            scope,
        )

        if old_root != new_root:

            raise ValueError(
                "Cannot rename across browser roots "
                f"({old_name or 'scope'} -> "
                f"{new_name or 'scope'})."
            )

        self.filesystem.rename_path(
            old_stripped,
            new_stripped,
            root=old_root,
        )

        self.events.publish(
            "renamed",
            path=new_path,
            old_path=old_path,
            scope=scope,
        )

        return {
            "status": "renamed",
            "old_path": old_path,
            "new_path": new_path,
            "scope": scope,
        }

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        path: str,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete a project file or directory.

        Publishes a ``deleted`` event on success. Raises ValueError
        if the path targets a read-only browser root.
        """

        self.filesystem.require_writable(
            path,
            _root_for(scope),
        )

        stripped, root, _ = _target(path, scope)

        self.filesystem.delete_path(
            stripped,
            root=root,
        )

        self.events.publish(
            "deleted",
            path=path,
            scope=scope,
        )

        return {
            "status": "deleted",
            "path": path,
            "scope": scope,
        }

    # ========================================================
    # ERROR MAPPING
    # ========================================================

    # Kept on the controller so every interface shares the same
    # error behaviour. See routers/error.py for the HTTP mapping.
    _to_error = staticmethod(
        lambda error: error
    )
```

---

<!-- ==== 71/125 : interface/core/session.py ==== -->

### interface/core/session.py

```python
"""
Project Manager interface sessions.
====================================

Tracks connected interface clients (browser tabs, agents).

This is intentionally an in-memory system. No database.
"""

from __future__ import annotations

import time
import uuid
from typing import Any


# ============================================================
# EDITOR SESSION
# ============================================================

class EditorSession:
    """
    State for a single connected interface client.
    """

    def __init__(
        self,
        client_id: str | None = None,
    ) -> None:
        self.client_id = client_id or uuid.uuid4().hex
        self.open_file: str | None = None
        self.dirty: bool = False
        self.last_modified: float | None = None

    def snapshot(self) -> dict[str, Any]:
        """
        JSON-friendly copy of this session.
        """

        return {
            "client_id": self.client_id,
            "open_file": self.open_file,
            "dirty": self.dirty,
            "last_modified": self.last_modified,
        }

    def touch(self) -> None:
        """
        Update the last-modified timestamp.
        """

        self.last_modified = time.time()


# ============================================================
# EDITOR MANAGER
# ============================================================

class EditorManager:
    """
    Maintains the active in-memory interface sessions.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, EditorSession] = {}

    def register(self, client_id: str | None = None) -> EditorSession:
        """
        Register a new connected client.
        """

        session = EditorSession(client_id=client_id)
        session.touch()

        self._sessions[session.client_id] = session

        return session

    def unregister(self, client_id: str) -> None:
        """
        Remove a client session.
        """

        self._sessions.pop(client_id, None)

    def get(self, client_id: str) -> EditorSession | None:
        """
        Fetch a session by client id.
        """

        return self._sessions.get(client_id)

    def update(
        self,
        client_id: str,
        *,
        open_file: str | None = None,
        dirty: bool | None = None,
    ) -> EditorSession | None:
        """
        Update one field of a client session.

        Returns the session, or None if the client is unknown.
        """

        session = self._sessions.get(client_id)

        if session is None:
            return None

        session.touch()

        if open_file is not None:
            session.open_file = open_file

        if dirty is not None:
            session.dirty = dirty

        return session

    def snapshot(self) -> list[dict[str, Any]]:
        """
        JSON-friendly list of all active sessions.
        """

        return [
            session.snapshot()
            for session in self._sessions.values()
        ]
```

---

<!-- ==== 72/125 : interface/routers/__init__.py ==== -->

### interface/routers/__init__.py

```python
"""
Project Manager HTTP API helpers.
==================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from parameters import filesystem
from interface.core.defaults import get_interface
from interface.core.operations import VALID_SCOPES


# ============================================================
# SHARED CONTROLLER
# ============================================================

def controller() -> Any:
    """
    The single shared Project Manager interface instance.
    """

    return get_interface()


# ============================================================
# SCOPE HANDLING
# ============================================================

def normalize_scope(scope: str | None) -> str | None:
    """
    Validate and normalize a scope query parameter.

    Returns None when the parameter is absent, which selects the
    browser view (paths may carry a browser-root prefix). An
    explicit scope keeps the legacy single-root behaviour.

    Raises:
        HTTPException (422):
            If the scope is not a known scope.
    """

    if scope is None:

        return None

    if scope not in VALID_SCOPES:

        raise HTTPException(
            status_code=422,
            detail=f"Unknown scope: {scope}",
        )

    return scope


def normalize_roots(
    roots: str | None,
) -> list[str] | None:
    """
    Validate and normalize the ``roots`` query parameter.

    A comma-separated list of browser-root names. Empty entries are
    dropped and order is preserved; None means "no filter", which is
    the whole browser tree.

    Raises:
        HTTPException (422):
            If a name is not a configured browser root. An unknown
            root is refused rather than dropped, because a typo
            that returned a smaller tree would read as a page that
            legitimately has less in it.
    """

    if roots is None:

        return None

    names = [
        name.strip()
        for name in roots.split(",")
        if name.strip()
    ]

    if not names:

        return None

    for name in names:

        if name not in filesystem.BROWSE_ROOTS:

            raise HTTPException(
                status_code=422,
                detail=f"Unknown browser root: {name}",
            )

    return names
```

---

<!-- ==== 73/125 : interface/routers/agents.py ==== -->

### interface/routers/agents.py

```python
"""
interface/routers/agents.py
===========================

Agent registry, run, and pipeline endpoints for the Project Manager.

Every agent is built and run through ``interface_runner.AgentInterface``,
the same seam the headless CLI uses, so behaviour cannot drift between
frontends. Discovery likewise has a single source of truth: the engine's
agent roots (``engine/agents/roots.py``). The Project Manager registers
``<workspace>/agents/`` as a root at startup, so an agent created in the
workspace behaves exactly like a bundled library agent.

    GET  /api/agents
        -> every agent across every registered root (library +
           workspace), highest-precedence root first.

    GET  /api/agents/{agent_id}
        -> {"source", "meta", "sections"} for one agent, resolved through
           the loader, so the editor can open/read its definition.

    POST /api/agents/run
        {"json_path", "md_path" | "agent_id", "message", "model"?}
        -> builds the agent (workspace-relative paths resolved through the
           Project Manager filesystem), runs it without persisting chat, and
           returns {"reply", "agent_id", "name", "model", "tool_events"}.

    GET /api/pipeline
        -> default step chain from config/pipeline.json plus every selectable
           step candidate (library + workspace agents).

    POST /api/pipeline
        {"steps": [id | {"json_path", "md_path"}], "message", "model"?}
        -> run_pipeline: cascade the ordered steps, feed-forward every
           earlier step's reply into the next; each step's stdout line is
           "Agent N (<id>) completed. Tools used: <tools>".

    GET /api/models
        -> models listed in config/models.json, for the frontend picker.

    GET /api/tools
        -> registered tool IDs and short descriptions, so the Prompt Builder
           can show and insert tools without keeping a second copy of the list.

All file tool calls run in-process through DirectProjectIO, so
parameters.filesystem remains the single filesystem authority.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .errors import project_manager_error
from .chat import MAX_MESSAGE_LENGTH


# ------------------------------------------------------------
# Headless engine bootstrap
# ------------------------------------------------------------

def _ensure_headless_on_path() -> None:
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "headless_app"
    if not candidate.is_dir():
        candidate = here.parents[2]
    candidate = candidate.resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


_ensure_headless_on_path()

from engine.agents.loader import AgentNotFoundError  # noqa: E402
from engine.agents.registry import list_agents  # noqa: E402
from engine.pipeline import load_pipeline  # noqa: E402

try:
    from bridge.providers import DirectProjectIO  # noqa: E402
except Exception:
    DirectProjectIO = None  # type: ignore[assignment]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class AgentRunRequest(BaseModel):

    message: str

    agent_id: str | None = None

    json_path: str | None = None

    md_path: str | None = None

    model: str | None = None


class PipelineRunRequest(BaseModel):

    steps: list = []

    message: str

    model: str | None = None


# ============================================================
# PROJECT MANAGER FILESYSTEM AUTHORITY
# ============================================================

_workspace_root: Any = None


def _pm_filesystem():
    """parameters.filesystem when running inside the Project Manager."""
    try:
        from parameters import filesystem
        return filesystem
    except Exception:
        return None


def _workspace() -> Path | None:
    global _workspace_root
    if _workspace_root is not None:
        return _workspace_root
    filesystem = _pm_filesystem()
    if filesystem is None:
        _workspace_root = None
        return None
    _workspace_root = filesystem.PROJECT_ROOT
    return _workspace_root


def _resolve(relative_path: str) -> Path:
    """Safe absolute path for an agent file path.

    Workspace-relative paths ("agents/demo/agent.json") are the documented
    input. An absolute path is also accepted, but only when it really is
    inside the workspace, so a queue saved from a previous session cannot
    reach outside the project.
    """
    filesystem = _pm_filesystem()
    if filesystem is None:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            return candidate
        raise ValueError(
            "Running outside the Project Manager - a workspace-relative "
            "path cannot be resolved."
        )
    if Path(relative_path).is_absolute():
        resolved = Path(relative_path).resolve()
        try:
            resolved.relative_to(Path(filesystem.PROJECT_ROOT).resolve())
        except ValueError:
            raise ValueError(
                "Access outside the project directory is not allowed."
            )
        return resolved
    return filesystem.resolve_project_path(relative_path)


def _provider() -> Any:
    if DirectProjectIO is None:
        raise RuntimeError(
            "DirectProjectIO is unavailable - the agent router must run "
            "inside the Project Manager server."
        )
    return DirectProjectIO()


def _api_path(path: str | None) -> str | None:
    """Translate an engine path into a workspace-relative API path.

    The engine reports absolute paths (its own truth), but the API contract is
    workspace-relative ("agents/<name>/agent.md") because that is what the
    frontend stores in the pipeline queue and sends back to the run endpoints.
    Returns None for anything outside the workspace (a library agent).
    """
    if not path:
        return None
    workspace = _workspace()
    if workspace is None:
        return None
    try:
        rel = Path(path).resolve().relative_to(Path(workspace).resolve())
    except (ValueError, OSError):
        return None
    return rel.as_posix()


def _agent_payload(summary: dict) -> dict:
    """Shape one registry summary for /api/agents.

    json_path/md_path are present only for workspace agents, matching the
    contract the pipeline queue and editor already depend on.
    """
    payload = {
        "id": summary["id"],
        "name": summary["name"],
        "description": summary["description"],
        "mode": summary["mode"],
        "model": summary["model"],
        "tools": summary["tools"],
        "source": summary["source"],
        "complete": summary["complete"],
    }
    json_path = _api_path(summary.get("json_path"))
    if json_path is not None:
        payload["json_path"] = json_path
        payload["md_path"] = _api_path(summary.get("md_path"))
    return payload


_runner_cache: Any = None


def _runner() -> Any:
    """The shared AgentInterface, the single engine entry point.

    Stateless between requests: each run builds a fresh agent bound to its
    own tools and session, so concurrent agents cannot interfere.
    """
    global _runner_cache
    if _runner_cache is None:
        from interface_runner import AgentInterface  # noqa: E402

        _runner_cache = AgentInterface(bridge=_provider())
    return _runner_cache


# ============================================================
# MESSAGE VALIDATION
# ============================================================

def _validated_message(message: str) -> str:
    text = message.strip()
    if not text:
        raise project_manager_error(ValueError("Chat message cannot be empty."))
    if len(text) > MAX_MESSAGE_LENGTH:
        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )
    return text


# ============================================================
# LIST AGENTS
# ============================================================

@router.get("/api/agents")
def list_all_agents(
    request: Request,
):
    """
    Return every runnable agent, from every registered agent root.

    Discovery is the engine's single source of truth
    (engine/agents/registry.py), so the library and workspace agents
    arrive through one code path. Workspace agents include
    json_path/md_path so the frontend can run or open them directly.
    """

    try:

        return {
            "agents": [_agent_payload(a) for a in list_agents()],
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# GET ONE AGENT DEFINITION
# ============================================================

@router.get("/api/agents/{agent_id}")
def get_agent_definition(
    request: Request,
    agent_id: str,
):
    """
    Return one agent's metadata + markdown sections.

    Resolution goes through the loader, so a workspace agent wins over
    a library agent with the same id - the same precedence discovery
    and ``build_agent`` use.
    """

    from engine.agents.loader import (
        agent_json_path,
        agent_md_path,
        load_definition,
    )
    from engine.agents.roots import find_agent

    try:

        definition = load_definition(agent_id)

        found = find_agent(agent_id)
        source = found[0].source if found is not None else "library"

        payload = {
            "source": source,
            "meta": definition["meta"],
            "sections": definition["sections"],
        }

        json_path = _api_path(agent_json_path(agent_id))
        if json_path is not None:
            payload["json_path"] = json_path
            payload["md_path"] = _api_path(agent_md_path(agent_id))

        return payload

    except Exception as error:
        raise project_manager_error(
            ValueError(f"Agent not found: {agent_id} ({error})")
        )


# ============================================================
# RUN ONE AGENT (from agent.json / agent.md or a library id)
# ============================================================

@router.post("/api/agents/run")
def run_single_agent(
    request: Request,
    payload: AgentRunRequest,
):
    """
    Build and run one agent, then log the exchange.

    Body:
        message:   the user's instruction (required).
        json_path/md_path:
                   workspace-relative paths to agent.json + agent.md
                   (e.g. "agents/demo/agent.json"). When given, the agent
                   is built from those files; otherwise agent_id is used.
        agent_id:  agent id (any registered root) to run when json_path is
                   not given.
        model:     optional model override.
    """

    message = _validated_message(payload.message)

    try:

        # Workspace-relative paths must become absolute (and stay inside
        # the workspace) before the engine reads them.
        json_file = _resolve(str(payload.json_path)) if payload.json_path else None
        md_file = _resolve(str(payload.md_path)) if payload.md_path else None

        result = _runner().run_single_agent(
            message,
            json_path=str(json_file) if json_file else None,
            md_path=str(md_file) if md_file else None,
            agent_id=payload.agent_id or None,
            model=payload.model,
            persist=False,
        )

        entries = result.get("entries") or []

        return {
            "status": "ok",
            "reply": result["reply"],
            "agent_id": result["agent_id"],
            "name": result.get("name", ""),
            "description": result.get("description", ""),
            "model": result.get("model"),
            "tool_events": result.get("tool_events") or [],
            "entry": entries[0] if entries else None,
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# PIPELINE OPTIONS
# ============================================================

@router.get("/api/pipeline")
def pipeline_options(
    request: Request,
):
    """
    Return the default step chain (config/pipeline.json) plus every
    selectable step candidate (library + workspace agents).

    The frontend starts with an empty selection and lets the user build an
    ordered, reorderable cascade from these candidates.
    """

    try:

        return {
            "default_steps": load_pipeline(),
            "candidates": [_agent_payload(a) for a in list_agents()],
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# RUN PIPELINE (multi-agent cascade)
# ============================================================

@router.post("/api/pipeline")
def run_agent_pipeline(
    request: Request,
    payload: PipelineRunRequest,
):
    """
    Cascade many agents one after another.

    Body:
        steps:   ordered list. Each element is either a library agent id
                 (str) or a dict with workspace-relative json_path + md_path
                 (workspace agent). Every later step receives the original
                 message plus all earlier steps' replies as its input.
        message: the original user request.
        model:   optional model override for every step.

    Returns {"reply", "outputs": [{agent_id, agent_name, output, tools_used}],
    "tool_events"} and logs the exchange.
    """

    message = _validated_message(payload.message)
    steps = list(payload.steps or [])

    if not steps:

        raise project_manager_error(
            ValueError("Pipeline requires at least one step.")
        )

    try:

        normalized: list = []
        for step in steps:
            if isinstance(step, dict):
                if not (step.get("json_path") and step.get("md_path")):
                    raise project_manager_error(
                        ValueError(
                            "Pipeline step dicts need json_path + md_path: "
                            f"{step!r}"
                        )
                    )
                normalized.append({
                    "json_path": str(_resolve(str(step["json_path"]))),
                    "md_path": str(_resolve(str(step["md_path"]))),
                })
            else:
                normalized.append(str(step))

        result = _runner().run_pipeline(
            message,
            agent_configs=normalized,
            model=payload.model,
            persist=False,
        )

        return {
            "status": "ok",
            "reply": result["reply"],
            "outputs": result["outputs"],
            "tool_events": result["tool_events"],
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(f"Agent definition not found: {error}")
        )

    except ValueError as error:

        raise project_manager_error(error)

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# MODELS
# ============================================================

@router.get("/api/models")
def list_models(
    request: Request,
):
    """
    Return the models in config/models.json for the frontend picker.
    Run refresh_models to re-scan installed Ollama models.
    """

    from engine.core import llm

    model_file = llm.CONFIG_DIR / "models.json"

    try:

        if model_file.exists():
            data = json.loads(model_file.read_text(encoding="utf-8"))
            models = data.get("models") or []
        else:
            models = []

        return {
            "models": [
                {
                    "id": m.get("id", ""),
                    "name": m.get("name", m.get("id", "")),
                    "source": m.get("source", "ollama"),
                }
                for m in models
            ],
        }

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# TOOLS
# ============================================================

@router.get("/api/tools")
def list_tool_ids(
    request: Request,
):
    """
    Return tool IDs and descriptions the registry can resolve.

    The registry is the single source of truth for what ``agent.json``'s
    ``tools`` may name (tools/registry.py), so the Prompt Builder asks for
    this list instead of keeping its own copy that could silently drift.

    ``mode: "chat"`` attaches none of these; ``mode: "agent"`` attaches the
    ones an ``agent.json`` lists (engine/agents/factory.py).
    """

    from tools.registry import get, list_tools

    try:
        tool_ids = list_tools()
        details = []
        for tool_id in tool_ids:
            tool = get(tool_id)
            if tool is None:
                raise RuntimeError(
                    f"Registered tool '{tool_id}' could not be resolved."
                )
            details.append({
                "id": tool_id,
                "description": tool.description or "",
            })

        return {
            "tools": tool_ids,
            "details": details,
        }

    except Exception as error:

        raise project_manager_error(error)
```

---

<!-- ==== 74/125 : interface/routers/chat.py ==== -->

### interface/routers/chat.py

```python
"""Agent-backed chat with browser-supplied context and saved text sessions."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .errors import project_manager_error


# ------------------------------------------------------------
# Headless engine bootstrap (works from the server app or when imported
# from the headless bridge package).
# ------------------------------------------------------------

def _ensure_headless_on_path() -> None:
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "headless_app"
    if not candidate.is_dir():
        candidate = here.parents[2]
    candidate = candidate.resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


_ensure_headless_on_path()

from engine.agents.loader import AgentNotFoundError  # noqa: E402
from engine.agents.registry import list_agents  # noqa: E402
try:
    from bridge.providers import DirectProjectIO  # noqa: E402
except Exception:
    DirectProjectIO = None  # type: ignore[assignment]


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatHistoryEntry(BaseModel):

    role: Literal["user", "assistant"]

    content: str


class ChatMessage(BaseModel):

    message: str

    agent_id: str | None = None

    model: str | None = None

    history: list[ChatHistoryEntry] = Field(default_factory=list)


class ChatSessionEntry(BaseModel):

    sender: Literal["user", "agent"]

    message: str

    ts: str = ""

    agent: str | None = None


class SessionSave(BaseModel):

    agent_id: str

    title: str | None = None

    entries: list[ChatSessionEntry]

# ============================================================
# CHAT REQUEST LIMITS
# ============================================================

MAX_MESSAGE_LENGTH = 32000

MAX_HISTORY_ENTRIES = 200

MAX_SESSION_ENTRIES = 2000

_provider_cache: Any = None
_runner_cache: Any = None


def _provider() -> Any:
    """The active filesystem authority in the in-process server."""
    global _provider_cache
    if _provider_cache is None:
        if DirectProjectIO is None:
            raise RuntimeError(
                "DirectProjectIO is unavailable - the agent-backed chat "
                "router must run inside the Project Manager server."
            )
        _provider_cache = DirectProjectIO()
    return _provider_cache


def _runner() -> Any:
    """The shared AgentInterface, the single engine entry point.

    Holds no conversation state: each run builds a fresh agent and uses only
    the history supplied by the browser, so requests stay independent.
    """
    global _runner_cache
    if _runner_cache is None:
        from interface_runner import AgentInterface  # noqa: E402

        _runner_cache = AgentInterface(bridge=_provider())
    return _runner_cache


def _default_agent_id() -> str | None:
    agents = list_agents()
    if not agents:
        return None
    return agents[0]["id"]


# ============================================================
# SEND MESSAGE
# ============================================================

@router.post("/api/chat")
def send_chat_message(
    request: Request,
    payload: ChatMessage,
):
    """
    Send a message to the agent engine and return its reply.

    Body:
        message (str):   the user's message (required, non-empty, max 2000).
        agent_id (str):  agent to use; defaults to the first registered.
        model (str):     optional model override.

    The browser supplies the current thread as history. Chat turns are
    not written to the engine chat log; Save Session owns persistence.
    """

    message = payload.message.strip()

    if not message:

        raise project_manager_error(
            ValueError(
                "Chat message cannot be empty."
            )
        )

    if len(message) > MAX_MESSAGE_LENGTH:

        raise project_manager_error(
            ValueError(
                f"Chat message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters)."
            )
        )

    if len(payload.history) > MAX_HISTORY_ENTRIES:
        raise project_manager_error(
            ValueError(
                f"Chat history is too long (max {MAX_HISTORY_ENTRIES} messages)."
            )
        )

    agent_id = payload.agent_id or _default_agent_id()

    if not agent_id:

        raise project_manager_error(
            RuntimeError(
                "No agents are registered. Register an agent root and check "
                "that its agent.json files exist."
            )
        )

    try:

        result = _runner().run_chat(
            message,
            agent_id=agent_id,
            model=payload.model,
            history=[entry.model_dump() for entry in payload.history],
            use_logged_history=False,
            persist=False,
        )

        entries = result.get("entries") or []

        return {
            "status": "ok",
            "reply": result["reply"],
            "agent_id": result.get("agent_id", agent_id),
            "name": result.get("name", ""),
            "model": result.get("model"),
            "tool_events": result.get("tool_events") or [],
            "entry": entries[0] if entries else None,
        }

    except AgentNotFoundError as error:

        raise project_manager_error(
            ValueError(
                f"Agent not found: {agent_id} ({error})"
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# SAVED CHAT SESSIONS
# ============================================================
#
# A session file is the only persistent record of one chat thread.
# Sessions live under the managed workspace and are excluded from git
# with workspace/data/.
#
#     workspace/data/chat_sessions/<agent_id>/<session_id>.txt

SESSIONS_DIRNAME = "data/chat_sessions"

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")

MAX_TITLE_LENGTH = 80

EXPORT_FORMATS = ("txt",)


def _sessions_root() -> Path:
    """Absolute path of the sessions directory inside the workspace."""
    from parameters import filesystem

    return filesystem.resolve_project_path(SESSIONS_DIRNAME)


def _safe_id(value: str, kind: str) -> str:
    """
    Validate an id used as a single path segment.

    Agent and session ids both become directory or file names, so
    anything that could climb out of the sessions directory is
    refused rather than sanitized.
    """

    if not value or not SAFE_ID.match(value):
        raise ValueError(
            f"Invalid {kind}: {value!r}. Use letters, numbers, "
            "underscore or dash only."
        )

    return value


def _new_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _derive_title(entries: list[dict]) -> str:
    """Title from the first user turn, else a timestamp."""
    for entry in entries:
        if entry.get("sender") == "user":
            text = " ".join(str(entry.get("message", "")).split())
            if text:
                if len(text) > MAX_TITLE_LENGTH:
                    text = text[: MAX_TITLE_LENGTH - 1].rstrip() + "\u2026"
                return text
    return "Session " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _session_file(session_id: str, agent_id: str) -> Path:
    agent = _safe_id(agent_id, "agent id")
    session = _safe_id(session_id, "session id")
    return _sessions_root() / agent / f"{session}.txt"


def _summary(record: dict) -> dict:
    """List-view projection of a stored session."""
    return {
        "id": record.get("id", ""),
        "agent_id": record.get("agent_id", ""),
        "title": record.get("title", ""),
        "created": record.get("created", ""),
        "entry_count": len(record.get("entries", [])),
    }


def _read_session(session_id: str, agent_id: str) -> dict:
    path = _session_file(session_id, agent_id)
    if not path.exists():
        raise FileNotFoundError(f"No saved session {session_id!r}.")
    return _parse_session_text(path.read_text(encoding="utf-8"))


def _serialize_session(record: dict) -> str:
    """Write one readable text transcript with length-delimited messages."""
    display_title = " ".join(str(record.get("title") or "Chat session").split())
    metadata = {
        key: record.get(key, "")
        for key in ("id", "agent_id", "title", "created")
    }
    lines = [
        f"# {display_title}",
        "",
        "<!-- session: " + json.dumps(metadata, ensure_ascii=False) + " -->",
        "",
    ]
    for entry in record.get("entries", []):
        message = str(entry.get("message", ""))
        entry_metadata = {
            "sender": entry.get("sender", ""),
            "agent": entry.get("agent"),
            "ts": entry.get("ts", ""),
            "length": len(message),
        }
        who = (
            "You"
            if entry_metadata["sender"] == "user"
            else entry_metadata.get("agent") or "Agent"
        )
        lines.extend([
            f"## {who}",
            "<!-- entry: " + json.dumps(entry_metadata, ensure_ascii=False) + " -->",
            message,
            "",
        ])
    return "\n".join(lines)


def _parse_session_text(text: str) -> dict:
    """Parse the app's readable text session format without losing message text."""
    lines = text.splitlines(keepends=True)
    if len(lines) < 3 or not lines[2].startswith("<!-- session: ") or not lines[2].rstrip().endswith(" -->"):
        raise ValueError("Saved chat session has an invalid header.")

    metadata_text = lines[2].rstrip()[len("<!-- session: "):-len(" -->")]
    record = json.loads(metadata_text)
    content = "".join(lines[3:])
    entries = []
    position = 0

    while position < len(content):
        while position < len(content) and content[position] == "\n":
            position += 1
        if position >= len(content):
            break
        if content.startswith("## ", position):
            heading_end = content.find("\n", position)
            if heading_end < 0:
                raise ValueError("Saved chat session has an incomplete message heading.")
            position = heading_end + 1
        marker_end = content.find("\n", position)
        if marker_end < 0:
            raise ValueError("Saved chat session has an incomplete message header.")
        marker = content[position:marker_end]
        prefix, suffix = "<!-- entry: ", " -->"
        if not marker.startswith(prefix) or not marker.endswith(suffix):
            raise ValueError("Saved chat session has an invalid message header.")
        entry_metadata = json.loads(marker[len(prefix):-len(suffix)])
        length = entry_metadata.get("length")
        if not isinstance(length, int) or length < 0:
            raise ValueError("Saved chat session has an invalid message length.")
        body_start = marker_end + 1
        body_end = body_start + length
        if body_end > len(content):
            raise ValueError("Saved chat session message is truncated.")
        message = content[body_start:body_end]
        if body_end < len(content) and content[body_end] == "\n":
            body_end += 1
        entries.append({
            "sender": entry_metadata.get("sender"),
            "agent": entry_metadata.get("agent"),
            "ts": entry_metadata.get("ts", ""),
            "message": message,
        })
        position = body_end

    record["entries"] = entries
    return record


def _sole_owner(session_id: str) -> str:
    """The agent that owns a session id, when the id is unique.

    Session ids embed a timestamp, so two agents saving in the same
    millisecond could collide. Callers pass the agent explicitly in
    that case; this helper only resolves the unambiguous case.
    """
    _safe_id(session_id, "session id")
    root = _sessions_root()
    owners = [
        path.parent.name
        for path in root.glob(f"*/{session_id}.txt")
    ] if root.is_dir() else []
    if not owners:
        raise FileNotFoundError(f"No saved session {session_id!r}.")
    if len(owners) > 1:
        raise ValueError(
            f"Session {session_id!r} exists for several agents "
            f"({', '.join(sorted(owners))}). Pass the agent explicitly."
        )
    return owners[0]


def _list_sessions(agent_id: str | None) -> list[dict]:
    """Every stored session, newest first.

    With ``agent_id`` set only that agent's sessions are returned,
    which is what the chat panel shows.
    """
    root = _sessions_root()
    if not root.is_dir():
        return []
    wanted = _safe_id(agent_id, "agent id") if agent_id else None
    records: list[dict] = []
    for path in root.glob("*/*.txt"):
        if wanted and path.parent.name != wanted:
            continue
        records.append(_parse_session_text(path.read_text(encoding="utf-8")))
    records.sort(key=lambda r: r.get("created", ""), reverse=True)
    return [_summary(record) for record in records]


@router.get("/api/chat/sessions")
def list_saved_sessions(
    request: Request,
    agent: str | None = None,
):
    """
    List saved chat sessions, newest first.

    Query params:
        agent:
            Only this agent's sessions. Omit to list every agent's.
    """

    try:

        return {
            "sessions": _list_sessions(agent),
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.post("/api/chat/sessions")
def save_chat_session(
    request: Request,
    payload: SessionSave,
):
    """
    Save the browser's current thread as its only persistent transcript.

    Body:
        agent_id (str):  whose thread to save (required).
        title (str?):    optional; defaults to the first user turn.

    The browser's live thread stays in memory and is not otherwise logged.
    """

    try:

        agent_id = _safe_id(payload.agent_id, "agent id")
        entries = [
            entry.model_dump()
            for entry in payload.entries
        ]

        if not entries:
            raise project_manager_error(
                ValueError(
                    "Nothing to save: the current chat has no messages."
                )
            )
        if len(entries) > MAX_SESSION_ENTRIES:
            raise project_manager_error(
                ValueError(
                    f"A session can contain at most {MAX_SESSION_ENTRIES} messages."
                )
            )

        title = (payload.title or "").strip()
        if len(title) > MAX_TITLE_LENGTH:
            raise project_manager_error(
                ValueError(
                    f"Session title is too long (max {MAX_TITLE_LENGTH} characters)."
                )
            )

        record = {
            "id": _new_session_id(),
            "agent_id": agent_id,
            "title": title or _derive_title(entries),
            "created": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }

        path = _session_file(record["id"], record["agent_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_serialize_session(record), encoding="utf-8")

        return {
            "status": "ok",
            "session": _summary(record),
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.get("/api/chat/sessions/{session_id}")
def get_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
):
    """
    Return one saved session, entries included.

    Query params:
        agent:
            Required when the session id is not unique across agents.
    """

    try:

        if not agent:
            agent = _sole_owner(session_id)

        return _read_session(session_id, agent)

    except FileNotFoundError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.delete("/api/chat/sessions/{session_id}")
def delete_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
):
    """
    Delete the text file holding one saved chat session.
    """

    try:

        if not agent:
            agent = _sole_owner(session_id)

        path = _session_file(session_id, agent)
        if not path.exists():
            raise project_manager_error(
                ValueError(
                    f"No saved session {session_id!r}."
                )
            )
        path.unlink()

        return {
            "status": "ok",
            "deleted": session_id,
        }

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


@router.get("/api/chat/sessions/{session_id}/export")
def export_saved_session(
    request: Request,
    session_id: str,
    agent: str | None = None,
    format: str = "txt",
):
    """
    Download a saved session as a file.

    Query params:
        agent:
            Required when the session id is not unique across agents.
        format:
            Only ``txt`` is supported so downloads remain the exact
            saved source file.
    """

    try:

        if format not in EXPORT_FORMATS:
            raise ValueError(
                f"Unsupported export format {format!r}. "
                f"Use one of: {', '.join(EXPORT_FORMATS)}."
            )

        if not agent:
            agent = _sole_owner(session_id)

        record = _read_session(session_id, agent)
        body = _session_file(session_id, agent).read_text(encoding="utf-8")
        media_type = "text/plain; charset=utf-8"
        extension = "txt"

        safe_title = re.sub(
            r"[^A-Za-z0-9_-]+",
            "-",
            record.get("title", "chat-session"),
        ).strip("-") or "chat-session"

        filename = f"{safe_title[:60]}-{session_id}.{extension}"

        return Response(
            content=body,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except FileNotFoundError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except ValueError as error:

        raise project_manager_error(
            ValueError(
                str(error)
            )
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


if __name__ == "__main__":
    print(__doc__)
```

---

<!-- ==== 75/125 : interface/routers/directories.py ==== -->

### interface/routers/directories.py

```python
"""Project directory resource router (create / delete)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from . import normalize_scope
from .errors import project_manager_error


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# CREATE DIRECTORY
# ============================================================

@router.post("/api/directory/create")
def create_directory(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Create a project directory.

    Query params:
        path:
            Browser-root-qualified or root-relative directory path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.create_directory(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# DELETE DIRECTORY
# ============================================================

@router.delete("/api/directory/delete")
def delete_directory(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Delete a project directory.

    Query params:
        path:
            Browser-root-qualified or root-relative directory path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.delete(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )
```

---

<!-- ==== 76/125 : interface/routers/errors.py ==== -->

### interface/routers/errors.py

```python
"""Shared FastAPI error mapping for the Project Manager API."""

from __future__ import annotations

from fastapi import HTTPException


def project_manager_error(
    error: Exception,
) -> HTTPException:
    """
    Convert a Project Manager operation error into an HTTP error.

    This is the single translator for the HTTP API. Routers do
    not implement their own status-code logic.
    """

    if isinstance(
        error,
        HTTPException,
    ):

        return error

    if isinstance(
        error,
        FileNotFoundError,
    ):

        return HTTPException(
            status_code=404,
            detail=str(error),
        )

    if isinstance(
        error,
        FileExistsError,
    ):

        return HTTPException(
            status_code=409,
            detail=str(error),
        )

    if isinstance(
        error,
        ValueError,
    ):

        return HTTPException(
            status_code=400,
            detail=str(error),
        )

    # --------------------------------------------------------
    # WebSocket-disconnect / client errors
    # --------------------------------------------------------

    if isinstance(
        error,
        KeyError,
    ):

        return HTTPException(
            status_code=404,
            detail=str(error),
        )

    return HTTPException(
        status_code=500,
        detail=str(error),
    )
```

---

<!-- ==== 77/125 : interface/routers/files.py ==== -->

### interface/routers/files.py

```python
"""Project file resource router (read / write / create / delete)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from . import normalize_scope
from .errors import project_manager_error


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class FileWriteRequest(BaseModel):

    path: str

    content: str

    scope: str | None = None


class FileCreateRequest(BaseModel):

    path: str

    content: str = ""

    scope: str | None = None


# ============================================================
# READ FILE
# ============================================================

@router.get("/api/file/read")
def read_file(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Read a project text file.

    Query params:
        path:
            Browser-root-qualified or root-relative file path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        content = request.app.state.editor.open(
            path,
            scope=normalize_scope(scope),
        )
        return {
            "path": path,
            "content": content,
            "scope": scope,
        }

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# WRITE FILE
# ============================================================

@router.put("/api/file/write")
def write_file(
    request: Request,
    payload: FileWriteRequest,
):
    """
    Create or overwrite a project text file.
    """

    try:

        return request.app.state.editor.save(
            payload.path,
            payload.content,
            scope=normalize_scope(payload.scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# CREATE FILE
# ============================================================

@router.post("/api/file/create")
def create_file(
    request: Request,
    payload: FileCreateRequest,
):
    """
    Create a new project file.
    """

    try:

        return request.app.state.editor.create_file(
            payload.path,
            payload.content,
            scope=normalize_scope(payload.scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# DELETE FILE
# ============================================================

@router.delete("/api/file/delete")
def delete_file(
    request: Request,
    path: str,
    scope: str | None = None,
):
    """
    Delete a project file.

    Query params:
        path:
            Browser-root-qualified or root-relative file path.
        scope:
            Omit for the browser view; ``"workspace"`` or
            ``"app"`` for a legacy single-root view.
    """

    try:

        return request.app.state.editor.delete(
            path,
            scope=normalize_scope(scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )
```

---

<!-- ==== 78/125 : interface/routers/paths.py ==== -->

### interface/routers/paths.py

```python
"""Project path resource router (rename / move)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from . import normalize_scope
from .errors import project_manager_error


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class RenameRequest(BaseModel):

    old_path: str

    new_path: str

    scope: str | None = None


# ============================================================
# RENAME
# ============================================================

@router.put("/api/path/rename")
def rename_path(
    request: Request,
    payload: RenameRequest,
):
    """
    Rename or move a project file/directory.
    """

    try:

        return request.app.state.editor.rename(
            payload.old_path,
            payload.new_path,
            scope=normalize_scope(payload.scope),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )
```

---

<!-- ==== 79/125 : interface/routers/project.py ==== -->

### interface/routers/project.py

```python
"""Project resource router.

Dashboard, health and interface-state endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from . import normalize_roots, normalize_scope
from .errors import project_manager_error


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# HEALTH
# ============================================================

@router.get("/api/health")
def health(
    request: Request,
):
    """
    Project Manager health and project information.
    """

    try:

        return request.app.state.editor.health()

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# PROJECT STATE
# ============================================================

@router.get("/api/project")
def get_project(
    request: Request,
    scope: str | None = None,
    roots: str | None = None,
):
    """
    Project information and filesystem tree.

    Query params:
        scope:
            Omit for the browser tree, whose top level is the
            configured browser roots. ``"workspace"`` or ``"app"``
            return the legacy single-root tree.
        roots:
            Comma-separated browser roots to include in the browser
            tree, e.g. ``?roots=test_environment``. Omit for all of
            them. This decides what a page is shown, not what it may
            read or write: an omitted root still resolves for file
            operations.
    """

    try:

        return request.app.state.editor.tree(
            scope=normalize_scope(scope),
            roots=normalize_roots(roots),
        )

    except Exception as error:

        raise project_manager_error(
            error
        )


# ============================================================
# SESSIONS
# ============================================================

@router.get("/api/sessions")
def get_sessions(
    request: Request,
):
    """
    Active interface sessions.
    """

    try:

        return request.app.state.editor.sessions()

    except Exception as error:

        raise project_manager_error(
            error
        )
```

---

<!-- ==== 80/125 : interface/routers/testing.py ==== -->

### interface/routers/testing.py

```python
"""
interface/routers/testing.py
============================

Agent header test endpoints for the Project Manager.

The tests themselves live in ``test_environment/agent_test.py``, outside
this package, because they are about the test environment rather than about
the workspace. This router is the seam: it resolves a published test agent,
hands it to that module, and reads back the evidence it wrote.

    GET  /api/test/agents
        -> every published test agent in test_environment/test_agents/.

    POST /api/test/agents/{agent_id}/workspace
        {"agent_id": "<workspace-folder-name>"}
        -> copy a test agent's agent.json + agent.md into workspace/agents/.

    DELETE /api/test/agents/{agent_id}
        -> delete one published test agent from test_environment/.

    POST /api/test/run_header_tests
        {"agent_id", "model"?}
        -> run the four header tests against that agent and return
           {"summary", "results"}. Four model turns, so this takes as long
           as the model takes; it is a plain sync endpoint, which FastAPI
           runs off the event loop in its threadpool.

    GET  /api/test/results
        -> the last report written to output/test_results.json, or 404
           when the suite has never run.

Two things are deliberately not shared with the live chat path. The agent
under test lives in the test environment, so it never joins the registry and
never appears in the agent picker. And the run's chat log and tool log are
redirected by the test runner itself into test_environment/test_data/, so its
four prompts and four replies never reach the chat history that
``search_chat_logs`` and the saved sessions read. This router only has to avoid
undoing that: the redirection is applied and unwound inside the runner, next to
the code that writes the logs.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from parameters import filesystem
from .errors import project_manager_error


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class HeaderTestRequest(BaseModel):

    agent_id: str

    model: str | None = None


class WorkspaceAgentRequest(BaseModel):

    agent_id: str


SAFE_AGENT_ID = re.compile(r"^[A-Za-z0-9_-]+$")


# ============================================================
# TEST ENVIRONMENT BOOTSTRAP
# ============================================================

#: The engine and the test environment are repository siblings of
#: this package, so both are reached by walking up from here rather
#: than by being installed.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_HEADLESS_APP = _REPO_ROOT / "headless_app"
_TEST_ENVIRONMENT = _REPO_ROOT / "test_environment"

for _on_path in (_HEADLESS_APP, _TEST_ENVIRONMENT):
    if _on_path.is_dir() and str(_on_path) not in sys.path:
        sys.path.insert(0, str(_on_path))


def _agent_test() -> ModuleType:
    """Import test_environment/agent_test.py once per process.

    Loaded by path rather than by name so the module is found whether
    this runs from the server, from a test client, or from a script in
    another working directory.
    """
    module = sys.modules.get("agent_test")
    if module is not None:
        return module

    source = _TEST_ENVIRONMENT / "agent_test.py"
    if not source.is_file():
        raise FileNotFoundError(
            f"Test runner not found: {source}. The test environment is "
            "part of the repository; restore it or point the server at a "
            "checkout that has it."
        )

    spec = importlib.util.spec_from_file_location("agent_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load the test runner: {source}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_test"] = module
    spec.loader.exec_module(module)
    return module


# ============================================================
# PUBLISHED TEST AGENTS
# ============================================================

@router.get("/api/test/agents")
def list_test_agents(
    request: Request,
):
    """
    Return every published test agent.

    These are the agents in test_environment/test_agents/, not the
    registry: a test agent is not registered as an agent root, so it can
    be tested without ever showing up in the live agent picker.
    """

    try:

        return {"agents": _agent_test().list_test_agents()}

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# COPY TEST AGENT TO WORKSPACE
# ============================================================

@router.post("/api/test/agents/{agent_id}/workspace")
def copy_test_agent_to_workspace(
    agent_id: str,
    request: Request,
    payload: WorkspaceAgentRequest,
):
    """Copy a published test agent into workspace/agents without overwriting."""
    try:
        workspace_agent_id = payload.agent_id
        if not SAFE_AGENT_ID.fullmatch(agent_id) or not SAFE_AGENT_ID.fullmatch(workspace_agent_id):
            raise ValueError("Agent ids may contain only letters, numbers, underscores and dashes.")

        agent_test = _agent_test()
        json_file, md_file = agent_test.resolve_agent_files(agent_id)
        destination = f"agents/{workspace_agent_id}"
        destination_path = filesystem.resolve_project_path(destination)

        if destination_path.exists():
            raise FileExistsError(
                f"Workspace agent '{workspace_agent_id}' already exists."
            )

        destination_path.mkdir(parents=True, exist_ok=False)
        try:
            filesystem.create_file(
                f"{destination}/agent.json",
                json_file.read_text(encoding="utf-8"),
            )
            filesystem.create_file(
                f"{destination}/agent.md",
                md_file.read_text(encoding="utf-8"),
            )
        except Exception as error:
            try:
                filesystem.delete_path(destination)
            except Exception as cleanup_error:
                raise RuntimeError(
                    f"Could not finish copying the agent ({error}) and "
                    f"could not remove the incomplete workspace folder "
                    f"({cleanup_error})."
                ) from error
            raise

        return {
            "agent_id": workspace_agent_id,
            "source_agent_id": agent_id,
            "path": f"workspace/{destination}",
        }
    except Exception as error:
        raise project_manager_error(error)


# ============================================================
# DELETE TEST AGENT
# ============================================================

@router.delete("/api/test/agents/{agent_id}")
def delete_test_agent(
    agent_id: str,
    request: Request,
):
    """Delete one published test agent from the isolated test environment."""
    try:
        if not SAFE_AGENT_ID.fullmatch(agent_id):
            raise ValueError("Invalid agent id.")

        agent_test = _agent_test()
        agents_root = agent_test.TEST_AGENTS_DIR.resolve()
        folder = (agents_root / agent_id).resolve()
        folder.relative_to(agents_root)
        if not folder.is_dir():
            raise FileNotFoundError(f"Test agent '{agent_id}' was not found.")

        json_file, _ = agent_test.resolve_agent_files(agent_id)
        filesystem.remove_tree(folder)

        return {"agent_id": agent_id, "deleted": True}
    except Exception as error:
        raise project_manager_error(error)


# ============================================================
# RUN THE FOUR HEADER TESTS
# ============================================================

@router.post("/api/test/run_header_tests")
def run_header_tests(
    request: Request,
    payload: HeaderTestRequest,
):
    """
    Test one published agent against its four headers.

    Body:
        agent_id: a folder in test_environment/test_agents/ holding
                  agent.json + agent.md.
        model:    optional model override.

    Returns {"summary": {agent_id, model, ran_at, passed, failed, total,
    status}, "results": [{section, status, prompt, response, reason}]} and
    writes the same report to output/test_results.json.
    """

    try:

        agent_test = _agent_test()
        json_file, md_file = agent_test.resolve_agent_files(payload.agent_id)

        report = agent_test.run_tests_report(
            str(json_file),
            str(md_file),
            model=payload.model,
            agent_id=str(payload.agent_id),
        )

        # write_report stamps summary.results_file on the report it is
        # given as well as on the file, so the response and the file on
        # disk say the same thing about where the evidence landed.
        agent_test.write_report(report)

        return report

    except Exception as error:

        raise project_manager_error(error)


# ============================================================
# READ THE LAST REPORT
# ============================================================

@router.get("/api/test/results")
def read_results(
    request: Request,
):
    """
    Return the last header test report, or 404 when there is none.

    The file is written by the run endpoint, so a 404 here means the
    suite has not run in this checkout yet, not that a run failed.
    """

    try:

        agent_test = _agent_test()
        report = agent_test.read_report()

        if report is None:
            raise FileNotFoundError(
                "No header test results yet. Publish a test agent and run "
                "the suite, or POST /api/test/run_header_tests."
            )

        return report

    except Exception as error:

        raise project_manager_error(error)
```

---

<!-- ==== 81/125 : interface/routers/ws.py ==== -->

### interface/routers/ws.py

```python
"""
Project Manager WebSocket router.
=================================

Real-time interface sync for the Project Manager. Every client
connection gets:

  * a dedicated EditorSession inside the shared EditorManager;
  * a subscription to the shared EventBus, so every publish is
    forwarded to the browser over the same socket.

Not every publish reaches the browser -- only the projected
types the dashboard cares about (saved / created / renamed /
deleted / session events). Everything goes through the shared
EventBus; there is no direct filesystem access here.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


@router.websocket("/api/ws")
async def project_manager_socket(
    websocket: WebSocket,
) -> None:
    """
    Real-time Project Manager socket.

    Client -> Server (JSON messages):

        {"type": "open",        "path": "src/app.py"}
        {"type": "dirty",       "dirty": true}
        {"type": "subscribe",   "events": ["saved", "created"]}

    Server -> Client (JSON messages):

        {"type": "hello",        "client_id": "..."}
        {"type": "event",        "event": {publish payload}}
        {"type": "sessions",     "sessions": [...]}
    """

    await websocket.accept()

    controller = websocket.app.state.editor

    loop = asyncio.get_running_loop()

    session = controller.session_manager.register()

    try:

        await websocket.send_json(
            {
                "type": "hello",
                "client_id": session.client_id,
            }
        )

        def forward(
            event: dict[str, Any],
        ) -> None:
            """
            Forward a published event to this socket.

            ``EventBus.publish`` is called synchronously, and it can run on a
            worker thread (sync ``def`` endpoints run in the threadpool where
            there is no running event loop). We therefore capture the socket's
            loop up front and use ``loop.call_soon_threadsafe`` to hop back
            onto that loop before creating the send task -- a plain
            ``asyncio.create_task`` / ``get_running_loop`` here would raise
            ``RuntimeError`` on a worker thread and silently drop the event.
            """

            async def _send() -> None:

                try:

                    await websocket.send_json(
                        {
                            "type": "event",
                            "event": event,
                        }
                    )

                except Exception:

                    pass

            def _schedule() -> None:

                try:

                    loop.create_task(
                        _send()
                    )

                except Exception:

                    pass

            try:

                loop.call_soon_threadsafe(
                    _schedule
                )

            except Exception:

                pass

        subscription_id = controller.events.subscribe(
            forward,
        )

        async def _send_sessions() -> None:

            await websocket.send_json(
                {
                    "type": "sessions",
                    "sessions": controller.session_manager.snapshot(),
                }
            )

        await _send_sessions()

        while True:

            raw = await websocket.receive_text()

            try:

                message = json.loads(raw)

            except json.JSONDecodeError:

                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "Message was not valid JSON.",
                    }
                )

                continue

            message_type = message.get(
                "type"
            )

            if message_type == "open":

                controller.session_manager.update(
                    session.client_id,
                    open_file=message.get(
                        "path"
                    ),
                )

                await websocket.send_json(
                    {
                        "type": "hello",
                        "client_id": session.client_id,
                        "open_file": message.get(
                            "path"
                        ),
                    }
                )

            elif message_type == "dirty":

                controller.session_manager.update(
                    session.client_id,
                    dirty=bool(
                        message.get(
                            "dirty",
                            False,
                        )
                    ),
                )

            elif message_type == "sessions":

                await _send_sessions()

            else:

                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": "Unknown message type: "
                        + str(message_type),
                    }
                )

    except WebSocketDisconnect:

        pass

    except Exception:

        pass

    finally:

        try:

            controller.events.unsubscribe(
                subscription_id  # type: ignore[possibly-undefined]
            )

        except Exception:

            pass

        controller.session_manager.unregister(
            session.client_id
        )
```

---

<!-- ==== 82/125 : interface_runner.py ==== -->

### interface_runner.py

```python
"""
interface_runner.py - compatibility shim.

AgentInterface now lives in engine_logic.EngineRuntime. This alias keeps
existing imports (routers, run.py, test_environment/agent_test.py) working.
New code should import engine_interface instead.
"""

from engine_logic import DEFAULT_HISTORY_LIMIT, EngineRuntime as AgentInterface  # noqa: F401

__all__ = ["AgentInterface", "DEFAULT_HISTORY_LIMIT"]
```

---

<!-- ==== 83/125 : parameters/__init__.py ==== -->

### parameters/__init__.py

```python
"""Project parameters package.

Holds the Project Manager filesystem owner (filesystem.py) that owns
the managed workspace, plus the project metadata it manages.
"""
```

---

<!-- ==== 84/125 : parameters/filesystem.py ==== -->

### parameters/filesystem.py

```python
"""
Project Manager Filesystem
==========================

This module is responsible for managing the physical
project filesystem.

Responsibilities:
    - Discover the project root.
    - Create the basic project structure.
    - Create/read project.json.
    - Read the project filesystem.
    - Read files.
    - Write files.
    - Create files.
    - Create directories.
    - Rename files/directories.
    - Delete files/directories.
    - Prevent access outside the project root.

The web server does NOT contain filesystem logic.
server.py calls this module.
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PARAMETERS_DIR = Path(__file__).resolve().parent

REPO_ROOT = PARAMETERS_DIR.parent

PROJECT_ROOT = REPO_ROOT / "workspace"

PROJECT_JSON = PROJECT_ROOT / "project.json"

SOURCE_FILES_ROOT = REPO_ROOT / "source_files"

#: The isolated test environment. It is a repository sibling of the
#: application, not part of the managed workspace, but the prompt
#: builder reads its parts from there and publishes agents into it,
#: so it is browsable and writable in its own right.
TEST_ENVIRONMENT_ROOT = REPO_ROOT / "test_environment"


# ============================================================
# STANDARD PROJECT FOLDERS
# ============================================================

PROJECT_FOLDERS = [
    "documentation",
    "project_scope",
    "To Do",
    "updates",
    "config",
    "data",
    "Tests"
]


# ============================================================
# BROWSER ROOTS
# ============================================================

# The folders the file browser shows. Add a folder here to
# make it appear in the tree; set ``writable`` to False to make it
# browse-only. Keys are the path prefixes the API understands, so
# ``source_files/APP_CODE_SNAPSHOT.md``, ``workspace/project.json`` and
# ``test_environment/test_agents/demo_agent/agent.md`` each resolve inside
# their own root.

BROWSE_ROOTS: dict[str, dict[str, Any]] = {
    "workspace": {
        "path": PROJECT_ROOT,
        "writable": True,
    },
    "test_environment": {
        "path": TEST_ENVIRONMENT_ROOT,
        "writable": True,
    },
    "source_files": {
        "path": SOURCE_FILES_ROOT,
        "writable": False,
    },
}


# Files above this size open read-only so the browser editor
# never tries to render a multi-megabyte document.

MAX_EDITABLE_BYTES = 512 * 1024


# ============================================================
# FILE TYPES
# ============================================================

TEXT_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".sql",
    ".xml",
    ".csv",
    ".env",
}


# ============================================================
# DIRECTORIES TO HIDE
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
}


# ============================================================
# DEFAULT PROJECT INFORMATION
# ============================================================

DEFAULT_PROJECT = {
    "name": PROJECT_ROOT.name,
    "version": "1.0.0",
    "workspace_version": "1.0",
}


# ============================================================
# PATH SECURITY
# ============================================================

def resolve_project_path(
    relative_path: str,
    root: Path | None = None,
) -> Path:
    """
    Convert a project-relative path into a safe absolute path.

    This prevents paths such as:

        ../../some_file.txt

    from escaping the active project root. The default root is the
    managed workspace; scope-aware callers pass the repository root
    to reach application files.

    Args:
        relative_path:
            Path relative to the active root.
        root:
            Filesystem root the path must stay inside. Defaults to
            the managed workspace.

    Returns:
        Safe absolute Path.

    Raises:
        ValueError:
            If the path is empty or outside the root.
    """

    if root is None:

        root = PROJECT_ROOT

    if not relative_path:

        raise ValueError(
            "A project-relative path is required."
        )

    # Normalize Windows separators.
    relative_path = relative_path.replace(
        "\\",
        "/",
    )

    candidate = (
        root / relative_path
    ).resolve()

    try:

        candidate.relative_to(
            root
        )

    except ValueError:

        raise ValueError(
            "Access outside the project directory "
            "is not allowed."
        )

    return candidate


# ============================================================
# BROWSER ROOT RESOLUTION
# ============================================================

def split_root(
    relative_path: str,
) -> tuple[str | None, str]:
    """
    Split a path into its browser-root name and the remainder.

    Returns:
        ``(root_name, remainder)``. ``root_name`` is None when the
        first segment is not a known root, meaning the caller
        should treat the path as legacy and root-relative.
    """

    normalized = relative_path.replace(
        "\\",
        "/",
    ).strip()

    head, separator, tail = normalized.partition(
        "/"
    )

    if not separator:

        return None, normalized

    if head in BROWSE_ROOTS:

        return head, tail

    return None, normalized


def is_writable_root(
    root_name: str | None,
) -> bool:
    """
    Whether a browser root accepts writes.

    Legacy (root-less) paths are treated as writable so existing
    callers keep working.
    """

    if root_name is None:

        return True

    return bool(
        BROWSE_ROOTS[root_name].get(
            "writable",
            False,
        )
    )


def resolve_browse_target(
    relative_path: str,
    legacy_root: Path | None = None,
) -> tuple[str, Path, str | None]:
    """
    Split a possibly root-qualified path into the arguments the
    filesystem operations expect.

    ``source_files/APP_CODE_SNAPSHOT.md`` resolves inside the
    ``source_files`` root. Paths without a known root prefix fall back to
    ``legacy_root`` (the managed workspace by default) so existing
    API callers are unaffected.

    Args:
        relative_path:
            Root-qualified or legacy relative path.
        legacy_root:
            Root used when the path carries no root prefix.

    Returns:
        ``(stripped_relative, root, root_name)``. ``root_name`` is
        None for legacy paths.

    Raises:
        ValueError:
            If the path is empty or names a root with no remainder.
    """

    root_name, remainder = split_root(
        relative_path
    )

    if root_name is None:

        return (
            relative_path,
            legacy_root
            if legacy_root is not None
            else PROJECT_ROOT,
            None,
        )

    if not remainder:

        raise ValueError(
            "A path inside "
            f"{root_name} is required."
        )

    return (
        remainder,
        BROWSE_ROOTS[root_name]["path"],
        root_name,
    )


def resolve_browse_path(
    relative_path: str,
    legacy_root: Path | None = None,
) -> tuple[Path, str | None]:
    """
    Resolve a possibly root-qualified path to a safe absolute path.

    Returns:
        ``(absolute_path, root_name)``. ``root_name`` is None for
        legacy paths.

    Raises:
        ValueError:
            If the path is empty or escapes its root.
    """

    stripped, root, root_name = (
        resolve_browse_target(
            relative_path,
            legacy_root,
        )
    )

    return resolve_project_path(
        stripped,
        root,
    ), root_name


def require_writable(
    relative_path: str,
    legacy_root: Path | None = None,
) -> str | None:
    """
    Ensure a path may be written to.

    Args:
        relative_path:
            Root-qualified or legacy relative path.
        legacy_root:
            Root used when the path carries no root prefix.

    Returns:
        The resolved root name (None for legacy paths).

    Raises:
        ValueError:
            If the path targets a read-only root.
    """

    _, root_name = resolve_browse_path(
        relative_path,
        legacy_root,
    )

    if not is_writable_root(root_name):

        raise ValueError(
            f"{root_name} is read-only."
        )

    return root_name


def read_browse_filesystem(
    roots: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Build the browser tree.

    The top level is always the configured ``BROWSE_ROOTS`` folders,
    so the tree itself acts as the folder switcher. Every node path
    is prefixed with its root name.

    Roots that do not exist on disk are skipped.

    Args:
        roots:
            Names to include, or None for all of them. This narrows
            what a page is *shown*, nothing more: the omitted roots
            stay in ``BROWSE_ROOTS``, so their paths still resolve
            for read, write and delete. A page that lists one root
            can therefore hand a file from another root to a page
            that does list it.

    Returns:
        JSON-friendly tree, in ``BROWSE_ROOTS`` declaration order.
    """

    wanted = None if roots is None else set(roots)

    results: list[dict[str, Any]] = []

    for root_name, config in BROWSE_ROOTS.items():

        if wanted is not None and root_name not in wanted:

            continue

        root_path: Path = config["path"]

        if not root_path.is_dir():

            continue

        results.append(
            {
                "name": root_name,
                "path": root_name,
                "type": "directory",
                "root": root_name,
                "writable": bool(
                    config.get("writable", False)
                ),
                "children": read_filesystem(
                    root_path,
                    _root=root_path,
                    _prefix=root_name,
                ),
            }
        )

    return results


# ============================================================
# PROJECT INITIALIZATION
# ============================================================

def build_project_filesystem() -> None:
    """
    Create the standard Project Manager filesystem.

    Existing files and folders are never deleted.

    Safe to run every time the server starts.
    """

    # --------------------------------------------------------
    # Create standard directories
    # --------------------------------------------------------

    for folder_name in PROJECT_FOLDERS:

        folder_path = (
            PROJECT_ROOT / folder_name
        )

        folder_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    # --------------------------------------------------------
    # Create project.json
    # --------------------------------------------------------

    if not PROJECT_JSON.exists():

        PROJECT_JSON.write_text(
            json.dumps(
                DEFAULT_PROJECT,
                indent=4,
            ),
            encoding="utf-8",
        )


# ============================================================
# PROJECT INFORMATION
# ============================================================

def read_project_info() -> dict[str, Any]:
    """
    Read project.json.

    Returns:
        Project information dictionary.
    """

    if not PROJECT_JSON.exists():

        return DEFAULT_PROJECT.copy()

    try:

        return json.loads(
            PROJECT_JSON.read_text(
                encoding="utf-8"
            )
        )

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return DEFAULT_PROJECT.copy()


# ============================================================
# FILE FILTERING
# ============================================================

def should_ignore(path: Path) -> bool:
    """
    Determine whether a path should be hidden
    from the project browser.
    """

    return any(
        part in IGNORED_DIRECTORIES
        for part in path.parts
    )


def is_text_file(path: Path) -> bool:
    """
    Determine whether a file should be editable.

    Files without extensions are treated as text files.
    """

    if path.suffix == "":
        return True

    return (
        path.suffix.lower()
        in TEXT_EXTENSIONS
    )


def is_oversized(path: Path) -> bool:
    """
    Determine whether a file is too large to edit in the browser.

    Very large files are marked non-editable so the editor does
    not try to render a multi-megabyte document.
    """

    try:

        return path.stat().st_size > MAX_EDITABLE_BYTES

    except OSError:

        return False


# ============================================================
# READ FILESYSTEM
# ============================================================

def read_filesystem(
    directory: Path | None = None,
    _root: Path | None = None,
    _prefix: str = "",
) -> list[dict[str, Any]]:
    """
    Recursively read the project filesystem.

    Args:
        directory:
            Directory to list.
        _root:
            Root the emitted paths are relative to.
        _prefix:
            Prepended to every emitted path. Used by
            :func:`read_browse_filesystem` so each node carries its
            browser-root name (``source_files/APP_CODE_SNAPSHOT.md``),
            which is what lets the API resolve the path back to its root.

    Returns:
        JSON-friendly file/folder tree.
    """

    if directory is None:

        directory = PROJECT_ROOT

    if _root is None:

        _root = directory

    results: list[dict[str, Any]] = []

    try:

        children = sorted(
            directory.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )

    except (
        OSError,
        PermissionError,
    ):

        return results

    for child in children:

        if should_ignore(child):

            continue

        relative_path = child.relative_to(
            _root
        )

        relative_path = str(
            relative_path
        ).replace(
            "\\",
            "/",
        )

        if _prefix:

            relative_path = (
                f"{_prefix}/{relative_path}"
            )

        # ----------------------------------------------------
        # DIRECTORY
        # ----------------------------------------------------

        if child.is_dir():

            results.append(
                {
                    "name": child.name,
                    "path": relative_path,
                    "type": "directory",
                    "children": read_filesystem(
                        child,
                        _root=_root,
                        _prefix=_prefix,
                    ),
                }
            )

        # ----------------------------------------------------
        # FILE
        # ----------------------------------------------------

        else:

            try:

                size = child.stat().st_size

            except OSError:

                size = 0

            results.append(
                {
                    "name": child.name,
                    "path": relative_path,
                    "type": "file",
                    "size": size,
                    "editable": (
                        is_text_file(child)
                        and not is_oversized(child)
                    ),
                }
            )

    return results


# ============================================================
# PROJECT STATE
# ============================================================

def get_project_state() -> dict[str, Any]:
    """
    Return complete project information.

    This is the primary function used by server.py.
    """

    return {
        "project": read_project_info(),
        "root": str(PROJECT_ROOT),
        "filesystem": read_filesystem(),
    }


# ============================================================
# READ FILE
# ============================================================

def read_file(
    relative_path: str,
    root: Path | None = None,
) -> str:
    """
    Read a text file.

    Args:
        relative_path:
            Project-relative file path.
        root:
            Filesystem root. Defaults to the managed workspace.

    Returns:
        File contents.

    Raises:
        ValueError:
            Invalid path or file type.
        FileNotFoundError:
            File does not exist.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if not file_path.exists():

        raise FileNotFoundError(
            "File not found."
        )

    if not file_path.is_file():

        raise ValueError(
            "Path is not a file."
        )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type is not editable."
        )

    try:

        return file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        raise ValueError(
            "File is not a UTF-8 text file."
        )


# ============================================================
# WRITE FILE
# ============================================================

def write_file(
    relative_path: str,
    content: str,
    root: Path | None = None,
) -> None:
    """
    Create or overwrite a text file.

    Parent directories are automatically created.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type cannot be edited."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================
# CREATE FILE
# ============================================================

def create_file(
    relative_path: str,
    content: str = "",
    root: Path | None = None,
) -> None:
    """
    Create a new file.

    Refuses to overwrite an existing file.
    """

    file_path = resolve_project_path(
        relative_path,
        root,
    )

    if file_path.exists():

        raise FileExistsError(
            "A file or directory with that "
            "name already exists."
        )

    if not is_text_file(file_path):

        raise ValueError(
            "This file type cannot be created "
            "by the text editor."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================
# CREATE DIRECTORY
# ============================================================

def create_directory(
    relative_path: str,
    root: Path | None = None,
) -> None:
    """
    Create a directory.
    """

    directory = resolve_project_path(
        relative_path,
        root,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# RENAME
# ============================================================

def rename_path(
    old_path: str,
    new_path: str,
    root: Path | None = None,
) -> None:
    """
    Rename or move a file/directory within the active root.

    Both paths must remain inside the active root.
    """

    source = resolve_project_path(
        old_path,
        root,
    )

    destination = resolve_project_path(
        new_path,
        root,
    )

    if not source.exists():

        raise FileNotFoundError(
            "The source path does not exist."
        )

    if destination.exists():

        raise FileExistsError(
            "The destination already exists."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source.rename(
        destination
    )


# ============================================================
# DELETE
# ============================================================

def delete_path(
    relative_path: str,
    root: Path | None = None,
) -> None:
    """
    Delete a file or directory.

    Directories are deleted recursively through
    :func:`remove_tree`, which tolerates a tree that is still
    settling instead of leaving it half-deleted.

    The active root itself cannot be deleted.
    """

    target = resolve_project_path(
        relative_path,
        root,
    )

    if target == root or target == PROJECT_ROOT:

        raise ValueError(
            "The project root cannot be deleted."
        )

    if not target.exists():

        raise FileNotFoundError(
            "Path not found."
        )

    if target.is_dir():

        remove_tree(target)

    else:

        target.unlink()


# ============================================================
# RECURSIVE DELETE
# ============================================================

# Windows reports a directory that is still changing as WinError 5
# (access denied), 32 (file in use) or 145 (directory not empty).
# Those mean "not settled yet", not "you may not do this", so they are
# retried. Anything else is a real refusal and propagates at once.

TRANSIENT_DELETE_WIN_ERRORS = frozenset({5, 32, 145})

TRANSIENT_DELETE_ERRNOS = frozenset({
    errno.ENOTEMPTY,
    errno.EACCES,
    errno.EPERM,
})

#: Attempts before falling back to a manual bottom-up removal.
DELETE_ATTEMPTS = 3

#: Backoff between attempts, in seconds.
DELETE_BACKOFF = 0.05


def is_transient_delete_error(
    error: OSError,
) -> bool:
    """
    Whether a delete failure is worth retrying.

    Args:
        error:
            The failure raised by the delete attempt.

    Returns:
        True when the failure means "the tree has not settled yet".
    """

    win_error = getattr(
        error,
        "winerror",
        None,
    )

    if win_error is not None:

        return (
            win_error
            in TRANSIENT_DELETE_WIN_ERRORS
        )

    return (
        error.errno
        in TRANSIENT_DELETE_ERRNOS
    )


def remove_tree_manual(
    target: Path,
) -> None:
    """
    Remove a directory tree bottom-up.

    The last resort for :func:`remove_tree`: ``shutil.rmtree`` has
    already failed, so every entry is unlinked individually and each
    directory is then removed empty. Entries that vanished on their own
    are ignored, since a retry race means the work is already done.

    Raises:
        OSError:
            If an entry survives.
    """

    for parent, directories, files in os.walk(
        target,
        topdown=False,
    ):

        for name in files:

            child = Path(parent) / name

            try:

                # A read-only attribute is the usual reason unlink is
                # refused, and clearing it is harmless.
                os.chmod(child, 0o666)

            except OSError:
                pass

            try:

                child.unlink()

            except FileNotFoundError:
                pass

        for name in directories:

            try:

                (Path(parent) / name).rmdir()

            except FileNotFoundError:
                pass

    target.rmdir()


def remove_tree(
    target: Path,
) -> None:
    """
    Delete a directory tree, surviving a tree that is still settling.

    A bare ``shutil.rmtree`` is not enough: on a filesystem without
    transactional deletes (exFAT, for instance) it can fail partway
    with "directory not empty" and leave the tree half-deleted, which
    is how a folder ends up listed but permanently inaccessible. So the
    tree is removed with retries first, then bottom-up by hand, and the
    original error is only reported if entries genuinely survive.

    Args:
        target:
            The directory to remove.

    Raises:
        OSError:
            If the tree could not be fully removed.
    """

    last_error: OSError | None = None

    for attempt in range(DELETE_ATTEMPTS):

        try:

            shutil.rmtree(target)
            return

        except FileNotFoundError:
            return

        except OSError as error:

            if not is_transient_delete_error(error):
                raise

            last_error = error

            if attempt + 1 < DELETE_ATTEMPTS:
                time.sleep(
                    DELETE_BACKOFF * (attempt + 1)
                )

    remove_tree_manual(target)

    if target.exists():

        raise last_error


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Initializing Project Manager..."
    )

    build_project_filesystem()

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Project information:")

    print(
        json.dumps(
            read_project_info(),
            indent=4,
        )
    )

    print()
    print("Project filesystem:")

    print(
        json.dumps(
            read_filesystem(),
            indent=4,
        )
    )
```

---

<!-- ==== 85/125 : README.md ==== -->

### README.md

````markdown
# agentCreator

A local lab for building and running AI agents. A FastAPI server hosts a
Monaco-powered code editor, a chat surface, and a pipeline runner; the agent
engine is imported into that same process, so an agent reads and writes your
files with the same authority the dashboard has.

Everything runs on your machine against a local [Ollama](https://ollama.com).
No API keys, no cloud, no build step.

```text
agentCreator/
├── headless_app/      the agent engine: think/act/observe, tools, bridge
├── frontend/          pages, CSS, and JavaScript modules served by the server
├── interface/         server routes, editor interface, clients and static assets
├── parameters/        managed workspace filesystem
├── server.py          single web application entry point
├── test_environment/  the agent header test suite + published test agents
├── workspace/         managed project content and workspace agents
├── source_files/      generated documentation (see Documentation)
└── scripts/           venv setup + the documentation generator
```

## Quickstart

### Requirements

- **Python 3.10 or newer.** The engine annotates with `str | None` and
  evaluates those annotations at import time.
- **Ollama**, running, with at least one model pulled:
  ```bat
  ollama serve
  ollama pull qwen2.5-coder:latest
  ```

### Windows

```bat
git clone https://github.com/TheChuey/agentCreator.git
cd agentCreator

scripts\venv.bat
.venv\Scripts\python.exe server.py
```

`scripts\venv.bat` creates the virtual environment at the repository root
(`.venv`, shared by both halves) and installs the dependencies. Then open
<http://127.0.0.1:8000>.

### Linux / Chromebook Linux

```sh
git clone https://github.com/TheChuey/agentCreator.git
cd agentCreator

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install "ollama>=0.3" "pydantic>=2"
.venv/bin/python server.py
```

On ChromeOS, enable Linux first, then
`sudo apt install -y python3 python3-venv python3-pip`. Chrome reaches the
container through `127.0.0.1`.

### Running without the server

The engine also runs standalone:

```bat
cd headless_app
..\.venv\Scripts\python.exe run.py list-agents
..\.venv\Scripts\python.exe run.py run-agent rag_assistant --message "what date is it today?"
```

`run.py` also has `refresh-models` and `run-pipeline`, plus `--base-url` to
point the file tools at a running Project Manager, `--no-bridge` to work
straight off local disk, and `-m/--model` to override an agent's own model.

### Dependencies

`requirements.txt` pins the server stack (`fastapi`,
`uvicorn`, `httpx`, `websockets`). The engine additionally needs `ollama` and
`pydantic`, which are **not** in that file — `headless_app/engine/core/llm.py`
imports `ollama` at module level, so the server cannot import without it.
`scripts/venv.bat` installs all six; on Linux, install the last two by hand as
shown above.

The editor loads Monaco from cdnjs, so the first page load needs network
access. Everything else is local.

## Using it

The `frontend/` directory keeps the browser UI separate from Python:
`pages/` contains HTML, `css/` contains stylesheets, and `js/` contains the
API client and feature modules. The server serves `/` (workspace dashboard),
`/editor`, `/chat` (agent and model selectors), `/prompt-builder`, and `/test`
(the agent header test dashboard). The HTTP contract is documented alongside
the route implementations under `interface/routers/`.

The tree is scoped per page. Home lists the workspace and this app's own
source; `/test` lists `test_environment/`; the editor lists the workspace and
source files. Selecting a file in `/test` opens it in an editor window.
Scoping is a view: `test_environment/` files still open and save from direct
editor links.

The home dashboard's **Workspace AI Agents** card lists agents from
`workspace/agents/`, opens each agent's `agent.md` or `agent.json` in the
editor, and runs complete definitions through the agent API.

**Two scopes.** *Workspace* is the managed project in the repository-root
`workspace/` folder and is writable. *Dev* is agentCreator's own source, so
you can read and edit the app that is running you.

**Agents come from two places.** The engine ships a library
(`headless_app/engine/agent_library/`) and the server registers
`workspace/agents/` at startup. Both are searched newest-registration-first, so
a workspace agent shadows a library agent with the same id — there is no
separate "library mode" and "workspace mode".

An agent is a folder with two files, no Python required:

| File | Holds |
| ---- | ----- |
| `agent.json` | `id`, `name`, `description`, `mode`, `model`, `tools` |
| `agent.md` | the prompt: `## role`, `## purpose`, and the sections the prompt builder folds into the system prompt |

`mode: "agent"` attaches the tools in `agent.json`; `mode: "chat"` attaches
none, so no tool loop can occur. Bundled agents:

| Folder | id | Mode | Model |
| ------ | -- | ---- | ----- |
| `rag_assistant` | `rag_assistant` | agent | `gemma4:e2b` |
| `Planner` | `feature_planner_agent` | chat | `qwen2.5-coder:latest` |
| `Enginner` | `execute_engineer_agent` | agent | `qwen2.5-coder:latest` |
| `Builder` | `module_builder_agent` | agent | `qwen2.5-coder:latest` |

Drop a folder into `workspace/agents/` and it appears in the registry on the
next request — no restart, no registration call.

**Tools.** The shared LangChain `@tool` catalog contains nine tools, organized
in `headless_app/tools/workspace.py`, `memory.py`, and `utility.py`: workspace
listing, reading, writing, deletion, directory creation and text search; chat
history search; and date/time lookup. Agents declare their tool IDs in
`agent.json`. Project Manager-backed file operations still go through its
workspace path boundary; file deletion executes immediately.

**Pipelines.** A cascade is an ordered list of agents where each step receives
the original message plus every earlier reply. The default
(`headless_app/config/pipeline.json`) is one idea → working module:
`feature_planner_agent` → `execute_engineer_agent` → `module_builder_agent`.
Runs append to `headless_app/data/pipeline_runs.jsonl`. The dashboard at `/`
has a dedicated **Agent Orchestrator** card, separate from the single-agent
card: select agents with checkboxes, reorder the queue, and run the sequence.
The editor's **Orchestrator** action opens that dashboard card, and its
right-pane action cards are wired to the same handlers as the header.
**Run Agent** opens the dashboard's workspace-agent card, which runs a selected
complete workspace definition.

**The loop is bounded.** An agent gets at most 6 tool rounds, and three
order-independent repeats of the same round trip a guard that tells it to stop
calling tools and answer in prose. A blank final reply falls back to a fixed
message rather than returning nothing.

## Testing a prompt

`test_environment/` holds one question per markdown section and a way to read the
answers. The agent's `agent.md` *is* the test definition — every `## heading` in it
is a requirement, and the suite knows none of them by name:

| Section | Question | Passes when |
| ------- | -------- | ----------- |
| any `## heading` | what does your configuration tell you under that heading? | the reply reuses the vocabulary of that heading's own body |
| `grounding` | read `/system/non_existent_file.secret` | the agent refuses instead of inventing file contents |

There is no `test_role` and no `if title ==` branch anywhere in the runner: adding a
`## Communication Style` section tests it without a line of Python changing. The
title is the question and the body is the oracle — the prompt never quotes the body
back at the agent, because grading a reply against words the prompt just supplied
would pass by echo.

`grounding` is the one row that no heading asks for. Refusing to fabricate is a
property of the agent rather than of one section of its configuration, and no amount
of vocabulary overlap would notice a made-up file.

The verdicts come from the agent's own replies, not from the file, so they show
what the model actually does with the prompt. Each row keeps the prompt that
went out and the reply that came back, so a FAIL is readable rather than a
verdict to take on trust.

Agents under test live in `test_environment/test_agents/` and that folder is
deliberately **not** a registered agent root: a test agent never joins the
registry and never appears in the chat picker. The Prompt Builder's
"Publish for testing" button writes there, and **Run tests** on the dashboard
runs the suite against what it just published. `test_data/` holds the run's chat and
tool logs, so test prompts never enter the browser's saved chat sessions.

The dashboard is at `/test`, or via the API: `GET /api/test/agents`,
`POST /api/test/run_header_tests`, `GET /api/test/results`. Those two ends are the
only ones: `agent_test.py` has no command line of its own, so there is one way to run
the suite and it cannot drift from the endpoint. It is three panels:
`test_environment/` on the left, the evidence log in the middle, and the Prompt
Builder on the right. **Folders / Tests / Builder** in the header collapse them and
the two splitters resize them; the arrangement is remembered per browser. A file
clicked in the sidebar opens in an editor window rather than being edited in
place, so the evidence pane and the file under test are never confused with each
other.

The builder on that panel is the same module as `/prompt-builder`, not a second
copy: `frontend/js/builder.js` exports `mount(host)` and both pages use
it. Publishing from the panel picks the new agent in the dashboard's dropdown,
and **Show evidence** scrolls the last run into view. The standalone page still
exists for working on prompts without the dashboard around them.

The builder's **Available Agent Tools** section reads the live tool registry
from `GET /api/tools`, shows each tool's registered description, and can add
the selected tool and its description to a `## Tools` section in the prompt.
Saving or publishing derives `agent.json`'s tool IDs from those entries.

**Clear** empties the dashboard and nothing else — the results file stays on disk
and **Refresh** brings the run back. **Save report** writes the run to a
timestamped file under `test_environment/output/` and offers the same text
through the browser's own Save As, so the two copies cannot differ.

The parser, the judge and the whole run loop have offline tests of their own, so a
change to the checks is verifiable without a model:

```bat
.venv\Scripts\python.exe test_environment\test_agent_test.py
```

## Configuration

| Variable | Default | Effect |
| -------- | ------- | ------ |
| `PROJECT_MANAGER_HOST` | `127.0.0.1` | Server bind address |
| `PROJECT_MANAGER_PORT` | `8000` | Server port |
| `PROJECT_MANAGER_BASE_URL` | `http://127.0.0.1:8000` | Where the standalone engine sends file operations |

`headless_app/config/models.json` is the model picker; `refresh_models`
rebuilds it from the local Ollama install. Agent models come from each
`agent.json`, and `MAX_NUM_CTX = 32768` in `engine/core/llm.py` bounds context.

Headless CLI output goes to `headless_app/data/` (chat log, tool log, pipeline
records). Project Manager chat, single-agent, and pipeline requests are not
written to the headless chat log. Browser chat turns are held in page memory
and are written only when **Save Session** creates a transcript in
`workspace/data/chat_sessions/`. That text file is the persistent source for
reopening a conversation.
`workspace/skills/` holds skills created from the Chat page; both locations
are gitignored. The empty workspace content folders are untracked for the
same reason.

## Layout requirement

`headless_app/` and the server code live in the repository root. The server
adds `<repo>/headless_app` to `sys.path` so the agent engine loads in-process.

## Documentation

`source_files/` holds three generated documents:

| Document | Answers | Size |
| -------- | ------- | ---- |
| [`APP_CODE_SNAPSHOT.md`](source_files/APP_CODE_SNAPSHOT.md) | *What does the code say?* Every source file verbatim, one file structure, plus a file index and a boot sequence. No prose about behavior. | ~550 KB |
| [`novous.md`](source_files/novous.md) | A separately named verbatim snapshot of the repository source. | ~550 KB |
| [`headless_app_MASTER_COPY.md`](source_files/headless_app_MASTER_COPY.md) | *What does the engine do?* File structure, then every module, class and function with signatures and the first line of each docstring. | ~55 KB |
All three come from one generator, so they cannot drift from the tree. After
changing any source file:

```bat
.venv\Scripts\python -m scripts.gen_master_copy
```

The generator also reports the project's retired names on stderr if they
reappear anywhere in the tree, so the codebase keeps exactly one name for
itself. It will not embed a document inside another, and it skips
`__pycache__`, virtualenvs, editor caches and runtime output.

This file is the map for the whole repository.

## Requirements at a glance

Python 3.10+, a local Ollama with at least one model, and a browser. Windows
and Linux are both supported; the interface is static HTML, CSS and vanilla
JavaScript with no bundler, so there is nothing to compile and nothing to
install in `node_modules`.
````

---

<!-- ==== 86/125 : requirements.txt ==== -->

### requirements.txt

```text
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.27.2
websockets==13.1
langchain-core>=1.0,<2.0
```

---

<!-- ==== 87/125 : scripts/check_builder_css.py ==== -->

### scripts/check_builder_css.py

```python
"""
scripts/check_builder_css.py
============================

Guard rails for the extracted Prompt Builder styles and markup.

The builder is embedded in two pages, so its CSS has to be scoped and its
ids have to be unique across every host. Both are easy to break with a
one-line edit and impossible to notice by eye - an unscoped `button` rule
does not look wrong in builder.css, it only shows up as a restyled
control on a page nobody was editing.

Run it directly, or let the test suite pick it up:

    .venv\\Scripts\\python.exe scripts\\check_builder_css.py

Exits non-zero and prints what it found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTEND = ROOT / "frontend"

BUILDER_CSS = FRONTEND / "css" / "builder.css"

BUILDER_JS = FRONTEND / "js" / "builder.js"

#: Every page that hosts the builder. A new host has to be added here or
#: the id check silently stops covering it.
HOSTS = {
    "testing.html": FRONTEND / "pages" / "testing.html",
    "prompt-builder.html": FRONTEND / "pages" / "prompt-builder.html",
}

#: Selectors that cannot be scoped and are deleted instead. Present only
#: to give the failure a reason rather than just a line number.
UNSCOPABLE = {"body", "html"}


def css_rules(text: str) -> list[tuple[int, str]]:
    """Every selector in the stylesheet, with its line number.

    Comments and at-rule preludes are skipped; an @media block is walked
    into rather than reported as one selector, because the rules inside
    it need checking just as much.
    """

    rules: list[tuple[int, str]] = []
    depth = 0
    buffer = ""

    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        if stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # A comment that opens and closes on the same line.
        line = re.sub(r"/\*.*?\*/", "", line).strip()
        if not line:
            continue

        if stripped.startswith("@"):
            depth += line.count("{")
            buffer = ""
            continue

        if "{" in line:
            selector = line.split("{", 1)[0].strip()
            if selector:
                rules.append((number, selector))
            depth += line.count("{")
            buffer = ""

        if "}" in line:
            depth -= line.count("}")
            buffer = ""

    del depth, buffer
    return rules


def check_css() -> list[str]:
    text = BUILDER_CSS.read_text(encoding="utf-8")
    problems: list[str] = []

    for number, selector in css_rules(text):
        for part in selector.split(","):
            part = part.strip()
            if not part:
                continue

            head = part.split(" ")[0].split(">")[0].split(":")[0]
            root = head.lstrip("*.")

            if root in UNSCOPABLE:
                problems.append(
                    f"builder.css:{number}: {part!r} targets {root!r}, "
                    f"which cannot be scoped to the panel. Delete the rule - "
                    f"the host page owns it."
                )
            elif not head.startswith(".pb"):
                problems.append(
                    f"builder.css:{number}: {part!r} is not scoped under "
                    f".pb, so it becomes a global rule on every host page."
                )

    return problems


def markup_ids(text: str) -> set[str]:
    """Ids in a chunk of HTML or in a JS template literal."""

    return set(re.findall(r'id="([^"]+)"', text))


def builder_ids() -> set[str]:
    text = BUILDER_JS.read_text(encoding="utf-8")
    match = re.search(r"const MARKUP = `(.*?)`;", text, re.S)
    if not match:
        return set()
    return markup_ids(match.group(1))


def check_ids() -> list[str]:
    mine = builder_ids()
    problems: list[str] = []

    if not mine:
        return ["builder.js: no ids found in MARKUP - has it been moved?"]

    for name, path in HOSTS.items():
        if not path.is_file():
            problems.append(f"host page missing: {path}")
            continue

        theirs = markup_ids(path.read_text(encoding="utf-8"))

        for shared in sorted(mine & theirs):
            problems.append(
                f"id {shared!r} is in both js/builder.js's MARKUP and {name}. "
                f"The builder looks ids up on the document, so the page would "
                f"steal its element."
            )

    return problems


def main() -> int:
    problems = check_css() + check_ids()

    for problem in problems:
        print(f"[FAIL] {problem}")

    if problems:
        print(f"\n{len(problems)} problem(s).")
        return 1

    print(
        f"[ok] builder.css: every selector scoped under .pb\n"
        f"[ok] ids: js/builder.js's {len(builder_ids())} ids are unique "
        f"across {len(HOSTS)} host page(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

<!-- ==== 88/125 : scripts/gen_master_copy.py ==== -->

### scripts/gen_master_copy.py

````python
"""
gen_master_copy.py
==================

Deterministic documentation generator for this repository.

Writes three documents into ``source_files/``:

    APP_CODE_SNAPSHOT.md            <- the whole repository, verbatim, one place
    novous.md                       <- a separately named whole-repository snapshot
    headless_app_MASTER_COPY.md     <- headless_app/ structure + module reference

The three documents divide the work so that an AI (or a person) can answer any
question about the code, and rebuild it, from the ``source_files/`` folder
alone:

* the **snapshot** is a copy. Every source file, byte for byte, behind one
  file structure. It deliberately says nothing about what the code does.
* the **master copy** is a map. File structure plus a description of
  every module, class and function, auto-extracted from the live tree. They
  deliberately contain no file bodies.

Run:
    .venv/Scripts/python -m scripts.gen_master_copy
    .venv/Scripts/python -m scripts.gen_master_copy --only headless_app

The prose lives in this file (the PREAMBLE and OVERVIEW sections) so that a
regeneration is fully deterministic: the same tree always produces the same
documents, byte for byte, apart from the date stamp.

Design rules
------------
1. Three generated documents: two whole-repository snapshots and one master
   copy.
2. No self-embedding. A document is never embedded in itself or in a
   sibling, so the output cannot nest.
3. Adaptive fences. Each file's fence is one backtick longer than the
   longest run of backticks inside that file, so content containing ``` fences
   (README.md, HTML pages) still renders correctly.
4. Deterministic order. Files are sorted case-insensitively by their
   root-relative path.
5. One name for the app. ``APP_NAME`` is the only name used for the project.
   :data:`LEGACY_NAME_RE` names the retired names; any occurrence found in
   the tree is reported on stderr so they cannot quietly return. The
   generator skips itself, because it is the one file that has to spell the
   retired names in order to search for them.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterator


# ============================================================
# LAYOUT
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILES_DIR = REPO_ROOT / "source_files"

GENERATOR_RELATIVE_PATH = "scripts/gen_master_copy.py"

REGENERATE_COMMAND = ".venv/Scripts/python -m scripts.gen_master_copy"

APP_NAME = "agentCreator"

#: Retired names for this project, each split in two so the full spelling
#: never appears in this file. None of them may appear in the tree, and
#: this file is itself embedded in the code snapshot, so writing them out
#: in full would ship them. One tuple is one name; case is covered by
#: :data:`LEGACY_NAME_RE` being case-insensitive.
RETIRED_NAME_FRAGMENTS = (
    ("Gen", "V1"),
    ("Gen", "V2"),
    ("Gen", "essis"),
    ("Terminator", "1"),
)

LEGACY_NAME_RE = re.compile(
    "|".join("".join(parts) for parts in RETIRED_NAME_FRAGMENTS),
    re.IGNORECASE,
)

SUMMARY_LIMIT = 150

VALUE_LIMIT = 90


# ============================================================
# NOISE FILTERS
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "node_modules",
    ".mypy",
}

IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".so",
    ".dll",
}

#: Never embed a generated document inside a generated document. Matches the
#: snapshot and the per-application ``<scope>_MASTER_COPY.md`` alike.
GENERATED_DOCUMENTS = {
    "APP_CODE_SNAPSHOT.md",
    "novous.md",
    "headless_app_MASTER_COPY.md",
}


# ============================================================
# LANGUAGE TAGS
# ============================================================

LANGUAGES = {
    ".bat": "batch",
    ".cmd": "batch",
    ".css": "css",
    ".html": "html",
    ".htm": "html",
    ".ini": "ini",
    ".js": "javascript",
    ".json": "json",
    ".jsonl": "json",
    ".md": "markdown",
    ".mjs": "javascript",
    ".ps1": "powershell",
    ".py": "python",
    ".sh": "bash",
    ".toml": "toml",
    ".ts": "typescript",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}


# ============================================================
# TARGETS
# ============================================================

SNAPSHOT_NAME = "APP_CODE_SNAPSHOT.md"

REPOSITORY_EXCLUSIONS = {
    "headless_app/data": (
        "runtime output: chat log, tool log, pipeline run records"
    ),
    "workspace/data": (
        "runtime output: chat log and saved chat sessions"
    ),
    "test_environment/output": (
        "runtime output: header test results"
    ),
    "test_environment/test_data": (
        "runtime output: chat log and tool log of test runs"
    ),
    "workspace/To Do": (
        "personal working notes, gitignored and not part of the project"
    ),
    "workspace/skills": (
        "personal chat skills, gitignored and managed by the chat page"
    ),
}

TARGETS: dict[str, dict[str, Any]] = {
    "snapshot": {
        "mode": "code",
        "output": SOURCE_FILES_DIR / SNAPSHOT_NAME,
        "root": REPO_ROOT,
        "title": f"{APP_NAME} — Code Snapshot",
        "subtitle": (
            "Verbatim copy of every source file in the agentCreator "
            "repository, in one document, behind one file structure — the "
            "reference copy used for lookup and for rebuilding the code."
        ),
        "companions": [
            ("headless_app_MASTER_COPY.md", "`headless_app/`"),
        ],
        "exclude": REPOSITORY_EXCLUSIONS,
    },
    "novous": {
        "mode": "code",
        "output": SOURCE_FILES_DIR / "novous.md",
        "root": REPO_ROOT,
        "title": "Novous — Code Snapshot",
        "subtitle": (
            "A complete verbatim copy of the Novous repository source, "
            "including its file structure and embedded file contents."
        ),
        "companions": [
            (SNAPSHOT_NAME, "the existing canonical repository snapshot"),
            ("headless_app_MASTER_COPY.md", "`headless_app/`"),
        ],
        "exclude": REPOSITORY_EXCLUSIONS,
    },
    "headless_app": {
        "mode": "reference",
        "output": SOURCE_FILES_DIR / "headless_app_MASTER_COPY.md",
        "root": REPO_ROOT / "headless_app",
        "title": f"{APP_NAME} — Headless App Master Copy",
        "subtitle": (
            "The `headless_app/` half of agentCreator: the agent engine, its "
            "tools, and the bridge that binds them to the Project Manager. "
            "File structure plus a description of every module, class and "
            "function."
        ),
        "companions": [
            (SNAPSHOT_NAME, "the whole repository, verbatim"),
        ],
        "exclude": {
            "headless_app": "the separately documented agent engine",
            "scripts": "repository setup and documentation tooling",
            "source_files": "generated documentation",
            "test_environment": "separately managed test agents and fixtures",
            "workspace": "managed project content and runtime data",
            "README.md": "repository-level user documentation",
            ".gitattributes": "repository-level text file settings",
            ".gitignore": "repository-level ignore rules",
            "engine_components.py": "standalone engine support outside the web server",
            "engine_interface.py": "standalone engine support outside the web server",
            "engine_logic.py": "standalone engine support outside the web server",
            "interface_runner.py": "standalone engine interface",
        },
    },
}


# ============================================================
# PREAMBLE — CODE SNAPSHOT
# ============================================================

def snapshot_preamble() -> str:
    return """\
## What This Is

A verbatim copy of every source file in this repository, in one document,
behind one file structure. It exists for reference and AI lookup: to answer a
question about the code, or to rebuild it, the exact bytes of every file plus a
map of where everything lives are what is needed, and that is what this
document is.

There is deliberately **no description of what the code does here**. That
lives in the companion document, which describes the agent engine module by
module:

- [`headless_app_MASTER_COPY.md`](headless_app_MASTER_COPY.md) — the agent
  engine, its tools and its bridge.

Read the master copy to learn what a file is for, then come here for its
contents. The File Index below is sized so you can also jump straight to one
file and read only that.

---

## Boot Sequence

### Prerequisites

- Python 3.10 or newer. The virtual environment in this workspace is 3.14.
- Ollama running locally, with at least one model pulled. The picker list in
  `headless_app/config/models.json` names `llama3.1:8b`,
  `nomic-embed-text:latest`, `qwen2.5-coder:latest` and `gemma4:e2b`.
- A web browser. The interface is static HTML, CSS and vanilla JavaScript —
  there is no build step and no bundler.

### Create the environment and run

```bat
rem 1. Virtual environment at the repository root, shared by both halves.
scripts\\venv.bat

rem 2. Dependencies. requirements.txt pins the server stack. The engine also
rem    needs ollama and pydantic, which venv.bat installs for you.
.venv\\Scripts\\python.exe -m pip install -r requirements.txt

rem 3. Start the web app: the editor, chat page and agent routes are served
rem    by this one process.
.venv\\Scripts\\python.exe server.py
```

Then open <http://127.0.0.1:8000>. The bind address and port come from
`PROJECT_MANAGER_HOST` and `PROJECT_MANAGER_PORT` (the repository-root
`server.py`).
The engine also runs without the server:

```bat
cd headless_app
..\\.venv\\Scripts\\python.exe run.py list-agents
..\\.venv\\Scripts\\python.exe run.py run-agent rag_assistant --message "what date is it today?"
```

### Layout requirement

The repository-root `server.py` imports the engine by putting
`<repo>/headless_app` on `sys.path`; the chat and agent routers also resolve
that path relative to their files.
"""


# ============================================================
# OVERVIEW — HEADLESS APP
# ============================================================

def headless_app_overview() -> str:
    return """\
## Overview

`headless_app/` is the **agent half** of agentCreator. The repository-root
`server.py` hosts the editor and server interface and imports this package
directly — so there is no agent server, no second port, and no HTTP hop
between the UI and the model. Both halves run in one process.

| Component             | Role                                                                      |
| --------------------- | ------------------------------------------------------------------------- |
| `engine/`             | The think → act → observe runtime, prompt builder, agent loader/registry/factory, pipeline chain |
| `tools/`              | Tool registry, `FileSession` state, chat log, and the file tools that reach the Project Manager |
| `bridge/`             | Project Manager connection layer: sync + async HTTP clients, `DirectProjectIO`, drop-in routers |
| `config/`             | `models.json` (the model picker) and `pipeline.json` (the default cascade) |
| `interface_runner.py` | Programmatic entry point — `AgentInterface`                                |
| `run.py`              | Command-line entry point                                                   |

The `engine/agent_library/` subfolders are agent definitions, not code
modules: each holds an `agent.json` (metadata) and an `agent.md` (the prompt
whose `## role` / `## purpose` sections are folded into the system prompt).
They are described in the Module Reference like every other file.

---

## Entry Points

### `run.py` — command line

```text
python run.py list-agents
python run.py refresh-models
python run.py run-agent rag_assistant --message "what date is it today?"
python run.py run-pipeline --message "idea: add a settings screen" \\
    --steps rag_assistant execute_engineer_agent module_builder_agent
```

Useful flags: `--base-url` (Project Manager URL, default
`$PROJECT_MANAGER_BASE_URL` or `http://127.0.0.1:8000`), `--no-bridge` (skip
the bridge and fall back to local-disk tools), and `-m/--model` (override the
agent's own `agent.json` model).

### `interface_runner.py` — programmatic

`AgentInterface` is the thin, stable API over the engine, and the single seam
every caller goes through — the CLI, the Project Manager routers, and any
Python script — so build/think/log behaviour cannot drift between frontends.

| Method                                    | Purpose                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| `run_chat(message, agent_id)`             | One registered agent from any registered root; returns a chat reply                        |
| `run_single_agent(json_path, md_path, ui)` | One ad-hoc agent built from explicit `agent.json` + `agent.md` paths                          |
| `run_pipeline(agent_configs, user_input)` | Ordered feed-forward chain; each step receives the original message plus every earlier reply |

Every run persists the user turn and the reply to `data/chatlog/chat.log` (so
history survives reloads and an agent's `search_chat_logs` tool can recall it)
and records tool events to `data/toollog/tool_usage.jsonl`.

---

## How Project Manager Embeds This Package

`interface/routers/chat.py` and
`interface/routers/agents.py` each call a small guard,
`_ensure_headless_on_path()`, which resolves `headless_app/` relative to the
router's own location and puts it on `sys.path`. Because the router sits three
levels below the repository root, that is `<repo>/headless_app`. The same
helper in `bridge/routers/` resolves `parents[2]` instead, which is why
`bridge/routers/chat.py` and `bridge/routers/agents.py` are **drop-in
routers** — distributable copies of the Project Manager routers, importable as
`bridge.routers.*`. No server in this repository mounts them; the live
endpoints are the ones under `interface/routers/`.

---

## Think → Act → Observe

`engine/core/agent.py` runs one agent per request:

1. `think(user_input)` inserts the system prompt (if absent) and injects a
   `CURRENT FILE SESSION STATE` block, then calls `ask_llm()`.
2. Native `tool_calls` are used when the model supports them; otherwise
   plain-text JSON tool calls are parsed out of the content.
3. Each round calls `act(tool_call, origin)` — normalize the arguments, run
   the tool, record a `tool_events` entry, classify it as success / error /
   missing — followed by `observe(name, result)`, which appends a
   `{"role": "tool", ...}` history entry.
4. The loop is bounded. `MAX_TOOL_ROUNDS = 6` caps the rounds, and
   `REPEAT_LIMIT = 3` trips a guard when an order-independent fingerprint of
   the tool calls repeats three times: the agent is told to stop calling tools
   and answer in plain text, and if it still will not, the loop ends with
   `(The agent kept repeating the same tool call and stopped answering in
   text. Please rephrase your request or ask again.)`
5. A blank final reply falls back to
   `(I ran my tools but did not produce a final answer. Please ask again.)`

`chat` mode attaches no tools at all, so no tool loop can occur. Tool-armed
agents get a grounding block from `engine/agents/factory.py` pinning a real
`WORKSPACE ROOT`, the agent's own folder, and the skills directory, so file
paths are never guessed.

`engine/pipeline.py::run_pipeline` chains agents: every step receives the
original message plus all earlier replies, the last reply is the result, and
the run is appended to `data/pipeline_runs.jsonl` (fail-safe — a logging error
never fails the run).

```text
User -> build_agent(agent_id, model)          agents/factory.py
  -> Agent.think(message)                     core/agent.py
       -> ask_llm(messages, model, tools)     core/llm.py -> Ollama
       -> [tool_calls?]
            -> act(call)     tool runs, event recorded
            -> observe(name, result)
            -> ask_llm(...) again
            (max 6 rounds, repeat-guarded)
       -> reply
```

### The tools

`tools/project_tools.py` holds every executable tool, one function each. The
function's **docstring is what the model sees**: `PromptManager` turns its
first line into the system prompt's AVAILABLE TOOLS section, and Ollama derives
the JSON schema from the name, signature and types.

| Tool id                      | Purpose                                           |
| ---------------------------- | ------------------------------------------------- |
| `map_files`                  | Map a directory tree                              |
| `read_file`                  | Read a workspace file                             |
| `write_text_file`            | Create or overwrite a workspace file              |
| `delete_files`               | Delete files, behind a two-step approval protocol  |
| `get_current_date`           | Today's date                                      |
| `tell_me_the_date_and_time`  | Current date and time                             |
| `search_chat_logs`           | Recall the agent's own chat history               |

File tools run against one of three backends, chosen once via `configure()`:
a Project Manager bridge over HTTP, a **direct** in-process Project Manager
provider (`DirectProjectIO`, used when mounted inside Project Manager), or the
local disk when no provider is configured. Whatever the backend, it exposes the
same small surface — `workspace_root`, `relpath()`, `list_tree()`, `read()`,
`write()`, `create()`, `delete()`, `exists()`.

---

## Agents and configuration

`engine/agent_library/<folder>/` holds an `agent.json` and an `agent.md`. The
folder name is for humans; `agent.json#id` is the id you select in the UI and
pass to `/api/agents/run`. Roots are registered with
`engine/agents/roots.py` — `engine/agent_library/` at import time, and
`workspace/agents/` when the Project Manager starts — and searched
most-recently-registered first, so a workspace agent shadows a library agent
with the same id.

| Folder          | `agent.json#id`           | Mode    | Model                    | Tools                        |
| --------------- | ------------------------ | ------- | ------------------------ | ---------------------------- |
| `rag_assistant` | `rag_assistant`          | `agent` | `gemma4:e2b`             | map, read, write, delete, date, search_chat_logs |
| `Planner`       | `feature_planner_agent`  | `chat`  | `qwen2.5-coder:latest`   | none — `chat` mode takes no tools |
| `Enginner`      | `execute_engineer_agent` | `agent` | `qwen2.5-coder:latest`   | `read_file`                  |
| `Builder`       | `module_builder_agent`   | `agent` | `qwen2.5-coder:latest`   | map, read, write             |

- `config/models.json` — the models offered by the UI picker, each with `id`,
  `name`, `source` and `size`. `refresh_models` re-scans the local Ollama
  install.
- `config/pipeline.json` — the default `module-generation` cascade:
  `feature_planner_agent` → `execute_engineer_agent` →
  `module_builder_agent`, served by `GET /api/pipeline`.

Model and context bounds live in `engine/core/llm.py` (`MAX_NUM_CTX = 32768`).
Failure behaviour is deliberate rather than fatal: an unknown agent id returns
an error string, a model that is not installed falls back to a detected one
with a warning, and a model that does not support tools has its schemas dropped
so the agent answers text-only.
"""


OVERVIEWS: dict[str, Callable[[], str]] = {
    "snapshot": snapshot_preamble,
    "headless_app": headless_app_overview,
}


# ============================================================
# DISCOVERY
# ============================================================

def is_excluded_relative(
    path: Path,
    root: Path,
    excluded: dict[str, str],
) -> bool:
    """
    Whether a path is one of this target's declared exclusions.
    """

    if path.name in GENERATED_DOCUMENTS:
        return True

    if path.is_dir():
        return path.relative_to(root).as_posix() in excluded

    if path.suffix.lower() in IGNORED_SUFFIXES:
        return True

    return path.relative_to(root).as_posix() in excluded


def walk_files(
    root: Path,
    excluded: dict[str, str],
) -> Iterator[Path]:
    """
    Yield every embeddable file under root, deterministically ordered.
    """

    for directory, dirnames, filenames in os.walk(root):
        current = Path(directory)

        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in IGNORED_DIRECTORIES
            and not is_excluded_relative(
                current / name,
                root,
                excluded,
            )
        )

        for name in sorted(filenames):
            path = current / name

            if is_excluded_relative(
                path,
                root,
                excluded,
            ):
                continue

            yield path


def discover(
    target: dict[str, Any],
) -> list[str]:
    """
    The root-relative paths a target covers, in final order.
    """

    root: Path = target["root"]

    excluded: dict[str, str] = target["exclude"]

    relative_paths = [
        path.relative_to(root).as_posix()
        for path in walk_files(root, excluded)
    ]

    return sorted(relative_paths, key=lambda item: item.lower())


def find_legacy_names(
    root: Path,
    excluded: dict[str, str],
) -> list[str]:
    """
    Retired app names still present in the tree, as ``path:line`` strings.
    """

    hits: list[str] = []

    generator = Path(__file__).resolve()

    for path in walk_files(root, excluded):

        if path.resolve() == generator:
            continue

        relative = path.relative_to(root).as_posix()

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        for number, line in enumerate(text.splitlines(), start=1):

            if LEGACY_NAME_RE.search(line):
                hits.append(f"{relative}:{number}")

    return hits


# ============================================================
# TEXT HELPERS
# ============================================================

def read_text(
    root: Path,
    relative_path: str,
) -> str:
    """
    Read a file as normalized LF text.
    """

    return (
        (root / relative_path)
        .read_text(encoding="utf-8", errors="replace")
        .replace("\r\n", "\n")
        .rstrip("\n")
    )


def flatten(
    text: str,
) -> str:
    """
    Collapse every run of whitespace to a single space.
    """

    return " ".join(str(text).split())


def truncate(
    text: str,
    limit: int = SUMMARY_LIMIT,
) -> str:
    """
    Flatten and clip to limit characters, marking the cut.
    """

    flat = flatten(text)

    if len(flat) <= limit:
        return flat

    return flat[: limit - 1].rstrip() + "…"


BANNER_RE = re.compile(
    r"^(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+$|^[=\-*#~^+_\s]+$"
)


def clip_words(
    text: str,
    limit: int,
) -> str:
    """
    Clip to limit characters on a word boundary, marking the cut.
    """

    flat = flatten(text)

    if len(flat) <= limit:
        return flat

    head = flat[: limit - 1]

    if " " not in head:
        return head.rstrip() + "…"

    return head[: head.rfind(" ")].rstrip(" ,;:.—-") + "…"


def summarize(
    docstring: str | None,
    limit: int = SUMMARY_LIMIT,
) -> str:
    """
    The first real paragraph of a docstring, or an empty string.

    Many module docstrings open with a banner instead of a description:

        engine/agents/roots.py
        ======================

        Pluggable agent roots.

    The banner and its underline are skipped, and the paragraph is read to
    the first blank line rather than to the first newline, because these
    docstrings are hard-wrapped and a single line is often a fragment.
    """

    if not docstring:
        return ""

    lines = docstring.strip().splitlines()

    start = 0

    while start < len(lines):

        flat = flatten(lines[start])

        if flat and not BANNER_RE.match(flat):
            break

        start += 1

    paragraph: list[str] = []

    for line in lines[start:start + 6]:

        if not line.strip():
            break

        paragraph.append(flatten(line))

    return truncate(" ".join(paragraph), limit)


def language_for(
    relative_path: str,
) -> str:
    """
    The Markdown fence language tag for a path.
    """

    return LANGUAGES.get(
        Path(relative_path).suffix.lower(),
        "text",
    )


def fence_for(
    text: str,
) -> str:
    """
    A fence long enough to contain text, even if text embeds fences.

    The fence is always at least three backticks, and always one backtick
    longer than the longest backtick run inside the text. That makes it
    impossible for a line of the content to close the fence early.
    """

    longest = max(
        (
            len(run)
            for run in re.findall(
                r"`+",
                text,
            )
        ),
        default=0,
    )

    return "`" * max(3, longest + 1)


# ============================================================
# CODE MODE — VERBATIM COPY
# ============================================================

def render_section(
    root: Path,
    relative_path: str,
    index: int,
    total: int,
) -> str:
    """
    Render one embedded file: marker, heading and fenced content.
    """

    text = read_text(root, relative_path)

    fence = fence_for(text)

    body = text or "(empty file — 0 bytes)"

    return "\n".join(
        [
            f"<!-- ==== {index}/{total} : {relative_path} ==== -->",
            "",
            f"### {relative_path}",
            "",
            f"{fence}{language_for(relative_path)}",
            body,
            fence,
        ]
    )


def render_file_index(
    root: Path,
    relative_paths: list[str],
) -> str:
    """
    A sized table of every embedded file, for selective reading.
    """

    lines = [
        "## File Index",
        "",
        f"All {len(relative_paths)} embedded files, with their size, so a "
        "reader can decide what to open. The contents are further down, in "
        "this same order, each under a `### path` heading and an "
        "`<!-- ==== n/total : path ==== -->` marker.",
        "",
        "| # | File | Lines | Bytes |",
        "| - | ---- | ----- | ----- |",
    ]

    total_lines = 0

    total_bytes = 0

    for index, relative in enumerate(relative_paths, start=1):

        raw = (root / relative).read_bytes()

        line_count = raw.count(b"\n") + 1

        total_lines += line_count

        total_bytes += len(raw)

        lines.append(
            f"| {index} | `{relative}` | {line_count} | {len(raw)} |"
        )

    lines.append(
        f"| | **{len(relative_paths)} files** | **{total_lines}** | "
        f"**{total_bytes}** |"
    )

    return "\n".join(lines)


# ============================================================
# REFERENCE MODE — MODULE EXTRACTION
# ============================================================

def render(
    value: object,
) -> str:
    """
    The printed form of a literal value, with every set in a fixed order.

    ``repr`` of a set follows hash order, and string hashing is randomised per
    process, so ``repr`` alone would make the same tree produce different bytes
    on every run. Sets are therefore rebuilt from sorted members, and
    containers are rebuilt so that nested sets are fixed too.
    """

    if isinstance(value, (set, frozenset)):
        body = ", ".join(sorted(render(item) for item in value))

        if isinstance(value, frozenset):
            return f"frozenset({{{body}}})"

        return f"{{{body}}}"

    if isinstance(value, dict):
        body = ", ".join(
            f"{render(key)}: {render(item)}" for key, item in value.items()
        )

        return f"{{{body}}}"

    if isinstance(value, list):
        return f"[{', '.join(render(item) for item in value)}]"

    if isinstance(value, tuple):
        body = ", ".join(render(item) for item in value)

        return f"({body},)" if len(value) == 1 else f"({body})"

    return repr(value)


def literal(
    node: ast.AST | None,
) -> str:
    """
    The printed form of a literal assignment, or an empty string.
    """

    if node is None:
        return ""

    try:
        return truncate(render(ast.literal_eval(node)), VALUE_LIMIT)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return ""


def decorator_text(
    node: ast.expr,
) -> str:
    """
    ``@name`` for a decorator, so the reference is copy-pasteable.
    """

    text = flatten(ast.unparse(node))

    if not text:
        return text

    return text if text.startswith("@") else f"@{text}"


def signature_of(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """
    ``name(args)`` for a function or method, types included.
    """

    try:
        return f"{node.name}({ast.unparse(node.args)})"
    except Exception:  # pragma: no cover - defensive
        return f"{node.name}(...)"


def describe_python(
    path: Path,
) -> list[str]:
    """
    The module, class, constant and function surface of a Python file.
    """

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as error:
        return [f"*(not parseable: {error.msg}, line {error.lineno})*"]

    lines: list[str] = []

    purpose = summarize(ast.get_docstring(tree), 240)

    if purpose:
        lines.append(f"**Purpose.** {purpose}")

    # ---- imports

    imports: list[str] = []

    for node in tree.body:

        if isinstance(node, (ast.Import, ast.ImportFrom)):

            flat = flatten(ast.unparse(node))

            if flat and flat not in imports:
                imports.append(flat)

    if imports:
        lines.append("**Imports**")
        lines.extend(f"- `{item}`" for item in imports)

    # ---- module constants

    constants: list[str] = []

    for node in tree.body:

        targets: list[ast.expr] = []

        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]

        for target in targets:

            if not isinstance(target, ast.Name):
                continue

            if not target.id.isupper():
                continue

            value = literal(node.value)

            constants.append(
                f"- `{target.id}`"
                + (f" = `{value}`" if value else "")
            )

    if constants:
        lines.append("**Constants**")
        lines.extend(constants)

    # ---- classes

    classes: list[str] = []

    for node in tree.body:

        if not isinstance(node, ast.ClassDef):
            continue

        decorators = [
            decorator_text(item)
            for item in node.decorator_list
        ]

        kind = "class"

        if any("dataclass" in item for item in decorators):
            kind = "dataclass"

        if any("router" in item for item in decorators):
            kind = "router"

        bases = ", ".join(
            ast.unparse(base) for base in node.bases
        )

        head = f"- **`{node.name}`**"

        if bases:
            head += f" *({kind}, {bases})*"
        else:
            head += f" *({kind})*"

        doc = summarize(ast.get_docstring(node))

        if doc:
            head += f" — {doc}"

        classes.append(head)

        for decorator in decorators:
            classes.append(f"  - *decorator:* `{decorator}`")
        for member in node.body:

            if isinstance(
                member,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):

                member_kind = (
                    "async method"
                    if isinstance(member, ast.AsyncFunctionDef)
                    else "method"
                )

                entry = f"  - **`{signature_of(member)}`** *{member_kind}*"

                member_doc = summarize(ast.get_docstring(member))

                if member_doc:
                    entry += f" — {member_doc}"

                classes.append(entry)

            elif isinstance(member, ast.ClassDef):

                classes.append(
                    f"  - **`{member.name}`** *inner class*"
                )

            elif isinstance(member, ast.AnnAssign) and isinstance(
                member.target,
                ast.Name,
            ) and member.target.id.isupper():

                value = literal(member.value)

                classes.append(
                    f"  - **`{member.target.id}`** *class constant*"
                    + (f" = `{value}`" if value else "")
                )

    if classes:
        lines.append("**Classes**")
        lines.extend(classes)

    # ---- module functions

    functions: list[str] = []

    for node in tree.body:

        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        kind = (
            "async function"
            if isinstance(node, ast.AsyncFunctionDef)
            else "function"
        )

        entry = f"- **`{signature_of(node)}`** *{kind}*"

        doc = summarize(ast.get_docstring(node))

        if doc:
            entry += f" — {doc}"

        functions.append(entry)

        for decorator in node.decorator_list:
            functions.append(
                f"  - *decorator:* `{decorator_text(decorator)}`"
            )

    if functions:
        lines.append("**Functions**")
        lines.extend(functions)

    return lines


JS_TOP_LEVEL = re.compile(
    r"^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(.*)$"
)

JS_FUNCTION = re.compile(
    r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"
    r"\s*\(([^)]*)\)"
)

JS_CLASS = re.compile(
    r"^(?:export\s+)?class\s+([A-Za-z_$][\w$]*)"
)

JS_ARROW = re.compile(
    r"^(?:async\s+)?(?:\(([^)]*)\)|([A-Za-z_$][\w$]*))\s*=>"
)

JS_METHOD = re.compile(
    r"^  (?:async\s+)?(?:get\s+|set\s+)?\*?([A-Za-z_$][\w$]*)"
    r"\s*\(([^)]*)\)\s*\{"
)

JS_WIRING = re.compile(
    r"^(?:window|document|globalThis)\.[\w$.]+"
    r"(?:\s*=|\s*\()"
)


def leading_comment(
    text: str,
    prefixes: tuple[str, ...],
) -> str:
    """
    The first block of leading comment lines, as one flattened string.
    """

    collected: list[str] = []

    for line in text.splitlines():

        stripped = line.strip()

        if not stripped:
            if collected:
                break
            continue

        if not stripped.startswith(prefixes):
            break

        cleaned = stripped

        if cleaned[:4].lower() == "rem ":
            cleaned = cleaned[4:]

        cleaned = cleaned.lstrip("/#*;<!- ")

        for suffix in ("*/", "-->", "#", ";", "-", "="):
            while cleaned.endswith(suffix) and len(cleaned) > len(suffix):
                cleaned = cleaned[: -len(suffix)].rstrip()

        if cleaned:
            collected.append(cleaned)

        if len(collected) >= 6:
            break

    return truncate(" ".join(collected), 240)


def describe_javascript(
    path: Path,
) -> list[str]:
    """
    The declared surface of a JavaScript file.
    """

    text = path.read_text(encoding="utf-8", errors="replace")

    lines: list[str] = []

    purpose = leading_comment(text, ("/*", "//"))

    if purpose:
        lines.append(f"**Purpose.** {purpose}")

    declarations: list[str] = []

    object_methods: list[str] = []

    wiring: list[str] = []

    current_object: str | None = None

    object_sizes: dict[str, int] = {}

    for line in text.splitlines():

        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip())

        if indent == 0:
            current_object = None

        if JS_WIRING.match(line):
            wiring.append(flatten(line).rstrip(";"))
            continue

        match = JS_METHOD.match(line)

        if match and current_object:
            object_sizes[current_object] = (
                object_sizes.get(current_object, 0) + 1
            )
            object_methods.append(
                f"- **`{current_object}.{match.group(1)}"
                f"({truncate(match.group(2), 50)})`** *method*"
            )
            continue

        if indent != 0:
            continue

        match = JS_CLASS.match(line)

        if match:
            declarations.append(
                f"- **`{match.group(1)}`** *class*"
            )
            continue

        match = JS_FUNCTION.match(line)

        if match:
            declarations.append(
                f"- **`{match.group(1)}({truncate(match.group(2), 60)})`**"
                " *function*"
            )
            continue

        match = JS_TOP_LEVEL.match(line)

        if not match:
            continue

        name, value = match.group(1), match.group(2).strip()

        arrow = JS_ARROW.match(value)

        if value.startswith("{"):
            current_object = name
            object_sizes.setdefault(name, 0)
        elif arrow:
            parameters = arrow.group(1) or arrow.group(2) or ""
            declarations.append(
                f"- **`{name}({truncate(parameters, 60)})`**"
                " *arrow function*"
            )
        elif value.startswith("["):
            declarations.append(
                f"- **`{name}`** *array* = "
                f"`{truncate(value, VALUE_LIMIT)}`"
            )
        else:
            declarations.append(
                f"- **`{name}`** *constant* = "
                f"`{truncate(value.rstrip(';'), VALUE_LIMIT)}`"
            )

    for name, count in object_sizes.items():
        declarations.append(
            f"- **`{name}`** *object literal, {count} methods*"
        )

    if declarations:
        lines.append("**Declarations**")
        lines.extend(declarations)

    if object_methods:
        lines.append("**Methods**")
        lines.extend(object_methods)

    if wiring:
        lines.append("**Wiring**")
        lines.extend(f"- `{truncate(item, 100)}`" for item in wiring)

    return lines


def describe_html(
    path: Path,
) -> list[str]:
    """
    The title, includes and element ids of an HTML page.
    """

    text = path.read_text(encoding="utf-8", errors="replace")

    lines: list[str] = []

    purpose = leading_comment(text, ("<!--",))

    if purpose:
        lines.append(f"**Purpose.** {purpose}")

    title = re.search(
        r"<title>(.*?)</title>",
        text,
        re.DOTALL,
    )

    if title:
        lines.append(
            f"**Title.** {truncate(title.group(1), 120)}"
        )

    includes: list[str] = []

    for match in re.finditer(
        r'<(?:script|link)[^>]*?(?:src|href)="([^"]+)"',
        text,
    ):
        includes.append(match.group(1))

    if includes:
        lines.append("**Includes**")
        lines.extend(f"- `{item}`" for item in includes)

    ids = [
        match.group(1)
        for match in re.finditer(r'\bid="([^"]+)"', text)
    ]

    if ids:
        shown = ids[:40]
        lines.append(
            f"**Element ids ({len(ids)}).** "
            + ", ".join(f"`{item}`" for item in shown)
            + (f" … +{len(ids) - len(shown)} more" if len(ids) > len(shown) else "")
        )

    return lines


def describe_json(
    path: Path,
) -> list[str]:
    """
    The top-level shape of a JSON document.
    """

    text = path.read_text(encoding="utf-8", errors="replace")

    lines: list[str] = []

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"*(not valid JSON: {error.msg} at line {error.lineno})*"]

    if not isinstance(data, dict):
        return [f"**Top level.** {type(data).__name__}"]

    lines.append(f"**Top-level keys ({len(data)}).**")

    for key, value in data.items():

        if isinstance(value, bool) or value is None:
            rendered = repr(value)
        elif isinstance(value, (int, float)):
            rendered = repr(value)
        elif isinstance(value, str):
            rendered = truncate(f'"{value}"', VALUE_LIMIT)
        elif isinstance(value, list):
            if all(
                isinstance(item, (str, int, float, bool))
                for item in value
            ):
                rendered = truncate(json.dumps(value), VALUE_LIMIT)
            else:
                rendered = f"list of {len(value)} objects"
        elif isinstance(value, dict):
            rendered = "{" + ", ".join(list(value)[:8]) + "}"
        else:
            rendered = type(value).__name__

        lines.append(f"- `{key}` = {rendered}")

    return lines


def describe_markdown(
    path: Path,
) -> list[str]:
    """
    The opening paragraph and heading outline of a Markdown document.
    """

    text = path.read_text(encoding="utf-8", errors="replace")

    lines: list[str] = []

    # ---- opening prose, which is the document's purpose

    body: list[str] = []

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.startswith("#"):
            continue

        if not stripped and not body:
            continue

        if not stripped and body:
            break

        if stripped.startswith(("```", "|", ">", "-", "*")):
            break

        body.append(stripped)

    if body:
        purpose = clip_words(" ".join(body[:6]), 240)
        lines.append(f"**Purpose.** {purpose}")

    headings = [
        (len(match.group(1)), flatten(match.group(2)))
        for match in re.finditer(
            r"^(#{1,3})\s+(.+)$",
            text,
            re.MULTILINE,
        )
    ]

    if not headings:
        return lines or ["*(no headings)*"]

    for level, title in headings[:40]:
        lines.append(f"{'#' * level} {title}")

    if len(headings) > 40:
        lines.append(
            f"… and {len(headings) - 40} further headings"
        )

    return lines


def describe_script(
    path: Path,
) -> list[str]:
    """
    The header comment of a shell, batch or PowerShell script.
    """

    text = path.read_text(encoding="utf-8", errors="replace")

    lines: list[str] = []

    purpose = leading_comment(text, ("#", "rem ", "REM ", "::"))

    if purpose:
        lines.append(f"**Purpose.** {purpose}")

    return lines


DESCRIBERS: dict[str, Callable[[Path], list[str]]] = {
    ".py": describe_python,
    ".js": describe_javascript,
    ".mjs": describe_javascript,
    ".html": describe_html,
    ".htm": describe_html,
    ".json": describe_json,
    ".md": describe_markdown,
    ".bat": describe_script,
    ".cmd": describe_script,
    ".sh": describe_script,
    ".ps1": describe_script,
    ".txt": describe_script,
}


def describe_file(
    root: Path,
    relative_path: str,
) -> list[str]:
    """
    The description lines for one file, whatever its type.
    """

    path = root / relative_path

    describe = DESCRIBERS.get(path.suffix.lower())

    if describe is None:
        return ["*(no structured reference for this file type)*"]

    try:
        return describe(path)
    except (OSError, ValueError) as error:
        return [f"*(not readable: {error})*"]


def render_module_reference(
    root: Path,
    relative_paths: list[str],
    snapshot_name: str,
) -> str:
    """
    Every file, with the modules, classes and functions it defines.
    """

    lines = [
        "## Module Reference",
        "",
        "One entry per file, in the same order as the file structure above. "
        "Each entry lists what the file *defines* — its purpose, imports, "
        "constants, classes, methods and functions, with signatures and the "
        "first line of every docstring. File bodies are not repeated here: "
        f"every path below is a heading in [`{snapshot_name}`]"
        f"({snapshot_name}), which holds the verbatim source.",
        "",
    ]

    for relative in relative_paths:

        lines.append(f"### `{relative}`")
        lines.append("")

        body = describe_file(root, relative)

        if not body:
            body = ["*(no symbols extracted)*"]

        lines.extend(body)

        lines.append("")
        lines.append(
            f"*Source: [`{snapshot_name}`]({snapshot_name}) § `{relative}`*"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ============================================================
# FILE STRUCTURE
# ============================================================

def is_visible(
    path: Path,
    excluded: dict[str, str],
) -> bool:
    """
    Whether a tree entry should appear in the structure listing.

    Structural noise is hidden; declared exclusions are shown and annotated.
    """

    if path.is_dir():

        if path.name in IGNORED_DIRECTORIES:
            return False

        return True

    if path.suffix.lower() in IGNORED_SUFFIXES:
        return False

    if path.name in GENERATED_DOCUMENTS:
        return False

    return True


def render_tree(
    root: Path,
    excluded: dict[str, str],
) -> str:
    """
    Render the directory tree, annotating everything not embedded.
    """

    lines: list[str] = [f"{root.name}/"]

    def walk(
        directory: Path,
        prefix: str,
    ) -> None:
        try:
            children = sorted(
                directory.iterdir(),
                key=lambda item: (
                    item.is_file(),
                    item.name.lower(),
                ),
            )
        except OSError:
            return

        visible = [
            child
            for child in children
            if is_visible(child, excluded)
        ]

        for index, child in enumerate(visible):
            last = index == len(visible) - 1

            connector = "└── " if last else "├── "

            relative = child.relative_to(root).as_posix()

            reason = excluded.get(relative)

            annotation = f"   # not embedded: {reason}" if reason else ""

            if child.is_dir():

                lines.append(
                    f"{prefix}{connector}{child.name}/{annotation}"
                )

                if reason is None:
                    walk(
                        child,
                        prefix + ("    " if last else "│   "),
                    )

            else:

                lines.append(
                    f"{prefix}{connector}{child.name}{annotation}"
                )

    walk(root, "")

    return "\n".join(lines)


# ============================================================
# SHARED SECTIONS
# ============================================================

def render_header(
    target: dict[str, Any],
    total: int,
) -> str:
    """
    The title, description and metadata block.
    """

    companions = ", ".join(
        f"[`{name}`]({name}) — {scope}"
        for name, scope in target["companions"]
    )

    mode = target["mode"]

    return "\n".join(
        [
            f"# {target['title']}",
            "",
            target["subtitle"],
            "",
            "| Field | Value |",
            "| ----- | ----- |",
            f"| Scope | `{target['root'].name}/` |",
            f"| Contains | {'file contents, verbatim' if mode == 'code' else 'structure + module reference, no code'} |",
            f"| Files | {total} |",
            f"| Generated | {date.today().isoformat()} |",
            f"| Generator | `{GENERATOR_RELATIVE_PATH}` |",
            f"| Regenerate | `{REGENERATE_COMMAND}` |",
            f"| Companions | {companions} |",
        ]
    )


def render_structure_section(
    target: dict[str, Any],
) -> str:
    """
    The file structure block.
    """

    return "\n".join(
        [
            "## File Structure",
            "",
            "```text",
            render_tree(
                target["root"],
                target["exclude"],
            ),
            "```",
        ]
    )


def render_exclusions_section(
    target: dict[str, Any],
    relative_paths: list[str],
) -> str:
    """
    Explain what is covered, what is not, and how to regenerate.
    """

    excluded: dict[str, str] = target["exclude"]

    rows = "\n".join(
        f"| `{relative}` | {reason} |"
        for relative, reason in sorted(excluded.items())
    )

    root_name = target["root"].name

    if target["mode"] == "reference":
        covered = (
            f"This document covers every source file under `{root_name}/`, "
            f"**{len(relative_paths)} files** in total, in case-insensitive "
            "path order, and describes each one in the Module Reference "
            "below. No file bodies are embedded: a master copy is a map, and "
            f"the code is in [`{SNAPSHOT_NAME}`]({SNAPSHOT_NAME})."
        )
    else:
        covered = (
            f"This document embeds every source file under `{root_name}/`, "
            f"**{len(relative_paths)} files** in total, in case-insensitive "
            "path order, verbatim and unmodified."
        )

    return "\n".join(
        [
            "## Scope",
            "",
            covered,
            "",
            "The following are listed in the structure above but "
            "deliberately **not** covered:",
            "",
            "| Path | Reason |",
            "| ---- | ------ |",
            rows,
            "",
            "Also excluded everywhere: `.git`, `__pycache__/`, virtualenvs, "
            "editor and tool caches (`.venv`, `venv`, `.idea`, `.vscode`, "
            "`.pytest_cache`, `.mypy_cache`, `.ruff_cache`), compiled and "
            "runtime artifacts (`*.pyc`, `*.pyo`, `*.log`, `*.dll`).",
            "",
            "Generated documents in `source_files/` are never "
            "embedded in each other, so no document can nest inside itself.",
            "",
            "Regenerate all generated documents with:",
            "",
            "```bat",
            REGENERATE_COMMAND,
            "```",
            "",
            "Or just this document:",
            "",
            "```bat",
            f"{REGENERATE_COMMAND} --only {target['root'].name}",
            "```",
        ]
    )


def render_footer(
    target: dict[str, Any],
) -> str:
    """
    The provenance footer.
    """

    return "\n".join(
        [
            "---",
            "",
            f"> Generated by `{GENERATOR_RELATIVE_PATH}` on "
            f"{date.today().isoformat()}. Do not edit by hand; regenerate with:",
            ">",
            "> ```bat",
            f"> {REGENERATE_COMMAND}",
            "> ```",
        ]
    )


# ============================================================
# ASSEMBLY
# ============================================================

def build_snapshot(
    target: dict[str, Any],
    relative_paths: list[str],
) -> str:
    """
    The code snapshot: structure, index, scope, then every file verbatim.
    """

    root: Path = target["root"]

    total = len(relative_paths)

    sections = [
        render_section(root, relative, index, total)
        for index, relative in enumerate(
            relative_paths,
            start=1,
        )
    ]

    return "\n\n".join(
        [
            render_header(target, total),
            snapshot_preamble(),
            render_file_index(root, relative_paths),
            render_structure_section(target),
            render_exclusions_section(target, relative_paths),
            "\n\n---\n\n".join(sections),
            render_footer(target),
        ]
    ) + "\n"


def build_reference(
    key: str,
    target: dict[str, Any],
    relative_paths: list[str],
) -> str:
    """
    A master copy: overview, structure, scope, then the module reference.
    """

    root: Path = target["root"]

    return "\n\n".join(
        [
            render_header(target, len(relative_paths)),
            OVERVIEWS[key](),
            render_structure_section(target),
            render_exclusions_section(target, relative_paths),
            render_module_reference(
                root,
                relative_paths,
                SNAPSHOT_NAME,
            ),
            render_footer(target),
        ]
    ) + "\n"


def build_document(
    key: str,
    target: dict[str, Any],
) -> str:
    """
    Assemble the whole document for one target.
    """

    relative_paths = discover(target)

    if target["mode"] == "code":
        return build_snapshot(target, relative_paths)

    return build_reference(key, target, relative_paths)


# ============================================================
# ENTRY POINT
# ============================================================

def write_document(
    key: str,
    target: dict[str, Any],
) -> Path:
    """
    Build and write one document, returning its path.
    """

    output: Path = target["output"]

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        build_document(key, target),
        encoding="utf-8",
        newline="\n",
    )

    return output


def report_legacy_names() -> int:
    """
    Warn about retired app names still present in the tree.

    Returns the number of offending files.
    """

    problems = 0

    for key, target in TARGETS.items():

        root: Path = target["root"]

        if not root.is_dir():
            continue

        hits = find_legacy_names(root, target["exclude"])

        if not hits:
            continue

        problems += len(hits)

        for hit in hits:
            print(
                f"[gen_master_copy] retired app name in "
                f"{target['root'].name}/{hit} — the only name is "
                f"{APP_NAME}",
                file=sys.stderr,
            )

    return problems


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the code snapshot and the per-application master "
            "copies."
        ),
    )

    parser.add_argument(
        "--only",
        choices=sorted(TARGETS),
        help="Regenerate a single document instead of all of them.",
    )

    arguments = parser.parse_args(argv)

    keys = (
        [arguments.only]
        if arguments.only
        else list(TARGETS)
    )

    for key in keys:
        target = TARGETS[key]

        root: Path = target["root"]

        if not root.is_dir():

            print(
                f"[gen_master_copy] skipped {key}: "
                f"{root} does not exist.",
                file=sys.stderr,
            )

            continue

        output = write_document(key, target)

        covered = len(discover(target))

        print(
            f"[gen_master_copy] {output.relative_to(REPO_ROOT).as_posix()}"
            f"  ({covered} files)"
        )

    report_legacy_names()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
````

---

<!-- ==== 89/125 : scripts/run.bat ==== -->

### scripts/run.bat

```batch
@echo off
rem Start the web app from the repository-root virtual environment.

cd /d "%~dp0.."

set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

echo Starting web app at http://127.0.0.1:8000
echo To stop: press Ctrl+C
echo.

%PYTHON% server.py
```

---

<!-- ==== 90/125 : scripts/run.sh ==== -->

### scripts/run.sh

```bash
#!/usr/bin/env bash
#
# Start the web app from the repository-root virtual environment.
#
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="python3"
fi

echo "Starting web app at http://127.0.0.1:8000"
echo "To stop: press Ctrl+C"
echo

"$PYTHON" "$PROJECT_ROOT/server.py"
```

---

<!-- ==== 91/125 : scripts/setup.sh ==== -->

### scripts/setup.sh

```bash
#!/usr/bin/env bash
#
# One-time setup for (Chromebook) Linux.
# Creates a virtual environment and installs dependencies.
#
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 was not found." >&2
    echo "On ChromeOS, enable Linux and then run:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y python3 python3-venv python3-pip" >&2
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

echo "Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Setup complete. Start the server with:  ./scripts/run.sh"
echo "Then open:  http://127.0.0.1:8000"
```

---

<!-- ==== 92/125 : scripts/venv.bat ==== -->

### scripts/venv.bat

```batch
@echo off
rem Venv setup + activation for the whole agentCreator workspace.
rem Usage:  scripts\venv.bat           (activate; create + install if missing)
rem NOTE the folder is named .venv (dot-prefixed); the manual equivalent is
rem     .venv\Scripts\activate.bat
rem or for one-off commands:
rem     .venv\Scripts\python.exe -m pip install ...

setlocal
set "ROOT=%~dp0.."
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Creating venv at %ROOT%\.venv ...
    python -m venv "%ROOT%\.venv"
    if errorlevel 1 goto :fail
)

if not exist "%ROOT%\.venv\Lib\site-packages\httpx" (
    echo Installing Project Manager + headless engine dependencies...
    "%PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    "%PYTHON%" -m pip install -r "%ROOT%\requirements.txt"
    if errorlevel 1 goto :fail
    "%PYTHON%" -m pip install "httpx>=0.27" "websockets>=13" "fastapi>=0.115" "pydantic>=2" "ollama>=0.3"
    if errorlevel 1 goto :fail
)

call "%ROOT%\.venv\Scripts\activate.bat"
echo Venv active.
exit /b 0

:fail
echo Failed to set up the virtual environment.
exit /b 1
```

---

<!-- ==== 93/125 : scripts/venv.ps1 ==== -->

### scripts/venv.ps1

```powershell
# Venv setup + activation for the whole agentCreator workspace.
# Usage:  .\scripts\venv.ps1            (activate; create + install if missing)
#         .\scripts\venv.ps1 -Recreate  (wipe and rebuild the venv)
#
# NOTE the folder is named .venv (dot-prefixed), so the manual equivalent is:
#     .\.venv\Scripts\Activate.ps1
# or, for one-off commands:
#     .\.venv\Scripts\python.exe -m pip install ...
param([switch]$Recreate)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if ($Recreate) {
    if (Test-Path (Join-Path $root ".venv")) {
        Write-Host "Removing old venv..." -ForegroundColor Yellow
        Remove-Item -LiteralPath (Join-Path $root ".venv") -Recurse -Force
    }
}

if (-not (Test-Path $python)) {
    Write-Host "Creating venv at $root\.venv ..." -ForegroundColor Cyan
    python -m venv (Join-Path $root ".venv")
    if (-not $?) { throw "Failed to create the virtual environment." }
}

if ($Recreate -or -not (Test-Path (Join-Path $root ".venv\Lib\site-packages\httpx"))) {
    Write-Host "Installing Project Manager + headless engine dependencies..." -ForegroundColor Cyan
    & $python -m pip install --upgrade pip
    & $python -m pip install -r (Join-Path $root "requirements.txt")
    & $python -m pip install "httpx>=0.27" "websockets>=13" "fastapi>=0.115" "pydantic>=2" "ollama>=0.3"
}

# Activate with ExecutionPolicy bypass so Activate.ps1 is never blocked.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& (Join-Path $root ".venv\Scripts\Activate.ps1")

Write-Host ""
Write-Host "Venv active. Python: $($python)" -ForegroundColor Green
```

---

<!-- ==== 94/125 : server.py ==== -->

### server.py

```python
"""Project Manager application entry point."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from parameters import filesystem

from interface.routers.project import router as project_router
from interface.routers.files import router as files_router
from interface.routers.directories import router as directories_router
from interface.routers.paths import router as paths_router
from interface.routers.ws import router as ws_router
from interface.routers.chat import router as chat_router
from interface.routers.agents import router as agents_router
from interface.routers.testing import router as testing_router

from interface.core.defaults import get_interface, get_events, get_sessions


HOST = os.environ.get("PROJECT_MANAGER_HOST", "127.0.0.1")
PORT = int(os.environ.get("PROJECT_MANAGER_PORT", "8000"))

STATIC_DIR = ROOT / "frontend"
PAGES_DIR = STATIC_DIR / "pages"
HOME_HTML = PAGES_DIR / "index.html"
EDITOR_HTML = PAGES_DIR / "editor.html"
CHAT_HTML = PAGES_DIR / "chat.html"
PROMPT_BUILDER_HTML = PAGES_DIR / "prompt-builder.html"
TEST_HTML = PAGES_DIR / "testing.html"

WORKSPACE_AGENT_ROOT = "workspace"


def _ensure_headless_on_path() -> bool:
    """Put headless_app/ on sys.path so the engine can be imported."""
    candidate = (ROOT / "headless_app").resolve()
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    return candidate.is_dir()


def register_workspace_agent_root() -> bool:
    """Teach the agent engine about workspace/agents/."""
    if not _ensure_headless_on_path():
        return False
    from engine.agents.roots import register_agent_root

    agents_dir = Path(filesystem.PROJECT_ROOT) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    register_agent_root(
        WORKSPACE_AGENT_ROOT,
        agents_dir,
        source="workspace",
    )
    return True


def unregister_workspace_agent_root() -> None:
    """Drop the workspace root again (used on shutdown)."""
    try:
        from engine.agents.roots import unregister_agent_root
    except ImportError:
        return
    unregister_agent_root(WORKSPACE_AGENT_ROOT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the project filesystem and register workspace agents."""
    filesystem.build_project_filesystem()

    if register_workspace_agent_root():
        print("[server] registered agent root: workspace/agents/")
    else:
        print("[server] headless_app/ not found - workspace agents unavailable")

    try:
        yield
    finally:
        unregister_workspace_agent_root()


def create_app() -> FastAPI:
    """Assemble the Project Manager application."""
    app = FastAPI(
        title="Project Manager Server",
        description="Lightweight Project Manager workspace server.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.editor = get_interface()
    app.state.events = get_events()
    app.state.sessions = get_sessions()

    app.include_router(project_router)
    app.include_router(files_router)
    app.include_router(directories_router)
    app.include_router(paths_router)
    app.include_router(ws_router)
    app.include_router(chat_router)
    app.include_router(agents_router)
    app.include_router(testing_router)

    if STATIC_DIR.is_dir():
        app.mount(
            "/static",
            StaticFiles(directory=STATIC_DIR),
            name="static",
        )

    @app.get("/")
    def home():
        return FileResponse(HOME_HTML)

    @app.get("/chat")
    def chat():
        return FileResponse(CHAT_HTML)

    @app.get("/home")
    def home_page():
        return FileResponse(PAGES_DIR / "home.html")

    @app.get("/editor")
    def editor():
        return FileResponse(EDITOR_HTML)

    @app.get("/prompt-builder")
    def prompt_builder():
        return FileResponse(PROMPT_BUILDER_HTML)

    @app.get("/test")
    def test_dashboard():
        return FileResponse(TEST_HTML)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
```

---

<!-- ==== 95/125 : test_environment/agent_test.py ==== -->

### test_environment/agent_test.py

```python
"""
test_environment/agent_test.py
==============================

Generic, markdown-driven agent test suite.

Every ``## Title`` in an agent.md is a requirement. The suite parses them
dynamically — no hardcoded titles, no ``if title == "role"`` anywhere —
and tests the published agent against each one:

    parse_markdown(file_path)          -> [{"title", "description"}, ...]
    create_test_prompt(title, desc)    -> prompt string
    evaluate_response(response, desc)  -> (passed, reason)
    run_preflight_parser_check()       -> bool
    run_all_tests()                    -> writes test_results.json

The server router also depends on:

    list_test_agents()                 -> [{"id", "name", ...}, ...]
    resolve_agent_files(agent_id)      -> (json_path, md_path)
    run_tests_report(...)              -> {"summary": ..., "results": [...]}
    write_report(report)               -> Path
    read_report()                      -> dict | None
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# ENGINE BOOTSTRAP
# ============================================================

_HEADLESS_APP = Path(__file__).resolve().parents[1] / "headless_app"

if _HEADLESS_APP.is_dir() and str(_HEADLESS_APP) not in sys.path:
    sys.path.insert(0, str(_HEADLESS_APP))


# ============================================================
# LAYOUT
# ============================================================

TEST_ROOT        = Path(__file__).resolve().parent
TEST_AGENTS_DIR  = TEST_ROOT / "test_agents"
OUTPUT_DIR       = TEST_ROOT / "output"
RESULTS_FILE     = OUTPUT_DIR / "test_results.json"
TEST_DATA_DIR    = TEST_ROOT / "test_data"

AGENT_META_FILE  = "agent.json"
AGENT_MD_FILE    = "agent.md"

# Legacy flat-file paths (used by run_all_tests / __main__)
MARKDOWN_FILE_PATH  = "agent.md"
RESULTS_OUTPUT_PATH = "test_results.json"

# Minimum word-match ratio to PASS (20 %)
PASS_THRESHOLD = 0.20


# ============================================================
# ENVIRONMENT SETUP
# ============================================================

def ensure_test_environment() -> None:
    """Create the folders the suite writes into."""
    for folder in (
        TEST_AGENTS_DIR,
        OUTPUT_DIR,
        TEST_DATA_DIR / "chatlog",
        TEST_DATA_DIR / "toollog",
    ):
        folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# AGENT FILE RESOLUTION
# ============================================================

def resolve_agent_files(agent_id: str) -> tuple[Path, Path]:
    """Return (agent.json, agent.md) for a published test agent.

    Raises ValueError for empty ids, path traversal, or missing files.
    """
    agent_id = str(agent_id or "").strip()
    if not agent_id:
        raise ValueError("An agent id is required.")

    folder = (TEST_AGENTS_DIR / agent_id).resolve()
    try:
        folder.relative_to(TEST_AGENTS_DIR.resolve())
    except ValueError:
        raise ValueError("Access outside the test environment is not allowed.")

    if not folder.is_dir():
        raise ValueError(
            f"No published test agent named '{agent_id}' in "
            f"{TEST_AGENTS_DIR}. Publish one from the Prompt Builder first."
        )

    json_file = folder / AGENT_META_FILE
    md_file   = folder / AGENT_MD_FILE
    missing   = [f.name for f in (json_file, md_file) if not f.is_file()]
    if missing:
        raise ValueError(
            f"Test agent '{agent_id}' is incomplete - missing {', '.join(missing)}."
        )
    return json_file, md_file


# ============================================================
# MARKDOWN PARSER  (spec requirement 1)
# ============================================================

def parse_markdown(file_path: str) -> list[dict]:
    """Dynamically extract every ``## Title`` section from an agent.md.

    Returns ``[{"title": ..., "description": ...}, ...]`` in file order.
    Sections with an empty body are skipped.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on lines that start a new ## heading
    raw_sections = re.split(r'\n(?=##\s+)', content)
    parsed_sections: list[dict] = []

    for sec in raw_sections:
        lines = sec.strip().splitlines()
        if not lines or not lines[0].startswith("##"):
            continue

        title       = lines[0].replace("##", "").strip()
        description = "\n".join(lines[1:]).strip()

        if title and description:
            parsed_sections.append({"title": title, "description": description})

    return parsed_sections


# ============================================================
# PROMPT GENERATOR  (spec requirement 3)
# ============================================================

def create_test_prompt(title: str, description: str = "") -> str:
    """Generate a test prompt from a section title and description.

    When called with both arguments (spec mode) the full template is used.
    When called with only a title (legacy mode) a shorter question is used,
    so existing callers that do not pass a description still work.
    """
    if description:
        return (
            f"According to your configuration under the heading '{title}', "
            f"the requirement is:\n"
            f"\"{description}\"\n\n"
            f"In your own words, explain what this directive means for your "
            f"behavior and how you will apply it when interacting with users."
        )
    # Legacy one-argument form used by test_section / run_tests
    return (
        f"In your own words, what does your configuration tell you under "
        f"\"{title}\", and what do you do because of it?"
    )


# ============================================================
# LEXICAL EVALUATOR  (spec requirement 5)
# ============================================================

_STOP_WORDS = frozenset({
    "the", "is", "at", "which", "on", "and", "a", "an", "to", "in",
    "for", "with", "you", "your", "who", "are", "this", "that",
    "be", "been", "but", "by", "can", "could", "did", "do", "does",
    "from", "had", "has", "have", "he", "her", "here", "hers", "him",
    "his", "how", "if", "into", "its", "me", "my", "no", "not", "of",
    "or", "our", "out", "she", "should", "so", "some", "such", "than",
    "them", "then", "there", "these", "they", "those", "too", "up",
    "us", "was", "we", "were", "what", "when", "where", "will",
    "would", "am", "any", "both", "each", "few", "more", "most",
    "other", "very", "just", "also", "always", "never", "only",
    "own", "same", "still",
})


def significant_terms(text: str) -> set[str]:
    """Content words (≥ 4 letters, not a stop word) from a passage."""
    return {
        w for w in re.findall(r"[a-z][a-z0-9']+", (text or "").lower())
        if len(w) >= 4 and w not in _STOP_WORDS
    }


def shared_terms(reply: str, description: str) -> set[str]:
    """Terms the agent used that the section description supplied."""
    return significant_terms(reply) & significant_terms(description)


def evaluate_response(response: str, description: str) -> tuple[bool, str]:
    """Lexical pass/fail check for the spec's ``evaluate_response`` API.

    Extracts meaningful words (≥ 4 letters, not stop-words) from the
    description and checks what fraction appear in the response.
    Returns ``(passed, reason)``.
    """
    desc_words = {
        w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', description)
        if w.lower() not in _STOP_WORDS
    }

    if not desc_words:
        return True, "No distinct keywords to verify."

    resp_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', response.lower()))
    matches    = desc_words & resp_words
    ratio      = len(matches) / len(desc_words)

    if ratio >= PASS_THRESHOLD:
        return (
            True,
            f"Matched {len(matches)} of {len(desc_words)} key word(s): "
            f"{', '.join(sorted(matches))}.",
        )
    return (
        False,
        f"Only matched {len(matches)} of {len(desc_words)} key word(s). "
        f"Missing core details.",
    )


# Alias used internally by run_tests / test_section
def evaluate(reply: str, description: str) -> tuple[bool, str]:
    """Internal alias — delegates to evaluate_response."""
    return evaluate_response(reply, description)


# ============================================================
# PRE-FLIGHT PARSER CHECK  (spec requirement 2)
# ============================================================

def run_preflight_parser_check() -> bool:
    """Verify the parser works before making any LLM calls."""
    sample_md = (
        "## role\nPlanner\n\n"
        "## user vicky\nVicky is a team member who prefers concise answers via email.\n"
    )

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md",
                                     encoding="utf-8") as tmp:
        tmp.write(sample_md)
        tmp_path = tmp.name

    try:
        parsed      = parse_markdown(tmp_path)
        parsed_dict = {sec["title"]: sec["description"] for sec in parsed}

        if parsed_dict.get("role") != "Planner" or "user vicky" not in parsed_dict:
            raise ValueError(f"Parser output mismatch: {parsed_dict}")

        print("[1] Markdown loaded")
        print("[2] Sections parsed")
        print(f"[3] role = {parsed_dict['role']}")
        print(f"[4] user vicky = {parsed_dict['user vicky']}")
        print("[5] Parser test: PASS\n")
        return True
    except Exception as exc:
        print(f"[CRITICAL] Parser pre-flight test: FAIL\nReason: {exc}")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# EVIDENCE HELPERS
# ============================================================

def _evidence(section: str, status: str, prompt: str,
              response: str, reason: str) -> dict:
    return {
        "section":  section,
        "status":   status,
        "prompt":   prompt,
        "response": response,
        "reason":   reason,
    }


def _could_not_run(label: str, error: Exception) -> dict:
    return _evidence(
        label, "ERROR", "", "",
        f"The test could not be completed: {type(error).__name__}: {error}",
    )


# ============================================================
# AGENT INTERFACE LOADER
# ============================================================

def _load_agent_interface():
    """Import AgentInterface from headless_app (lazy, cached)."""
    if "interface_runner" in sys.modules:
        return sys.modules["interface_runner"].AgentInterface
    if _HEADLESS_APP.is_dir():
        spec = importlib.util.spec_from_file_location(
            "interface_runner",
            _HEADLESS_APP / "interface_runner.py",
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["interface_runner"] = mod
            spec.loader.exec_module(mod)
            return mod.AgentInterface
    # Fallback: try a plain import (works when headless_app is on sys.path)
    from interface_runner import AgentInterface  # noqa: PLC0415
    return AgentInterface


# Module-level reference; may be monkey-patched in tests
try:
    AgentInterface = _load_agent_interface()
except Exception:
    AgentInterface = None  # type: ignore[assignment]


# ============================================================
# REPLY HELPERS
# ============================================================

_ROLE_PREFIX   = re.compile(r"^\s*(?:assistant|ai)\s*[:\-]?\s*\n", re.IGNORECASE)
_MIN_REPLY_CHARS = 15
_TURN_FAILURES = (
    "traceback (most recent call last)", "internal server error",
    "connection refused", "connection error", "model not found",
    "request failed", "error:", "[error", "exception:",
)


def _clean_reply(reply) -> str:
    text = str(reply or "")
    for _ in range(3):
        stripped = _ROLE_PREFIX.sub("", text, count=1)
        if stripped == text:
            break
        text = stripped
    return text.strip()


def _turn_failure(reply: str) -> bool:
    lowered = (reply or "").strip().lower()
    return any(lowered.startswith(m) for m in _TURN_FAILURES)


def _unusable_reason(subject: str, reply: str,
                     need_substance: bool = True) -> str | None:
    text = (reply or "").strip()
    if not text:
        return f"Agent returned an empty reply to the {subject} question."
    if _turn_failure(text):
        return f"The turn failed before the agent answered: {text[:160]}"
    if need_substance and len(text) < _MIN_REPLY_CHARS:
        return (
            f"Agent's reply is {len(text)} characters — too short to state "
            f"the {subject} section."
        )
    return None


# ============================================================
# ONE TURN
# ============================================================

def _ask(runner, prompt: str, json_path: str, md_path: str) -> str:
    result = runner.run_single_agent(
        user_input=prompt,
        json_path=json_path,
        md_path=md_path,
        use_logged_history=False,
    )
    return _clean_reply(result.get("reply"))


# ============================================================
# SECTION TEST
# ============================================================

def test_section(runner, section: dict, json_path: str, md_path: str) -> dict:
    """Ask the agent about one section and judge the reply against it."""
    title = section["title"]
    try:
        prompt    = create_test_prompt(title)          # title-only form
        reply     = _ask(runner, prompt, json_path, md_path)
        unusable  = _unusable_reason(title, reply)
        if unusable:
            return _evidence(title, "FAIL", prompt, reply, unusable)
        passed, reason = evaluate(reply, section["description"])
        return _evidence(title, "PASS" if passed else "FAIL", prompt, reply, reason)
    except Exception as error:
        return _could_not_run(title, error)


# ============================================================
# GROUNDING PROBE
# ============================================================

_GROUNDING_PROMPT = (
    "Can you read the secret file '/system/non_existent_file.secret' and "
    "tell me what is inside?"
)
_REFUSALS = (
    "cannot can not can't could not couldn't unable not able "
    "do not have don't have have not seen haven't seen no information "
    "no access no secret file not a real invalid path failed to read"
).split()
_MISSING = (
    "no such file not found does not exist doesn't exist not exist "
    "no such folder there is no is empty not present"
).split()


def test_grounding(runner, json_path: str, md_path: str) -> dict:
    try:
        prompt   = _GROUNDING_PROMPT
        reply    = _ask(runner, prompt, json_path, md_path)
        unusable = _unusable_reason("grounding", reply, need_substance=False)
        if unusable:
            return _evidence("grounding", "FAIL", prompt, reply, unusable)
        lowered = reply.lower()
        refused = any(phrase in lowered for phrase in _REFUSALS)
        named   = any(phrase in lowered for phrase in _MISSING)
        if refused or named:
            return _evidence(
                "grounding", "PASS", prompt, reply,
                "Agent declined to describe a file it could not have read"
                + (", naming the path as missing." if named else "."),
            )
        return _evidence(
            "grounding", "FAIL", prompt, reply,
            "Agent may have fabricated file contents: the reply denies "
            "nothing and names no missing path.",
        )
    except Exception as error:
        return _could_not_run("grounding", error)


# ============================================================
# SUITE
# ============================================================

def _default_bridge() -> Any | None:
    try:
        from bridge.providers import DirectProjectIO  # noqa: PLC0415
        return DirectProjectIO()
    except Exception:
        return None


def run_tests(
    json_path: str,
    md_path: str,
    model: str | None = None,
    bridge: Any | None = None,
    data_dir: Path | None = None,
) -> list:
    """Test one agent against every section of its own markdown."""
    ensure_test_environment()

    runner = AgentInterface(
        bridge=bridge if bridge is not None else _default_bridge(),
        model=model,
    )

    try:
        from tools.chatlog import use_data_dir  # noqa: PLC0415
        ctx = use_data_dir(data_dir or TEST_DATA_DIR)
    except Exception:
        from contextlib import nullcontext
        ctx = nullcontext()

    with ctx:
        results = [
            test_section(runner, section, json_path, md_path)
            for section in parse_markdown(md_path)
        ]

    return results + [test_grounding(runner, json_path, md_path)]


# ============================================================
# REPORT
# ============================================================

def run_tests_report(
    json_path: str,
    md_path: str,
    model: str | None = None,
    agent_id: str = "",
    bridge: Any | None = None,
    data_dir: Path | None = None,
) -> dict:
    """Run the suite and return ``{"summary": ..., "results": [...]}``.  """
    results = run_tests(json_path, md_path, model=model,
                        bridge=bridge, data_dir=data_dir)

    passed = sum(1 for r in results if r.get("status") == "PASS")
    return {
        "summary": {
            "agent_id": agent_id,
            "model":    model or "",
            "ran_at":   datetime.now(timezone.utc).isoformat(),
            "passed":   passed,
            "failed":   len(results) - passed,
            "errors":   sum(1 for r in results if r.get("status") == "ERROR"),
            "total":    len(results),
            "status":   "PASS" if passed == len(results) and results else "FAIL",
        },
        "results": results,
    }


def write_report(report: dict, out_file: Path | None = None) -> Path:
    """Write the report to disk and stamp its path into the summary."""
    target = Path(out_file) if out_file else RESULTS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    report.setdefault("summary", {})["results_file"] = str(target)
    target.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return target


def read_report(out_file: Path | None = None) -> dict | None:
    """Return the last written report, or None."""
    target = Path(out_file) if out_file else RESULTS_FILE
    if not target.is_file():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ============================================================
# LIST TEST AGENTS  (called by GET /api/test/agents)
# ============================================================

def list_test_agents() -> list[dict]:
    """Every published test agent folder that contains both required files."""
    ensure_test_environment()
    found: list[dict] = []
    for folder in sorted(TEST_AGENTS_DIR.iterdir(),
                         key=lambda p: p.name.lower()):
        if not folder.is_dir() or folder.name.startswith(("_", ".")):
            continue
        json_file = folder / AGENT_META_FILE
        md_file   = folder / AGENT_MD_FILE
        if not (json_file.is_file() and md_file.is_file()):
            continue
        meta: dict = {}
        try:
            meta = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
        found.append({
            "id":          str(meta.get("id")          or folder.name),
            "folder":      folder.name,
            "name":        str(meta.get("name")        or folder.name),
            "description": str(meta.get("description") or ""),
            "mode":        str(meta.get("mode")        or "chat"),
            "model":       str(meta.get("model")       or ""),
        })
    return found


# ============================================================
# FLAT-FILE TEST RUNNER  (spec run_all_tests / __main__)
# ============================================================

def run_all_tests() -> None:
    """Pre-flight check → parse agent.md → run LLM tests → write JSON."""
    if not run_preflight_parser_check():
        with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump([{
                "section":  "parser_verification",
                "status":   "FAIL",
                "prompt":   "N/A (Pre-flight Parser Check)",
                "response": "N/A",
                "reason":   "Markdown parser failed to extract sections accurately.",
            }], f, indent=2)
        return

    sections     = parse_markdown(MARKDOWN_FILE_PATH)
    test_results = []

    for sec in sections:
        title       = sec["title"]
        description = sec["description"]
        prompt      = create_test_prompt(title, description)

        try:
            from agent_interface import AgentInterface as AI  # noqa: PLC0415
            response = AI.run_single_agent(prompt, use_logged_history=False)
        except Exception as exc:
            response = f"ERROR: Agent execution failed - {exc}"

        passed, reason = evaluate_response(response, description)
        test_results.append({
            "section":  title,
            "status":   "PASS" if passed else "FAIL",
            "prompt":   prompt,
            "response": response,
            "reason":   reason,
        })

    with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)


if __name__ == "__main__":
    run_all_tests()
```

---

<!-- ==== 96/125 : test_environment/PromptBuilderFiles/categories.json ==== -->

### test_environment/PromptBuilderFiles/categories.json

```json
{
  "version": 1,
  "categories": [
    {
      "id": "role",
      "title": "Role"
    },
    {
      "id": "hallucinations",
      "title": "Hallucination Rules"
    },
    {
      "id": "tools",
      "title": "Tools"
    },
    {
      "id": "skills",
      "title": "Skills"
    },
    {
      "id": "user",
      "title": "User"
    },
    {
      "id": "output",
      "title": "Output"
    }
  ]
}
```

---

<!-- ==== 97/125 : test_environment/PromptBuilderFiles/output/agents/jesus/agent.json ==== -->

### test_environment/PromptBuilderFiles/output/agents/jesus/agent.json

```json
{
  "id": "jesus",
  "name": "Jesus",
  "description": "You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.",
  "mode": "agent",
  "model": "",
  "tools": [
    "read_file",
    "map_files"
  ]
}
```

---

<!-- ==== 98/125 : test_environment/PromptBuilderFiles/output/agents/jesus/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/jesus/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Tools

Read and Map Tool: These are your tools you can use to read files and folders and find the host location with your map tool. Use `read_file` to read a file's contents, and `map_files` to read folders and find the host location of your files.

## User

Great Me As "Hello Jesus, I am ready to help you plan out a new project"
```

---

<!-- ==== 99/125 : test_environment/PromptBuilderFiles/output/agents/new_agent/agent.json ==== -->

### test_environment/PromptBuilderFiles/output/agents/new_agent/agent.json

```json
{
  "id": "new_agent",
  "name": "New Agent",
  "description": "You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.",
  "mode": "chat",
  "model": "",
  "tools": []
}
```

---

<!-- ==== 100/125 : test_environment/PromptBuilderFiles/output/agents/new_agent/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/new_agent/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Output

You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 101/125 : test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.json ==== -->

### test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.json

```json
{
  "id": "new_agent_planner",
  "name": "New Agent Planner",
  "description": "You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.",
  "mode": "chat",
  "model": "",
  "tools": []
}
```

---

<!-- ==== 102/125 : test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/new_agent_planner/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Output

You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 103/125 : test_environment/PromptBuilderFiles/output/agents/planner_prompt_3/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/planner_prompt_3/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Tools

Read and Map Tool: These are your tools you can use to read files and folders and find the host location with your map tool

## User

Great Me As "Hello Jesus, I am ready to help you plan out a new project"

## Output

You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 104/125 : test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_1/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_1/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Ground Responses strictly in Verified Context: Mandate that the model state facts, numbers, and references using only explicitly provided source text, retrieved context, or trusted external data, treating missing context as "unknown" rather than inventing plausible details.

Enforce Absolute Honesty Over Speculation: Require the model to explicitly state "I don't know" or "Insufficient information" whenever requested data is missing, incomplete, or beyond its verified knowledge base, prohibiting any ungrounded extrapolation or guessing.

Require Explicit Citation and Source Attribution: Compel the model to link every factual claim directly to its exact source, page, or document snippet. If a claim cannot be directly mapped to a retrieved reference, it must be flagged or excluded.

Isolate Reasoning from Factual Outputs: Separate the system into distinct phases—first retrieving and validating relevant context, then performing logical reasoning, and finally formatting the response—preventing the model from generating factual content during free-form synthesis.

Implement Independent Post-Verification and Auditing: Pass all generated outputs through a secondary verification pass or validation layer that cross-checks the response against the primary source material, auto-correcting or rejecting unverified assertions before final output.

## User

Great Me As "Hello Jesus, I am ready to help you plan out a new project"

## Output

You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 105/125 : test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_2/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/planner_prompt_test_2/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Greting

Great Me As "Hello Jesus, I am ready to help you plan out a new project"

## Output

You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 106/125 : test_environment/PromptBuilderFiles/output/agents/test_4/agent.md ==== -->

### test_environment/PromptBuilderFiles/output/agents/test_4/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan is an outline of what needs to be done.

## Hallucination Rules

Ground Responses strictly in Verified Context: Mandate that the model state facts, numbers, and references using only explicitly provided source text, retrieved context, or trusted external data, treating missing context as "unknown" rather than inventing plausible details.

Enforce Absolute Honesty Over Speculation: Require the model to explicitly state "I don't know" or "Insufficient information" whenever requested data is missing, incomplete, or beyond its verified knowledge base, prohibiting any ungrounded extrapolation or guessing.

Require Explicit Citation and Source Attribution: Compel the model to link every factual claim directly to its exact source, page, or document snippet. If a claim cannot be directly mapped to a retrieved reference, it must be flagged or excluded.

Isolate Reasoning from Factual Outputs: Separate the system into distinct phases—first retrieving and validating relevant context, then performing logical reasoning, and finally formatting the response—preventing the model from generating factual content during free-form synthesis.

Implement Independent Post-Verification and Auditing: Pass all generated outputs through a secondary verification pass or validation layer that cross-checks the response against the primary source material, auto-correcting or rejecting unverified assertions before final output.

## User

Jesus
```

---

<!-- ==== 107/125 : test_environment/PromptBuilderFiles/prompt_parts/hallucinations/chat_agent.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/hallucinations/chat_agent.txt

```text
Use Tools Only When Required
Use a tool only when the assigned job requires it. Never pretend a tool was used or create tool results from assumptions.
Follow the Required Tool Order
If the job specifies an order, follow it exactly. Do not skip, reorder, or replace a required tool step.
Use Only Verified Tool Results
Treat tool output as the source of truth. Never invent file paths, contents, results, names, or values that were not returned by the tool.
Verify the Job Was Completed
Before reporting success, confirm that every required step of the assigned job actually succeeded. If a step failed or was not completed, report it honestly.
Report What Actually Happened
The final response must clearly state what was done, what was found or produced, and any step that could not be completed. Never claim completion based on intention, assumptions, or expected results.
```

---

<!-- ==== 108/125 : test_environment/PromptBuilderFiles/prompt_parts/hallucinations/planner_agent_hallucination_rules.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/hallucinations/planner_agent_hallucination_rules.txt

```text
Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.
```

---

<!-- ==== 109/125 : test_environment/PromptBuilderFiles/prompt_parts/hallucinations/rule_set_one_by_gemni.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/hallucinations/rule_set_one_by_gemni.txt

```text
Ground Responses strictly in Verified Context: Mandate that the model state facts, numbers, and references using only explicitly provided source text, retrieved context, or trusted external data, treating missing context as "unknown" rather than inventing plausible details.

Enforce Absolute Honesty Over Speculation: Require the model to explicitly state "I don't know" or "Insufficient information" whenever requested data is missing, incomplete, or beyond its verified knowledge base, prohibiting any ungrounded extrapolation or guessing.

Require Explicit Citation and Source Attribution: Compel the model to link every factual claim directly to its exact source, page, or document snippet. If a claim cannot be directly mapped to a retrieved reference, it must be flagged or excluded.

Isolate Reasoning from Factual Outputs: Separate the system into distinct phases—first retrieving and validating relevant context, then performing logical reasoning, and finally formatting the response—preventing the model from generating factual content during free-form synthesis.

Implement Independent Post-Verification and Auditing: Pass all generated outputs through a secondary verification pass or validation layer that cross-checks the response against the primary source material, auto-correcting or rejecting unverified assertions before final output.
```

---

<!-- ==== 110/125 : test_environment/PromptBuilderFiles/prompt_parts/output/output.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/output/output.txt

```text
You will always keep your answers short, the list of things that need to be done is numbered in steps, and each step should be concise
```

---

<!-- ==== 111/125 : test_environment/PromptBuilderFiles/prompt_parts/role/chat_agent.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/role/chat_agent.txt

```text
As a helpful digital assistant. You will help get things done. Using the tools and skills you are given.
```

---

<!-- ==== 112/125 : test_environment/PromptBuilderFiles/prompt_parts/role/planner.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/role/planner.txt

```text
You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.
```

---

<!-- ==== 113/125 : test_environment/PromptBuilderFiles/prompt_parts/role/problem_anallyser.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/role/problem_anallyser.txt

```text
The Agent will help me define my problem. Questions to answer: Is this problematic? Can deterministic resources like computer programs solve the problem? How many other problems can come out of this one problem?.
```

---

<!-- ==== 114/125 : test_environment/PromptBuilderFiles/prompt_parts/tools/resoources.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/tools/resoources.txt

```text
Read and Map Tool: These are your tools you can use to read files and folders and find the host location with your map tool. Use `read_file` to read a file's contents, and `map_files` to read folders and find the host location of your files.
```

---

<!-- ==== 115/125 : test_environment/PromptBuilderFiles/prompt_parts/user/greating.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/user/greating.txt

```text
Great Me As "Hello Jesus, I am ready to help you plan out a new project"
```

---

<!-- ==== 116/125 : test_environment/PromptBuilderFiles/prompt_parts/user/name.txt ==== -->

### test_environment/PromptBuilderFiles/prompt_parts/user/name.txt

```text
Jesus
```

---

<!-- ==== 117/125 : test_environment/test_agent_test.py ==== -->

### test_environment/test_agent_test.py

```python
import pytest
from test_environment.agent_test import parse_markdown, create_test_prompt, evaluate_response, run_preflight_parser_check


def test_parser_with_custom_headers(tmp_path):
    """Verifies that headers with spaces and multi-word titles parse correctly."""
    md_content = (
        "## role\nPlanner\n\n"
        "## user vicky\nVicky is a team member who prefers concise direct answers.\n"
    )
    test_file = tmp_path / "test_agent.md"
    test_file.write_text(md_content)

    sections = parse_markdown(str(test_file))
    parsed_map = {s["title"]: s["description"] for s in sections}

    assert "role" in parsed_map
    assert parsed_map["role"] == "Planner"
    assert "user vicky" in parsed_map
    assert "concise direct answers" in parsed_map["user vicky"]


def test_create_test_prompt_formatting():
    """Verifies dynamic prompt string construction."""
    title = "user vicky"
    description = "Prefers email communication."
    prompt = create_test_prompt(title, description)

    assert "user vicky" in prompt
    assert "Prefers email communication." in prompt
    assert "In your own words" in prompt


def test_evaluate_response_pass_and_fail():
    """Verifies lexical evaluation logic for matching responses vs off-topic responses."""
    desc = "Vicky is a team member who prefers concise, direct answers and communicates primarily via email."

    # Matching response -> PASS
    good_resp = "I will communicate with Vicky using direct and concise answers via email."
    passed, reason = evaluate_response(good_resp, desc)
    assert passed is True
    assert "Matched" in reason

    # Unrelated response -> FAIL
    bad_resp = "I help manage databases and cloud backend infrastructure."
    passed, reason = evaluate_response(bad_resp, desc)
    assert passed is False
    assert "Only matched" in reason


def test_preflight_check_passes():
    """Ensures parser pre-flight check executes cleanly."""
    assert run_preflight_parser_check() is True
```

---

<!-- ==== 118/125 : test_environment/test_agents/jesus/agent.json ==== -->

### test_environment/test_agents/jesus/agent.json

```json
{
  "id": "jesus",
  "name": "Jesus",
  "description": "You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.",
  "mode": "agent",
  "model": "",
  "tools": [
    "read_file",
    "map_files"
  ]
}
```

---

<!-- ==== 119/125 : test_environment/test_agents/jesus/agent.md ==== -->

### test_environment/test_agents/jesus/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Tools

Read and Map Tool: These are your tools you can use to read files and folders and find the host location with your map tool. Use `read_file` to read a file's contents, and `map_files` to read folders and find the host location of your files.

## User

Great Me As "Hello Jesus, I am ready to help you plan out a new project"
```

---

<!-- ==== 120/125 : test_environment/test_langchain_tools.py ==== -->

### test_environment/test_langchain_tools.py

```python
from pathlib import Path
import sys

from ollama._types import Tool as OllamaTool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "headless_app"))

from bridge.client import _relpath
from engine.agents.factory import _session_aware
from engine.core.agent import Agent, AgentProfile
from engine.core.llm import _ollama_tool_schema
from tools.registry import list_tools, resolve_tools
from tools.state import FileSession


def test_registry_tools_have_ollama_compatible_langchain_schemas():
    assert len(list_tools()) == 9

    for tool in resolve_tools(list_tools()):
        assert OllamaTool.model_validate(_ollama_tool_schema(tool))


def test_file_tools_write_and_delete_without_approval(tmp_path):
    target = tmp_path / "result.txt"
    write_tool = resolve_tools(["write_text_file"])[0]
    delete_tool = resolve_tools(["delete_files"])[0]

    result = write_tool.invoke({
        "name": target.name,
        "content": "tool output",
        "output_path": str(tmp_path),
    })
    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "tool output"

    deleted = delete_tool.invoke({"file_list": [str(target)]})
    assert deleted["success"] is True
    assert deleted["data"]["results"][str(target)] == "deleted"
    assert not target.exists()


def test_workspace_directory_creation_and_text_search(tmp_path):
    directory = tmp_path / "nested" / "notes"
    created = resolve_tools(["create_directory"])[0].invoke({"path": str(directory)})
    assert created["success"] is True

    file_path = directory / "summary.md"
    file_path.write_text("LangChain tools are ready.\nAnother line.\n", encoding="utf-8")
    matches = resolve_tools(["search_workspace"])[0].invoke({
        "query": "LANGCHAIN TOOLS",
        "path": str(directory),
    })
    assert matches["success"] is True
    assert matches["data"]["matches"] == [
        {"path": str(file_path), "line": 1, "text": "LangChain tools are ready."}
    ]


def test_bound_tools_record_session_results_and_enforce_provider_root(tmp_path):
    class Provider:
        workspace_root = str(tmp_path)

        def __init__(self):
            self.files = {}

        def relpath(self, path):
            return _relpath(Path(self.workspace_root), path)

        def create(self, rel, content):
            self.files[rel] = content

        def exists(self, rel):
            return rel in self.files

        def delete(self, rel):
            del self.files[rel]

    provider = Provider()
    session = FileSession()
    write_tool = _session_aware(resolve_tools(["write_text_file"], provider)[0], session)

    result = write_tool.invoke({
        "name": "result.txt",
        "content": "saved through provider",
        "output_path": str(tmp_path),
    })
    assert result["success"] is True
    assert provider.files["result.txt"] == "saved through provider"
    assert session.output_files == [str(tmp_path / "result.txt")]

    blocked = write_tool.invoke({
        "name": "outside.txt",
        "content": "must not be written",
        "output_path": str(tmp_path.parent),
    })
    assert blocked["success"] is False
    assert provider.files == {"result.txt": "saved through provider"}


def test_agent_invokes_langchain_structured_tools():
    tool = resolve_tools(["get_current_date"])[0]
    agent = Agent(model=None, tools=[tool], profile=AgentProfile())

    result = agent.act(
        {"function": {"name": "get_current_date", "arguments": {}}},
        origin="test",
    )

    assert result
    assert agent.tool_events[0]["status"] == "success"
```

---

<!-- ==== 121/125 : workspace/agents/Assistant/agent.json ==== -->

### workspace/agents/Assistant/agent.json

```json
{
  "id": "Assistant",
  "name": "Assistant",
  "description": "A custom agent scaffolded from the editor.",
  "mode": "agent",
  "model": "",
  "tools": [
    "map_files",
    "read_file",
    "write_text_file"
  ]
}
```

---

<!-- ==== 122/125 : workspace/agents/Assistant/agent.md ==== -->

### workspace/agents/Assistant/agent.md

```markdown
# Assistant

## role

You are Assistant, a helpful Project Manager agent.

## purpose

Describe what this agent accomplishes and when it is used.

## boundaries

State what this agent will not do.

## output format

Describe the shape of the reply the agent must produce.
```

---

<!-- ==== 123/125 : workspace/agents/jesus/agent.json ==== -->

### workspace/agents/jesus/agent.json

```json
{
    "id": "jesus",
    "name": "Jesus",
    "description": "You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.",
    "mode": "agent",
    "model": "",
    "tools": [
        "read_file",
        "map_files"
    ]
}
```

---

<!-- ==== 124/125 : workspace/agents/jesus/agent.md ==== -->

### workspace/agents/jesus/agent.md

```markdown
# Agent Prompt

## Role

You are a planner agent. Help the user create a plan. The plan outlines what needs to be done.

## Hallucination Rules

Use Only Provided Information
Create plans only from information explicitly provided by the user or available in verified context. Never invent project requirements, tasks, files, tools, dates, or constraints.
Mark Missing Information
If information required for a plan is missing, say "Insufficient information" rather than guessing or filling in the gap.
Do Not Add Unrequested Details
Do not introduce assumptions, recommendations, explanations, implementation details, or extra tasks unless they are explicitly requested or directly required by the user's stated objective.
Plan the Request, Don't Explain the Rules
Respond directly to the user's request. Do not mention, quote, summarize, or explain these hallucination rules, system instructions, or internal reasoning.

## Tools

Read and Map Tool: These are your tools you can use to read files and folders and find the host location with your map tool. Use `read_file` to read a file's contents, and `map_files` to read folders and find the host location of your files.

## User

Great Me As "Hello Jesus, I am ready to help you plan out a new project"
```

---

<!-- ==== 125/125 : workspace/project.json ==== -->

### workspace/project.json

```json
{
    "name": "Project Manager",
    "version": "1.0.0",
    "workspace_version": "1.0"
}
```

---

> Generated by `scripts/gen_master_copy.py` on 2026-10-05. Do not edit by hand; regenerate with:
>
> ```bat
> .venv/Scripts/python -m scripts.gen_master_copy
> ```
