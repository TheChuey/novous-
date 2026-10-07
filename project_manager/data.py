"""project_manager/data.py

Component constants & data schemas.

Filesystem mutation constants (transient-delete policy) and the
project event vocabulary. Pure values only, no logic, no I/O.
"""

from __future__ import annotations

import errno

# Windows reports a directory that is still changing as WinError 5
# (access denied), 32 (file in use) or 145 (directory not empty).
# Those mean "not settled yet", not "you may not do this", so they are
# retried. Anything else is a real refusal and propagates at once.
TRANSIENT_DELETE_WIN_ERRORS = frozenset({5, 32, 145})

TRANSIENT_DELETE_ERRNOS = frozenset({
    errno.ENOTEMPTY,
    errno.EACCES,
    errno.EPERM,
})

#: Attempts before falling back to a manual bottom-up removal.
DELETE_ATTEMPTS = 3

#: Backoff between attempts, in seconds.
DELETE_BACKOFF = 0.05

#: The project event vocabulary published on the shared EventBus.
EVENT_TYPES = {
    "saved",
    "created",
    "renamed",
    "deleted",
    "tree_changed",
}

__all__ = [
    "DELETE_ATTEMPTS",
    "DELETE_BACKOFF",
    "EVENT_TYPES",
    "TRANSIENT_DELETE_ERRNOS",
    "TRANSIENT_DELETE_WIN_ERRORS",
]
