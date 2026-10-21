"""One small log file per LLM: running totals plus the most recent test runs."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "model_logs"
MAX_ENTRIES = 25


def _slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", str(model).lower()).strip("-")[:80] or "unknown-model"


def _path(model: str) -> Path:
    return LOG_DIR / f"{_slug(model)}.json"


def get_log(model: str) -> dict:
    path = _path(model)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"model": model, "runs": 0, "passes": 0, "probe_failures": {}, "entries": []}


def record_run(model: str, title: str, passed: bool, components: list[dict],
               strengths: list[str], weaknesses: list[str], improvements: list[str]) -> dict:
    log = get_log(model)
    log["model"] = model
    log["runs"] += 1
    log["passes"] += 1 if passed else 0
    for component in components:
        for check in component.get("checks", []):
            if not check.get("passed"):
                log["probe_failures"][check["id"]] = log["probe_failures"].get(check["id"], 0) + 1
    log["entries"].append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": title,
        "passed": passed,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    })
    log["entries"] = log["entries"][-MAX_ENTRIES:]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _path(model).write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return log
