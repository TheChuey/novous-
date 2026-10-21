"""Saved test reports (JSON files) so results can be reviewed and learned from later."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "test_reports"
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:40] or "report"


def save_report(kind: str, title: str, model: str, result: dict,
                subject: str = "", notes: str = "") -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    report_id = f"{now.strftime('%Y%m%dT%H%M%S%f')}-{kind}-{_slug(title)}"
    record = {
        "id": report_id,
        "kind": kind,
        "title": title,
        "model": model,
        "created_at": now.isoformat(),
        "passed": bool(result.get("passed")),
        "verdict": result.get("verdict", ""),
        "notes": notes,
        "subject": subject,
        "result": result,
    }
    (REPORTS_DIR / f"{report_id}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def list_reports() -> list[dict]:
    if not REPORTS_DIR.is_dir():
        return []
    summaries = []
    for path in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summaries.append({key: record.get(key) for key in
                          ("id", "kind", "title", "model", "created_at", "passed", "verdict", "notes")})
    return summaries


def get_report(report_id: str) -> dict:
    if not _ID_PATTERN.match(report_id):
        raise ValueError(f"Invalid report id: {report_id!r}")
    path = REPORTS_DIR / f"{report_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Report not found: {report_id}")
    return json.loads(path.read_text(encoding="utf-8"))
