"""Shared scratchpad tools for the coding agents.

The Code Development Squad posts its plans, code, test results, and fixes here
automatically; chat coding agents read them and post notes the squad picks up.
"""

import json

from core_engine.tool_catalog import tool
from agentMemory import interface

_TOOL_POST_KINDS = {"note", "plan", "code", "test", "fix"}
_READ_CONTENT_LIMIT = 4_000


@tool(provider="agentMemory")
def read_code_scratchpad(kind: str = "", limit: str = "10") -> str:
    """Read the coding agents' shared scratchpad, newest first.

    kind filters by entry type: plan, code, test, fix, summary, or note ('' for all).
    """
    try:
        count = max(1, min(int(limit or 10), 50))
    except (TypeError, ValueError):
        count = 10
    entries = interface.read_code_scratchpad(limit=count, kind=str(kind or "").strip())
    compact = []
    for entry in entries:
        content = entry.get("content", "")
        item = {key: entry.get(key) for key in ("author", "kind", "title", "run_id", "created_at")}
        item["content"] = content[:_READ_CONTENT_LIMIT]
        if len(content) > _READ_CONTENT_LIMIT:
            item["content_truncated"] = True
        compact.append(item)
    return json.dumps({"entries": compact}, ensure_ascii=False, indent=2)


@tool(provider="agentMemory")
def post_code_scratchpad(title: str, content: str, kind: str = "note") -> str:
    """Post an entry to the coding agents' shared scratchpad so the code squad and other agents see it.

    kind is note (default), plan, code, test, or fix.
    """
    from core_engine.runtime import current_agent_id

    kind = str(kind or "note").strip().lower()
    if kind not in _TOOL_POST_KINDS:
        raise ValueError("kind must be one of: " + ", ".join(sorted(_TOOL_POST_KINDS)))
    if not str(content or "").strip():
        raise ValueError("content must not be empty.")
    entry = interface.post_code_note(current_agent_id() or "agent", kind, title, content, run_id="chat")
    return json.dumps(
        {"posted": True, "id": entry["id"], "author": entry["author"], "kind": entry["kind"]},
        ensure_ascii=False,
    )
