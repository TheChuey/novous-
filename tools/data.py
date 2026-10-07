"""tools/data.py

Component constants, data-store paths, session schema and provider state.

Two data stores live here (plain text so a single file can be read by the
agent's ``search_chat_logs`` tool):

    data/chatlog/chat.log            - every user turn + agent reply (JSON lines)
    data/toollog/tool_usage.jsonl    - every tool execution event (JSON lines)

The data root is ``<repo>/data`` unless ``AGENT_DATA_DIR`` names another one;
:func:`tools.logic.use_data_dir` points it somewhere else for the duration of
a block (test runs). Path constants are read at call time through this module,
so rebinding them here redirects every caller at once.
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any

__all__ = [
    "CHATLOG_DIR",
    "CHATLOG_FILE",
    "DATA_DIR",
    "DATA_DIR_ENV",
    "DEFAULT_HISTORY_LIMIT",
    "DEFAULT_IGNORE_DIRS",
    "FileSession",
    "MAX_HISTORY_LIMIT",
    "MAX_MESSAGE_LENGTH",
    "PLAIN_TEXT_EXTENSIONS",
    "TOOLLOG_DIR",
    "TOOLLOG_FILE",
    "default_data_dir",
]


#: Environment variable naming an alternative data root.
DATA_DIR_ENV = "AGENT_DATA_DIR"


def default_data_dir() -> Path:
    """The data root this process writes to.

    ``AGENT_DATA_DIR`` when it is set to an existing path, otherwise the
    repository's own ``data`` folder beside this package.
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

# Plain-text formats are read straight off disk (fast path). Everything else
# (PDF/DOCX/PPTX/XLSX/HTML/images/...) goes through IBM Docling's pipeline,
# which returns clean, structurally-formatted markdown.
PLAIN_TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".log", ".text",
    ".csv", ".tsv",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".py", ".pyw", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx",
    ".css", ".scss", ".sass", ".xml", ".tex", ".rst",
}

#: Ordinary noise excluded from directory listings and searches.
DEFAULT_IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode",
}


# ============================================================
# PROVIDER STATE
# ============================================================

#: Process-wide default provider (None = operate on the local disk). This is
#: only the fallback for callers that do not bind a provider of their own;
#: per-agent binding goes through the ``_bound_provider`` context variable so
#: two agents can never fight over one module global.
_io: Any = None

#: Provider bound for the duration of a single tool call (see
#: tools.interface.resolve_tools). A ContextVar keeps the binding scoped to
#: the running thread/task, so concurrent agents stay independent.
_bound_provider: ContextVar = ContextVar("tool_provider", default=None)


# ============================================================
# FILE SESSION SCHEMA
# ============================================================

class FileSession:
    """Manages file-management working state for AI agents dynamically.

    Tracks, across tool calls in one process:

        discovered_files   - paths surfaced by map_files / other listing tools
        selected_files     - paths the agent has explicitly chosen to work on
        read_files         - paths whose contents have already been read
        working_content    - path -> last extracted text content (read_file)
        output_files       - paths the agent has written (write_text_file)

    The session is process-wide: one instance is created lazily and shared by
    every agent that is built in this process.

    It is injected into the conversation by Agent._inject_session_context and
    hydrated from tool results by the _record_result wrapper in the agent
    factory.
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
