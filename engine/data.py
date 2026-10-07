"""engine/data.py

Constants and schemas for the agent engine component.

Component: Core Reasoning & Think-Loop Runtime. Agent identity (the
profile dataclass), prompt-section names, run limits and the saved
chat-session constants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Turns of prior conversation handed to the model, per agent.
DEFAULT_HISTORY_LIMIT = 20

#: Hard cap on the Ollama context window we ever request.
MAX_NUM_CTX = 32768

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


# ==========================================================================
# SAVED CHAT SESSIONS
# --------------------------------------------------------------------------
# A session file is the only persistent record of one chat thread.
# Sessions live under the managed workspace and are excluded from git
# with workspace/data/.
#
#     workspace/data/chat_sessions/<agent_id>/<session_id>.txt
# ==========================================================================

SESSIONS_DIRNAME = "data/chat_sessions"

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")

MAX_TITLE_LENGTH = 80

MAX_HISTORY_ENTRIES = 200

MAX_SESSION_ENTRIES = 2000

EXPORT_FORMATS = ("txt",)
