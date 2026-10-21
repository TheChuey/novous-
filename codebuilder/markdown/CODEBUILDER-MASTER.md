# CodeBuilder Architecture Master Reference

## Overview

CodeBuilder provides isolated Python code execution, interactive Monaco editor integration, and human-in-the-loop questionnaire workflows for Novous2 agents.

---

## Tool Architecture & `core_engine/tool_catalog.py`

### 1. Transition: From Single Master File to Registry-Only Catalog

Previously, `core_engine/tool_catalog.py` served as a single master file containing both the registration logic and the inline implementations of all system tools. 

Under the locked modular architecture, **`core_engine/tool_catalog.py` is registry-only**. Tool implementations have been migrated into dedicated modules under the `tools/` directory. `tool_catalog.py` is strictly responsible for:
- Maintaining `REGISTRY: dict[str, dict]` and the `@tool` decorator.
- Discovering and dynamically loading tool modules from `tools/`.
- Tracking isolated module load failures in `LOAD_ERRORS`.
- Generating comprehensive diagnostics through `get_catalog_report()`.

### 2. Target Layout (`tools/`)

```
tools/
├── __init__.py            # Minimal; no eager module imports
├── interface.py           # Doorway: FastAPI router + Python functions + promoted-module IO
├── core_tools.py          # calculator, docling_parse, rag_agent_tool, agent_info (+ _safe_eval, _OPERATORS)
├── editor_tools.py        # read_file, write_file, create_file, delete_file, list_directory, extract_docstrings, search_workspace
├── workspace_tools.py     # project_status
├── file_manager_tools.py  # fm_list_directory, fm_read_file, fm_write_file (file-manager-backed tools)
├── map_tools.py           # list_allowed_paths, map_folder, map_file (allow-list restricted folder/file mapping)
├── codebuilder_tools.py   # run_python_code, send_code_to_editor, run_code_in_editor, ask_user_questions (module currently has load errors)
├── promoted.py            # Workbench-promoted custom tools (with promotion marker section)
└── allowed_paths.json     # Allow-list of root paths for map tools
```

#### Module Responsibilities
- **`tools/core_tools.py`**: Evaluation tools, document parsing via Docling, RAG search, and agent profile inspection.
- **`tools/editor_tools.py`**: Workspace filesystem manipulation, directory tree inspection, AST docstring extraction, and workspace searches.
- **`tools/workspace_tools.py`**: Project state reporting (`project_status`).
- **	ools/codebuilder_tools.py**: CodeBuilder pillar tools:
  - 
un_python_code: executes code through codebuilder.execution.execute_python_code.
  - send_code_to_editor: queues code insertion into Monaco editor.
  - 
un_code_in_editor: triggers execution of active editor buffer.
  - sk_user_questions: Questionnaire flow (registered only when host supports questionnaires). 
  - **Note:** Current file contains an IndentationError (line 41) preventing load; see Diagnostics below.
- **	ools/file_manager_tools.py**: File-manager-backed tools for listing/reading/writing under the configured file-manager root.
- **	ools/map_tools.py**: Read-only folder/file mapping restricted to roots in llowed_paths.json (list_allowed_paths, map_folder with paging, map_file with AST inspection).
- **	ools/promoted.py**: Holds workbench-promoted custom tools. Maintains the # PROMOTION_MARKER separator.
- **	ools/interface.py**: The single doorway for tool catalog HTTP routes and Python APIs.

### 3. Dynamic Auto-Discovery & Isolation

The loader (`tool_catalog.load_tools(reload=False)`) discovers tool modules automatically:
- Scans all `*.py` files in `tools/`, strictly excluding `__init__.py`, `interface.py`, and any private files starting with `_*`.
- Loads each module in isolation using `importlib.util.spec_from_file_location`.
- **Fault-Tolerance**: If a tool module contains syntax errors, broken imports, or duplicate tool name collisions, the error is captured in `LOAD_ERRORS[filename]` and the module is skipped. The failure is non-fatal: `/api/tools`, the catalog registry, and all other agents remain operational (HTTP 200).
- Adding a new tool module to `tools/` requires no edits to `__init__.py`.

### 4. Promotion Flow (`tools/promoted.py`)

Tools created and tested in the Function Testing Workbench are promoted into the active runtime:
1. Workbench tests and validates the tool function.
2. Promotion calls `tools.interface.register_tool(source, name)`.
3. The source is decorated with `@tool` and appended to `tools/promoted.py` below the `# PROMOTION_MARKER`.
4. The function block is executed into `tool_catalog.__dict__` for instant runtime availability without server restart.
5. If execution fails, `promoted.py` is rolled back and the entry is popped from `REGISTRY`.
6. Deletion via `tools.interface.remove_tool(name)` removes the function span from `tools/promoted.py` and pops it from `REGISTRY`. Promoted file additions and removals are byte-identical round-trips.

### 5. Doorway APIs & Routes (`tools/interface.py`)

#### HTTP Routes:
- `GET /api/tools`: Returns `{tools: [...], providers: {...}, warnings: [...]}`. Base tools plus custom overlay (`custom: true` for promoted tools).
- `GET /api/tools/{name}`: Returns metadata for a specific tool.
- `POST /api/tools/register`: Registers a custom tool (`{source, name}`).
- `DELETE /api/tools/{name}`: Removes a custom tool.
- POST /api/tools/map-page: Returns paged folder tree (body: {path, max_depth, include_files, offset}) for allow-listed absolute paths via 	ools.map_tools.render_map_page.
- `GET /api/tools/health`: Returns catalog health and any active `load_errors`.

#### Python Doorway:
- `list_tools()`
- `get_tool(name)`
- `get_tool_source(name)`
- `register_tool(source, name)`
- `remove_tool(name)`
- `provider_bindings()`
- `catalog_report()`

### 6. Diagnostics & Verification

`tool_catalog.get_catalog_report()` walks all registered agent definitions under the agent library (`LIBRARY_ROOT = REPO_ROOT / "library"`; see `core_engine/agent_factory.py`) and parses `library/*.md` agent files (YAML frontmatter) to detect missing tools. It maps requested tools against `REGISTRY`. 

**Current state:** `core_engine.tool_catalog.load_tools()` reports load errors for tool modules (e.g. `tools/codebuilder_tools.py` currently fails to load due to an IndentationError). The catalog captures these in `LOAD_ERRORS` and marks failures as warnings in `get_catalog_report()`; the system remains operational. Builtin tool set includes `calculator`, `docling_parse`, `rag_agent_tool`, `agent_info`, `read_file`, `write_file`, `create_file`, `delete_file`, `list_directory`, `extract_docstrings`, `search_workspace`, `fm_list_directory`, `fm_read_file`, `fm_write_file`, `list_allowed_paths`, `map_folder`, `map_file`, `project_status` (18 tools registered at runtime as observed; counts may vary if any modules fail to load).



**Note:** Per this request (plan-only update scope), the CodeBuilder pillar (execution engine, /api/codebuilder/* routes, terminal, files, HITL questionnaire flow) is not expanded in this refresh. 
