"""Human-in-the-Loop (HITL) bridge for interactive agent questionnaires.

Shared in-memory registry that connects the ``ask_user_questions`` workspace
tool (which blocks the agent's Think-Act-Observe thread) with the core doorway
endpoints (which the browser polls and posts answers back to).
"""

import threading
import uuid
from typing import Any

PENDING_QUESTION_REQUESTS: dict[str, dict] = {}
_LOCK = threading.Lock()


def create_request(questions: list[Any], session_id: str | None = None) -> dict:
    """Register a new questionnaire and return its record (with a wait Event)."""
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    record = {
        "request_id": request_id,
        "questions": questions,
        "answers": {},
        "completed": False,
        "event": threading.Event(),
        "session_id": session_id,
    }
    with _LOCK:
        PENDING_QUESTION_REQUESTS[request_id] = record
    return record


def submit_answers(request_id: str, answers: dict) -> bool:
    """Store user answers and unblock the waiting tool thread. Returns success."""
    with _LOCK:
        record = PENDING_QUESTION_REQUESTS.get(request_id)
        if record is None or record.get("completed"):
            return False
        record["answers"] = dict(answers or {})
        record["completed"] = True
        event = record["event"]
    event.set()
    return True


def resolve_request(request_id: str) -> dict | None:
    """Remove and return a request record, or None if it is no longer active."""
    with _LOCK:
        return PENDING_QUESTION_REQUESTS.pop(request_id, None)


def list_pending() -> list[dict]:
    """Return active questionnaires currently awaiting user input."""
    with _LOCK:
        return [
            {
                "request_id": request_id,
                "questions": record.get("questions", []),
                "session_id": record.get("session_id"),
            }
            for request_id, record in PENDING_QUESTION_REQUESTS.items()
            if not record.get("completed")
        ]
