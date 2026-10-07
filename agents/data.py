"""agents/data.py

Constants, schemas and registry state for the agents component.

Component: Agent Discovery, Registry & Lifecycle. Everything here is
declarative: file names, the built-in library location, the error types
and the agent-root descriptor with its process-wide root list.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

#: Canonical file names inside an agent folder.
AGENT_META_FILE = "agent.json"
AGENT_MD_FILE = "agent.md"

#: The root the component ships with.
LIBRARY_ROOT_NAME = "library"

#: The built-in agent library: one folder per agent, inside this component.
DEFAULT_LIBRARY_DIR = Path(__file__).resolve().parent / "agents"

#: Backwards-compatible alias for the built-in library root directory.
AGENT_LIBRARY_DIR = DEFAULT_LIBRARY_DIR


class AgentNotFoundError(FileNotFoundError):
    """Raised when an agent folder or its required files are missing."""


class AgentDefinitionError(ValueError):
    """A definition parsed, but cannot produce a working agent.

    Distinct from AgentNotFoundError (no definition at all) so callers can
    tell "this agent does not exist" from "this agent is broken".
    """


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
# ROOT REGISTRY STATE
# ==========================================================================

#: Registered roots, lowest precedence first.
_roots: list[AgentRoot] = []
