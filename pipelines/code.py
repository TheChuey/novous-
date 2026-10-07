"""pipelines/code.py

File-backed cascade state: reading the default step chain and appending
one JSONL record per run.

    load_pipeline() -> steps from pipeline.json ([] when missing/broken)
    _record_run()   -> one line in data/pipeline_runs.jsonl (fail-safe)
"""

from __future__ import annotations

import json

from .data import CONFIG_FILE, RECORDS_FILE
from .helperfunctions import _iso_now

__all__ = ["load_pipeline", "_record_run"]


def load_pipeline(config_path=None) -> list:
    """Ordered step configs from pipeline.json ([] when missing/broken).

    Missing files return [] so the app degrades gracefully to plain per-agent
    chat instead of crashing on a config problem.
    """
    path = config_path or CONFIG_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("steps") or []


def _record_run(snapshot: dict) -> None:
    """Append one JSONL line per pipeline run. Fail-safe: a recording failure
    never breaks the run itself (same philosophy as the tool log)."""
    record = {
        "time": _iso_now(),
        "request": snapshot.get("request", ""),
        "model": snapshot.get("model"),
        "steps": snapshot.get("steps", []),
        "reply": snapshot.get("reply", ""),
    }
    try:
        target = RECORDS_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # a recording failure never blocks the pipeline
