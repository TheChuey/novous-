# Novous Application Component-Based Architecture Refactoring Plan

## 1. Architectural Overview & The 5-File Component Standard

The Novous application—spanning 125 core source files across its FastAPI server, agent runtime, prompt builder, test suite, and vanilla JavaScript frontend—is being refactored from a multi-layer codebase into a **Component-Based Architecture**. 

The governing principle of this architecture is: **Folder = Component, and Files = Responsibilities inside that component**.

To maintain strict modularity, eliminate bloated monolith files (such as `agent.py` at 505 lines, `client.py` at 910 lines, and `project_tools.py` at 776 lines), and ensure clean separation of concerns, every functional component folder adopts a standardized **5-file internal layout**:

```text
component_name/
│
├── interface.py         ← Public Doorway (API Entry Point)
├── logic.py             ← Workflows & Decision Routing
├── code.py              ← Core Classes & Execution Methods
├── data.py              ← Data Schemas, Models & Persistence
└── helperfunctions.py   ← Supporting Utility Functions
```

### Responsibility Breakdown of the 5-File Layout

| File | Primary Responsibility | Allowed Contents & Dependencies |
| :--- | :--- | :--- |
| **`interface.py`** | **The Public Doorway.** Serves as the sole entry point for outside callers. Exposes public function signatures and API contracts. | Imports strictly from `logic.py`, `code.py`, and `data.py`. Outside modules must *only* import this file. |
| **`logic.py`** | **Workflow & Routing.** Handles business logic, event orchestration, step sequencing, conditional routing, and error handling. | Imports from `code.py`, `data.py`, and `helperfunctions.py`. Does not export to outside callers. |
| **`code.py`** | **Execution Engine & Core Classes.** Implements stateful runtime engines, core object behavior, class definitions, and active execution loops. | Imports from `data.py` and `helperfunctions.py`. Holds active stateful objects during execution. |
| **`data.py`** | **Data Schemas, State & Persistence.** Defines Pydantic schemas, dataclasses, static constants, JSON/YAML file loaders/savers, and session state containers. | Pure data models, type definitions, and persistence utilities. Has zero external component dependencies. |
| **`helperfunctions.py`** | **Pure Utilities.** Contains small, stateless, side-effect-free helper functions (string parsing, path formatting, sanitization). | Reusable utilities. Has zero dependencies on other component files. |

### Dependency Flow & Communication Rules

Dependency flows strictly downward from the public doorway to data and helper utilities:

$$\text{Outside Caller} \longrightarrow \text{interface.py} \longrightarrow \text{logic.py} \longrightarrow \text{code.py} \longrightarrow \text{data.py} \longrightarrow \text{helperfunctions.py}$$

Both `logic.py` and `code.py` may also consume `data.py` and `helperfunctions.py` directly. Cross-component communication must always pass through the target component's `interface.py`. Direct internal imports across component boundaries (e.g., `logic.py` in Component A importing `code.py` in Component B) are strictly prohibited.

---

## 2. Detailed Component Specifications

### 2.1 `engine/` (Core Execution Runtime)

* **`interface.py`**: Public doorway for executing chat turns, single agents, and pipelines.
  * *Exposes*: `run_chat()`, `run_single_agent()`, `run_pipeline()`, `list_agents()`, `tool_catalog()`.
* **`logic.py`**: Handles chat turn sequencing, history replaying into LLM messages, think-loop orchestration, repeat-tool loop suppression, and fallback reply handling.
* **`code.py`**: Houses the `Agent` execution class, `PromptManager` builder, and `ask_llm()` communication methods.
* **`data.py`**: Defines `AgentProfile` dataclass, `EngineRuntime` configuration state, `MessageHistory` schemas, prompt template constants, and token limit constants (`MAX_MESSAGE_LENGTH = 2000`, `MAX_NUM_CTX = 32768`).
* **`helperfunctions.py`**: Contains prompt formatting, context window clipping, and text-based tool call JSON parsers (`_extract_text_tool_calls`).

### 2.2 `agents/` (Discovery, Loader & Roots Registry)

* **`interface.py`**: Public API for agent definitions and discovery.
  * *Exposes*: `build_agent()`, `build_agent_from_definition()`, `get_agent_meta()`, `list_agents()`, `register_agent_root()`.
