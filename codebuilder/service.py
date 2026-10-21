"""CodeBuilder application layer: the use-cases, and the ONLY bridge to the host app.

Layer rule: no FastAPI here (HTTP lives in ``interface.py``), no process handling
(that lives in ``execution.py``). Everything that touches ``core_engine`` is
imported lazily inside the functions below, so this package imports cleanly even
while the host is still initialising (no import cycles) and so the host-coupling
surface is visible in one place.
"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .schemas import StructuredEditRequest

PILLAR_ROOT = Path(__file__).resolve().parent
AGENTS_ROOT = PILLAR_ROOT / "agents"

_FALLBACK_AGENT: Dict[str, Any] = {
    "id": "codebuilder-agent",
    "name": "CodeBuilder Specialist",
    "description": "Agent dedicated to writing, refactoring, and diagnosing Python code.",
    "mode": "agent",
    "tools": [
        "read_file", "write_file", "create_file", "list_directory",
        "run_python_code", "send_code_to_editor", "run_code_in_editor",
    ],
}


class EditRejected(ValueError):
    """A structured edit was refused (the HTTP layer maps this to 400)."""


# --------------------------------------------------------------------------- #
# Pillar info
# --------------------------------------------------------------------------- #
def health() -> Dict[str, str]:
    return {"status": "ok", "pillar": "codebuilder"}


def agent_meta() -> Dict[str, Any]:
    """Resolve the specialist profile metadata from the centralized agent library."""
    from core_engine.agent_factory import load_agent

    for agent_id in ("codingagent", "codebuilder-agent"):
        try:
            profile = load_agent(agent_id, "codebuilder")
            return {
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "mode": profile.mode,
                "model": profile.model,
                "tools": profile.tools,
                "squad": "",
                "environment": "workspace",
            }
        except FileNotFoundError:
            continue
    return dict(_FALLBACK_AGENT)


# --------------------------------------------------------------------------- #
# Host bridge: agents
# --------------------------------------------------------------------------- #
def list_agents() -> List[dict]:
    """Agents of the ``codebuilder`` environment (resolved by the host's agent factory)."""
    from core_engine.agent_factory import list_agents as host_list_agents

    return host_list_agents("codebuilder")


# --------------------------------------------------------------------------- #
# Structured edits
# --------------------------------------------------------------------------- #
def _edit_root() -> Path:
    return Path(os.environ.get("CODEBUILDER_EDIT_ROOT") or Path.cwd()).resolve()


def apply_edit(req: StructuredEditRequest) -> Dict[str, Any]:
    """Write an approved file update. Targets must stay inside the project root."""
    root = _edit_root()
    requested = Path(req.target_path)
    target = (requested if requested.is_absolute() else root / requested).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise EditRejected(f"Target path must stay inside the project root ({root}).") from None
    if target.is_dir():
        raise EditRejected("Target path points to a directory, not a file.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    return {
        "status": "applied",
        "target_path": str(target),
        "bytes_written": len(req.content.encode("utf-8")),
        "explanation": req.explanation,
    }


# --------------------------------------------------------------------------- #
# Host bridge: human-in-the-loop questionnaire
# --------------------------------------------------------------------------- #
def host_supports_questionnaire() -> bool:
    """True when the host ships ``core_engine.hitl`` (older hosts do not)."""
    try:
        return importlib.util.find_spec("core_engine.hitl") is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _load_questions(json_file_path: str) -> List[dict]:
    from core_engine import langgraph_tools

    relative = str(json_file_path).strip().lstrip("/")
    if relative.startswith("workspace/"):
        relative = relative[len("workspace/"):]

    raw = langgraph_tools.read_file_tool.invoke({"relative_path": relative})
    if not isinstance(raw, str) or raw.startswith("Error reading file"):
        raise ValueError(f"Questions file '{json_file_path}' was not found in the workspace.")
    try:
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Error parsing questions JSON file: {exc}") from exc

    items = data.get("questions", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    questions = []
    for index, item in enumerate(items):
        if isinstance(item, dict):
            questions.append({"id": str(item.get("id", index)), "question": str(item.get("question", item))})
        else:
            questions.append({"id": str(index), "question": str(item)})
    if not questions:
        raise ValueError("No questions found in the provided JSON file.")
    return questions


def ask_user(json_file_path: str, timeout_seconds: float = 300.0) -> str:
    """Block until the user answers a questionnaire (or the wait times out). Returns a string."""
    from core_engine import hitl

    try:
        questions = _load_questions(json_file_path)
    except ValueError as exc:
        return f"Error: {exc}"

    try:
        wait = min(max(float(timeout_seconds), 1.0), 900.0)
    except (TypeError, ValueError):
        wait = 300.0

    record = hitl.create_request(questions)
    request_id = record["request_id"]
    completed = record["event"].wait(timeout=wait)
    request_data = hitl.resolve_request(request_id)  # always release the pending entry

    if not completed or request_data is None:
        return "Error: User questionnaire timed out waiting for input."

    answers = request_data.get("answers", {})
    return json.dumps(
        {
            "status": "COMPLETED",
            "qa_pairs": [
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answer": answers.get(q["id"], answers.get(str(i), "No answer provided")),
                }
                for i, q in enumerate(questions)
            ],
        },
        indent=2,
    )
