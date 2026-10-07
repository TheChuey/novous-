"""tools/logic.py

Orchestration & business rules: provider selection and data-store routing.

Which provider a tool call uses is resolved by current_provider(): the
binding installed for that specific call (tools.interface.resolve_tools)
wins over the process default, so agents running side by side never share
filesystem state.

use_data_dir redirects both data stores for the duration of a block - that
is how the test environment keeps its runs out of the real chat history.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

from . import data

__all__ = [
    "configure",
    "current_provider",
    "use_data_dir",
    "using",
]


# ============================================================
# PROVIDER SELECTION
# ============================================================

def configure(provider: Any) -> None:
    """Set the process-wide default provider (None for local disk).

    The provider decides where files live AND how paths are translated. Both
    the HTTP bridge (project_manager.ProjectManagerBridge) and the
    in-process filesystem authority (project_manager.DirectProjectIO)
    implement the same surface.

    Prefer per-agent binding (tools.interface.resolve_tools(ids, provider)):
    this global remains for backwards compatibility and for the standalone
    headless CLI.
    """
    data._io = provider


def current_provider() -> Any:
    """The provider in force right now: the per-call binding, else the default."""
    bound = data._bound_provider.get()
    return data._io if bound is None else bound


@contextmanager
def using(provider: Any):
    """Activate ``provider`` for the duration of the block."""
    token = data._bound_provider.set(provider)
    try:
        yield provider
    finally:
        data._bound_provider.reset(token)


# ============================================================
# DATA-STORE ROUTING
# ============================================================

@contextmanager
def use_data_dir(path: str | Path):
    """Write both logs under ``path`` for the duration of the block.

    The path constants are rebound on entry and restored on exit, so a
    test run cannot leave the real chat log pointing at a test folder
    and a failure inside the block cannot leave it rebound at all.
    """
    previous = (
        data.DATA_DIR,
        data.CHATLOG_DIR,
        data.CHATLOG_FILE,
        data.TOOLLOG_DIR,
        data.TOOLLOG_FILE,
    )
    target = Path(path).expanduser().resolve()

    data.DATA_DIR = target
    data.CHATLOG_DIR = target / "chatlog"
    data.CHATLOG_FILE = data.CHATLOG_DIR / "chat.log"
    data.TOOLLOG_DIR = target / "toollog"
    data.TOOLLOG_FILE = data.TOOLLOG_DIR / "tool_usage.jsonl"

    try:
        yield target
    finally:
        (
            data.DATA_DIR,
            data.CHATLOG_DIR,
            data.CHATLOG_FILE,
            data.TOOLLOG_DIR,
            data.TOOLLOG_FILE,
        ) = previous