* **`logic.py`**: Implements root scanning workflows, shadowing precedence (workspace agents overriding library agents), definition validation, and section cleanup.
* **`code.py`**: Contains `AgentRoot` manager, `AgentLoader`, and `AgentFactory` assembly logic.
* **`data.py`**: Stores `AgentMetadata` Pydantic models, `AgentGroupNode` hierarchy models, `AgentDefinitionError` and `AgentNotFoundError` exception classes, and default library path constants (`DEFAULT_LIBRARY_DIR`).
* **`helperfunctions.py`**: Utilities for resolving `agent_json_path()`, `agent_md_path()`, markdown section parsing (`_parse_sections`), and slug sanitization (`safeSlug`).

### 2.3 `tools/` (Tool Catalog, Binding & Execution)

* **`interface.py`**: Public tool catalog interface.
  * *Exposes*: `list_tools()`, `resolve_tools()`, `bind_tools()`, `unbind_tools()`, and tool invocation endpoints.
* **`logic.py`**: Manages provider binding (`using`), tool execution routing, error isolation, and LangChain wrapper logic.
* **`code.py`**: Implements tool handlers (`map_files`, `read_file`, `write_text_file`, `delete_files`, `create_directory`, `search_workspace`, `search_chat_logs`, `get_current_date`).
* **`data.py`**: Houses `FileSession` working-state tracking class (`discovered_files`, `selected_files`, `read_files`, `working_content`, `output_files`), `TOOL_ENDPOINT_MAP` documentation dictionary, and tool parameter JSON schemas.
* **`helperfunctions.py`**: Contains date/time string formatters, text-search match formatting, argument normalization, and local file unquoting.

### 2.4 `project_manager/` (Editor Operations & Filesystem Authority)

* **`interface.py`**: Public doorway for editor operations.
  * *Exposes*: `EditorInterface`, `health()`, `open()`, `save()`, `create_file()`, `create_directory()`, `rename()`, `delete()`.
* **`logic.py`**: Manages event bus publishing (`saved`, `created`, `renamed`, `deleted`), scope-based access checks, file locking, and session lifecycle tracking.
* **`code.py`**: Implements `DirectProjectIO`, `ProjectManagerBridge`, `EditorSession`, `EditorManager`, and `EventBus`.
* **`data.py`**: Defines `EditorSessionSnapshot` dataclass, `VALID_SCOPES` tuple (`"workspace"`, `"app"`), `EVENT_TYPES` set, and default project information dictionary (`DEFAULT_PROJECT`).
* **`helperfunctions.py`**: Contains path sanitization, scope resolution (`_root_for`), path target resolution (`_target`), and browser filesystem tree builder (`read_browse_filesystem`).

### 2.5 `pipelines/` (Multi-Agent Cascades)

* **`interface.py`**: Public doorway for multi-agent cascades.
  * *Exposes*: `load_pipeline()`, `run_pipeline()`.
* **`logic.py`**: Handles feed-forward message construction (passing Step N-1 output to Step N), pipeline step execution sequencing, and step-by-step stdout progress logging.
* **`code.py`**: Implements `PipelineRunner` execution loop and step output capture engines.
* **`data.py`**: Defines `PipelineConfig` schema, `PipelineStep` models, `pipeline_runs.jsonl` record data structures, and feed-forward template constants (`_STEP_FEED_TEMPLATE`).
* **`helperfunctions.py`**: Utilities for step label resolution (`_step_label`), path resolution for step definition files, and output formatting.

### 2.6 `testing/` (Header Test Suite & Prompt Evaluator)

* **`interface.py`**: Public API for testing operations.
  * *Exposes*: `run_header_tests()`, `get_results()`, `list_test_agents()`, `publish_test_agent()`, `copy_test_agent_to_workspace()`.
* **`logic.py`**: Orchestrates 4-question section test generation, grading agent replies against section criteria, pre-flight verification, and test report assembly.
* **`code.py`**: Implements `HeaderTestRunner`, `LexicalEvaluator`, assertion runners, and test environment fixtures.
* **`data.py`**: Defines `TestReport` dataclass, `SectionTestResult` schemas, `test_results.json` persistence formats, and test suite section constants (`HEADERS`).
* **`helperfunctions.py`**: Contains markdown section parsing (`parse_markdown`), keyword overlap matching (`evaluate_response`), and timestamped report filename generation (`reportFileName`).

### 2.7 `configuration/` (Models & Environment Management)

* **`interface.py`**: Public configuration interface.
  * *Exposes*: `list_models()`, `refresh_models()`, `load_config()`.
* **`logic.py`**: Handles local Ollama instance scanning, model availability verification, and configuration fallback logic.
* **`code.py`**: Implements `ModelScanner` and configuration manager execution logic.
* **`data.py`**: Defines `ModelSpec` schema, `models.json` data loader/saver, model size and capability models, and default model constants.
* **`helperfunctions.py`**: Utilities for JSON configuration file reading/writing and Ollama CLI command execution.

