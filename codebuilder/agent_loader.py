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
