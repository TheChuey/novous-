# codebuilder/ — refactored pillar (drop-in)

Replaces the existing `codebuilder/` folder. Nothing else in the app changes: same package name,
same import paths, same URLs, and same JSON/SSE shapes.

## Layers (dependencies point downward only)

```
interface.py   HTTP adapter: routes, status codes, SSE framing      ─┐
tools/         agent adapter: @tool functions                        ─┼─> service.py ─> host bridge (lazy imports)
                                                                      │
execution.py   engine: isolated runs + stuck handling                ─┘ (interface also calls the engine directly)
schemas.py     contracts (pydantic only)
```

| Module | Concern | Knows about |
| :-- | :-- | :-- |
| `schemas.py` | data shapes | pydantic |
| `execution.py` | processes, deadlines, diagnostics | stdlib + schemas |
| `service.py` | use-cases (edits, agent info, questionnaire) and the **only** `core_engine` coupling | schemas |
| `interface.py` | HTTP | FastAPI, service, execution |
| `tools/tool_library.py` | agent tools | core `@tool`, service |

12 modules became 6 (+ a one-line `tools/__init__.py`). Removed: `agent_codebuilder`,
`execution_codebuilder`, `codebuilder_schemas`, `interface_codebuilder` (aliases), `runner` + `execution`
(merged), `agent_loader` (now in `service`), `diagnostics` (unused; folded into the engine).

## Host contract (unchanged)

| Host code | Needs |
| :-- | :-- |
| `server.py` | `codebuilder.interface.router`, `tools.interface.router` |
| `tools/codebuilder_tools.py` | `codebuilder.execution.execute_python_code`, `codebuilder.schemas.CodeExecutionRequest`, `codebuilder.service` |
| `core_engine/tool_catalog.py` | auto-discovers `tools/codebuilder_tools.py` (registry-only) |
| `core_engine/agent_factory.py` | `library/<id>.md` |

## When code gets stuck

Both modes run in a child process under one supervisor, so user code can never freeze the server.

| Situation | What happens |
| :-- | :-- |
| Infinite loop / long `sleep` / blocking call | Killed at the deadline. `faulthandler` reports the line it was stuck on. |
| Unbounded `print` loop | Stopped at 64 KiB (`output_limit`) instead of spinning until timeout. |
| `input()` | stdin is closed: immediate `EOFError`, no hang. |
| Code spawned child processes | The whole process tree is killed (`taskkill /T` on Windows, process group elsewhere). |
| Browser tab closed / stream abandoned | Generator close kills the run; a watchdog kills it at `timeout + 1s` regardless. |
| User or tool wants to stop it | `POST /api/codebuilder/execute/{run_id}/cancel` (id is in the stream's `start` event). |
| Agent runs hanging code | `run_python_code` returns `timed_out` + `stuck {reason, line, source, hint}` so the model can fix it. |

`timeout_seconds` is clamped to 0.1–120 s. The editor marker lands on the stuck line.

## Behaviour changes to be aware of

* `safe` mode no longer executes inside the server process (it is an isolated child, ~60 ms start-up).
  Its timeout is now actually enforced; before, `timeout_seconds` was ignored in safe mode.
* `/edit` rejects paths outside the project root (override with `CODEBUILDER_EDIT_ROOT`).
* `ask_user_questions` registers only if the host has `core_engine.hitl`.

## Tests

`python -m pytest codebuilder/tests -q` (needs pytest, fastapi, httpx; no Ollama, no running host).