### 2.8 `workspace_manager/` (Workspace Directory Authority & Agent Squads)

* **`interface.py`**: Public workspace doorway.
  * *Exposes*: `get_workspace_tree()`, `scaffold_workspace_agent()`, `list_workspace_squads()`, `read_workspace_file()`.
* **`logic.py`**: Handles workspace agent scaffolding workflow, unsaved state tracking, and squad hierarchy resolution (`core/` vs `groups/`).
* **`code.py`**: Implements `WorkspaceSession`, `WorkspaceAgentDefinition`, and squad folder manager classes.
* **`data.py`**: Defines `WorkspaceConfig` models, `squad.json` / `group.json` metadata schemas, workspace file state cache models, and standard workspace directory lists (`PROJECT_FOLDERS`).
* **`helperfunctions.py`**: Utilities for path normalization, workspace-relative path resolution, and initial template scaffolding.

### 2.9 `test_environment_manager/` (Isolated Sandbox Management)

* **`interface.py`**: Public sandbox doorway.
  * *Exposes*: `publish_test_agent()`, `copy_test_agent_to_workspace()`, `delete_test_agent()`, `get_test_output()`.
* **`logic.py`**: Handles prompt builder part assembly, test agent publishing, and isolated execution setup.
* **`code.py`**: Implements `PromptPartAssembler` and `TestSandboxManager` classes.
* **`data.py`**: Defines `PromptPart` schemas, `categories.json` category manifest data model (`CATEGORIES_VERSION`), and isolated log path resolvers (`test_environment/test_data/`).
* **`helperfunctions.py`**: Utilities for part slug generation (`safeSlug`), category directory path resolution, and short path formatting (`shortenPath`).

### 2.10 `directory_layout/` (Multi-Root Filesystem Security & Navigation)

* **`interface.py`**: Root authority doorway.
  * *Exposes*: `resolve_browse_target()`, `get_browse_roots()`, `require_writable()`, `build_full_project_tree()`.
* **`logic.py`**: Enforces path security boundaries (preventing directory traversal outside project roots) and filters hidden directories (`.git`, `.venv`, `__pycache__`).
* **`code.py`**: Implements `BrowseRoot`, `PathSecurityBoundary`, and `DirectoryNode` classes.
* **`data.py`**: Stores `BROWSE_ROOTS` configuration dictionary, `TEXT_EXTENSIONS` set, `IGNORED_DIRECTORIES` set, and `MAX_EDITABLE_BYTES` threshold (512 KB).
* **`helperfunctions.py`**: Utilities for path sanitization, file extension checking (`is_text_file`), file size threshold validation (`is_oversized`), and root matching.

---

## 3. Source File Mapping Matrix (125 Files -> Component Architecture)

Below is the complete mapping of existing source files from the codebase into their new 5-file component destinations:

| Existing Source File | Original Location | Target Component | Target File |
| :--- | :--- | :--- | :--- |
| `engine_interface.py` | `<repo>/` | `engine/` | `interface.py` |
| `engine_logic.py` | `<repo>/` | `engine/` | `logic.py` |
| `engine_components.py` | `<repo>/` | `engine/` | `code.py` |
| `headless_app/engine/core/agent.py` | `headless_app/engine/core/` | `engine/` | `code.py` |
| `headless_app/engine/core/llm.py` | `headless_app/engine/core/` | `engine/` | `code.py` |
| `headless_app/engine/core/prompt.py` | `headless_app/engine/core/` | `engine/` | `code.py` |
| `interface_runner.py` | `<repo>/` | `engine/` | `interface.py` |
| `headless_app/engine/agents/factory.py` | `headless_app/engine/agents/` | `agents/` | `code.py` |
| `headless_app/engine/agents/loader.py` | `headless_app/engine/agents/` | `agents/` | `logic.py` |
| `headless_app/engine/agents/registry.py` | `headless_app/engine/agents/` | `agents/` | `code.py` |
| `headless_app/engine/agents/roots.py` | `headless_app/engine/agents/` | `agents/` | `code.py` |
| `interface/routers/agents.py` | `interface/routers/` | `agents/` | `interface.py` |
| `headless_app/tools/project_tools.py` | `headless_app/tools/` | `tools/` | `code.py` |
| `headless_app/tools/registry.py` | `headless_app/tools/` | `tools/` | `interface.py` |
| `headless_app/tools/state.py` | `headless_app/tools/` | `tools/` | `data.py` |
| `headless_app/tools/workspace.py` | `headless_app/tools/` | `tools/` | `code.py` |
| `headless_app/tools/memory.py` | `headless_app/tools/` | `tools/` | `code.py` |
| `headless_app/tools/chatlog.py` | `headless_app/tools/` | `tools/` | `code.py` |
| `headless_app/tools/utility.py` | `headless_app/tools/` | `tools/` | `helperfunctions.py` |
| `headless_app/bridge/tools_adapter.py` | `headless_app/bridge/` | `tools/` | `logic.py` |
| `interface/core/operations.py` | `interface/core/` | `project_manager/` | `interface.py` |
| `interface/core/session.py` | `interface/core/` | `project_manager/` | `code.py` |
| `interface/core/events.py` | `interface/core/` | `project_manager/` | `code.py` |
| `interface/core/defaults.py` | `interface/core/` | `project_manager/` | `logic.py` |
| `headless_app/bridge/client.py` | `headless_app/bridge/` | `project_manager/` | `code.py` |
| `headless_app/bridge/providers.py` | `headless_app/bridge/` | `project_manager/` | `code.py` |
| `interface/routers/files.py` | `interface/routers/` | `project_manager/` | `interface.py` |
| `interface/routers/directories.py` | `interface/routers/` | `project_manager/` | `interface.py` |
| `interface/routers/project.py` | `interface/routers/` | `project_manager/` | `interface.py` |
| `interface/routers/chat.py` | `interface/routers/` | `engine/` | `interface.py` |
| `interface/clients/editor_client.py` | `interface/clients/` | `project_manager/` | `code.py` |
| `headless_app/engine/pipeline.py` | `headless_app/engine/` | `pipelines/` | `logic.py` |
| `headless_app/config/pipeline.json` | `headless_app/config/` | `pipelines/` | `data.py` |
| `test_environment/agent_test.py` | `test_environment/` | `testing/` | `code.py` |
| `test_environment/test_agent_test.py` | `test_environment/` | `testing/` | `logic.py` |
| `test_environment/test_langchain_tools.py` | `test_environment/` | `testing/` | `code.py` |
| `interface/routers/testing.py` | `interface/routers/` | `testing/` | `interface.py` |
| `headless_app/config/models.json` | `headless_app/config/` | `configuration/` | `data.py` |
| `parameters/filesystem.py` | `parameters/` | `directory_layout/` | `code.py` |
| `interface/routers/paths.py` | `interface/routers/` | `directory_layout/` | `interface.py` |
| `workspace/project.json` | `workspace/` | `workspace_manager/` | `data.py` |
| `test_environment/PromptBuilderFiles/categories.json` | `test_environment/` | `test_environment_manager/` | `data.py` |
| `server.py` | `<repo>/` | `<repo>/` | `server.py` (Main Application Entry) |

---

## 4. Migration Strategy & Refactoring Roadmap

To refactor Novous safely without breaking existing server capabilities or CLI functionality, execute the migration across four distinct phases:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Create Component Directory Shells & Standard 5-File Headers    │
│ └── Create folders: engine/, agents/, tools/, project_manager/, etc.    │
│ └── Populate interface.py, logic.py, code.py, data.py, helperfunctions  │
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: Data & Model Extraction (Extract schemas into data.py)         │
│ └── Move AgentProfile, FileSession, EditorSession, BROWSE_ROOTS, etc.   │
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: Logic & Code Relocation                                        │
│ └── Move core classes to code.py, workflows to logic.py, utils to helpers│
├─────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: Interface Boundary Sealing & Server Router Re-wiring           │
│ └── Update server.py and router endpoints to call interface.py only     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Directory Shell Creation
Construct all 10 component folders (`engine/`, `agents/`, `tools/`, `project_manager/`, `pipelines/`, `testing/`, `configuration/`, `workspace_manager/`, `test_environment_manager/`, `directory_layout/`) and instantiate the 5 standardized files in each.

### Phase 2: Data Layer Isolation (`data.py`)
Extract all dataclasses, Pydantic models, JSON file loaders, session state trackers, and static constants into each component's `data.py`. Ensure `data.py` has zero dependencies on other component files.

### Phase 3: Logic and Execution Separation
Split core execution classes into `code.py`, workflows into `logic.py`, and utility functions into `helperfunctions.py`.

### Phase 4: Interface Sealing & Router Re-wiring
Update `server.py` and top-level HTTP routers so that external callers import exclusively from each component's `interface.py`. Run `test_environment/test_agent_test.py` and header verification suites to validate complete operational fidelity.
